from fastapi import APIRouter
from fastapi.responses import JSONResponse
import services.apiService as apiService
from config import Config
from services import duckDbService
from services import queriesService

router = APIRouter()


@router.get("/queries/runQuery")
def getServices(id_query: int):
    print("Running query " + str(id_query))
    
    # Get query as a dictionary
    query = queriesService.getQuery(id_query)

    limitedQuery = "SELECT * FROM (" + query["query"] + ") LIMIT 10"

    print("Query:" + str(limitedQuery))

    # Run query
    df = duckDbService.runQuery(limitedQuery)

    if (df is not None):
        result = df.to_dict(orient="records")
        print("Result:" + str(result))
        return JSONResponse(content=result, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)
    

