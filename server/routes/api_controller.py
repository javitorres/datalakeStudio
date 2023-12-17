from fastapi import APIRouter
from fastapi import Response
from fastapi.responses import JSONResponse
import services.apiService as apiService

from config import Config

router = APIRouter()


@router.get("/getServices")
def getServices(serviceName: str = None):
    print("Getting services")
    services = apiService.getServices(serviceName)
    return JSONResponse(content=services, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=serverStatus.config["port"])

@router.get("/getRepositoryMethodList")
def getRepositoryMethodList(serviceName: str, 
                            methodPath: str = "", 
                            environment: str = "pro", 
                            api_domain: str  = None, 
                            api_context: str = None):
    print("XXXXXXXXXXXXXX")
    if api_domain is None:
        api_domain = Config.get_instance().get_secrets.get("api_domain")
    if api_context is None:
        api_context = Config.get_instance().get_secrets.get("api_context")


    print("Getting method list of repository. serviceName: " + serviceName)
    print("methodName: " + methodPath)
    print("environment: " + environment)
    print("api_domain: " + api_domain)
    print("api_context: " + api_context)

    result = apiService.getRepositoryMethodList(serviceName, methodPath, environment, api_domain, api_context)
    return JSONResponse(content=result, status_code=200)

@router.get("/getMethodInfo")
def getMethodInfo(serviceName: str, 
                  methodPath: str, 
                  methodMethod: str,
                  environment: str = "pro", 
                  api_domain: str  = None, 
                  api_context: str = None):
    if api_domain is None:
        api_domain = Config.get_instance().get_secrets.get("api_domain")
    if api_context is None:
        api_context = Config.get_instance().get_secrets.get("api_context")

    result = apiService.getMethodInfo(serviceName, methodPath, methodMethod, environment, api_domain, api_context)
    return JSONResponse(content=result, status_code=200)