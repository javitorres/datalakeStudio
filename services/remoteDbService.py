import streamlit as st

import psycopg2
import pandas as pd

def connect_to_db(database_name):
    with open(st.secrets["pgpass_file"], 'r') as f:
        lines = f.readlines()

    for line in lines:
        # If line is a comment, skip it
        if line.startswith('#'):
            continue
        try:

            host, port, db, user, password = line.strip().split(':')
            print("Database:"+ db + " with host: " + host + " and port: " + port)
            if db == database_name:
                print("Connecting to database::"+ db + " with host: " + host + " and port: " + port)
                connection = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=db,
                    user=user,
                    password=password
                )
                print("Connecting to database returned no error")
                return connection
        except:
            print("Error connecting to database")
            pass
    return None  # Si no se encuentra la base de datos

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

def getDbList(database_search_text):
    databaseList = []

    try:
        with open(st.secrets["pgpass_file"], 'r') as f:
            lines = f.readlines()
    except:
        st.write("You must define pgpass_file in secrets.toml file")
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

def closeConnection(connection):
    if connection is not None:
        connection.close()
        print('Database connection closed')

def showTables(connection, schema):
    if (connection is None or connection.closed):
        return []
    
    print("Getting tables for schema:"+ str(schema))
    cursor = connection.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = '" + schema +"' ORDER BY table_name;")
    tables = cursor.fetchall()
    print("Tables:"+ str(tables))
    cursor.close()
    return tables

def runQuery(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        # Load data as dataframe
        data = cursor.fetchall()
        # Get column names
        column_names = [column[0] for column in cursor.description]
        cursor.close()
        # Convert to pandas DataFrame
        df = pd.DataFrame(data, columns=column_names)
        return df
    except Exception as e:
        st.write("Error: " + str(e))
        connection.rollback()
    finally:
        cursor.close()
    
    return None
    
