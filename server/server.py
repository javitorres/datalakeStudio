from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import services.duckDbService as duckDbService

from routes import remoteDb_controller
from routes import duckdb_controller
from routes import s3_controller
from routes import chatgpt_controller
from routes import api_controller
from routes import profiler_controller

import yaml

from config import Config

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

class ServerStatus:
    def __init__(self):
        print("Initializing server...")

        # Check if data folder existsin filesistem and create if not
        if (Config.get_instance().get_config.get("database") is not None):
            print("Checking data folder...")
            import os
            if not os.path.exists(Config.get_instance().get_config.get("database")):
                os.makedirs("data")
                print("Data folder created")

        print("Connecting to database..." + Config.get_instance().get_config.get("database"))
        duckDbService.init(Config.get_instance().get_secrets, Config.get_instance().get_config)

        self.serverStatus = {}
        self.serverStatus["databaseReady"] = True
    
    '''def _load_config(self):
        try:
            with open('config.yml', 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {}
            '''

    def get(self):
        return self.serverStatus

serverStatus = ServerStatus()
print("Server initialized")
print("Server port:" + str(Config.get_instance().get_config.get("port")))


# Include routes
app.include_router(duckdb_controller.router)
app.include_router(remoteDb_controller.router)
app.include_router(s3_controller.router)
app.include_router(chatgpt_controller.router)
app.include_router(api_controller.router)
app.include_router(profiler_controller.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.get_instance().get_config.get("port"))