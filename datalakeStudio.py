import duckDbService as db
import s3IndexService as s3Index
import chatGPTService as chatGpt

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import time
import datetime
import os
import psutil
import gc
import json
import sys
from PIL import Image
from dataprofiler import Data, Profiler

if 'sessionObject' not in st.session_state:
    print("Initializing session")
    st.session_state.sessionObject = {}
    global ses
    ses = st.session_state.sessionObject
    ses["fileName"] = "https://gist.githubusercontent.com/netj/8836201/raw/6f9306ad21398ea43cba4f7d537619d0e07d5ae3/iris.csv"
    ses["candidates"] = []
    ses["chatGptResponse"] = None
    ses["totalTime"] = 0
    ses["lastQueryTime"] = 0
    ses["lastQuery"] = "SELECT * FROM iris"
    ses["selectedTable"] = None
    ses["df"] = None
    ses["loadedTables"] = {}
    ses["queries"] = []
    
    print("Session initialized:"+ str(ses))

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

def getStr(dict, key):
    if (key in dict):
        return str(dict[key])
    else:
        return "-"
    
def showProfilerAnalysis(df, tableName):
    #count = db.runQuery("SELECT count(*) as total FROM "+ df)
    #st.write("Records: " + str(count["total"].iloc[0]))
    
    readable_report = getProfile(df)
    ses["loadedTables"][tableName]["profile"]=readable_report
    if (readable_report is None): return
    c1,c2,c3,c4= st.columns([1, 1, 1, 1])
    with c1: st.metric("Total columns", readable_report["global_stats"]["column_count"])
    #with c2: st.metric("Total rows", str(count["total"].iloc[0]))
    with c3: st.metric("Samples used", readable_report["global_stats"]["samples_used"])
    
    c1,c2,c3,c4= st.columns([1, 1, 1, 1])
    with c1: st.metric("Unique row ratio", readable_report["global_stats"]["unique_row_ratio"])
    with c2: st.metric("Duplicate row count", readable_report["global_stats"]["duplicate_row_count"])
    with c3: st.metric("Any Null ratio", readable_report["global_stats"]["row_has_null_ratio"])
    with c4: st.metric("Full null rows ratio", readable_report["global_stats"]["row_is_null_ratio"])
    
    st.divider()
    c1,c2= st.columns([1, 3])
    selectedColumn = None
    
    with c1:
        # Get column names in dataCol["column_name"] to an array
        column_names = [entry['column_name'] for entry in readable_report['data_stats']]

        option = st.selectbox(label="Select a field to see description", options=column_names, key=tableName + "_selectbox")
        selectedColumn = option
               
    with c2:
        for dataCol in readable_report["data_stats"]:
            if (dataCol["column_name"] == selectedColumn):
                st.markdown("####  Field: " + dataCol["column_name"])
                c1,c2,c3,c4= st.columns([1, 1, 1, 1])
                with c1: 
                    st.markdown("**Data type**: :red["+dataCol["data_type"]+"]")
                    st.markdown("**Mean**: "+ getStr(dataCol["statistics"], "mean"))
                    st.markdown("**Sum**:" + getStr(dataCol["statistics"],"sum"))
                    try:
                        st.markdown("**Quantile 0.25**: " + str(dataCol["statistics"]["quantiles"][0]))
                    except:
                        st.markdown("**Quantile 0.25**: -")
                with c2: 
                    st.markdown("**Categorical**: " + str(dataCol["categorical"]))
                    st.markdown("**Stddev**: "+ getStr(dataCol["statistics"],"stddev"))
                    st.markdown("**Variance**:" + getStr(dataCol["statistics"],"variance"))
                    try:
                        st.markdown("**Quantile 0.50**:" + str(dataCol["statistics"]["quantiles"][1]))
                    except:
                        st.markdown("**Quantile 0.50**: -")    
                with c3: 
                    st.markdown("**Min**: " + getStr(dataCol["statistics"], "min"))
                    st.markdown("**Mode**: " + getStr(dataCol["statistics"], "mode"))
                    st.markdown("**Skewness**:" + getStr(dataCol["statistics"], "skewness"))
                    try:
                        st.markdown("**Quantile 0.75**:" + str(dataCol["statistics"]["quantiles"][2]))
                    except:
                        st.markdown("**Quantile 0.75**: -")
                with c4: 
                    st.markdown("**Max**: " + getStr(dataCol["statistics"], "max"))
                    st.markdown("**Median**:" + getStr(dataCol["statistics"],"median"))
                    st.markdown("**Kurtosis**:" + getStr(dataCol["statistics"],"kurtosis"))
                
def showTableScan(tableName):
    ses = st.session_state.sessionObject
    if (tableName != "-"):
        if (st.button("Delete table '" + tableName + "' 🚫")):
            #tableDf = None
            db.runQuery("DROP TABLE "+ tableName)
            st.experimental_rerun()
        tableDf = db.runQuery("SELECT * FROM "+ tableName +" LIMIT 1000")
        c1,c2 = st.columns([1, 7])
        with c1:
            st.write("Schema")
            # Check this arrow warn
            st.write(tableDf.dtypes)
        with c2:
            st.write("Sample data (1000)")
            st.write(tableDf.head(1000))
        
        #if (ses["loadedTables"][tableName]["profile"] is not None or st.button("Show profiler analysis", key="profiler_"+tableName)):
        #    showProfilerAnalysis(tableDf, tableName)
                

def main():
    ses = st.session_state.sessionObject
    with st.sidebar:
        loadSaveFile = st.text_input('Project file (.dls)', '', key='projectFile')
        if (not loadSaveFile.endswith(".dls")):
            loadSaveFile = loadSaveFile + ".dls"
        col1, col2 = st.columns(2)
        with col1:
            if (st.button("Load")):
                with open(loadSaveFile, "r") as read_file:
                    data = json.load(read_file)
                    db.dropAllTables()
                    ses["loadedTables"] = {}
                    for tableName in data["loadedTables"]:
                        db.loadTable(tableName, data["loadedTables"][tableName], ses)
                        #ses["loadedTables"][tableName]["profile"] = None

                    try:
                        ses["queries"] = data["queries"]
                    except:
                        ses["queries"] = []
                        
                    try:
                        ses["lastQuery"] = data["lastQuery"]
                    except:
                        ses["lastQuery"] = "SELECT * FROM XXXXXX"
                    st.write("Project loaded")

        with col2:
            if (st.button("Save")):
                with open(loadSaveFile, "w") as write_file:
                    data = {}
                    data["loadedTables"] = ses["loadedTables"]
                    data["queries"] = ses["queries"]
                    data["lastQuery"] = ses["lastQuery"]
                    json.dump(data, write_file)
                    st.write("Project saved as "+ loadSaveFile + " at " + str(datetime.datetime.now().strftime('%H:%M:%S')))
    
        st.markdown(
                '<a href="tutorial/tutorial.html">🎓 Tutorial</a></h6>',
                unsafe_allow_html=True,
            )

    logo = Image.open('images/logo.png')
    st.image(logo, width=200)
    global S3_BUCKET
    if len(sys.argv) > 1:
        S3_BUCKET = sys.argv[1]
    else:
        S3_BUCKET = None    
    startTime = queryTime = int(round(time.time() * 1000))
    endTime = 0

    ################### Load data #################
    with st.expander("**Load data** 📂", expanded=True):
        fcol1,fcol2,fcol3 = st.columns([4, 2, 1])
        with fcol1:
            ses["fileName"] = st.text_input('Local file, folder, http link or find S3 file (pressing Enter) 👇', ses["fileName"],  key='s3SearchText', on_change=s3SearchFile)

        with fcol2:
            tableName = st.text_input('Table name', 'iris', key='tableName')
        with fcol3:
            if (st.button("Load 👈")):
                if (str(ses["fileName"]).endswith("/")):
                    files = os.listdir(ses["fileName"])
                    for file in files:
                        if (file.endswith(".csv") or file.endswith(".parquet") or file.endswith(".json")):
                            tableName = os.path.splitext(file)[0]
                            db.loadTable(tableName, ses["fileName"] + str(file), ses)
                            if (ses["selectedTable"] is None): 
                                ses["selectedTable"] = tableName
                else:
                    db.loadTable(tableName, str(ses["fileName"]), ses)
                
        if (len(ses["candidates"]) > 0):
            st.markdown("#### Select a S3 file:")
            for path in ses["candidates"]:
                if st.button(path):
                    ses["fileName"] = path
                    st.experimental_rerun() 
            if (st.button("Close S3 file list")):
                ses["candidates"] = []
                st.experimental_rerun()

    ################### Loaded tables       ################
    tableListArray = None
    try:
        print("Loading tables")
        tableList = db.runQuery("SHOW TABLES")
        tableListArray = None
        if (tableList is not None):
            tableListArray = tableList["name"].to_list()
    except:
        print("No tables loaded")
    
    if (tableListArray is not None and len(tableListArray) > 0):
        with st.expander(label="**Tables** 📄", expanded=True):
            tableListArray = tableListArray + (10 - len(tableListArray)) * ["-"]
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(tableListArray)
            with tab1:showTableScan(tableListArray[0])
            with tab2:showTableScan(tableListArray[1])
            with tab3:showTableScan(tableListArray[2])
            with tab4:showTableScan(tableListArray[3])
            with tab5:showTableScan(tableListArray[4])
            with tab6:showTableScan(tableListArray[5])
            with tab7:showTableScan(tableListArray[6])
            with tab8:showTableScan(tableListArray[7])
            with tab9:showTableScan(tableListArray[8])
            with tab10:showTableScan(tableListArray[9])
            
        with st.expander("**Query** 🔧", expanded=True):
            col1,col2 = st.columns(2)
            with col1:
                #lastQuery = ses["queries"][len(ses["queries"]) - 1] if len(ses["queries"]) > 0 else ""
                lastQuery = ses["lastQuery"]
                queryToRun = st.text_area("Query SQL ✏️", lastQuery)

                ses["lastQuery"] = queryToRun
                c1,c2,c3,c4 = st.columns([2,2,2,4])
                with c1:
                    if st.button("Run query 🚀"):
                        with st.spinner('Running query...'):
                            ses["df"] = db.runQuery(queryToRun)
                            ses["df"].columns = ses["df"].columns.str.replace('.', '_')
                            queryTime = int(round(time.time() * 1000))
                with c2:
                    if st.button("Save query 💾"):
                        ses["queries"].append(queryToRun)
                
                with c3:
                    if st.button("Load query 📂"):
                        if (len(ses["queries"]) > 0):
                            st.markdown("#### Saved queries:")
                            ses["queries"] = list(dict.fromkeys(ses["queries"]))
                            for query in ses["queries"]:
                                st.text_area("",query)
                            if (st.button("Close saved queries")):
                                ses["queries"] = []
                                st.experimental_rerun()

            with col2:
                askChat = st.text_area("Ask ChatGPT 💬. Example: Show me the 10 characters with the most published comics in descending order. I also want their gender and race")
                #st.write("Example: Show me the 10 characters with the most published comics in descending order. I also want their gender and race")
                if st.button("Suggest query 🤔"):
                    tables = db.runQuery("SHOW TABLES")
                    with st.spinner('Waiting OpenAI API...'):
                        ses["chatGptResponse"] = chatGpt.askGpt(askChat, tables, st.secrets["openai_organization"], st.secrets["openai_api_key"])
                
                if (ses["chatGptResponse"] is not None):
                    st.text_area("ChatGPT answer", ses["chatGptResponse"])

            ################### Time and resources #################
            c1, c2, c3, c4 = st.columns([1, 1, 1, 5])
            with c1:
                pid = os.getpid()
                process = psutil.Process(pid)
                memory_info = process.memory_info()
                st.metric("Memory", str(round(memory_info.rss/1024/1024, 1)) + " Mb")
                if (st.button("Run GC 🧹")):
                    collected_objects = gc.collect()
            with c2:
                if (ses["totalTime"] != 0):
                    st.metric("Time last query", str(ses["lastQueryTime"]) + " ms")    
            with c3:
                if (ses["totalTime"] != 0):
                    st.metric("Total Time", str(ses["totalTime"]) + " ms")  

        ################### Column analysis    #################
        with st.expander("Analysis 📊", expanded=True):
            if (ses["df"] is not None):
                df = ses["df"]
                col1,col2 = st.columns([1, 5])
                with col1:
                    st.markdown("#### Schema")
                    st.write(df.dtypes)
                    st.write("Records: " + str(len(df)))
                with col2:
                    st.markdown("#### Sample data")
                    if (len(df.columns) < 10):
                        st.write(df.head(10))
                    else:
                        st.write(df.head(len(df.columns)))

                    if (st.button("Download full result")):
                        st.write("Download table")
                        file_type = st.radio("Doanload as:", ("CSV", "Excel"), horizontal=True, label_visibility="collapsed")
                        if file_type == "CSV":
                            file = convert_df(df)
                            st.download_button("Download dataframe", file, "report.csv", "text/csv", use_container_width=True)
                        elif file_type == "Excel":
                            file = convert_excel(df)
                            st.download_button("Download dataframe", file, "report.xlsx", use_container_width=True)
                
                #if (st.button("Show profiler analysis")):
                    #showProfilerAnalysis(df, "query_")
                
                if (("lat" in df.columns and "lon" in df.columns) or
                    ("latitude" in df.columns and "longitude" in df.columns)):

                    st.header("Detected spatial data")
                    st.map(df)
                else:
                    st.header("No spatial data detected")
                    st.write("Spatial fields should be named 'lat', 'latitude', 'LAT', 'LATITUDE' AND 'lon', 'longitude', 'LON', 'LONGITUDE' to be plotted in a map, use a SQL query to rename them if needed: Ej: Latitude as lat, Longitude as lon")

                st.header("Column data analysis")

                for col in df.columns:
                    if (col.startswith("grp_")):
                        continue
                    st.divider()
                    st.markdown("####  " + col)
                    query='SELECT "' + col + '", count(*) as quantity FROM df GROUP BY "' + col + '" ORDER BY quantity DESC'
                    groupByValue = db.runQuery(query)
                    distinctValues = len(groupByValue)
                    rcol1,rcol2 = st.columns([4, 2])
                    if df[col].dtype == 'object' or df[col].dtype == 'bool':
                        with rcol1:
                            if distinctValues < 100:
                                fig = px.pie(groupByValue, values='quantity', names=col, title=f"{col} Pie Chart")
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.write("Too many values ("+str(distinctValues)+") in "+col+" to plot a chart")
                            
                        with rcol2:  
                            st.write(df[col].describe())
                    elif str(df[col].dtype).startswith('datetime'):
                        with rcol1:
                            st.write("Datetime column has no plots yet")
                        with rcol2:
                            st.write(df[col].describe())
                    else:
                        if (df[col].describe()["std"] == 0):
                            st.write("Column "+col+" has always the same value: " + str(df[col].iloc[0]))
                        else:
                            with rcol1:
                                if (distinctValues < 500):
                                    fig = px.bar(groupByValue, x=col, y='quantity', title=f"{col} Bar Chart")
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    num_intervals = 100
                                    q5 = df[col].quantile(0.05)
                                    q95 = df[col].quantile(0.95)
                                    if df[col].dtype == 'int64':
                                        bins = np.arange(q5, q95 + 2, step=max(1, (q95 - q5 + 1) // num_intervals))
                                        labels = [f"{i}-{(i + bins[1] - bins[0] - 1)}" for i in bins[:-1]]
                                    else:                                
                                        bins = np.linspace(q5, q95, num_intervals + 1)
                                        labels = [f"{i:.4f}-{(i + (q95 - q5) / num_intervals):.4f}" for i in bins[:-1]]
                                    if len(set(labels)) != len(labels):
                                        raise ValueError("Labels are not unique")
                                    
                                    df['grp_'+col] = pd.cut(df[col], bins=bins, labels=labels)
                                    new_df = df.groupby('grp_' + col).size().reset_index(name='quantity')
                                    fig = px.line(new_df, x="grp_" + col, y="quantity", title=col + " Distribution")
                                    st.plotly_chart(fig, use_container_width=True)
                            with rcol2:  
                                st.write(df[col].describe())
                                st.write("Distinct values:" + str(distinctValues))

                endTime = int(round(time.time() * 1000))
                st.write("Query execution time: " + str(queryTime - startTime) + " ms")
                ses["lastQueryTime"] = queryTime - startTime
                st.write("Total execution time: " + str(endTime - startTime) + " ms")
                ses["totalTime"] = endTime - startTime

def s3SearchFile():
    ses = st.session_state.sessionObject
    ses["s3SearchText"] = st.session_state.s3SearchText
    global S3_BUCKET
    if (ses["s3SearchText"] and not ses["s3SearchText"].startswith('/') and not ses["s3SearchText"].startswith('http') and S3_BUCKET is not None):
        with st.spinner('Searching in S3...'):
            ses["candidates"] = []
            s3Paths = s3Index.s3Search(S3_BUCKET, ses["s3SearchText"])
            if len(s3Paths) > 5:
                total = len(s3Paths)
                s3Paths = s3Paths[:5]
                s3Paths.append(f'... y {total - 5} mas')
            ses["candidates"] = s3Paths
            return
    else:
        if (S3_BUCKET is None):
            print("No S3_BUCKET defined")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Datalake Studio",
        page_icon="✳️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init()
    main()
    with st.sidebar:
            st.markdown("---")
            st.markdown(
                '<h6>Made in &nbsp<img src="https://streamlit.io/images/brand/streamlit-mark-color.png" alt="Streamlit logo" height="16">&nbsp Twitter: <a href="https://twitter.com/datalakestudio">@datalakestudio</a></h6>',
                unsafe_allow_html=True,
            )