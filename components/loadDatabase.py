import streamlit as st
import services.duckDbService as db
import services.remoteDbService as remoteDb


def loadDataFromDatabase(ses):
    with st.expander("**Load data from a Database** 🛢️"):
        c1, c2 = st.columns((1, 1))
        with c1:
            st.text_input("Search text", key="database_search_text")
            if (st.button("Search database")):
                ses["databases"] = remoteDb.getDbList(st.session_state.database_search_text)
                if (ses["databases"] is None or len(ses["databases"])==0):
                    st.write("Could not load any database")

            if (ses["databases"] is not None):

                ses["database"] = st.selectbox(label="Select database", options = ses["databases"], key="database")
                #st.write("Selected database: " + str(ses["database"]))

                if (st.button("Connect")):
                    remoteDb.closeConnection(ses["connection"])
                    ses["connection"] = remoteDb.getConnection(ses["database"])
                
                if (ses["connection"] is not None):
                    st.write("✅ Connected to database: " + str(ses["database"]))

                    ses["schemas"] = remoteDb.getSchemas(ses["connection"])
                    if (ses["schemas"] is not None):
                        ses["schema"] = st.selectbox(label="Select schema", options = ses["schemas"], key="schema")
                        st.write("Selected schema: " + str(ses["schema"]))
        
        with c2:
            if (ses["connection"] is not None and ses["schema"] is not None):
                tableList = remoteDb.showTables(ses["connection"], ses["schema"])
                strTables = [i[0] for i in tableList]
                result = "\n".join(strTables)
                st.text_area("Tables", value=result, height=300)
        
        queryToRun = st.text_area("Query SQL ✏️")
        
        if st.button("Run query 🚀", key="runQuery1"):
            with st.spinner('Running query...'):
                ses["dfRemoteDb"] = remoteDb.runQuery(ses["connection"], queryToRun)
                st.write(ses["dfRemoteDb"])

        if (ses["dfRemoteDb"] is not None):
            st.write("Save as a new table")
            tableName = st.text_input('Table name', 'table', key='newTableName2')
            if (tableName != ""):
                if (st.button("Save", key="saveTable2")):
                    df=ses["dfRemoteDb"]
                    db.saveDfAsTable("df", tableName)
                    st.write("Table saved")
                    st.experimental_rerun()