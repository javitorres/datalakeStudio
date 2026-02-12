from services import databaseService

def ensure_queries_metadata():
    # Keep metadata objects available even on fresh databases.
    databaseService.runQuery(
        "CREATE TABLE IF NOT EXISTS __queries (id_query INTEGER PRIMARY KEY, name VARCHAR, query VARCHAR, description VARCHAR);",
        False
    )
    databaseService.runQuery("CREATE SEQUENCE IF NOT EXISTS seq_id_query START 1;", False)

def saveSqlQuery(saveQueryRequestDTO):
    print("Saving query " + saveQueryRequestDTO.sqlQueryName + ": " + saveQueryRequestDTO.query + " (" + saveQueryRequestDTO.description + ")")
    ensure_queries_metadata()
    
    # Scape single quotes
    query = saveQueryRequestDTO.query.replace("'","''")

    # Insert query into __queries table
    databaseService.runQuery("INSERT INTO __queries (id_query, name, query, description) VALUES (nextval('seq_id_query'), '" + saveQueryRequestDTO.sqlQueryName + "', '" + query + "', '" + saveQueryRequestDTO.description + "')")

    return True
####################################################
def searchQuery(query):
    print("Searching query " + query)
    ensure_queries_metadata()
    search_term = query.lower().replace("'","''")
    
    # Search query into __queries table lower case
    df = databaseService.runQuery(
        "SELECT * FROM __queries WHERE LOWER(name) LIKE '%" + search_term + "%' OR LOWER(description) LIKE '%" + search_term + "%'"
    )

    if (df is not None):
        return df
    else:
        None
####################################################
def deleteQuery(id_query):
    print("Deleting query " + str(id_query))
    ensure_queries_metadata()
    databaseService.runQuery("DELETE FROM __queries WHERE id_query = " + str(id_query))

####################################################
def getQuery(id_query):
    print("Getting query " + str(id_query))
    ensure_queries_metadata()
    df = databaseService.runQuery("SELECT * FROM __queries WHERE id_query = " + str(id_query))

    if (df is not None):
        result = df.to_dict(orient="records")
        return result[0]
    else:
        None
    
