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

            host, port, db, schema, user, password = line.strip().split(':')
            print("Database:"+ db + " with host: " + host + " schema:" + schema + " and port: " + port)
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
def getConnection(databaseConfig):
    print("Connecting to database:"+ str(databaseConfig))
    connection = psycopg2.connect(
        host=databaseConfig["host"],
        port=databaseConfig["port"],
        dbname=databaseConfig["db"],
        user=databaseConfig["user"],
        password=databaseConfig["password"]
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

def getDbList(database_name):
    databaseList = []
    with open(st.secrets["pgpass_file"], 'r') as f:
        lines = f.readlines()

    for line in lines:
        # If line is a comment, skip it
        if line.startswith('#'):
            continue
        try:
            host, port, db, user, password = line.strip().split(':')
            print("Reading file. Database::"+ db + " with host: " + host + " and port: " + port)

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
        except Exception as e:
            print("Error reading file: " + str(e))
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
    
