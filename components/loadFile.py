import streamlit as st
import services.s3IndexService as s3Index
import services.duckDbService as db
import os


def s3SearchFile(ses, s3_bucket, s3SearchText):
    print("Searching in S3: " + s3SearchText)
    if (s3SearchText and not s3SearchText.startswith('/') and not s3SearchText.startswith('http')):
        with st.spinner('Searching in S3...'):
            ses["candidates"] = []
            s3Paths = s3Index.s3Search(s3_bucket, s3SearchText)
            if len(s3Paths) > 5:
                total = len(s3Paths)
                s3Paths = s3Paths[:5]
                s3Paths.append(f'... y {total - 5} mas')
            ses["candidates"] = s3Paths
            return

def loadDataFromFile(ses, s3_bucket):
    with st.expander("**Load data from files** 📂"):
        fcol1,fcol2,fcol3 = st.columns([4, 2, 1])
        with fcol1:
            ses["s3SearchText"]= st.text_input('Local file, folder, http link or find S3 file 👇', ses["s3SearchText"], key='s3SearchText')
            if (st.button("Search")):
                if (s3_bucket is None):
                    st.write("No S3_BUCKET defined use parameter '-- YOUR_BUCKET_NAME'")
                    return
                else:
                    s3SearchFile(ses, s3_bucket, str(ses["s3SearchText"]))

        with fcol2:
            tableName = st.text_input('Table name', 'iris', key='tableName')
        with fcol3:
            if (st.button("Load 👈")):
                if (str(ses["s3SearchText"]).endswith("/")):
                    files = os.listdir(ses["s3SearchText"])
                    for file in files:
                        if (file.endswith(".csv") or file.endswith(".parquet") or file.endswith(".json")):
                            tableName = os.path.splitext(file)[0]
                            db.loadTable(tableName, ses["s3SearchText"] + str(file), ses)
                            if (ses["selectedTable"] is None): 
                                ses["selectedTable"] = tableName
                else:
                    db.loadTable(tableName, str(ses["s3SearchText"]), ses)
                
        if (len(ses["candidates"]) > 0):
            st.markdown("#### Select S3 file:")
            for path in ses["candidates"]:
                if st.button(path):
                    ses["s3SearchText"] = path
                    st.experimental_rerun() 
            if (st.button("Close S3 file list")):
                ses["candidates"] = []
                st.experimental_rerun()

