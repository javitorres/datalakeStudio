from services import databaseService

def saveSqlQuery(saveQueryRequestDTO):
    print("Saving query " + saveQueryRequestDTO.sqlQueryName + ": " + saveQueryRequestDTO.query + " (" + saveQueryRequestDTO.description + ")")
    tableList = databaseService.getTableList( False)
    # check if meta data table __queries exists
    if "__queries" not in tableList:
        print("Creating table __queries")
        databaseService.runQuery("CREATE TABLE __queries (id_query INTEGER PRIMARY KEY, name VARCHAR, query VARCHAR, description VARCHAR);CREATE SEQUENCE seq_id_query START 1;")
    
    # Scape single quotes
    query = saveQueryRequestDTO.query.replace("'","''")

    # Insert query into __queries table
    databaseService.runQuery("INSERT INTO __queries (id_query, name, query, description) VALUES (nextval('seq_id_query'), '" + saveQueryRequestDTO.sqlQueryName + "', '" + query + "', '" + saveQueryRequestDTO.description + "')")

    return True
####################################################
def searchQuery(query):
    print("Searching query " + query)
    
    # Search query into __queries table lower case
    df = databaseService.runQuery("SELECT * FROM __queries WHERE LOWER(name) LIKE '%" + query.lower() + "%' OR LOWER(description) LIKE '%" + query.lower() + "%'")

    if (df is not None):
        return df
    else:
        None
####################################################
def deleteQuery(id_query):
    print("Deleting query " + str(id_query))
    databaseService.runQuery("DELETE FROM __queries WHERE id_query = " + str(id_query))

####################################################
def getQuery(id_query):
    print("Getting query " + str(id_query))
    df = databaseService.runQuery("SELECT * FROM __queries WHERE id_query = " + str(id_query))

    if (df is not None):
        result = df.to_dict(orient="records")
        return result[0]
    else:
        None
    