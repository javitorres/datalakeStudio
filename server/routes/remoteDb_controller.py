from fastapi import APIRouter
from services import duckDbService
from fastapi import Response
from fastapi.responses import JSONResponse
import services.remoteDbService as remoteDbService

from config import Config

router = APIRouter()


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
    global connection

    if (databaseName is None):
        response = {"status": "error", "message": "databaseName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Connecting to database '" + databaseName + "'")
    connection = remoteDbService.connectDatabase(databaseName, Config.get_instance().get_secrets.get("pgpass_file"))
    
    if (connection is not None):
        schemas = remoteDbService.getSchemas(connection)
        response = {"status": "ok", "schemas": schemas}
        return JSONResponse(content=response, status_code=200)
    else:
        return {"status": "error"}

@router.get("/getSchemas")
def getSchemas():
    global connection

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Getting schemas")
    schemas = remoteDbService.getSchemas(connection)
    return JSONResponse(content=schemas, status_code=200)

@router.get("/getTablesFromRemoteSchema")
def getTablesFromSchema(schema: str):
    global connection

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Getting tables from schema " + schema)
    tables = remoteDbService.getTables(connection, schema)
    response = {"status": "ok", "tables": tables}
    return JSONResponse(content=response, status_code=200)

@router.get("/runRemoteQuery")
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

@router.get("/createTableFromRemoteQuery")
def createTableFromRemoteQuery(query: str, tableName: str):
    global connection

    if (connection is None):
        response = {"status": "error", "message": "You must connect to a database first"}
        return JSONResponse(content=response, status_code=400)
    print("Creating table " + tableName + " from query " + query)
    dfRemoteDb = remoteDbService.runRemoteQuery(connection, query)
    if (dfRemoteDb is not None):
        duckDbService.createTableFromDataFrame("dfRemoteDb", tableName)
        return {"status": "ok"}
    else:
        return {"status": "error"}