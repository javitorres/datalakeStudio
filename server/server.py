from fastapi import FastAPI, Depends
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
from routes import maps_controller
from routes import auth_controller

import logging as log

from ServerStatus import ServerStatus
from config import Config
from auth import get_current_user
from middleware.cors_middleware import DualCORSMiddleware

app = FastAPI()

allowed_origins = Config.get_instance().get_config.get("allowedOrigins", ["*"])
app.add_middleware(DualCORSMiddleware, allowed_origins=allowed_origins)

serverStatus = ServerStatus()

# Auth dependency for protected routes
auth_dep = [Depends(get_current_user)]

# Public routes (no auth required)
app.include_router(auth_controller.router)

# Protected routes (auth required)
app.include_router(database_controller.router, dependencies=auth_dep)
app.include_router(remoteDb_controller.router, dependencies=auth_dep)
app.include_router(s3_controller.router, dependencies=auth_dep)
app.include_router(gpt_controller.router, dependencies=auth_dep)
app.include_router(apiretriever_controller.router, dependencies=auth_dep)
app.include_router(profiler_controller.router, dependencies=auth_dep)
app.include_router(queries_controller.router, dependencies=auth_dep)
app.include_router(apiserver_controller.router, dependencies=auth_dep)
app.include_router(api_controller.router, dependencies=auth_dep)
app.include_router(maps_controller.router, dependencies=auth_dep)


if __name__ == "__main__":
    format = "%(asctime)s %(filename)s:%(lineno)d - %(message)s "
    log.basicConfig(format=format, level=log.INFO, datefmt="%H:%M:%S")

    log.info("Initializing server on port " + str(Config.get_instance().get_config.get("port")) + "...")
    uvicorn.run(app, host="0.0.0.0", port=Config.get_instance().get_config.get("port"))
