import duckdb
import os
import logging as log
import contextvars
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


def _get_user_db_folder(username=None):
    if username is None:
        username = _current_user.get()
    return os.path.join(_config["databasesFolder"], username)


def get_user_temp_folder(username=None):
    if username is None:
        username = _current_user.get()
    folder = os.path.join(_config["downloadFolder"], username)
    os.makedirs(folder, exist_ok=True)
    return folder


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
        db = duckdb.connect(db_path, config={"allow_unsigned_extensions": "true"})
        _connections[username][active_db_name] = db
        _load_extensions_for_db(db)

    return _connections[username][active_db_name]


def get_db():
    return _ensure_user_db()


def _load_extensions_for_db(db):
    try:
        db.query("INSTALL httpfs;LOAD httpfs;SET s3_region='eu-west-1';")
        db.query("INSTALL spatial;LOAD spatial;")
        if _secrets and _secrets.get("s3_access_key_id"):
            db.query("SET s3_access_key_id='" + _secrets["s3_access_key_id"] + "';SET s3_secret_access_key='" + _secrets["s3_secret_access_key"] + "'")
            log.info("Loaded S3 credentials")
        else:
            db.query("INSTALL aws;LOAD aws")
            db.query("CALL load_aws_credentials();")
    except Exception as e:
        log.warning(f"Could not load S3/httpfs extensions: {e}")
        try:
            db.query("INSTALL httpfs;LOAD httpfs")
            db.query("INSTALL spatial;LOAD spatial;")
            db.query("INSTALL aws;LOAD aws")
            db.query("CALL load_aws_credentials();")
        except Exception as e2:
            log.warning(f"Could not load extensions (fallback): {e2}")
    try:
        db.query("INSTALL h3 FROM community;LOAD h3;")
        log.info("Loaded H3 extension")
    except Exception as e:
        log.warning(f"Could not load H3 extension: {e}")


####################################################
def loadTable(tableName, fileName):
    db = get_db()
    data_dir = get_user_temp_folder()

    format_list = ['csv', 'tsv', 'parquet', 'gz', 'json', 'geojson', 'gpkg', 'kml', 'shp']
    log.info(f"Loading table {tableName} from {fileName}")
    db.query("DROP TABLE IF EXISTS " + tableName)

    extracted_files = []
    if fileName.endswith('.zip'):
        extracted_data_file = None
        with ZipFile(fileName, 'r') as zip:
            for info in zip.infolist():
                zip.extract(info, data_dir)
                extracted_files.append(os.path.join(data_dir, info.filename))
                if '.' in info.filename and info.filename.split('.')[-1] in format_list:
                    extracted_data_file = info.filename
        os.remove(fileName)
        if extracted_data_file:
            fileName = os.path.join(data_dir, extracted_data_file)

    log.info(f"File to be integrated: {fileName}")
    if fileName.lower().endswith(".csv") or fileName.lower().endswith(".tsv"):
        try:
            db.query("CREATE TABLE " + tableName + " AS (SELECT * FROM read_csv_auto('" + fileName + "', HEADER=TRUE, SAMPLE_SIZE=1000000))")
        except Exception as e:
            log.error(f"Error reading CSV file: {e}")
    elif fileName.endswith(".parquet") or fileName.lower().endswith(".pq.gz"):
        db.query("CREATE TABLE " + tableName + " AS (SELECT * FROM read_parquet('" + fileName + "'))")
    elif fileName.lower().endswith(".json"):
        db.query("CREATE TABLE " + tableName + " AS (SELECT * FROM read_json_auto('" + fileName + "', maximum_object_size=60000000))")
    elif '.' in fileName and fileName.lower().split('.')[1] in ['shp', 'geojson', 'gpkg', 'kml']:
        db.query("INSTALL spatial;LOAD spatial;CREATE TABLE " + tableName + " AS (SELECT * FROM ST_Read('" + fileName + "'))")

    if (not fileName.lower().startswith("s3") and not fileName.lower().startswith("http")):
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

    r = db.query('SHOW TABLES')
    if tableName in r.df()["name"].to_list():
        r.show()
        return True
    else:
        log.warning(f"Table {tableName} not loaded: {r}")
        return False


####################################################
def runQuery(query, logQuery=True, format="df"):
    db = get_db()
    try:
        if logQuery:
            log.info(f"Executing query: {query}")
        r = db.query(query)
        if r is not None:
            if format == "arrow":
                return r.arrow()
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
def getTableDescriptionForChatGpt(tableName):
    db = get_db()
    fields = db.query("DESCRIBE " + tableName).df()
    tableDescription = ""
    for field in fields.iterrows():
        tableDescription += "," + field[1]["column_name"] + " (" + field[1]["column_type"] + ")"
    tableDescriptionForGPT = "One of the tables is called '" + tableName + "' and has following fields:" + tableDescription[1:]
    return tableDescriptionForGPT


####################################################
def createTableFromDataFrame(df, tableName):
    db = get_db()
    log.info(f"Creating table {tableName}")
    db.query("DROP TABLE IF EXISTS " + tableName)
    db.query("CREATE TABLE " + tableName + " AS (SELECT * FROM " + df + ")")


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
    db = get_db()
    query = "SELECT 'count' AS statistic"
    fields = db.query("DESCRIBE " + tableName).df()
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

    # Close current connection if exists
    if username in _connections and _active_db.get(username) in _connections[username]:
        old_db_name = _active_db[username]
        _connections[username][old_db_name].close()
        del _connections[username][old_db_name]

    db_name = databaseName + ".db" if not databaseName.endswith(".db") else databaseName
    _active_db[username] = db_name

    # This will open the new connection
    _ensure_user_db(username)
    return True


def createDatabase(databaseName):
    username = _current_user.get()
    user_db_folder = _get_user_db_folder(username)
    os.makedirs(user_db_folder, exist_ok=True)
    db_path = os.path.join(user_db_folder, databaseName)
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
