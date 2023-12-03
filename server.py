from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Response
from fastapi.responses import JSONResponse

import services.duckDbService as db
import services.apiService as apiService
#import services.remoteDbService as remoteDbService
import services.s3IndexService as s3Service

import pandas as pd
import yaml

app = FastAPI()

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
        db.init(secrets, self.config)

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
print("Serever port:" + str(serverStatus.config["port"]))




# Load file into duckdb endpoint (get)
@app.get("/loadFile")
def loadFile(fileName: str, tableName: str):
    if (fileName is None or tableName is None):
        response = {"status": "error", "message": "fileName and tableName are required"}
        return JSONResponse(content=response, status_code=400)
    
    print("Loading file '" + fileName + "' into table '" + tableName + "'")
    conf = config.get()
    
    db.loadTable(tableName, fileName)
    df = db.runQuery("SELECT COUNT(*) total FROM " + tableName)
    return {"status": "ok", "rows": df.to_json()}

@app.get("/runQuery")
def runQuery(query: str):
    r = db.runQuery(query)
    if r is not None:
        csv_data = r.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv", status_code=200)
    else:
        return Response(content="Query failed or returned no data", status_code=400)    

@app.get("/s3Search")
def s3Search(bucket: str, fileName: str):
    print("Searching for '" + fileName + "' in bucket '" + bucket + "'")
    if (bucket is None or fileName is None):
        response = {"status": "error", "message": "bucket and fileName are required"}
        return JSONResponse(content=response, status_code=400)
    # If filename size is less than 3, return error
    if (len(fileName) < 3):
        response = {"status": "error", "message": "fileName must be at least 3 characters"}
        return JSONResponse(content=response, status_code=400)

    results = s3Service.s3Search(bucket, fileName)
    # If  results array is greter than 100 items, return first 10
    if (len(results) > 10):
        results = results[:10]
    return {"results": results}
app.mount("/", StaticFiles(directory="client/dist", html=True), name="dist")

if __name__ == "__main__":
    import uvicorn

    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=serverStatus.config["port"])
