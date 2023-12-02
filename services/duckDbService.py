import duckdb

configLoaded = False
db = duckdb.connect()

def init(secrets, config):
    global db

    print("Secrets: " + str(secrets))
    print("Config: " + str(config))
    if (config["database"] is not None):
        print("Connecting to database..." + config["database"])
        db = duckdb.connect(config["database"])
    try:
        runQuery("INSTALL httpfs;LOAD httpfs;SET s3_region='eu-west-1';")
        runQuery("SET s3_access_key_id='" + secrets["s3_access_key_id"] + "';SET s3_secret_access_key='" + secrets["s3_secret_access_key"] +"'")
        print("Loaded S3 credentials")
    except Exception as e:
        print("Error loading S3 credentials: " + str(e))
        runQuery("INSTALL httpfs;LOAD httpfs")
        print("No s3 credentials found")
    
    global configLoaded
    configLoaded = True

def loadTable(tableName, fileName):
    global configLoaded
    if (configLoaded == False):
        print("Load config")
        return None

    print("Loading table " + tableName + " from " + fileName)
    duckdb.query("DROP TABLE IF EXISTS "+ tableName )
    
    if (fileName.endswith(".csv") or fileName.endswith(".tsv")):
        duckdb.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_csv_auto('" + fileName + "', HEADER=TRUE, SAMPLE_SIZE=1000000))")
    elif (fileName.endswith(".parquet") or fileName.endswith(".pq.gz")):
        duckdb.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_parquet('" + fileName + "'))")
    elif (fileName.endswith(".json")):
        duckdb.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_json_auto('" + fileName + "', maximum_object_size=60000000))")
    #ses["loadedTables"][tableName] = fileName
    r = duckdb.sql('SHOW TABLES')
    if (r is not None):
        r.show()
    else:
        print("duckDbService: No tables loaded")

def runQuery(query):
    try:
        print("Executing query: " + query)
        r = duckdb.query(query)
        if (r is not None):
            return r.df()
    except Exception as e:
        print("Error running query: " + str(e))
        return None
    
'''
METODOS NO PROBADOS AUN
'''    

def getTableDescriptionForChatGpt(tableName):
    fields = duckdb.query("DESCRIBE "+ tableName).df()
    tableDescription = ""
    for field in fields.iterrows():
        tableDescription += "," + field[1]["column_name"] + " (" + field[1]["column_type"] + ")"
    tableDescriptionForGPT = "One of the tables is called '"+ tableName +"' and has following fields:" + tableDescription[1:]
    return tableDescriptionForGPT

def getTableDescription(tableName):
    if (tableName is None):
        return []
    try:
        fields = duckdb.query("DESCRIBE "+ tableName).df()
        tableDescription = ""
        for field in fields.iterrows():
            tableDescription += "," + field[1]["column_name"] + " (" + field[1]["column_type"] + ")"

        columns = fields["column_name"].tolist()
        types = fields["column_type"].tolist()
        
        return columns
    except Exception as e:
        print("Error getting table description: " + str(e))
        return []


        
    
def dropAllTables():
    tableList = runQuery("SHOW TABLES")
    tableListArray = None
    if (tableList is not None):
        tableListArray = tableList["name"].to_list()
        for table in tableListArray:
            runQuery("DROP TABLE IF EXISTS "+ table )

def getTableList():
    tableList = runQuery("SHOW TABLES")
    tableListArray = None
    if (tableList is not None):
        tableListArray = tableList["name"].to_list()
    return tableListArray

def saveDfAsTable(dfName, tableName):
    print("Saving df as table " + tableName)
    duckdb.sql("CREATE TABLE "+ tableName +" AS SELECT * FROM " + dfName)