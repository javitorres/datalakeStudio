from fastapi import APIRouter
from fastapi.responses import JSONResponse
from config import Config
from model.SaveQueryRequestDTO import SaveQueryRequestDTO
from services import duckDbService

router = APIRouter()

@router.post("/queries/saveSqlQuery")
def saveSqlQuery(saveQueryRequestDTO: SaveQueryRequestDTO):
    print("Saving query " + saveQueryRequestDTO.sqlQueryName + ": " + saveQueryRequestDTO.query + " (" + saveQueryRequestDTO.description + ")")
    tableList = duckDbService.getTableList()
    # check if meta data table __queries exists
    if "__queries" not in tableList:
        print("Creating table __queries")
        duckDbService.runQuery("CREATE TABLE __queries (id_query INTEGER PRIMARY KEY, name VARCHAR, query VARCHAR, description VARCHAR);CREATE SEQUENCE seq_id_query START 1;")
    
    # Insert query into __queries table
    duckDbService.runQuery("INSERT INTO __queries (id_query, name, query, description) VALUES (nextval('seq_id_query'), '" + saveQueryRequestDTO.sqlQueryName + "', '" + saveQueryRequestDTO.query + "', '" + saveQueryRequestDTO.description + "')")

####################################################
    
@router.get("/queries/searchQuery")
def searchQuery(query: str):
    print("Searching query " + query)
    result=[]

    # Search query into __queries table lower caase
    df = duckDbService.runQuery("SELECT * FROM __queries WHERE LOWER(name) LIKE '%" + query.lower() + "%' OR LOWER(description) LIKE '%" + query.lower() + "%'")
    
    if (df is not None):
        result = df.to_dict(orient="records")
        print("Result:" + str(result))
        return JSONResponse(content=result, status_code=200)    
    else:
        return JSONResponse(content=[], status_code=200)

####################################################
    
@router.get("/queries/deleteQuery")
def deleteQuery(id_query: int):
    print("Deleting query " + str(id_query))
    result=[]

    # Search query into __queries table lower caase
    df = duckDbService.runQuery("DELETE FROM __queries WHERE id_query = " + str(id_query))
    
    return JSONResponse(content=[], status_code=200)