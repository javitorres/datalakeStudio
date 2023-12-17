import boto3
import requests
import json
import pandas as pd

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

####### NOT TESTED: ###############3    



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
    
def getApi(url):
    try:
        print("Calling API: " + url)
        r = requests.get(url)
        return r
    except Exception as e:
        print("Error calling API: " + str(e))
        return None   
    
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
            

