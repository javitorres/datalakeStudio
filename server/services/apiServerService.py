from services import duckDbService
from model.PublishEndpointRequestDTO import PublishEndpointRequestDTO
from services import queriesService
import json
from fastapi.responses import JSONResponse
import base64

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
        duckDbService.runQuery(updateQuery)
    except Exception as e:
        print("Error updating endpoint:" + str(e))
        return False        

    return True

####################################################

def getEndpointConfiguration(path):
    print("Getting endpoint " + path)
    
    # Search query into __queries table lower case
    df = duckDbService.runQuery("SELECT * FROM __endpoints WHERE endpoint = '" + path + "'")

    # Map df to PublishEndpointRequestDTO object
    endpoint = PublishEndpointRequestDTO.from_dataframe(df)


    if (endpoint is not None):
        return endpoint
    else:
        return None

####################################################
def getAndRunEndpoint(path, query_params, body):
    print("Getting and running endpoint " + path)

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
            raise Exception("Query contains parameters that are not present in query_params: " + query)
        
        
        # Run query
        print("Running query: " + query)
        df = duckDbService.runQuery(query)

        if (df is not None):
            return df
        else:
            return None
    
    # Search query into __queries table lower case
    df = duckDbService.runQuery("SELECT * FROM __endpoints WHERE endpoint = '" + path + "'")

    if (df is not None):
        result = df.to_dict(orient="records")
        print("Result:" + str(result))
        return result[0]
    else:
        None

####################################################
def listEndpoints():
    print("Getting available endpoints")

    # Search query into __queries table lower case
    try:
        df = duckDbService.runQuery("SELECT * FROM __endpoints ORDER BY endpoint ASC")
    except:
        createTable()
        df = duckDbService.runQuery("SELECT * FROM __endpoints ORDER BY endpoint ASC")

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
        r = duckDbService.runQuery("INSERT INTO __endpoints (id_endpoint) VALUES (nextval('seq_id_endpoint')) RETURNING (id_endpoint)")
    except:
        createTable()
        r = duckDbService.runQuery("INSERT INTO __endpoints (id_endpoint) VALUES (nextval('seq_id_endpoint')) RETURNING (id_endpoint)")
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
        duckDbService.runQuery("DELETE FROM __endpoints WHERE id_endpoint = " + str(id_endpoint))
    except:
        createTable()
        duckDbService.runQuery("DELETE FROM __endpoints WHERE id_endpoint = " + str(id_endpoint))
        return False        

    return True

####################################################
def createTable():
    tableList = duckDbService.getTableList( False)
    # check if meta data table __endpoints exists
    if "__endpoints" not in tableList:
        print("Creating table __endpoints")
        duckDbService.runQuery("CREATE TABLE __endpoints (id_endpoint INTEGER PRIMARY KEY, id_query INTEGER, endpoint VARCHAR(255), parameters VARCHAR(255), description VARCHAR(255), query VARCHAR(255), queryStringTest VARCHAR(255), status VARCHAR(10));CREATE SEQUENCE seq_id_endpoint START 1;")