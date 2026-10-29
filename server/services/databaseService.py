import duckdb
import os
import re
import logging as log
import contextvars
import threading
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
        db_path = os.path.join(user_db_folder, active_db_name)
        log.info(f"Opening database {db_path} for user {username}")
        sandboxed = _sandbox_enabled()
        # Persistent secrets are read from ~/.duckdb, outside the sandbox, and can't be disabled later
        db = duckdb.connect(db_path, config={"allow_persistent_secrets": False} if sandboxed else {})
        _load_extensions_for_db(db)
        if sandboxed:
            try:
                _apply_sandbox(db, username)
            except Exception:
                # Never hand out a connection without its sandbox
                db.close()
                raise
        _connections[username][active_db_name] = db

    return _connections[username][active_db_name]


def _user_lock(username):
    return _user_locks.setdefault(username, threading.RLock())


@contextmanager
def _db_session():
    # Results must be fully read inside the block: DuckDB 2.0 reads them lazily on fetch.
    username = _current_user.get()
    with _user_lock(username):
        yield _ensure_user_db(username)


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
        log.warning(f"Refusing to load local file outside the user's temp folder: {fileName}")
        return False
    runQuery("DROP TABLE IF EXISTS " + tableName)

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
    if fileName.lower().endswith(".csv") or fileName.lower().endswith(".tsv"):
        try:
            runQuery("CREATE TABLE " + tableName + " AS (SELECT * FROM read_csv_auto('" + fileName + "', HEADER=TRUE, SAMPLE_SIZE=1000000))")
        except Exception as e:
            log.error(f"Error reading CSV file: {e}")
    elif fileName.endswith(".parquet") or fileName.lower().endswith(".pq.gz"):
        runQuery("CREATE TABLE " + tableName + " AS (SELECT * FROM read_parquet('" + fileName + "'))")
    elif fileName.lower().endswith(".json"):
        runQuery("CREATE TABLE " + tableName + " AS (SELECT * FROM read_json_auto('" + fileName + "', maximum_object_size=60000000))")
    elif '.' in fileName and fileName.lower().split('.')[1] in ['shp', 'geojson', 'gpkg', 'kml']:
        # spatial is loaded with the connection (INSTALL/LOAD are refused inside the sandbox)
        runQuery("CREATE TABLE " + tableName + " AS (SELECT * FROM ST_Read('" + fileName + "'))")

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
def getDatabaseSchema():
    """Return the visible tables and their ordered columns for SQL completion."""
    with _db_session() as db:
        rows = db.query(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'main'
              AND NOT starts_with(table_name, '__')
              AND NOT starts_with(table_name, 'cube_index_')
            ORDER BY table_name, ordinal_position
            """
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
            db.query("DROP TABLE IF EXISTS " + tableName)
            db.query("CREATE TABLE " + tableName + " AS (SELECT * FROM __dataframe_import)")
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


def retrieve_json(query):
    sql = query.get("sql")
    df = runQuery(sql)
    if df is not None:
        return df.to_dict(orient="records")
    return []
