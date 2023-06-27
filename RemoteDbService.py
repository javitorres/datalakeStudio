import boto3
import requests
import json
import pandas as pd

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/codecommit.html
client = boto3.client('codecommit')

class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

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
        print("Status code: " + str(swaggerJson.status_code))
        data=json.loads(swaggerJson.content)
        return data
    data=json.loads(swaggerJson.content)
    return data

def getRepositories(repositoryName = None):
    print("Getting repositories")
    if (repositoryName is not None):
        return [repo['repositoryName'] for repo in client.list_repositories()['repositories'] if repositoryName.lower() in repo['repositoryName'].lower()]
    else:
        return [repo['repositoryName'] for repo in client.list_repositories()['repositories']]
    
# Return dataframe with methods in a service 
def getRepositoryMethodList(repositoryName, methodName, environment, api_domain, context):
    data = getDefinition(repositoryName, environment, api_domain, context)
    # Check if swagger definition has property "openapi": "3.0.1" or swagger: "2.0"
    if ('openapi' in data):
        print("Swagger 3.0")
        paths = data['paths']
        resultList=[]
        for path, methods in paths.items():
            if (methodName is not None):
                if (methodName.lower() in path.lower()):
                    for method, info in methods.items():
                        resultList.append(path)
            else:
                for method, info in methods.items():
                    resultList.append(path)
        df = pd.DataFrame(resultList)
        return df
    else:
        print("Swagger 2.0")
        paths = data['paths']
        resultList=[]
        for path, methods in paths.items():
            if (methodName is not None):
                if (methodName.lower() in path.lower()):
                    resultList.append(path)
            else:
                resultList.append(path)
        df = pd.DataFrame(resultList)
        return df


def getMethodInfo(serviceName, methodName, environment, api_domain, context):
    try:
        data = getDefinition(serviceName, environment, api_domain, context)
        if ('openapi' in data):
            print("Swagger 3.0")
            paths = data['paths']
            methodInfo = paths[methodName]
            result = {}
            result['summary'] = methodInfo['get']['responses']['200']['description']
            result['parameters'] = methodInfo['get']['parameters']
            result['responses'] = methodInfo['get']['responses']
            result['method'] = "GET"
            result['origin'] = "SWAGGER"
            result['url'] = "http://" + serviceName + "." + environment + "." + api_domain + methodName
        else:
            print("Swagger 2.0")
            paths = data['paths']
            methodInfo = paths[methodName]
            result = {}
            result['summary'] = methodInfo['get']['summary']
            result['parameters'] = methodInfo['get']['parameters']
            result['responses'] = methodInfo['get']['responses']
            result['method'] = "GET"
            result['origin'] = "SWAGGER"
            result['url'] = "http://" + serviceName + "." + environment + "." + api_domain + methodName
        return result
    except Exception as e:
        try:
            if ('openapi' in data):
                print("Swagger 3.0")
                paths = data['paths']
                methodInfo = paths[methodName]
                result = {}
                result['summary'] = methodInfo['post']['responses']['200']['description']
                result['requestBody'] = methodInfo['post']['requestBody']
                result['responses'] = methodInfo['post']['responses']
                result['method'] = "POST"
                result['origin'] = "SWAGGER"
                result['url'] = "http://" + serviceName + "." + environment + "." + api_domain + methodName
            else:
                print("Swagger 2.0")
                paths = data['paths']
                methodInfo = paths[methodName]
                result = {}
                result['summary'] = methodInfo['post']['summary']
                result['requestBody'] = methodInfo['post']['requestBody']
                result['responses'] = methodInfo['post']['responses']
                result['method'] = "POST"
                result['origin'] = "SWAGGER"
                result['url'] = "http://" + serviceName + "." + environment + "." + api_domain + methodName
            return result
        except Exception as e:
            print("Error getting method info: " + str(e))
            return None

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
            

