from services import databaseService
from model.PublishEndpointRequestDTO import PublishEndpointRequestDTO
from services import queriesService
import json
from fastapi.responses import JSONResponse
import base64
import requests

def update(publishEndpointRequestDTO: PublishEndpointRequestDTO):
    print("Publishing query " + publishEndpointRequestDTO.endpoint + " with parameters " + str(publishEndpointRequestDTO.parameters) + " for query " + str(publishEndpointRequestDTO.id_query))
    
    # Convert publishEndpointRequestDTO.parameters array to json
    # parametersJson = json.dumps(publishEndpointRequestDTO.parameters)
    parametersJson = json.dumps([param.model_dump() for param in publishEndpointRequestDTO.parameters])

    publishEndpointRequestDTO.query = base64.b64decode(publishEndpointRequestDTO.query).decode('utf-8')  

    if (publishEndpointRequestDTO.description is None):
        publishEndpointRequestDTO.description = ""
    if (publishEndpointRequestDTO.queryStringTest is None):
        publishEndpointRequestDTO.queryStringTest = ""

    publishEndpointRequestDTO.query = publishEndpointRequestDTO.query.replace("'","''")                

    try:
        updateQuery = "UPDATE __endpoints  SET id_query = " + str(publishEndpointRequestDTO.id_query) + ", \
                               endpoint = '" + publishEndpointRequestDTO.endpoint + "', \
                               parameters = '" + parametersJson + "', \
                               description = '" + publishEndpointRequestDTO.description + "', \
                               query = '" + publishEndpointRequestDTO.query + "', \
                               queryStringTest = '" + publishEndpointRequestDTO.queryStringTest + "', \
                               status = '" + publishEndpointRequestDTO.status + "' \
                                WHERE id_endpoint = " + str(publishEndpointRequestDTO.id_endpoint)
        print("updateQuery: " + updateQuery)
        databaseService.runQuery(updateQuery)
    except Exception as e:
        print("Error updating endpoint:" + str(e))
        return False        

    return True

####################################################

def getEndpointConfiguration(path):
    print("Getting endpoint " + path)
    
    # Search query into __queries table lower case
    df = databaseService.runQuery("SELECT * FROM __endpoints WHERE endpoint = '" + path + "'")

    # Map df to PublishEndpointRequestDTO object
    endpoint = PublishEndpointRequestDTO.from_dataframe(df)


    if (endpoint is not None):
        return endpoint
    else:
        return None

####################################################
def getAndRunEndpoint(path, query_params, body):
    print("Getting and running endpoint " + path + " with query_params " + str(query_params) + " and body " + str(body))

    endpoint = getEndpointConfiguration(path)
    

    if (endpoint is not None):
        print("endpoint: ", endpoint)

        # Query contains expressoins like {marca} or {marca_id} replace with query_params
        query = endpoint.query
        if (query_params is not None):
            for param in query_params:
                query = query.replace("{" + param + "}", query_params[param])

        # Check if any parameter remains in query, if so raise exception
        if ("{" in query):
            raise Exception("Some needed parameters were not found: " + query)
        
        
        # Run query
        print("Running query: " + query)
        df = databaseService.runQuery(query)

        if (df is not None):
            return df
        else:
            return None
    
    else:
        raise Exception("Endpoint not found: " + path)

####################################################
def listEndpoints():
    print("Getting available endpoints")

    # Search query into __queries table lower case
    try:
        df = databaseService.runQuery("SELECT * FROM __endpoints ORDER BY endpoint ASC")
    except:
        createTable()
        df = databaseService.runQuery("SELECT * FROM __endpoints ORDER BY endpoint ASC")

    if (df is not None):
        result = df.dropna().to_dict(orient="records")
        print("Result:" + str(result))
        return result
    else:
        None      

####################################################
def createEndpoint():
    print("Creating empty endpoint")
    r = None
    try:
        r = databaseService.runQuery("INSERT INTO __endpoints (id_endpoint) VALUES (nextval('seq_id_endpoint')) RETURNING (id_endpoint)")
    except:
        createTable()
        r = databaseService.runQuery("INSERT INTO __endpoints (id_endpoint) VALUES (nextval('seq_id_endpoint')) RETURNING (id_endpoint)")
        return False  

    if (r is not None):
        
        # get id_endpoint
        d = r.to_dict(orient="records")
        id_endpoint = d[0]["id_endpoint"]
        print("Result:" + str(id))
        
        print("id:" + str(id_endpoint))
        return id_endpoint
    else: 
        return None

####################################################
def deleteEndpoint(id_endpoint: int):
    print("Deleting endpoint " + str(id_endpoint))

    # Search query into __queries table lower case
    try:
        databaseService.runQuery("DELETE FROM __endpoints WHERE id_endpoint = " + str(id_endpoint))
    except:
        createTable()
        databaseService.runQuery("DELETE FROM __endpoints WHERE id_endpoint = " + str(id_endpoint))
        return False        

    return True

####################################################
def createTable():
    tableList = databaseService.getTableList( False)
    # check if meta data table __endpoints exists
    if "__endpoints" not in tableList:
        print("Creating table __endpoints")
        databaseService.runQuery("CREATE TABLE __endpoints (id_endpoint INTEGER PRIMARY KEY, id_query INTEGER, endpoint VARCHAR(255), parameters VARCHAR(255), description VARCHAR(255), query VARCHAR(255), queryStringTest VARCHAR(255), status VARCHAR(10));CREATE SEQUENCE seq_id_endpoint START 1;")

####################################################
# Return True if endpoint exists        
def checkIfEndPointExists(endpoint):
    print("Checking if endpoint exists " + str(endpoint))
    
    # Search query into __queries table lower case
    df = databaseService.runQuery("SELECT * FROM __endpoints WHERE endpoint = '" + endpoint + "'")

    if (df is not None and len(df) > 0):
        return True
    else:
        return False

####################################################
def getApiDefinition(path):
    print("Getting API definition for " + path)
    '''
    
    endpoints = [
        {
            "path": "/endpoint1",
            "query": "param1=value1&param2=value2",
            "response": {"key1": "value1", "key2": "value2"}
        },
        {
            "path": "/endpoint2",
            "query": "param3=value3",
            "response": {"key3": "value3"}
        }
    ]
    '''
    endpoints = listEndpoints()

    '''
    [
        {
            "id_endpoint": 37,
            "id_query": 11,
            "endpoint": "buscarMarca",
            "parameters": "[{\"name\": \"marca\", \"exampleValue\": \"FORD\"}]",
            "description": "Busca una marca",
            "query": "SELECT marca, marca_id \nFROM catalogoCoches\nWHERE marca LIKE '%{marca}%'\nGROUP BY marca, marca_id\nORDER BY marca_id asc",
            "queryStringTest": "?marca=FORD",
            "status": "DEV"
        },
        {
            "id_endpoint": 33,
            "id_query": 21,
            "endpoint": "irisBySepalLength",
            "parameters": "[{\"name\": \"max_length\", \"exampleValue\": \"5\"}, {\"name\": \"min_length\", \"exampleValue\": \"6\"}]",
            "description": "Search by sepal length",
            "query": "SELECT * FROM iris WHERE sepal_length>={max_length} and sepal_length<={min_length}  ",
            "queryStringTest": "?max_length=5&min_length=6",
            "status": "DEV"
        }
    ]
    
    '''
    endpointsDefinition = []
    #print("endpoints: ", endpoints)
    for endpoint in endpoints:
        endpointDict = {}
        endpointDict["path"] = endpoint["endpoint"]
        query = endpoint["queryStringTest"]
        # Remove first ? from query string
        endpointDict["query"] = endpoint["queryStringTest"][1:]
        response = {}
        res = getAndRunEndpoint(endpoint["endpoint"], query, None) 
        #urlTest = "http://localhost:8000/api/" + endpoint["endpoint"]  + endpoint["queryStringTest"]
        #print("urlTest: ", urlTest)
        #response = requests.get(urlTest)
        print("response: ", res)

        endpointDict["response"] = res.to_dict(orient="records")
        endpointsDefinition.append(endpointDict)
        



    openapi_dict = {
        "openapi": "3.0.0",
        "info": {
            "title": "Mi API",
            "version": "1.0.0"
        },
        "paths": {}
    }

    for endpoint in endpointsDefinition:
        path = endpoint["path"]
        query_params = endpoint["query"].split('&')
        response = endpoint["response"]

        parameters = []
        for param in query_params:
            name, _ = param.split('=')
            parameters.append({
                "name": name,
                "in": "query",
                "required": True,
                "schema": {"type": "string"}
            })

        openapi_dict["paths"][path] = {
            "get": {
                "parameters": parameters,
                "responses": {
                    "200": {
                        "description": "Éxito",
                        "content": {
                            "application/json": {
                                "example": response
                            }
                        }
                    }
                }
            }
        }

    return openapi_dict
