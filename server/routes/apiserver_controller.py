from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import services.apiRetrieverService as apiRetrieverService
from config import Config
from services import databaseService
from services import apiServerService
from services import queriesService

from model.PublishEndpointRequestDTO import PublishEndpointRequestDTO


router = APIRouter(prefix="/apiserver")

@router.get("/runQuery")
def getServices(id_query: int):
    print("Running query " + str(id_query))
    
    # Get query as a dictionary
    query = queriesService.getQuery(id_query)

    limitedQuery = "SELECT * FROM (" + query["query"] + ") LIMIT 10"

    print("Query:" + str(limitedQuery))

    # Run query
    df = databaseService.runQuery(limitedQuery)

    if (df is not None):
        result = df.to_dict(orient="records")
        print("Result:" + str(result))
        return JSONResponse(content=result, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)
    
####################################################
@router.get("/create")
def create():


    print("Creating empty endpoint")
    id_endpoint = apiServerService.createEndpoint()

    if (id is not None):
        result = {"id_endpoint" : id_endpoint}
        print("Result:" + str(result))
        return JSONResponse(content=result, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)




####################################################

@router.post("/update")
def publish( publishEndpointRequestDTO: PublishEndpointRequestDTO ):
    print("Updating query " + str(publishEndpointRequestDTO))
    apiServerService.update(publishEndpointRequestDTO)

    if (True):
        result = "ok"
        print("Result:" + str(result))
        return JSONResponse(content=result, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)
    
####################################################
@router.get("/listEndpoints")
def listEndpoints():
    print("Getting available endpoints")
    endpoints = apiServerService.listEndpoints()

    if (endpoints is not None):
        print("Result:" + str(endpoints))
        return JSONResponse(content=endpoints, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)
####################################################
@router.get("/deleteEndpoint")
def deleteEndpoint(id_endpoint: int):
    print("Deleting endpoint " + str(id_endpoint))

    result = apiServerService.deleteEndpoint(id_endpoint)

    if (result):
        print("Result:" + str(result))
        return JSONResponse(content=result, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)