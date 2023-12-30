from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import remoteDb_controller
from routes import duckdb_controller
from routes import s3_controller
from routes import chatgpt_controller
from routes import api_controller
from routes import profiler_controller

from ServerStatus import ServerStatus

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

serverStatus = ServerStatus()


# Include routes
app.include_router(duckdb_controller.router)
app.include_router(remoteDb_controller.router)
app.include_router(s3_controller.router)
app.include_router(chatgpt_controller.router)
app.include_router(api_controller.router)
app.include_router(profiler_controller.router)

if __name__ == "__main__":
    import uvicorn
    print("Initializing server on port " + str(Config.get_instance().get_config.get("port")) + "...")
    uvicorn.run(app, host="0.0.0.0", port=Config.get_instance().get_config.get("port"))
    
    