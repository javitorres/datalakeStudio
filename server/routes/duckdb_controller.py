from fastapi import APIRouter
from services import duckDbService
from fastapi import Response
from fastapi.responses import JSONResponse, FileResponse

router = APIRouter()

# Load file into duckdb endpoint (get)
@router.get("/loadFile")
def loadFile(fileName: str, tableName: str):
    if (fileName is None or tableName is None):
        response = {"status": "error", "message": "fileName and tableName are required"}
        return JSONResponse(content=response, status_code=400)
    
    print("Loading file '" + fileName + "' into table '" + tableName + "'")

    
    duckDbService.loadTable(tableName, fileName)
    df = duckDbService.runQuery("SELECT COUNT(*) total FROM " + tableName)
    return {"status": "ok", "rows": df.to_json()}

@router.get("/getTables")
def getTables():
    tableList = duckDbService.getTableList()
    # Remove __lastQuery table form the list
    tableList = [x for x in tableList if x != "__lastQuery"]
    print("Tables: " + str(tableList))

    if (tableList is not None):
        return JSONResponse(content=tableList, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)

@router.get("/getTableSchema")
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

@router.get("/getSampleData", response_class=Response)
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

@router.get("/runQuery")
def runQuery(query: str, rows: int = 1000):
    duckDbService.runQuery("DROP TABLE IF EXISTS __lastQuery")
    try:
        duckDbService.runQuery("CREATE TABLE __lastQuery as ("+ query +")")
    except Exception as e:
        print("Error runing query::: " + str(e))
        response = {"status": "error", "message": "Error running query: " + str(e)}
        return JSONResponse(content=response, status_code=400)
    
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

@router.get("/getRowCount")
def getRowsCount(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Getting rows count for table " + tableName)
    df = duckDbService.runQuery("SELECT COUNT(*) total FROM " + tableName)
    if (df is not None):
        print("DF:" + str(df))
        # extract total
        total = df["total"].values[0]
        print("Total:" + str(total))
        return {"status": "ok", "rows": str(total)}
    else:
        return {"status": "error"}

  
@router.get("/createTableFromQuery")
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

@router.get("/deleteTable")
def deleteTable(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Deleting table " + tableName)
    duckDbService.runQuery("DROP TABLE IF EXISTS "+ tableName )
    return {"status": "ok"}

@router.get("/exportData")
def exportData(tableName: str, format: str = "csv", fileName: str = None):
    if fileName is None:
        fileName = "data/" + tableName + "." + format

    if (tableName is None or fileName is None):
        response = {"status": "error", "message": "tableName and fileName are required"}
        return JSONResponse(content=response, status_code=400)
    print("Exporting data from table " + tableName + " to file " + fileName + " in format " + format)
    r = duckDbService.exportData(tableName, format, fileName)

    if (r):
        response = {"status": "ok", "message": "Exported"}
        return FileResponse(path=fileName, media_type='application/octet-stream', filename=fileName)
    else:
        response = {"status": "error", "message": "tableName and fileName are required"}
        return JSONResponse(content=response, status_code=500)
    
    