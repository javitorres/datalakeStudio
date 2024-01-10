from fastapi import APIRouter
from services import duckDbService
from fastapi import Response
from fastapi.responses import JSONResponse
import services.s3Service as s3Service
from model.Metadata import Metadata

router = APIRouter(prefix="/s3")

############################################################################################################

@router.get("/s3Search")
def s3Search(bucket: str, fileName: str):
    print("Searching for '" + fileName + "' in bucket '" + bucket + "'")
    if (bucket is None or fileName is None):
        response = {"status": "error", "message": "bucket and fileName are required"}
        return JSONResponse(content=response, status_code=400)
    
    results = []
    if (len(fileName) >= 3):
        results = s3Service.s3Search(bucket, fileName)

    # If  results array is greter than 100 items, return first 10
    if (len(results) > 10):
        results = results[:10]
    
    return {"results": results}

############################################################################################################

@router.get("/getContent")
def getContent(bucket: str, path: str):
    print("getContent bucket '" + bucket + "'" + " path '" + path + "'")
    if (bucket is None):
        response = {"status": "error", "message": "bucket is required"}
        return JSONResponse(content=response, status_code=400)
    
    result = {}
    result = s3Service.getContent(bucket, path)
    
    return result

############################################################################################################
@router.get("/getFilePreview")
def getContent(bucket: str, path: str):
    print("getFilePreview bucket '" + bucket + "'" + " path '" + path + "'")
    if (bucket is None):
        response = {"status": "error", "message": "bucket is required"}
        return JSONResponse(content=response, status_code=400)
    
    results = []
    results = s3Service.getFilePreview(bucket, path)
    
    return results

############################################################################################################
@router.post("/updateMetadata")
def updateMetadata(metadata: Metadata):
    print("updateMetadata '" + metadata.bucket + "'" + " path '" + metadata.path + "'" + " metadata '" + str(metadata) + "'")
    if (metadata.bucket is None or metadata.path is None):
        response = {"status": "error", "message": "bucket and path are required"}
        return JSONResponse(content=response, status_code=400)
    
    
    result = s3Service.updateMetadata(metadata)
    
    if result:
        response = {"status": "ok", "message": "metadata updated"}
        return JSONResponse(content=response, status_code=200)
    else:
        response = {"status": "error", "message": "metadata not updated"}
        return JSONResponse(content=response, status_code=400)