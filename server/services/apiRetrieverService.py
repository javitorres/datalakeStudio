import boto3
import requests
import json
import pandas as pd

from model.apiEnrichmentRequestDTO import ApiEnrichmentRequestDTO

from services import duckDbService

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/codecommit.html
client = None
try:
    client = boto3.client('codecommit')
except Exception as e:
    print("Error connecting to AWS: " + str(e))

class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

######################################################################
def getServices(serviceName = None):
    if (client is None):
        print("If you want to connect to your AWS Codecommit account you have to configure your AWS credentials in secrets.toml file")
        return []
    print("Getting services")
    if (serviceName is not None):
        return [repo['repositoryName'] for repo in client.list_repositories()['repositories'] if serviceName.lower() in repo['repositoryName'].lower()]
    else:
        return [repo['repositoryName'] for repo in client.list_repositories()['repositories']]

######################################################################
def getDefinition(repositoryName, environment, api_domain, context):
    url = "http://" + repositoryName + "." + environment + "." + api_domain + "/" + context + "/swagger/doc"
    print("Getting method list of repository " + repositoryName + ":" + url)
    swaggerJson = requests.get(url)
    print("Status code: " + str(swaggerJson.status_code))
    if (swaggerJson.status_code != 200):
        print("Error getting swagger definition from path /swagger/doc, trying with /v3/api-docs")
        url = "http://" + repositoryName + "." + environment + "." + api_domain + "/v3/api-docs"
        print("Getting method list of repository " + repositoryName + ":" + url)
        swaggerJson = requests.get(url)
        data=json.loads(swaggerJson.content)
        return data
    data=json.loads(swaggerJson.content)
    return data
######################################################################
# Return dataframe with methods in a service 
def getRepositoryMethodList(repositoryName, methodName, environment, api_domain, context):
    data = getDefinition(repositoryName, environment, api_domain, context)
    # Check if swagger definition has property "openapi": "3.0.1" or swagger: "2.0"
    if ('openapi' in data):
        print("Swagger 3.0")
        result = []
        for path, methods in data["paths"].items():
            if (methodName is not None and methodName.lower() in path.lower()):
                for method, details in methods.items():
                    if "tags" in details and details["tags"]:
                        result.append({
                            "controller": details["tags"][0],
                            "method": method.upper(),
                            "path": path
                        })
        return result
    else:
        print("Swagger 2.0")
        paths = data['paths']
        result = []
        for path, methods in data["paths"].items():
            if methodName is None or methodName.lower() in path.lower():
                for method, details in methods.items():
                    if "tags" in details and details["tags"]:
                        result.append({
                            "controller": details["tags"][0],
                            "method": method.upper(),
                            "path": path
                        })
        return result
######################################################################
def getMethodInfo(serviceName, methodPath, methodMethod, environment, api_domain, context):
    
    try:
        data = getDefinition(serviceName, environment, api_domain, context)
        if ('openapi' in data):
            print("Swagger 3.0")
            paths = data['paths']
            print("methodPath: " + methodPath)
            print("methodMethod: " + methodMethod)
            print("paths: " + str(paths))
            methodInfo = paths[methodPath]
            print("methodInfo: " + str(methodInfo))
            result = {}
            result['summary'] = methodInfo[methodMethod.lower()]['responses']['200']['description']
            result['parameters'] = methodInfo[methodMethod.lower()]['parameters']
            result['responses'] = methodInfo[methodMethod.lower()]['responses']
            if (methodMethod.lower()=="get"):
                result['method'] = "GET"
            else:
                result['method'] = "POST"
            
            
            result['origin'] = "SWAGGER"
            result['url'] = "http://" + serviceName + "." + environment + "." + api_domain + methodPath
        else:
            print("Swagger 2.0")
            paths = data['paths']
            methodInfo = paths[methodPath]
            result = {}
            result['summary'] = methodInfo[methodMethod.lower()]['summary']
            result['parameters'] = methodInfo[methodMethod.lower()]['parameters']
            result['responses'] = methodInfo[methodMethod.lower()]['responses']
            if (methodMethod=="get"):
                result['method'] = "GET"
            else:
                result['method'] = "POST"
            
            result['origin'] = "SWAGGER"
            result['url'] = "http://" + serviceName + "." + environment + "." + api_domain + methodPath
        return result
    except Exception as e:
        print("Error getting method info: " + str(e))
        return None
######################################################################    
def getApi(url):
    try:
        print("Calling API: " + url)
        r = requests.get(url)
        return r
    except Exception as e:
        print("Error calling API: " + str(e))
        return None   
######################################################################
def postApi(url, body):
    try:
        print("Calling API: " + url + " with body: " + str(body))
        r = requests.post(url, json=json.loads(body))
        r.raise_for_status()
        print("Response:" + str(r))
        return r
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print ("Something went wrong", err)
    except Exception as e:
        print("Error calling API: " + str(e))
    return None    

####### NOT TESTED: ###############
'''
def getDescription(param):
    if ( 'description' in param and param["description"] is not None):
        return str(param["description"])

def getApiAsDf(url):
    try:
        print("Calling API: " + url)
        df = pd.read_json(url)
        return df
    except Exception as e:
        st.write("Error calling API: " + str(e))
        return None
    

    
def getMethodInfoFromExample(url):
    result = {}
    if (url.find("?") > 0):
        urlParts = url.split("?")
        queryParams = urlParts[1]
        queryParamsList = queryParams.split("&")
        queryParamsDict = {}
        for param in queryParamsList:
            paramParts = param.split("=")
            queryParamsDict[paramParts[0]] = paramParts[1]

        if (queryParamsDict is not None):
            print("Query params: " + str(queryParamsDict))
            result['method'] = "GET"
            result['summary'] = "No summary available"
            result['parameters'] = [{'name': k} for k in queryParamsDict.keys()]
            result['origin'] = "EXAMPLE"
            result['url'] = urlParts[0]
            return result
    else:
        result['method'] = "POST"
        result['summary'] = "No summary available"
        result['origin'] = "EXAMPLE"
        result['url'] = url
        return result
'''

        
def runApiEnrichment(apiEnrichmentRequestDTO: ApiEnrichmentRequestDTO , api_domain, environment):
    print("ApiEnrichmentRequestDTO: " + str(apiEnrichmentRequestDTO))

    query = "SELECT * FROM " + apiEnrichmentRequestDTO.tableName
    if (apiEnrichmentRequestDTO.recordsToProcess is not None and apiEnrichmentRequestDTO.recordsToProcess != ""):
        query = "SELECT * FROM " + apiEnrichmentRequestDTO.tableName + " LIMIT " + str(apiEnrichmentRequestDTO.recordsToProcess)
    print("Query: " + query)
    
    dfNew = duckDbService.runQuery(query)
    
    if (dfNew is not None):
        # For each row in the table
        for index, row in dfNew.iterrows():
            queryString=""
            if (apiEnrichmentRequestDTO.method is not None and apiEnrichmentRequestDTO.parameters is not None):
                for param in apiEnrichmentRequestDTO.parameters.items():
                    # if param value is not none:
                    if (param[1] is not None and param[1] != ""):
                        queryString += param[0] + "=" + str(row[param[1]]) + "&"

            if(apiEnrichmentRequestDTO.method.method=="GET"):
                #url = "http://" + ses["service"] + "." + environment + "." + st.secrets["api_domain"] + ses["method"] + "?" + queryString
                url = apiEnrichmentRequestDTO.url + "?" + queryString
                r = getApi(url)
            elif(apiEnrichmentRequestDTO.method.method=="POST"):
                #if (apiEnrichmentRequestDTO.method == "SWAGGER"):
                url = "http://" + apiEnrichmentRequestDTO.service + "." + environment + "." + api_domain + apiEnrichmentRequestDTO.method
                #elif (apiEnrichmentRequestDTO.method == "EXAMPLE"):
                #    url = apiEnrichmentRequestDTO.manualApiUrl
                
                bodyTemplate = apiEnrichmentRequestDTO.jsonBody
                for col in dfFields:
                    bodyTemplate = bodyTemplate.replace("${"+col+"}", str(row[col]))

                r = postApi(url, bodyTemplate)
                if (r is not None):
                    if (r.status_code != 200):
                        print("Error calling API: " + str(r.status_code))
                    else:
                        jsonString = json.dumps(r.json(), indent=4)

            percent_complete = int((index+1) / len(dfNew) * 100)
            #my_bar.progress(percent_complete, text="Processing file..." + str(percent_complete) + "%" + " (" + str(index+1) + "/" + str(len(dfNew)) + ")")
            
        
            if (r is not None):
                if (apiEnrichmentRequestDTO.mappings is not None):
                    for mapping in apiEnrichmentRequestDTO.mappings:
                        if (mapping.jsonField is not None and mapping.jsonField != ""):
                            try:
                                dfNew.loc[index, mapping.newFieldName] = str(r.json()[mapping.jsonField])
                            except Exception as e:
                                print("Error getting field " + mapping.jsonField + " from json: " + str(e))
                            
                        else:
                            dfNew.loc[index, mapping.newFieldName] = str(r.json())
                else:
                    dfNew.loc[index, "RESPONSE"] = str(r.json())
                dfNew.loc[index, "RESPONSE_STATUS"] = str(r.status_code)
                
    # Create table with the dataframe dfNew
    print("Creating table " + apiEnrichmentRequestDTO.newTableName + "...")
    duckDbService.createTableFromDataFrame("dfNew", apiEnrichmentRequestDTO.newTableName)
    return dfNew
