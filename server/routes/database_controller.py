import shutil
from fastapi import APIRouter, File, Form, UploadFile
from services import databaseService, fileService
from fastapi import Response, Request
from fastapi.responses import JSONResponse, FileResponse
from model.QueryRequestDTO import QueryRequest
import os
import logging as log
import time

router = APIRouter(prefix="/database")
SLOW_QUERY_THRESHOLD = 5000

# Load file into duckdb endpoint (get)
@router.get("/loadFile")
def loadFile(fileName: str, tableName: str):
    if (fileName is None or tableName is None):
        response = {"status": "error", "message": "fileName and tableName are required"}
        return JSONResponse(content=response, status_code=400)

    log.info(f"Loading file '{fileName}' into table '{tableName}'")
    if databaseService.loadTable(tableName, fileName):
        df = databaseService.runQuery("SELECT COUNT(*) total FROM " + tableName)
        return {"status": "ok", "rows": df.to_json()}
    else:
        return {"status": "error", "rows": 0}

####################################################
@router.get("/getTables")
def getTables():
    tableList = databaseService.getTableList()
    # Remove all metatables starting from "__" from the list
    tableList = [x for x in tableList if not x.startswith("__")]
    tableList = [x for x in tableList if not x.startswith("cube_index_")]

    log.info(f"Tables: {tableList}")

    if (tableList is not None):
        return JSONResponse(content=tableList, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)
####################################################
@router.get("/getTableSchema")
def getTableSchema(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    log.info(f"Getting schema for table {tableName}")
    r = databaseService.runQuery("SELECT * FROM " + tableName + " LIMIT 1")
    # If any field name ends with () remove it
    r.columns = r.columns.str.replace(r"\(\)", "", regex=True)
    if (r is not None):
        schema_dict = r.dtypes.apply(lambda x: str(x)).to_dict()
        return JSONResponse(content=schema_dict, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)
####################################################
@router.get("/getSampleData", response_class=Response)
def getTableData(tableName: str, type: str = "First", records: int = 1000):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    log.info(f"Getting data for table {tableName}")
    if (records==0):
        LIMIT = ""
    else:
        LIMIT = " LIMIT " + str(records)
    df = databaseService.runQuery("SELECT * FROM " + tableName + LIMIT)

    # If any field name ends with () remove it
    df.columns = df.columns.str.replace(r"\(\)", "", regex=True)
    if (df is not None):
        return Response(df.to_csv(index=False, quotechar='"'), media_type="text/csv", status_code=200)
    else:
        return ""

####################################################
@router.post("/runQuery")
def runQuery(queryRequest: QueryRequest):
    log.info(f"POST runQuery {queryRequest}")

    databaseService.runQuery("DROP TABLE IF EXISTS __lastQuery")

    query = queryRequest.query

    query = query.strip()
    if query[-1] == ";":
        query = query[:-1]

    try:
        databaseService.runQuery("CREATE TABLE __lastQuery as ("+ query +")")
    except Exception as e:
        log.error(f"Error running query: {e}")
        response = {"status": "error", "message": "Error running query: " + str(e)}
        return JSONResponse(content=response, status_code=400)

    if (queryRequest.rows==0):
        LIMIT = ""
    else:
        LIMIT = " LIMIT " + str(queryRequest.rows)

    df = databaseService.runQuery("SELECT *  FROM __lastQuery" + LIMIT)

    if df is not None:
        csv_data = df.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv", status_code=200)
    else:
        return Response(content="Query failed or returned no data", status_code=400)
####################################################
@router.get("/getRowCount")
def getRowsCount(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    log.info(f"Getting rows count for table {tableName}")
    df = databaseService.runQuery("SELECT COUNT(*) total FROM " + tableName)
    if (df is not None):
        total = df["total"].values[0]
        return {"status": "ok", "rows": str(total)}
    else:
        return {"status": "error"}

####################################################
@router.get("/createTableFromQuery")
def createTableFromQuery(query: str, tableName: str):
    if (query is None or tableName is None):
        response = {"status": "error", "message": "query and tableName are required"}
        return JSONResponse(content=response, status_code=400)
    log.info(f"Creating table {tableName} from query {query}")
    try:
        databaseService.runQuery("DROP TABLE IF EXISTS "+ tableName )
    except Exception as e:
        log.error(f"Error dropping table: {e}")

    try:
        databaseService.runQuery("CREATE TABLE "+ tableName +" as ("+ query +")")
    except Exception as e:
        log.error(f"Error creating table: {e}")
        response = {"status": "error", "message": "Error creating table: " + str(e)}
        return JSONResponse(content=response, status_code=400)

    return {"status": "ok"}
####################################################
@router.get("/deleteTable")
def deleteTable(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    log.info(f"Deleting table {tableName}")
    databaseService.runQuery("DROP TABLE IF EXISTS "+ tableName )
    return {"status": "ok"}
####################################################
@router.get("/exportData")
def exportData(tableName: str, format: str = "csv", fileName: str = None):
    if fileName is None:
        fileName = databaseService.get_user_temp_folder() + "/" + tableName + "." + format

    if (tableName is None or fileName is None):
        response = {"status": "error", "message": "tableName and fileName are required"}
        return JSONResponse(content=response, status_code=400)
    log.info(f"Exporting data from table {tableName} to file {fileName} in format {format}")
    r = databaseService.exportData(tableName, format, fileName)

    if (r):
        return FileResponse(path=fileName, media_type='application/octet-stream', filename=os.path.basename(fileName))
    else:
        response = {"status": "error", "message": "Export failed"}
        return JSONResponse(content=response, status_code=500)

####################################################
@router.get("/getTableProfile")
def getProfile(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    log.info(f"Getting profile for table {tableName}")
    df = databaseService.getProfile(tableName)
    if (df is not None):
        return Response(df.to_csv(index=False, quotechar='"'), media_type="text/csv", status_code=200)
    else:
        return {"status": "error"}

####################################################
@router.post("/uploadFile")
def uploadFile(file: UploadFile = File(...), tableName: str = Form(None)):
    if (file is None):
        response = {"status": "error", "message": "file is required"}
        return JSONResponse(content=response, status_code=400)

    data_dir = databaseService.get_user_temp_folder()
    dest_file = os.path.join(data_dir, file.filename)
    log.info(f"Uploading file {file.filename} to {dest_file}")
    with open(dest_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    dest_file = os.path.abspath(dest_file)

    if (tableName is None):
        tableName = file.filename.split(".")[0]
    if databaseService.loadTable(tableName, dest_file):
        df = databaseService.runQuery("SELECT COUNT(*) total FROM " + tableName)
        return {"status": "ok", "rows": df.to_json()}
    else:
        return {"status": "error", "rows": 0}
####################################################
@router.get("/getDatabaseList")
def getDatabaseList():
    databaseList = databaseService.getDatabaseList()
    currentDatabase = databaseService.get_current_database_name()
    # Remove current database from the list
    databaseList = [x for x in databaseList if x != currentDatabase]
    databaseList.sort()
    # Put current database at the beginning
    databaseList.insert(0, currentDatabase)

    headers = {"X-Current-Database": currentDatabase}
    if (databaseList is not None):
        return JSONResponse(content=databaseList, status_code=200, headers=headers)
    else:
        return JSONResponse(content=[], status_code=200, headers=headers)

####################################################
@router.get("/changeDatabase")
def changeDatabase(databaseName: str):
    databaseService.changeDatabase(databaseName)
    return {"status": "ok"}

####################################################
@router.get("/createDatabase")
def createDatabase(databaseName: str):
    databaseService.createDatabase(databaseName)
    return {"status": "ok"}

# Based on https://github.com/uwdata/mosaic/blob/main/packages/duckdb-server/README.md
@router.post("/restConnector")
async def handle_query(request: Request):
    query = await request.json()
    log.debug(f"{query=}")

    start = time.time()
    sql = query.get("sql")
    command = query.get("type")

    try:
        if command == "exec":
            databaseService.runQuery(sql)
            response = {"status": "ok"}
        elif command == "arrow":
            buffer = databaseService.retrieve_arrow_bytes(query)
            response = Response(content=buffer, media_type="application/octet-stream")
        elif command == "json":
            json_data = databaseService.retrieve_json(query)
            response = JSONResponse(content=json_data)
        else:
            raise ValueError(f"Unknown command {command}")

    except Exception as e:
        log.exception("Error processing query")
        if command == "arrow":
            response = Response(content=str(e).encode(), media_type="text/plain", status_code=500)
        else:
            response = JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

    total = round((time.time() - start) * 1_000)
    if total > SLOW_QUERY_THRESHOLD:
        log.warning(f"DONE. Slow query took {total} ms: {sql}")
    else:
        log.info(f"DONE. Query took {total} ms: {sql}")

    return response

@router.get("/dropCubes")
def dropCubes():
    tables = databaseService.getTableList()
    for table in tables:
        if table.startswith("cube_index_"):
            log.info(f"Dropping table {table}")
            databaseService.runQuery("DROP TABLE IF EXISTS " + table)
    return {"status": "ok"}
