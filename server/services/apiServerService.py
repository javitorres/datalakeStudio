from services import duckDbService
from model.PublishEndpointRequestDTO import PublishEndpointRequestDTO
from services import queriesService
import json
from fastapi.responses import JSONResponse

def update(publishEndpointRequestDTO: PublishEndpointRequestDTO):
    print("Publishing query " + publishEndpointRequestDTO.endpoint + " with parameters " + str(publishEndpointRequestDTO.parameters) + " for query " + str(publishEndpointRequestDTO.id_query))
    
    # Convert publishEndpointRequestDTO.parameters array to json
    parametersJson = json.dumps(publishEndpointRequestDTO.parameters)        

    try:
        duckDbService.runQuery("INSERT INTO __endpoints (id_endpoint, id_query, endpoint, parameters, description) VALUES (nextval('seq_id_endpoint'), " + str(publishEndpointRequestDTO.id_query) + ", '" + publishEndpointRequestDTO.endpoint + "', '" + parametersJson + "', '" + publishEndpointRequestDTO.description + "')")
    except:
        createTable()
        duckDbService.runQuery("INSERT INTO __endpoints (id_endpoint, id_query, endpoint, parameters, description) VALUES (nextval('seq_id_endpoint'), " + str(publishEndpointRequestDTO.id_query) + ", '" + publishEndpointRequestDTO.endpoint + "', '" + parametersJson + "', '" + publishEndpointRequestDTO.description + "')")
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

        # Get query
        query = queriesService.getQuery(endpoint.id_query)
        print("query: ", query)

        # Run query
        df = duckDbService.runQuery(query["query"])

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