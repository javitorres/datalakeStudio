
import streamlit as st
import services.duckDbService as db

@st.cache_data
def convert_df(df):
    return df.to_csv().encode('utf-8')

def showTableScan(tableName):
    ses = st.session_state.sessionObject
    if (tableName != "-"):
        if (st.button("Delete table '" + tableName + "' 🚫")):
            #tableDf = None
            db.runQuery("DROP TABLE "+ tableName)
            st.experimental_rerun()
        print("Loading to df")
        tableDf = db.runQuery("SELECT * FROM "+ tableName + " LIMIT 1000")
        c1,c2 = st.columns([1, 7])
        with c1:
            st.write("Schema")
            # Check this arrow warn
            st.write(tableDf.dtypes)
        with c2:
            st.write("Sample data (1000)")
            st.write(tableDf.head(1000))
        
        if (st.button("Download CSV", key="downloadCsvTable_" + tableName  )):
            exportedData = convert_df(tableDf)
            fileType="text/csv"
            file_name="report.csv"
            st.download_button("Click to download the file", data=exportedData, file_name=file_name, mime=fileType, use_container_width=True)
        
        #if (ses["loadedTables"][tableName]["profile"] is not None or st.button("Show profiler analysis", key="profiler_"+tableName)):
        #    showProfilerAnalysis(tableDf, tableName)

def tablesTool(ses):
    tableListArray = None
    try:
        tableList = db.runQuery("SHOW TABLES")
        tableListArray = None
        if (tableList is not None):
            tableListArray = tableList["name"].to_list()
    except:
        print("No tables loaded")

    if (tableListArray is not None and len(tableListArray) > 0):
        with st.expander(label="**Tables** 📄"):
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