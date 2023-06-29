import services.duckDbService as db

import components.loadFile as loadFile
import components.loadDatabase as loadDatabase
import components.queryTool as queryTool
import components.apiTool as apiTool
import components.tablesTool as tablesTool
import components.sideBar as sideBar

import streamlit as st

import sys
from dataprofiler import Data, Profiler

if 'sessionObject' not in st.session_state:
    print("Initializing session")
    st.session_state.sessionObject = {}
    global ses
    ses = st.session_state.sessionObject
    ses["candidates"] = []
    ses["chatGptResponse"] = ses["selectedTable"] = ses["df"] = None
    ses["totalTime"] = ses["lastQueryTime"] = 0

    ses["lastQuery"] = "SELECT * FROM iris"
     
    ses["loadedTables"] = {}
    ses["queries"] = []
    ses["s3SearchText"] = "https://gist.githubusercontent.com/netj/8836201/raw/6f9306ad21398ea43cba4f7d537619d0e07d5ae3/iris.csv"
    
    ses["services"] = ses["service"] = ses["methods"] = ses["method"] = ses["methodInfo"] = ses["inParameters"] = ses["tableDfNew"] = None
    ses["fieldsToLoad"] = []
    
    ses["databases"] = ses["database"] = ses["connection"] = ses["dfRemoteDb"] = None

@st.cache_resource
def init():
    try:
        access_key = st.secrets["s3_access_key_id"]
        secret = st.secrets["s3_secret_access_key"]
        db.runQuery("INSTALL httpfs;LOAD httpfs;SET s3_region='eu-west-1';SET s3_access_key_id='" + access_key + "';SET s3_secret_access_key='" + secret +"'")
        print("Loaded S3 credentials")
    except:
        db.runQuery("INSTALL httpfs;LOAD httpfs")
        print("No s3 credentials found")
    
@st.cache_data
def convert_df(df):
    return df.to_csv().encode('utf-8')

@st.cache_data
def getProfile(df):
    try:
        profile = Profiler(df)
        readable_report = profile.report(report_options={"output_format": "compact"})
        return readable_report
    except:
        return None

def main():
    ses = st.session_state.sessionObject

    sideBar.sideBar()
    
    global S3_BUCKET
    if len(sys.argv) > 1:
        S3_BUCKET = sys.argv[1]
    else:
        S3_BUCKET = None    
    
    loadFile.loadDataFromFile(ses, S3_BUCKET)
    loadDatabase.loadDataFromDatabase(ses)
    tablesTool.tablesTool(ses)
    queryTool.query(ses)
    apiTool.apiTool(ses)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Datalake Studio",
        page_icon="✳️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init()
    main()        