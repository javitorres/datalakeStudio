from fastapi import APIRouter
from services import databaseService
from fastapi import Response
from fastapi.responses import JSONResponse
import services.remoteDbService as remoteDbService

from config import Config

router = APIRouter(prefix="/remotedb")

# Per-user remote database connections
_remote_connections = {}

def _get_connection():
    username = databaseService.get_current_user()
    return _remote_connections.get(username)

def _set_connection(conn):
    username = databaseService.get_current_user()
    _remote_connections[username] = conn


@router.get("/getDatabaseList")
def getDatabaseList(databaseName: str):
    if (databaseName is None):
        response = {"status": "error", "message": "databaseName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Getting database list for '" + databaseName + "'")
    databaseList = remoteDbService.getDbList(databaseName, Config.get_instance().get_secrets.get("pgpass_file"))
    return JSONResponse(content=databaseList, status_code=200)

@router.get("/connectDatabase")
def connectDatabase(databaseName: str):
    if (databaseName is None):
        response = {"status": "error", "message": "databaseName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Connecting to database '" + databaseName + "'")
    try:
        connection = remoteDbService.connectDatabase(databaseName, Config.get_instance().get_secrets.get("pgpass_file"))
    except Exception as e:
        _set_connection(None)
        response = {"status": "error", "message": "Could not connect to " + databaseName + ": " + str(e)}
        return JSONResponse(content=response, status_code=502)
    _set_connection(connection)

    if (connection is not None):
        schemas = remoteDbService.getSchemas(connection)
        response = {"status": "ok", "schemas": schemas}
        return JSONResponse(content=response, status_code=200)
    else:
        response = {"status": "error", "message": "Database not found in the pgpass file: " + databaseName}
        return JSONResponse(content=response, status_code=404)

@router.get("/getSchemas")
def getSchemas():
    connection = _get_connection()

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Getting schemas")
    schemas = remoteDbService.getSchemas(connection)
    return JSONResponse(content=schemas, status_code=200)

@router.get("/getTablesFromRemoteSchema")
def getTablesFromSchema(schema: str):
    connection = _get_connection()

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Getting tables from schema " + schema)
    tables = remoteDbService.getTables(connection, schema)
    response = {"status": "ok", "tables": tables}
    return JSONResponse(content=response, status_code=200)

@router.get("/runRemoteQuery")
def runRemoteQuery(query: str):
    connection = _get_connection()

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Running query " + query)
    try:
        df = remoteDbService.runRemoteQuery(connection, query)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)
    return JSONResponse(content=df.to_csv(index=False), status_code=200)

@router.get("/createTableFromRemoteQuery")
def createTableFromRemoteQuery(query: str, tableName: str):
    connection = _get_connection()

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Creating table " + tableName + " from query " + query)
    try:
        dfRemoteDb = remoteDbService.runRemoteQuery(connection, query)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)
    databaseService.createTableFromDataFrame(dfRemoteDb, tableName)
    return {"status": "ok"}
