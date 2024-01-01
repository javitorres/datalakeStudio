import psycopg2
import pandas as pd




def getDbList(database_search_text, pgpassfile):
    databaseList = []

    try:
        with open(pgpassfile, 'r') as f:
            lines = f.readlines()
    except:
        print("pgpassfile not found in '"+ pgpassfile +"'. You must define pgpass_file in secrets.yml file")
        return []

    words = database_search_text.split(" ")
    for line in lines:
        # If line is a comment, skip it
        if line.startswith('#'):
            continue
        try:
            host, port, db, user, password = line.strip().split(':')
            search_words = database_search_text.split(" ")
            wordsFound=0
            for word in search_words:
                if (word in host or word in port or word in db or word in user):
                    wordsFound+=1
                    
            if wordsFound == len(search_words):
                databaseList.append(host + " - " + str(port) + " - " + db + " - "  + user)
            
        except Exception as e:
            pass
    print("Database List:"+ str(databaseList))
    return databaseList  # Si no se encuentra la base de datos

#########################################################

def connectDatabase(database_name, pgpassfile):
    with open(pgpassfile, 'r') as f:
        lines = f.readlines()

    host, port, db, user, password = None, None, None, None, None
    for line in lines:
        # If line is a comment, skip it
        if line.startswith('#'):
            continue
        try:
            host, port, db, user, password = line.strip().split(':')
        except:
            #print(" reading line:" + line)
            continue
        
        try:
            #print("Database:"+ db + " with host: " + host + " and port: " + port + " Database name to connect:" + database_name)
            if host + " - " + port + " - " + db + " - " + user == database_name:
                print("########Connecting to database::"+ db + " with host: " + host + " and port: " + port)
                connection = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=db,
                    user=user,
                    password=password
                )
                print("Connecting to database returned no error")
                return connection
            
        except Exception as e:
            print("Error connecting to database:" + str(e))
            pass
    return None  # Si no se encuentra la base de datos

#########################################################

def getSchemas(connection):
    if (connection is None or connection.closed):
        return []
    cursor = connection.cursor()
    cursor.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;")
    schemas = cursor.fetchall()
    schemas = [schema[0] for schema in schemas]
    print("Schemas:"+ str(schemas))
    cursor.close()
    return schemas

#########################################################

def getTables(connection, schema):
    if (connection is None or connection.closed):
        return []
    
    print("Getting tables for schema:"+ str(schema))
    cursor = connection.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = '" + schema +"' ORDER BY table_name;")
    tables = cursor.fetchall()
    tablesArr = [t[0] for t in tables]
    print("Tables:"+ str(tablesArr))
    cursor.close()
    return tablesArr

#########################################################

def runRemoteQuery(connection, query):
    cursor = connection.cursor()
    try:
        #cursor.execute("SET search_path TO " + schema + ";")
        cursor.execute(query)
        data = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]
        cursor.close()
        df = pd.DataFrame(data, columns=column_names)
        print("Query result:"+ str(df))
        return df
    except Exception as e:
        print("Error running query:" + str(e))
        connection.rollback()
    finally:
        cursor.close()

    return None

######################################################### PROBADAS

def getPassword(host, port, db, user):
    with open(st.secrets["pgpass_file"], 'r') as f:
        lines = f.readlines()

    for line in lines:
        # If line is a comment, skip it
        if line.startswith('#'):
            continue
        try:
            hostFile, portFile, dbFile, userFile, password = line.strip().split(':')
            if (hostFile == host and portFile == port and dbFile == db and userFile == user):
                return password
        except:
            pass
    return None  

#########################################################

def getConnection(selectedDatabase):
    host, port, db, user = selectedDatabase.strip().split(' - ')
    password = getPassword(host, port, db, user)
    
    print("Connecting to database:"+ str(selectedDatabase))
    connection = psycopg2.connect(
        host=host,
        port=port,
        dbname=db,
        user=user,
        password=password
    )
    if (connection is None):
        print("Error connecting to database with config:"+ str(databaseConfig))
    return connection

#########################################################

def closeConnection(connection):
    if connection is not None:
        connection.close()
        print('Database connection closed')




    
