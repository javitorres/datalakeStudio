from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import Request

from config import Config
from services import duckDbService
from services import apiServerService
from services import queriesService

router = APIRouter(prefix="/api")

@router.api_route("/{path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path: str):
    print("Path: " + path)
    print("Method: " + request.method)

    # GET Parameters
    query_params = request.query_params
    print("Query parameters: ", dict(query_params))

    # POST and PUT body
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.json()
        print("Body: ", body)
    else:
        body = None
    
    df_result = apiServerService.getAndRunEndpoint(path, query_params, body)
    result = df_result.to_dict(orient="records")

    if (result is not None):
        print("Result:" + str(result))
        return JSONResponse(content=result, status_code=200)
    else:
        return JSONResponse(content=[], status_code=200)
    

