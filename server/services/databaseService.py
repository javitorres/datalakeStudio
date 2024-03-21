import duckdb
import os
import logging as log

configLoaded = False
db = None

format = "%(asctime)s %(filename)s:%(lineno)d - %(message)s "
log.basicConfig(format=format, level=log.INFO, datefmt="%H:%M:%S")

def init(secrets, config):
    global db
    #Check if config["databasesFolder"] folder exists. If not create it
    if not os.path.exists(config["databasesFolder"]):
        os.makedirs(config["databasesFolder"])
        print("Created folder " + config["databasesFolder"])


    if (config["databasesFolder"] is not None and config["defaultDatabase"] is not None):
        print("Connecting to database..." + config["defaultDatabase"])
        db = duckdb.connect(config["databasesFolder"] + "/" + config["defaultDatabase"])
    else:
        print("Connecting to in-memory database")
        db = duckdb.connect(':memory:')

    try:
        runQuery("INSTALL httpfs;LOAD httpfs;SET s3_region='eu-west-1';")
        runQuery("INSTALL spatial;LOAD spatial;")
        runQuery("SET s3_access_key_id='" + secrets["s3_access_key_id"] + "';SET s3_secret_access_key='" + secrets["s3_secret_access_key"] +"'", False)
        print("Loaded S3 credentials")
    except Exception as e:
        print("Could not load S3 credentials from secrets.yml file")
        runQuery("INSTALL httpfs;LOAD httpfs")
        runQuery("INSTALL spatial;LOAD spatial;")
        runQuery("INSTALL aws;LOAD aws")
        runQuery("CALL load_aws_credentials();")
    
    global configLoaded
    configLoaded = True

####################################################
def loadTable(tableName, fileName):
    global configLoaded
    if (configLoaded == False):
        print("Load config")
        return None

    print("Loading table " + tableName + " from " + fileName)
    db.query("DROP TABLE IF EXISTS "+ tableName )
    
    if (fileName.lower().endswith(".csv") or fileName.lower().endswith(".tsv")):
        db.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_csv_auto('" + fileName + "', HEADER=TRUE, SAMPLE_SIZE=1000000))")
    elif (fileName.endswith(".parquet") or fileName.lower().endswith(".pq.gz")):
        db.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_parquet('" + fileName + "'))")
    elif (fileName.lower().endswith(".json")):
        db.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_json_auto('" + fileName + "', maximum_object_size=60000000))")
    elif (fileName.lower().endswith(".shp") or fileName.lower().endswith(".shx")):
        # https://duckdb.org/2023/04/28/spatial.html
        db.query("INSTALL spatial;LOAD spatial;CREATE TABLE "+ tableName +" AS (SELECT * FROM ST_Read('" + fileName + "'))")

    r = db.sql('SHOW TABLES')
    if (r is not None):
        r.show()
    else:
        print("duckDbService: No tables loaded")
####################################################
def runQuery(query, logQuery=True):
    

    try:
        if (logQuery):
            print("Executing query: " + str(query))
        else:
            print("Executing query XXXXXXX")
        

        r = db.query(query)
        if (r is not None):
            return r.df()
    except Exception as e:
        if (logQuery):
            print("Error running query: " + str(e))
        else:
            print("Error running query XXXXXXX")
        # Raise exception to be handled by caller
        raise e
####################################################
def getTableList(hideMeta: bool = True):
    tableList = runQuery("SHOW TABLES")
    tableListArray = None
    if (tableList is not None):
        if (hideMeta):
            # Remove __lastQuery table form the list
            tableList = tableList[tableList["name"] != "__lastQuery"]
            tableList = tableList[tableList["name"] != "__queries"]
        tableListArray = tableList["name"].to_list()
    return tableListArray
####################################################
def getTableDescriptionForChatGpt(tableName):
    fields = db.query("DESCRIBE "+ tableName).df()
    tableDescription = ""
    for field in fields.iterrows():
        tableDescription += "," + field[1]["column_name"] + " (" + field[1]["column_type"] + ")"
    tableDescriptionForGPT = "One of the tables is called '"+ tableName +"' and has following fields:" + tableDescription[1:]
    return tableDescriptionForGPT
####################################################    
def createTableFromDataFrame(df, tableName):
    print("Creating table " + tableName)
    db.query("DROP TABLE IF EXISTS "+ tableName )
    db.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM "+ df +")")
####################################################

def exportData(tableName, format, fileName):
    if (format == "csv"):
        runQuery("COPY (SELECT * FROM "+ tableName +") TO '"+ fileName +"' (FORMAT CSV, HEADER)")
        return True
    elif (format == "parquet"):
        runQuery("COPY (SELECT * FROM "+ tableName +") TO '"+ fileName +"' (FORMAT PARQUET)")
        return True
    else:
        print("Format not supported")
        return False
    
####################################################

def getProfile(tableName):

    query = "SELECT 'count' AS statistic"
    fields = db.query("DESCRIBE "+ tableName).df()
    print("fields:"  + str(fields))
    
    # Only BIGINT and DOUBLE
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

    print(query)
    return runQuery(query)

####################################################

def getDatabaseList(config):
    # Return list of database files (*.db) in config["databasesFolder"]
    files = os.listdir(config["databasesFolder"])
    dbFiles = []
    for file in files:
        if file.endswith(".db"):
            # Remove file extension .db
            file = file[:-3]
            dbFiles.append(file)
    return dbFiles


def changeDatabase(config, databaseName):
    global db
    log.info("Changing database to " + databaseName)
    db.close()
    db = duckdb.connect(config["databasesFolder"] + "/" + databaseName + ".db")
    return True




def createDatabase(config, databaseName):
    log.info("Creating database " + databaseName)
    duckdb.connect(config["databasesFolder"] + "/" + databaseName)
    return True

