import psycopg2
import pandas as pd

def connect_to_db(database_name):
    with open('/home/jtorres/.pgpass', 'r') as f:
        lines = f.readlines()

    for line in lines:
        # If line is a comment, skip it
        if line.startswith('#'):
            continue
        try:

            host, port, db, user, password = line.strip().split(':')
            print("Database:"+ db + " with host: " + host + " and port: " + port)
            if db == database_name:
                print("Connecting to database:"+ db + " with host: " + host + " and port: " + port)
                connection = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=db,
                    user=user,
                    password=password
                )
                return connection
        except:
            pass
    return None  # Si no se encuentra la base de datos
def getConnection(databaseConfig):
    print("Connecting to database:"+ str(databaseConfig))
    connection = psycopg2.connect(
        host=databaseConfig["host"],
        port=databaseConfig["port"],
        dbname=databaseConfig["db"],
        user=databaseConfig["user"],
        password=databaseConfig["password"]
    )
    return connection

def getDbList(database_name):
    databaseList = []
    with open('/home/jtorres/.pgpass', 'r') as f:
        lines = f.readlines()

    for line in lines:
        # If line is a comment, skip it
        if line.startswith('#'):
            continue
        try:
            host, port, db, user, password = line.strip().split(':')
            print("Database:"+ db + " with host: " + host + " and port: " + port)

            if (db==database_name or database_name in db or database_name=="" or database_name==None):
                dbJson = {}
                dbJson['host'] = host
                dbJson['port'] = port
                dbJson['db'] = db
                dbJson['user'] = user
                dbJson['password'] = password
                dbJson['line'] = line

                # Add database to list
                databaseList.append(dbJson)
        except:
            pass
    print("Database List:"+ str(databaseList))
    return databaseList  # Si no se encuentra la base de datos

def closeConnection(connection):
    if connection is not None:
        connection.close()
        print('Database connection closed')

def showTables(connection, schema):
    if (connection is None or connection.closed):
        return []
    
    
    cursor = connection.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = '" + schema +"' ORDER BY table_name;")
    tables = cursor.fetchall()
    print("Tables:"+ str(tables))
    cursor.close()
    return tables

def runQuery(connection, query):
    cursor = connection.cursor()
    cursor.execute(query)
    # Load data as dataframe
    data = cursor.fetchall()
    # Get column names
    column_names = [column[0] for column in cursor.description]
    cursor.close()
    # Convert to pandas DataFrame
    df = pd.DataFrame(data, columns=column_names)
    return df

