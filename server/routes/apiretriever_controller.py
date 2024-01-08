from fastapi import APIRouter
from fastapi.responses import JSONResponse
import services.apiRetrieverService as apiRetrieverService
from config import Config
from model.apiEnrichmentRequestDTO import ApiEnrichmentRequestDTO

router = APIRouter(prefix="/apiRetriever")


@router.get("/getServices")
def getServices(serviceName: str = None):
    print("Getting services")
    services = apiRetrieverService.getServices(serviceName)
    return JSONResponse(content=services, status_code=200)

####################################################

@router.get("/getRepositoryMethodList")
def getRepositoryMethodList(serviceName: str, 
                            methodPath: str = "", 
                            environment: str = "pro", 
                            api_domain: str  = None, 
                            api_context: str = None):
    
    if api_domain is None:
        api_domain = Config.get_instance().get_secrets.get("api_domain")
    if api_context is None:
        api_context = Config.get_instance().get_secrets.get("api_context")


    print("Getting method list of repository. serviceName: " + serviceName)
    print("methodName: " + methodPath)
    print("environment: " + environment)
    print("api_domain: " + api_domain)
    print("api_context: " + api_context)

    result = apiRetrieverService.getRepositoryMethodList(serviceName, methodPath, environment, api_domain, api_context)
    return JSONResponse(content=result, status_code=200)

####################################################

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

    result = apiRetrieverService.getMethodInfo(serviceName, methodPath, methodMethod, environment, api_domain, api_context)
    return JSONResponse(content=result, status_code=200)

####################################################

@router.post("/runApiEnrichment")
async def runApiEnrichment(apiEnrichmentRequestDTO: ApiEnrichmentRequestDTO):
    print("Body: " + str(apiEnrichmentRequestDTO))
    apiRetrieverService.runApiEnrichment(apiEnrichmentRequestDTO, Config.get_instance().get_secrets.get("api_domain"), "pro")

    return JSONResponse(content="OK", status_code=200)


