from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from fastapi import Request

from config import Config
from services import databaseService
from services import apiServerService
from services import queriesService
import json

router = APIRouter(prefix="/api")

@router.api_route("/{path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path: str):
    print("Path: " + path)
    print("Method: " + request.method)

    # if path ends with /
    if (path.endswith("/")):
        openapi_dict = apiServerService.getApiDefinition(path)
        # openapi_dict to json
        # openapi_json = json.dumps(openapi_dict)
        return JSONResponse(content=openapi_dict, status_code=200)
    else:
        # GET Parameters
        query_params = request.query_params

        format = "JSON"
        print("Query parameters: ", dict(query_params))
        if (query_params is not None):
            query_params = dict(query_params)
            # get param format (CSV or JSON)
            format = query_params.get("format")
            if (format is not None):
                format = format.upper()
                if (format == "CSV"):
                    query_params.pop("format")
                else:
                    format = "JSON"
            
                

        # POST and PUT body
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.json()
            print("Body: ", body)
        else:
            body = None
        
        try:
            df_result = apiServerService.getAndRunEndpoint(path, query_params, body)
        except Exception as e:
            print("Error running endpoint:" + str(e))
            return JSONResponse(content={"error": str(e)}, status_code=400)


        

        if (df_result is not None):
            if (format == "CSV"):
                #return JSONResponse(content=result, status_code=200)
                csv_data = df_result.to_csv(index=False)
                return Response(content=csv_data, media_type="text/csv", status_code=200)
            else:
                result = df_result.to_dict(orient="records")
                #print("Result:" + str(result))
                return JSONResponse(content=result, status_code=200)
        else:
            return JSONResponse(content=[], status_code=200)
    

