import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import numpy as np
import time
import os
import psutil
import gc
from s3IndexService import s3Search
from chatGPTService import askGpt
from duckDbService import loadTable
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
    ses["chatGptResponse"] = ""
    ses["totalTime"] = 0
    ses["lastQuery"] = ""
    ses["selectedTable"] = None
    ses["df"] = None
    print("Session initialized:"+ str(ses))

@st.cache_resource
def init():
    try:
        
        access_key = st.secrets["s3_access_key_id"]
        secret = st.secrets["s3_secret_access_key"]
        duckdb.query("INSTALL httpfs;LOAD httpfs;SET s3_region='eu-west-1';SET s3_access_key_id='" + access_key + "';SET s3_secret_access_key='" + secret +"'")
        print("Loaded S3 credentials")
    except:
        duckdb.query("INSTALL httpfs;LOAD httpfs")
        print("No s3 credentials found")
    
@st.cache_data
def convert_df(df):
    return df.to_csv().encode('utf-8')

def showTableScan(tableName):
    if (tableName != "-"):
        st.write("Table name: " + tableName)
        count = duckdb.query("SELECT count(*) as total FROM "+ tableName).df()
        st.write("Records: " + str(count["total"].iloc[0]))
        tableDf = duckdb.query("SELECT * FROM "+ tableName +" LIMIT 1000").df()
        c1,c2,c3 = st.columns([1, 3, 4])
        with c1:
            st.write("Schema")
            # Check this arrow warn
            st.write(tableDf.dtypes)
        with c2:
            st.write("Description")
            st.write(tableDf.describe())
        with c3:
            st.write("Sample data (1000)")
            st.write(tableDf.head(1000))
        if (st.button("Delete table '" + tableName + "' 🚫")):
            tableDf = None
            duckdb.query("DROP TABLE "+ tableName)
            st.experimental_rerun() 

def main():
    ses = st.session_state.sessionObject
    with st.sidebar:
        st.text_input('Project file', '', key='projectFile')
        col1, col2 = st.columns(2)
        with col1:
            if (st.button("Load")):
                st.write("Feature not implemented yet")
        with col2:
            if (st.button("Save")):
                st.write("Feature not implemented yet")
    
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
            #st.session_state.fileName = st.text_input('Local file, folder, http link or find S3 file (pressing Enter) 👇', st.session_state.fileName,  key='s3SearchText', on_change=s3SearchFile)
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
                            loadTable(tableName, ses["fileName"] + str(file))
                            if (ses["selectedTable"] is None): 
                                ses["selectedTable"] = tableName
                else:
                    loadTable(tableName, str(ses["fileName"]))          
                
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
        t = duckdb.query("SHOW TABLES")
        tableListArray = None
        if (t is not None):
            tableList = t.df()
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
                query = st.text_area("Query SQL ✏️","""SELECT * FROM YOUR_TABLE""")
                if st.button("Run query 🚀"):
                    with st.spinner('Running query...'):
                        ses["df"] = duckdb.query(query).df()
                        ses["df"].columns = ses["df"].columns.str.replace('.', '_')
                        queryTime = int(round(time.time() * 1000))
            with col2:
                askChat = st.text_area("Ask ChatGPT 💬")
                st.write("Example: Show me the 10 characters with the most published comics in descending order. I also want their gender and race")
                if st.button("Suggest query 🤔"):
                    tables = duckdb.query("SHOW TABLES")
                    with st.spinner('Waiting OpenAI API...'):
                        ses["chatGptResponse"] = askGpt(askChat, tables, st.secrets["openai_organization"], st.secrets["openai_api_key"])
                
                if (ses["chatGptResponse"] is not None):
                    st.text_area("ChatGPT answer", ses["chatGptResponse"])

            ################### Time and resources #################
            c1, c2, c3 = st.columns(3)
            with c1:
                pid = os.getpid()
                process = psutil.Process(pid)
                memory_info = process.memory_info()
                st.metric("Memory", str(round(memory_info.rss/1024/1024, 1)) + " Mb")
                if (st.button("Run GC 🧹")):
                    collected_objects = gc.collect()
            with c2:
                if (ses["totalTime"] != 0):
                    st.metric("Time last query", str(ses["lastQuery"]) + " ms")    
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
                
                if (("lat" in df.columns and "lon" in df.columns) or
                    ("latitude" in df.columns and "longitude" in df.columns)):

                    st.header("Detected spatial data")
                    st.map(df)
                else:
                    st.header("No spatial data detected")
                    st.write("Spatial fields should be named 'lat', 'latitude', 'LAT', 'LATITUDE' AND 'lon', 'longitude', 'LON', 'LONGITUDE' to be plotted in a map, use a SQL query to rename them if needed: Ej: Latitude as lat, Longitude as lon")

                st.header("Column data analysis")

                profile = Profiler(df)
                readable_report = profile.report(report_options={"output_format": "compact"})
                print(readable_report)

                for col in df.columns:
                    if (col.startswith("grp_")):
                        continue
                    st.divider()
                    st.markdown("####  " + col)
                    query='SELECT "' + col + '", count(*) as quantity FROM df GROUP BY "' + col + '" ORDER BY quantity DESC'
                    groupByValue = duckdb.query(query).df()
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
                ses["lastQuery"] = queryTime - startTime
                st.write("Total execution time: " + str(endTime - startTime) + " ms")
                ses["totalTime"] = endTime - startTime

def s3SearchFile():
    ses = st.session_state.sessionObject
    global S3_BUCKET
    if (ses["s3SearchText"] and not ses["s3SearchText"].startswith('/') and not ses["s3SearchText"].startswith('http') and S3_BUCKET is not None):
        with st.spinner('Searching in S3...'):
            ses["candidates"] = []
            s3Paths = s3Search(S3_BUCKET, ses["s3SearchText"])
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