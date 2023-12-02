from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi import Response

import services.duckDbService as db
import services.apiService as apiService
import services.remoteDbService as remoteDbService
import services.s3IndexService as s3Service

import pandas as pd
import yaml

app = FastAPI()

class Config:
    def __init__(self):
        self._load_config()

    def _load_config(self):
        try:
            with open('secrets.yml', 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {}

    def get(self):
        return self.config

config = Config()


# Load file into duckdb endpoint (get)
@app.get("/loadFile")
def loadFile(fileName: str, tableName: str):
    conf = config.get()
    db.init(conf)
    db.loadTable(tableName, fileName)
    df = db.runQuery("SELECT COUNT(*) total FROM " + tableName)
    return {"status": "ok", "rows": df.to_json()}

@app.get("/runQuery")
def loadFile(query: str):
    r = db.runQuery(query)
    if r is not None:
        csv_data = r.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv", status_code=200)
    else:
        return Response(content="Query failed or returned no data", status_code=400)    

# Method to search for files in S3 (get)
@app.get("/s3Search")
def s3Search(bucket: str, fileName: str):
    results = s3Service.s3Search(bucket, fileName)
    return {"results": results}

app.mount("/", StaticFiles(directory="client/dist", html=True), name="dist")

if __name__ == "__main__":
    import uvicorn

    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
