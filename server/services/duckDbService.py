import duckdb

configLoaded = False
db = None

def init(secrets, config):
    global db

    if (config["database"] is not None):
        print("Connecting to database..." + config["database"])
        db = duckdb.connect(config["database"])
    else:
        print("Connecting to in-memory database")
        db = duckdb.connect(':memory:')

    try:
        runQuery("INSTALL httpfs;LOAD httpfs;SET s3_region='eu-west-1';")
        runQuery("SET s3_access_key_id='" + secrets["s3_access_key_id"] + "';SET s3_secret_access_key='" + secrets["s3_secret_access_key"] +"'", False)
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
    db.query("DROP TABLE IF EXISTS "+ tableName )
    
    if (fileName.endswith(".csv") or fileName.endswith(".tsv")):
        db.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_csv_auto('" + fileName + "', HEADER=TRUE, SAMPLE_SIZE=1000000))")
    elif (fileName.endswith(".parquet") or fileName.endswith(".pq.gz")):
        db.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_parquet('" + fileName + "'))")
    elif (fileName.endswith(".json")):
        ss = db.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM read_json_auto('" + fileName + "', maximum_object_size=60000000))")

    r = db.sql('SHOW TABLES')
    if (r is not None):
        r.show()
    else:
        print("duckDbService: No tables loaded")

def runQuery(query, logQuery=True):
    try:
        if (logQuery):
            print("Executing query: " + query)
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

def getTableList():
    tableList = runQuery("SHOW TABLES")
    tableListArray = None
    if (tableList is not None):
        tableListArray = tableList["name"].to_list()
    return tableListArray

def getTableDescriptionForChatGpt(tableName):
    fields = db.query("DESCRIBE "+ tableName).df()
    tableDescription = ""
    for field in fields.iterrows():
        tableDescription += "," + field[1]["column_name"] + " (" + field[1]["column_type"] + ")"
    tableDescriptionForGPT = "One of the tables is called '"+ tableName +"' and has following fields:" + tableDescription[1:]
    return tableDescriptionForGPT
    
def createTableFromDataFrame(df, tableName):
    print("Creating table " + tableName)
    db.query("DROP TABLE IF EXISTS "+ tableName )
    #db.register("df", df)
    db.query("CREATE TABLE "+ tableName +" AS (SELECT * FROM df)")
    #db.deregister("df")

'''
METODOS NO PROBADOS AUN
'''    



def getTableDescription(tableName):
    if (tableName is None):
        return []
    try:
        fields = db.query("DESCRIBE "+ tableName).df()
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



def saveDfAsTable(dfName, tableName):
    print("Saving df as table " + tableName)
    duckdb.sql("CREATE TABLE "+ tableName +" AS SELECT * FROM " + dfName)