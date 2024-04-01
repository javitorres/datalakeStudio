from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes import remoteDb_controller
from routes import database_controller
from routes import s3_controller
from routes import gpt_controller
from routes import apiretriever_controller
from routes import profiler_controller
from routes import queries_controller
from routes import apiserver_controller
from routes import api_controller
import logging as log

from ServerStatus import ServerStatus

from config import Config

app = FastAPI()
connection = None

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

serverStatus = ServerStatus()


# Include routes
app.include_router(database_controller.router)
app.include_router(remoteDb_controller.router)
app.include_router(s3_controller.router)
app.include_router(gpt_controller.router)
app.include_router(apiretriever_controller.router)
app.include_router(profiler_controller.router)
app.include_router(queries_controller.router)
app.include_router(apiserver_controller.router)
app.include_router(api_controller.router)


if __name__ == "__main__":
    format = "%(asctime)s %(filename)s:%(lineno)d - %(message)s "
    log.basicConfig(format=format, level=log.INFO, datefmt="%H:%M:%S")

    log.info("Initializing server on port " + str(Config.get_instance().get_config.get("port")) + "...")
    uvicorn.run(app, host="0.0.0.0", port=Config.get_instance().get_config.get("port"))
    
    
