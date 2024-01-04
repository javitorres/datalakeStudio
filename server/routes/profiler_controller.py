from fastapi import APIRouter
from services import duckDbService
from fastapi import Response
from fastapi.responses import JSONResponse
import services.profilerService as profilerService

router = APIRouter(prefix="/profiler")


@router.get("/getTableProfile")
def getProfile(tableName: str):
    if (tableName is None):
        response = {"status": "error", "message": "tableName is required"}
        return JSONResponse(content=response, status_code=400)
    print("Getting profile for table " + tableName)
    df = duckDbService.runQuery("SELECT * FROM " + tableName)
    if (df is not None):
        profile = profilerService.getProfile(df)
        response = {"status": "ok", "profile": profile}
        return response
    else:
        return {"status": "error"}

