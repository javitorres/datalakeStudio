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
    ''' Example: 
    SELECT 
  'count' AS statistic,
  COUNT(sepal_length) AS sepal_length,
  COUNT(sepal_width) AS sepal_width,
  COUNT(petal_length) AS petal_length,
  COUNT(petal_width) AS petal_width,
  COUNT(species) AS species
FROM iris
UNION ALL
SELECT 
  'mean' AS statistic,
  AVG(sepal_length) AS sepal_length,
  AVG(sepal_width) AS sepal_width,
  AVG(petal_length) AS petal_length,
  AVG(petal_width) AS petal_width,
  NULL AS species
FROM iris
UNION ALL
SELECT 
  'std' AS statistic,
  STDDEV(sepal_length) AS sepal_length,
  STDDEV(sepal_width) AS sepal_width,
  STDDEV(petal_length) AS petal_length,
  STDDEV(petal_width) AS petal_width,
  NULL AS species
FROM iris
UNION ALL
SELECT 
  'min' AS statistic,
  MIN(sepal_length) AS sepal_length,
  MIN(sepal_width) AS sepal_width,
  MIN(petal_length) AS petal_length,
  MIN(petal_width) AS petal_width,
  MIN(species) AS species
FROM iris
UNION ALL
SELECT 
  'p25' AS statistic,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY sepal_length) AS sepal_length,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY sepal_width) AS sepal_width,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY petal_length) AS petal_length,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY petal_width) AS petal_width,
  NULL AS species
FROM iris
UNION ALL
SELECT 
  'p50' AS statistic,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sepal_length) AS sepal_length,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sepal_width) AS sepal_width,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY petal_length) AS petal_length,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY petal_width) AS petal_width,
  NULL AS species
FROM iris
UNION ALL
SELECT 
  'p75' AS statistic,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY sepal_length) AS sepal_length,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY sepal_width) AS sepal_width,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY petal_length) AS petal_length,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY petal_width) AS petal_width,
  NULL AS species
FROM iris
UNION ALL
SELECT 
  'max' AS statistic,
  MAX(sepal_length) AS sepal_length,
  MAX(sepal_width) AS sepal_width,
  MAX(petal_length) AS petal_length,
  MAX(petal_width) AS petal_width,
  MAX(species) AS species
FROM iris
    
    
    '''

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

def getProfile2222(tableName):
    print("Getting schema for table " + tableName)
    r = runQuery("SELECT * FROM " + tableName + " LIMIT 1")
    if r is None:
        return None

    # Obtiene los tipos de datos de las columnas y los convierte a un diccionario
    schema_dict = r.dtypes.apply(lambda x: str(x)).to_dict()
    print("schema_dict:"  + str(schema_dict))

    numeric_fields = [field for field, dtype in schema_dict.items() if 'float' in dtype or 'int' in dtype]

    statistic_types = ['count', 'mean', 'std', 'min', 'p25', 'p50', 'p75', 'max']
    queries = []

    for statistic in statistic_types:
        query = f"SELECT '{statistic}' AS statistic"

        for field in numeric_fields:
            if statistic in ['count', 'min', 'max']:
                query += f", {statistic.upper()}({field}) AS {field}"
            elif statistic == 'p25':
                query += f", PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {field}) AS {field}"
            elif statistic == 'p50':
                query += f", PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {field}) AS {field}"
            elif statistic == 'p75':
                query += f", PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {field}) AS {field}"
            else:
                query += f", {statistic.upper()}({field}) AS {field}" if field in numeric_fields else ", NULL AS {field}"

        query += f" FROM {tableName}"
        queries.append(query)

    final_query = " UNION ALL ".join(queries)
    print(final_query)
    return runQuery(final_query)