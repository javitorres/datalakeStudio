from fastapi import APIRouter
from fastapi.responses import JSONResponse
from config import Config
from model.SaveQueryRequestDTO import SaveQueryRequestDTO
from services import queriesService

router = APIRouter()

@router.post("/queries/saveSqlQuery")
def saveSqlQuery(saveQueryRequestDTO: SaveQueryRequestDTO):
    queriesService.saveSqlQuery(saveQueryRequestDTO)

####################################################
    
@router.get("/queries/searchQuery")
def searchQuery(query: str):
    df = queriesService.searchQuery(query)
    
    
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

    queriesService.deleteQuery(id_query)
    
    return JSONResponse(content=[], status_code=200)