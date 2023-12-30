from fastapi import APIRouter
from fastapi.responses import JSONResponse
import services.apiService as apiService
from config import Config
from model.apiEnrichmentRequestDTO import ApiEnrichmentRequestDTO

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

'''
curl 'http://localhost:8000/runApiEnrichment' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: es-ES,es;q=0.9,en;q=0.8' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Origin: http://localhost:8080' \
  -H 'Referer: http://localhost:8080/' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-site' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Linux"' \
  --data-raw '{"tableName":"mini","parameters":{"refCat":"COD_REFCAT"},"mappings":[{"jsonField":"idEspacio","newFieldName":"idEspacio"},{"jsonField":"","newFieldName":""}],"recordsToProcess":10,"service":"ServiceCRMData","method":{"controller":"crm-data-controller","method":"GET","path":"/getDataByRefCat"},"url":"http://ServiceCRMData.pro.madiva.vpn/getDataByRefCat","newTableName":"enrichedTable"}' \
  --compressed
'''

@router.post("/runApiEnrichment")
async def runApiEnrichment(apiEnrichmentRequestDTO: ApiEnrichmentRequestDTO):
    print("Body: " + str(apiEnrichmentRequestDTO))
    apiService.runApiEnrichment(apiEnrichmentRequestDTO, Config.get_instance().get_secrets.get("api_domain"), "pro")
    

    


    return JSONResponse(content="OK", status_code=200)


