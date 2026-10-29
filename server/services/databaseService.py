import duckdb
import os
import re
import logging as log
import contextvars
import threading
import time
from contextlib import contextmanager
from zipfile import ZipFile
from pathlib import Path
from hashlib import sha256

import pyarrow as pa

import ujson

# Context variable for current user (set per-request by auth middleware)
_current_user = contextvars.ContextVar('current_user', default=None)

# Per-user state: {username: {db_name: duckdb_connection}}
_connections = {}
# Per-user active database name: {username: "datalakeStudio.db"}
_active_db = {}
# Per-user lock. A DuckDB connection can't be used by two threads at once (DuckDB 2.0 raises
# ResourceInUseException), so the request threads of a user take turns on its connection.
_user_locks = {}
# Last use of each open database, to close the idle ones: {(username, db_name): time.monotonic()}
_last_used = {}
# SQL of the last query of each user and database, to recreate __lastQuery when it is reopened
_last_query = {}
# Units in DuckDB's memory sizes ("3.1 GiB")
_SIZE_UNITS = {"bytes": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12,
               "KiB": 2**10, "MiB": 2**20, "GiB": 2**30, "TiB": 2**40}

# Database file names: letters, digits, "_" and "-", plus the ".db" suffix
_DATABASE_NAME = re.compile(r"[\w-]+")
# Folders with the CA bundle that httpfs needs for https/S3 inside the sandbox
_CA_CERT_DIRS = ["/etc/ssl/certs/", "/etc/pki/tls/certs/"]

_config = None
_secrets = None

BUNDLE_DIR = Path(".mosaic/bundle")

format = "%(asctime)s %(filename)s:%(lineno)d - %(message)s "
log.basicConfig(format=format, level=log.INFO, datefmt="%H:%M:%S")


def init(secrets, config):
    global _config, _secrets
    _config = config
    _secrets = secrets
    os.makedirs(config.get("downloadFolder", "temp"), exist_ok=True)
    os.makedirs(config.get("databasesFolder", "data"), exist_ok=True)
    threading.Thread(target=_close_idle_connections_periodically, daemon=True).start()


def set_current_user(username):
    _current_user.set(username)


def get_current_user():
    return _current_user.get()


def _check_path_component(name, what):
    # User and database names become folder/file names, so they can't contain path syntax
    if not name or name in (".", "..") or any(c in name for c in "/\\\0"):
        raise ValueError(f"Invalid {what}: {name!r}")
    return name


def _database_file_name(databaseName):
    name = databaseName.strip()
    if name.endswith(".db"):
        name = name[:-3]
    if not _DATABASE_NAME.fullmatch(name):
        raise ValueError(f"Invalid database name '{databaseName}'. Use letters, numbers, '_' and '-'.")
    return name + ".db"


def _is_inside(path, folder):
    path, folder = os.path.realpath(path), os.path.realpath(folder)
    return os.path.commonpath([path, folder]) == folder


def _get_user_db_folder(username=None):
    if username is None:
        username = _current_user.get()
    return os.path.join(_config["databasesFolder"], _check_path_component(username, "user name"))


def get_user_temp_folder(username=None):
    if username is None:
        username = _current_user.get()
    folder = os.path.join(_config["downloadFolder"], _check_path_component(username, "user name"))
    os.makedirs(folder, exist_ok=True)
    return folder


def _sandbox_enabled():
    # On by default when several users share the server (authEnabled); sandboxEnabled overrides it
    return _config.get("sandboxEnabled", _config.get("authEnabled", True))


def _max_open_databases():
    return _config.get("duckdbMaxOpenDatabases", 8)


def _shared_memory_limit():
    # DuckDB's default budget (80% of the RAM it can see, container limits included) split among
    # the databases that can be open at once, so together they can't exhaust the machine
    try:
        with duckdb.connect() as con:
            amount, unit = con.execute("SELECT current_setting('memory_limit')").fetchone()[0].split()
        return f"{int(float(amount) * _SIZE_UNITS[unit] / _max_open_databases() / 2**20)}MiB"
    except Exception as e:
        log.warning(f"Could not split DuckDB's memory limit, using its default: {e}")
        return None


def _duckdb_config(sandboxed):
    # Each open database is a DuckDB instance with its own memory budget and threads. They are set
    # when connecting: the sandbox locks the configuration afterwards.
    config = {}
    if sandboxed:
        # Persistent secrets are read from ~/.duckdb, outside the sandbox, and can't be disabled later
        config["allow_persistent_secrets"] = False
    memory_limit = _config.get("duckdbMemoryLimit")
    if memory_limit is None and _config.get("authEnabled", True):
        memory_limit = _shared_memory_limit()
    if memory_limit:
        config["memory_limit"] = memory_limit
    if _config.get("duckdbThreads"):
        config["threads"] = _config["duckdbThreads"]
    return config


def _apply_sandbox(db, username):
    # The user's SQL only reaches their own folders, the CA bundle and the allowed remote prefixes,
    # and the configuration is locked so SQL can't lift these limits.
    allowed = [os.path.abspath(_get_user_db_folder(username)) + os.sep,
               os.path.abspath(get_user_temp_folder(username)) + os.sep,
               *_CA_CERT_DIRS,
               *_config.get("sandboxAllowedPrefixes", ["https://", "s3://"])]
    db.query("SET allowed_directories = [" + ", ".join("'" + p.replace("'", "''") + "'" for p in allowed) + "]")
    db.query("SET enable_external_access = false")
    db.query("SET lock_configuration = true")


def _ensure_user_db(username=None):
    if username is None:
        username = _current_user.get()
    if username is None:
        raise Exception("No user context set")

    user_db_folder = _get_user_db_folder(username)
    os.makedirs(user_db_folder, exist_ok=True)

    if username not in _connections:
        _connections[username] = {}

    if username not in _active_db:
        default_db = _config.get("defaultDatabase", "datalakeStudio.db")
        _active_db[username] = default_db

    active_db_name = _active_db[username]

    if active_db_name not in _connections[username]:
        _close_idle_connections(keep_user=username, make_room=True)
        db_path = os.path.join(user_db_folder, active_db_name)
        log.info(f"Opening database {db_path} for user {username}")
        sandboxed = _sandbox_enabled()
        db = duckdb.connect(db_path, config=_duckdb_config(sandboxed))
        _load_extensions_for_db(db)
        if sandboxed:
            try:
                _apply_sandbox(db, username)
            except Exception:
                # Never hand out a connection without its sandbox
                db.close()
                raise
        if (username, active_db_name) in _last_query:
            try:
                # The last result was a temporary table, gone with the previous connection
                db.query("CREATE OR REPLACE TEMP VIEW __lastQuery AS " + _last_query[(username, active_db_name)])
            except Exception as e:
                log.warning(f"Could not recreate __lastQuery: {e}")
        _connections[username][active_db_name] = db
        _last_used[(username, active_db_name)] = time.monotonic()

    return _connections[username][active_db_name]


def _user_lock(username):
    return _user_locks.setdefault(username, threading.RLock())


@contextmanager
def _db_session():
    # Results must be fully read inside the block: DuckDB 2.0 reads them lazily on fetch.
    username = _current_user.get()
    with _user_lock(username):
        db = _ensure_user_db(username)
        try:
            yield db
        finally:
            # Idle time counts from the end of the last use
            _last_used[(username, _active_db[username])] = time.monotonic()


def _close_idle_connections(keep_user=None, make_room=False):
    """Close the databases idle for longer than duckdbIdleMinutes and, while more than
    duckdbMaxOpenDatabases are open, the least recently used ones. A database in use is never closed:
    its user's lock is busy. The next request of that user opens it again."""
    idle_seconds = _config.get("duckdbIdleMinutes", 30) * 60
    by_age = sorted(_last_used.items(), key=lambda item: item[1])
    excess = len(by_age) + (1 if make_room else 0) - _max_open_databases()
    now = time.monotonic()
    for (username, db_name), last_used in by_age:
        if username == keep_user or (excess <= 0 and now - last_used < idle_seconds):
            continue
        lock = _user_lock(username)
        if not lock.acquire(blocking=False):
            continue
        try:
            db = _connections.get(username, {}).pop(db_name, None)
            _last_used.pop((username, db_name), None)
            if db is not None:
                db.close()
                log.info(f"Closed database {db_name} of user {username} ({'too many open' if excess > 0 else 'idle'})")
            excess -= 1
        finally:
            lock.release()


def _close_idle_connections_periodically():
    while True:
        time.sleep(60)
        try:
            _close_idle_connections()
        except Exception:
            log.exception("Error closing idle databases")


def _load_extensions_for_db(db):
    try:
        db.query("INSTALL httpfs;LOAD httpfs;SET s3_region='eu-west-1';")
        db.query("INSTALL spatial;LOAD spatial;")
        db.query("INSTALL aws;LOAD aws;")
    except Exception as e:
        log.warning(f"Could not load httpfs/spatial/aws extensions: {e}")
    # S3 credentials go into a secret: load_aws_credentials() was removed in DuckDB 2.0, and an
    # explicit secret takes precedence over the default credential chain the aws extension registers.
    try:
        if _secrets and _secrets.get("s3_access_key_id"):
            key_id = _secrets["s3_access_key_id"].replace("'", "''")
            secret = _secrets["s3_secret_access_key"].replace("'", "''")
            db.query("CREATE OR REPLACE SECRET datalake_s3 (TYPE s3, KEY_ID '" + key_id + "', SECRET '" + secret + "', REGION 'eu-west-1')")
            log.info("Loaded S3 credentials")
        else:
            db.query("CREATE OR REPLACE SECRET datalake_s3 (TYPE s3, PROVIDER credential_chain, REGION 'eu-west-1')")
            log.info("Loaded S3 credentials from the AWS credential chain")
    except Exception as e:
        log.warning(f"Could not configure S3 credentials: {e}")
    try:
        db.query("INSTALL h3 FROM community;LOAD h3;")
        log.info("Loaded H3 extension")
    except Exception as e:
        log.warning(f"Could not load H3 extension: {e}")


####################################################
def loadTable(tableName, fileName):
    data_dir = get_user_temp_folder()

    format_list = ['csv', 'tsv', 'parquet', 'gz', 'json', 'geojson', 'gpkg', 'kml', 'shp']
    log.info(f"Loading table {tableName} from {fileName}")
    is_url = re.match(r"[a-z][a-z0-9+.-]*://", fileName, re.IGNORECASE) is not None
    if not is_url and _sandbox_enabled() and not _is_inside(fileName, data_dir):
        raise ValueError("Local files can only be loaded from your upload folder: " + fileName)

    extracted_files = []
    if fileName.endswith('.zip'):
        extracted_data_file = None
        with ZipFile(fileName, 'r') as zip:
            for info in zip.infolist():
                zip.extract(info, data_dir)
                extracted_files.append(os.path.join(data_dir, info.filename))
                if '.' in info.filename and info.filename.split('.')[-1] in format_list:
                    extracted_data_file = info.filename
        if _is_inside(fileName, data_dir):
            os.remove(fileName)
        if extracted_data_file:
            fileName = os.path.join(data_dir, extracted_data_file)

    log.info(f"File to be integrated: {fileName}")
    # Errors reach the caller, so the user sees why a file didn't load. CREATE OR REPLACE keeps the
    # previous table if the new file fails.
    try:
        # DuckDB reads gzip-compressed CSV and JSON directly
        if fileName.lower().endswith((".csv", ".tsv", ".csv.gz", ".tsv.gz")):
            runQuery("CREATE OR REPLACE TABLE " + tableName + " AS (SELECT * FROM read_csv_auto('" + fileName + "', HEADER=TRUE, SAMPLE_SIZE=1000000))")
        elif fileName.lower().endswith((".parquet", ".pq.gz")):
            runQuery("CREATE OR REPLACE TABLE " + tableName + " AS (SELECT * FROM read_parquet('" + fileName + "'))")
        elif fileName.lower().endswith((".json", ".json.gz")):
            runQuery("CREATE OR REPLACE TABLE " + tableName + " AS (SELECT * FROM read_json_auto('" + fileName + "', maximum_object_size=60000000))")
        elif fileName.lower().endswith((".shp", ".geojson", ".gpkg", ".kml")):
            # spatial is loaded with the connection (INSTALL/LOAD are refused inside the sandbox)
            runQuery("CREATE OR REPLACE TABLE " + tableName + " AS (SELECT * FROM ST_Read('" + fileName + "'))")
        else:
            raise ValueError("Unsupported file type: " + os.path.basename(fileName))
    finally:
        # Only uploads and extracted files are temporary: never delete a file outside the user's temp folder
        if _is_inside(fileName, data_dir):
            log.info(f"Removing file {fileName}")
            try:
                os.remove(fileName)
            except Exception:
                pass
            for f in extracted_files:
                try:
                    os.remove(f)
                except Exception:
                    pass

    tables = runQuery('SHOW TABLES')["name"].to_list()
    if tableName in tables:
        return True
    else:
        log.warning(f"Table {tableName} not loaded: {tables}")
        return False


####################################################
def runQuery(query, logQuery=True, format="df", params=None):
    try:
        if logQuery:
            log.info(f"Executing query: {query}")
        with _db_session() as db:
            r = db.query(query, params=params)
            if r is not None:
                if format == "arrow":
                    return r.to_arrow_table()
                else:
                    return r.df()
    except Exception as e:
        if logQuery:
            log.error(f"Error running query: {e}")
        else:
            log.error("Error running query XXXXXXX")
        raise e


####################################################
def runUserQuery(sql, rows=1000):
    """Run a script from the SQL panel and keep the result of its last statement as __lastQuery.

    The result is a temporary table, so it isn't written into the user's database file. Queries are
    stored with CREATE TABLE AS; other statements (PRAGMA, EXPLAIN, INSERT, SET...) are run and what
    they return is stored instead. Returns the first rows of the result (all of them with rows=0).
    """
    username = _current_user.get()
    with _db_session() as db:
        key = (username, _active_db[username])
        statements = db.extract_statements(sql)
        if not statements:
            raise ValueError("The query is empty")
        *setup, last = statements
        last_query = last.query
        if any(not statement.query.strip() for statement in statements):
            # DuckDB 1.5 splits PIVOT into pieces that can't run on their own: run the script as a whole
            setup, last_query = [], sql
        for statement in setup:
            db.query(statement.query)
        # __lastQuery used to be a table in the database file
        catalog = db.query("SELECT current_database()").fetchall()[0][0]
        db.query('DROP TABLE IF EXISTS "' + catalog.replace('"', '""') + '".main.__lastQuery')
        try:
            db.query("CREATE OR REPLACE TEMP TABLE __lastQueryData AS " + last_query)
            _last_query[key] = last_query
        except duckdb.ParserException:
            # Not a query, or a syntax error that running the statement reports as it is
            output = db.execute(last_query).df()
            db.register("__statement_output", output)
            try:
                db.query("CREATE OR REPLACE TEMP TABLE __lastQueryData AS SELECT * FROM __statement_output")
            finally:
                db.unregister("__statement_output")
            _last_query.pop(key, None)
        db.query("CREATE OR REPLACE TEMP VIEW __lastQuery AS SELECT * FROM __lastQueryData")
        return db.query("SELECT * FROM __lastQuery" + (" LIMIT " + str(int(rows)) if rows else "")).df()


####################################################
def getTableList(hideMeta: bool = True):
    tableList = runQuery("SHOW TABLES")
    tableListArray = None
    if tableList is not None:
        if hideMeta:
            tableList = tableList[tableList["name"] != "__lastQuery"]
            tableList = tableList[tableList["name"] != "__queries"]
        tableListArray = tableList["name"].to_list()
    return tableListArray


####################################################
def getDatabaseSchema(include_hidden=False):
    """Return the visible tables and their ordered columns for SQL completion (with include_hidden,
    also the app's own tables, such as __lastQuery)."""
    with _db_session() as db:
        rows = db.query(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'main'
              AND (? OR (NOT starts_with(table_name, '__') AND NOT starts_with(table_name, 'cube_index_')))
            ORDER BY table_name, ordinal_position
            """,
            params=[include_hidden]
        ).fetchall()

    schema = {}
    for table_name, column_name, data_type in rows:
        schema.setdefault(table_name, {})[column_name] = data_type
    return schema


####################################################
def getTableDescriptionForChatGpt(tableName):
    fields = runQuery("DESCRIBE " + tableName)
    tableDescription = ""
    for field in fields.iterrows():
        tableDescription += "," + field[1]["column_name"] + " (" + field[1]["column_type"] + ")"
    tableDescriptionForGPT = "One of the tables is called '" + tableName + "' and has following fields:" + tableDescription[1:]
    return tableDescriptionForGPT


####################################################
def createTableFromDataFrame(df, tableName):
    log.info(f"Creating table {tableName}")
    with _db_session() as db:
        # Since DuckDB 1.1 a DataFrame is no longer found by its variable name in the caller's
        # frame, so it is registered explicitly.
        db.register("__dataframe_import", df)
        try:
            db.query("CREATE OR REPLACE TABLE " + tableName + " AS (SELECT * FROM __dataframe_import)")
        finally:
            db.unregister("__dataframe_import")


####################################################
def exportData(tableName, format, fileName):
    if format == "csv":
        runQuery("COPY (SELECT * FROM " + tableName + ") TO '" + fileName + "' (FORMAT CSV, HEADER)")
        return True
    elif format == "parquet":
        runQuery("COPY (SELECT * FROM " + tableName + ") TO '" + fileName + "' (FORMAT PARQUET)")
        return True
    else:
        log.warning(f"Format not supported: {format}")
        return False


####################################################
def getProfile(tableName):
    query = "SELECT 'count' AS statistic"
    fields = runQuery("DESCRIBE " + tableName)
    log.info(f"fields: {fields}")

    for field in fields.iterrows():
        if field[1]["column_type"] in ["BIGINT", "DOUBLE"]:
            query += ",COUNT(" + field[1]["column_name"] + ") AS " + field[1]["column_name"]
    query += " FROM " + tableName
    query += " UNION ALL SELECT 'mean' AS statistic"
    for field in fields.iterrows():
        if field[1]["column_type"] in ["BIGINT", "DOUBLE"]:
            query += ",AVG(" + field[1]["column_name"] + ") AS " + field[1]["column_name"]
    query += " FROM " + tableName
    query += " UNION ALL SELECT 'std' AS statistic"
    for field in fields.iterrows():
        if field[1]["column_type"] in ["BIGINT", "DOUBLE"]:
            query += ",STDDEV(" + field[1]["column_name"] + ") AS " + field[1]["column_name"]
    query += " FROM " + tableName
    query += " UNION ALL SELECT 'min' AS statistic"
    for field in fields.iterrows():
        if field[1]["column_type"] in ["BIGINT", "DOUBLE"]:
            query += ",MIN(" + field[1]["column_name"] + ") AS " + field[1]["column_name"]
    query += " FROM " + tableName
    query += " UNION ALL SELECT 'p25' AS statistic"
    for field in fields.iterrows():
        if field[1]["column_type"] in ["BIGINT", "DOUBLE"]:
            query += ",PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY " + field[1]["column_name"] + ") AS " + field[1]["column_name"]
    query += " FROM " + tableName
    query += " UNION ALL SELECT 'p50' AS statistic"
    for field in fields.iterrows():
        if field[1]["column_type"] in ["BIGINT", "DOUBLE"]:
            query += ",PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY " + field[1]["column_name"] + ") AS " + field[1]["column_name"]
    query += " FROM " + tableName
    query += " UNION ALL SELECT 'p75' AS statistic"
    for field in fields.iterrows():
        if field[1]["column_type"] in ["BIGINT", "DOUBLE"]:
            query += ",PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY " + field[1]["column_name"] + ") AS " + field[1]["column_name"]
    query += " FROM " + tableName
    query += " UNION ALL SELECT 'max' AS statistic"
    for field in fields.iterrows():
        if field[1]["column_type"] in ["BIGINT", "DOUBLE"]:
            query += ",MAX(" + field[1]["column_name"] + ") AS " + field[1]["column_name"]
    query += " FROM " + tableName

    log.info(query)
    return runQuery(query)


####################################################
def getDatabaseList():
    username = _current_user.get()
    user_db_folder = _get_user_db_folder(username)
    os.makedirs(user_db_folder, exist_ok=True)
    files = os.listdir(user_db_folder)
    dbFiles = []
    for file in files:
        if file.endswith(".db"):
            dbFiles.append(file[:-3])
    return dbFiles


def get_current_database_name():
    username = _current_user.get()
    if username in _active_db:
        db_name = _active_db[username]
    else:
        db_name = _config.get("defaultDatabase", "datalakeStudio.db")
    if db_name.endswith(".db"):
        return db_name[:-3]
    return db_name


def changeDatabase(databaseName):
    username = _current_user.get()
    log.info(f"Changing database to {databaseName} for user {username}")
    db_name = _database_file_name(databaseName)

    # Wait for the user's running queries before closing their connection
    with _user_lock(username):
        # Close current connection if exists
        if username in _connections and _active_db.get(username) in _connections[username]:
            old_db_name = _active_db[username]
            _connections[username][old_db_name].close()
            del _connections[username][old_db_name]
            _last_used.pop((username, old_db_name), None)

        _active_db[username] = db_name

        # This will open the new connection
        _ensure_user_db(username)
    return True


def createDatabase(databaseName):
    username = _current_user.get()
    user_db_folder = _get_user_db_folder(username)
    os.makedirs(user_db_folder, exist_ok=True)
    db_path = os.path.join(user_db_folder, _database_file_name(databaseName))
    log.info(f"Creating database {db_path} for user {username}")
    temp_conn = duckdb.connect(db_path)
    temp_conn.close()
    return True


############################################
def retrieve_arrow_bytes(query):
    sql = query.get("sql")
    result = get_arrow_bytes(sql)
    return result

def get_arrow(sql):
    result = runQuery(sql, True, "arrow")
    return result

def arrow_to_bytes(arrow):
    sink = pa.BufferOutputStream()

    if isinstance(arrow, pa.RecordBatchReader):
        with pa.ipc.new_stream(sink, arrow.schema) as writer:
            for batch in arrow:
                writer.write_batch(batch)
        return sink.getvalue().to_pybytes()

    with pa.ipc.new_stream(sink, arrow.schema) as writer:
        if isinstance(arrow, pa.Table):
            writer.write_table(arrow)
        elif isinstance(arrow, pa.RecordBatch):
            writer.write_batch(arrow)
        else:
            raise ValueError(f"Unsupported Arrow payload type: {type(arrow)}")

    return sink.getvalue().to_pybytes()

def get_arrow_bytes(sql):
    return arrow_to_bytes(get_arrow(sql))


def to_json_records(df):
    # NULL and infinite values become null and dates ISO strings: pandas' NaN and Timestamps are not
    # valid in a JSON response
    return ujson.loads(df.to_json(orient="records", date_format="iso", default_handler=str, double_precision=15))


def retrieve_json(query):
    sql = query.get("sql")
    df = runQuery(sql)
    if df is not None:
        return to_json_records(df)
    return []
