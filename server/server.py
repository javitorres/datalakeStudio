from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Response
from fastapi.responses import FileResponse, JSONResponse

import services.duckDbService as duckDbService
import services.apiService as apiService
import services.remoteDbService as remoteDbService
import services.s3IndexService as s3Service
import services.chatGPTService as chatGPTService
import services.profilerService as profilerService

import yaml

app = FastAPI()
connection = None

origins = [
    "http://localhost:8080",
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Secrets:
    def __init__(self):
        self._load_config()

    def _load_config(self):
        try:
            print("Loading secrets...")
            with open('secrets.yml', 'r') as file:
                self.secrets = yaml.safe_load(file)
        except Exception as e:
            print(f"No secrets.yml file found")
            self.secrets = {}

    def get(self):
        return self.secrets
    

secrets = Secrets().secrets

class ServerStatus:
    def __init__(self, secrets):
        self._load_config()
        print("Initializing server...")

        # Check if data folder existsin filesistem and create if not
        if (self.config["database"] is not None):
            print("Checking data folder...")
            import os
            if not os.path.exists(self.config["database"]):
                os.makedirs("data")
                print("Data folder created")

        print("Connecting to database..." + self.config["database"])
        duckDbService.init(secrets, self.config)

        self.serverStatus = {}
        self.serverStatus["databaseReady"] = True
    
    def _load_config(self):
        try:
            with open('config.yml', 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {}

    def get(self):
        return self.serverStatus

serverStatus = ServerStatus(secrets)
print("Server initialized")
print("Server port:" + str(serverStatus.config["port"]))

# Load file into duckdb endpoint (get)
@app.get("/loadFile")
def loadFile(fileName: str, tableName: str):
    if (fileName is None or tableName is None):
        response = {"status": "error", "message": "fileName and tableName are required"}
        return JSONResponse(content=response, status_code=400)
    
    print("Loading file '" + fileName + "' into table '" + tableName + "'")

    
    duckDbService.loadTable(tableName, fileName)
    df = duckDbService.runQuery("SELECT COUNT(*) total FROM " + tableName)
    return {"status": "ok", "rows": df.to_json()}

@app.get("/getTables")
def getTables():
    tableList = duckDbService.getTableList()
    # Remove __lastQuery table form the list
    tableList = [x for x in tableList if x != "__lastQuery"]
    print("Tables: " + str(tableList))

    if (tableList is not None):
        return JSONResponse(content=tableList, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)

@app.get("/getTableSchema")
def getTableSchema(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Getting schema for table " + tableName)
    r = duckDbService.runQuery("SELECT * FROM " + tableName + " LIMIT 1")
    if (r is not None):
        schema_dict = r.dtypes.apply(lambda x: str(x)).to_dict()
        return JSONResponse(content=schema_dict, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)

@app.get("/getSampleData", response_class=Response)
def getTableData(tableName: str, type: str = "First", records: int = 1000):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Getting data for table " + tableName)
    if (records==0):
        LIMIT = ""
    else:
        LIMIT = " LIMIT " + str(records)
    r = duckDbService.runQuery("SELECT * FROM " + tableName + LIMIT)
    if (r is not None):
        #return JSONResponse(content=r.to_csv(index=False), status_code=200)
        return Response(r.to_csv(index=False, quotechar='"'), media_type="text/csv", status_code=200)
    else:
        return ""

@app.get("/runQuery")
def runQuery(query: str, rows: int = 1000):
    #duckDbService.loadTable("__lastquery", fileName)
    duckDbService.runQuery("DROP TABLE IF EXISTS __lastQuery")
    duckDbService.runQuery("CREATE TABLE __lastQuery as ("+ query +")")
    if (rows==0):
        LIMIT = ""
    else:
        LIMIT = " LIMIT " + str(rows)

    df = duckDbService.runQuery("SELECT *  FROM __lastQuery" + LIMIT)
    #return {"status": "ok", "rows": df.to_json()}

    if df is not None:
        csv_data = df.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv", status_code=200)
    else:
        return Response(content="Query failed or returned no data", status_code=400)   


  
@app.get("/createTableFromQuery")
def createTableFromQuery(query: str, tableName: str):
    if (query is None or tableName is None):
        response = {"status": "error", "message": "query and tableName are required"}
        return JSONResponse(content=response, status_code=400)
    print("Creating table " + tableName + " from query " + query)
    try:
        duckDbService.runQuery("DROP TABLE IF EXISTS "+ tableName )
    except Exception as e:
        print("Error dropping table: " + str(e))
    
    try:
        duckDbService.runQuery("CREATE TABLE "+ tableName +" as ("+ query +")")
    except Exception as e:
        print("Error creating table: " + str(e))
        response = {"status": "error", "message": "Error creating table: " + str(e)}
        return JSONResponse(content=response, status_code=400)
    
    return {"status": "ok"}

@app.get("/deleteTable")
def deleteTable(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Deleting table " + tableName)
    duckDbService.runQuery("DROP TABLE IF EXISTS "+ tableName )
    return {"status": "ok"}

############################################################################################################
# S3
############################################################################################################

@app.get("/s3Search")
def s3Search(bucket: str, fileName: str):
    print("Searching for '" + fileName + "' in bucket '" + bucket + "'")
    if (bucket is None or fileName is None):
        response = {"status": "error", "message": "bucket and fileName are required"}
        return JSONResponse(content=response, status_code=400)
    
    results = []
    if (len(fileName) >= 3):
        results = s3Service.s3Search(bucket, fileName)

    # If  results array is greter than 100 items, return first 10
    if (len(results) > 10):
        results = results[:10]
    
    return {"results": results}

############################################################################################################
# Chat GPT
############################################################################################################

@app.get("/askGPT")
def askGPT(question: str):
    tables = duckDbService.getTableList()

    if (tables is not None and len(tables) > 0):
        questionForChatGPT = " You have the following tables:"
        for table in tables:
            #if (table != "__lastQuery"):
            questionForChatGPT += " " + duckDbService.getTableDescriptionForChatGpt(table)
        questionForChatGPT += ". The query I need is:" + question

        chatGPTResponse = chatGPTService.askGpt(questionForChatGPT, secrets["openai_organization"], secrets["openai_api_key"])
        print("GPT response: " + chatGPTResponse)
    
    return JSONResponse(content=chatGPTResponse, status_code=200)

############################################################################################################
# Remote database queries
############################################################################################################

@app.get("/getDatabaseList")
def getDatabaseList(databaseName: str):
    if (databaseName is None):
        response = {"status": "error", "message": "databaseName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Getting database list for '" + databaseName + "'")
    databaseList = remoteDbService.getDbList(databaseName, secrets["pgpass_file"])
    return JSONResponse(content=databaseList, status_code=200)

@app.get("/connectDatabase")
def connectDatabase(databaseName: str):
    global connection

    if (databaseName is None):
        response = {"status": "error", "message": "databaseName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Connecting to database '" + databaseName + "'")
    connection = remoteDbService.connectDatabase(databaseName, secrets["pgpass_file"])
    
    if (connection is not None):
        schemas = remoteDbService.getSchemas(connection)
        response = {"status": "ok", "schemas": schemas}
        return JSONResponse(content=response, status_code=200)
    else:
        return {"status": "error"}

@app.get("/getSchemas")
def getSchemas():
    global connection

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Getting schemas")
    schemas = remoteDbService.getSchemas(connection)
    return JSONResponse(content=schemas, status_code=200)

@app.get("/getTablesFromRemoteSchema")
def getTablesFromSchema(schema: str):
    global connection

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Getting tables from schema " + schema)
    tables = remoteDbService.getTables(connection, schema)
    response = {"status": "ok", "tables": tables}
    return JSONResponse(content=response, status_code=200)

@app.get("/runRemoteQuery")
def runRemoteQuery(query: str):
    global connection

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Running query " + query)
    df = remoteDbService.runRemoteQuery(connection, query)
    if (df is not None):
        return JSONResponse(content=df.to_csv(index=False), status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)

@app.get("/createTableFromRemoteQuery")
def createTableFromRemoteQuery(query: str, tableName: str):
    global connection

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Creating table " + tableName + " from query " + query)
    df = remoteDbService.runRemoteQuery(connection, query)
    if (df is not None):
        duckDbService.createTableFromDataFrame(df, tableName)
        return {"status": "ok"}
    else:
        return {"status": "error"}

############################################################################################################
# Profiler
############################################################################################################

@app.get("/getTableProfile")
def getProfile(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Getting profile for table " + tableName)
    df = duckDbService.runQuery("SELECT * FROM " + tableName)
    if (df is not None):
        profile = profilerService.getProfile(df)
        response = {"status": "ok", "profile": profile}
        return response
    else:
        return {"status": "error"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=serverStatus.config["port"])
