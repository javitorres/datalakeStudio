import streamlit as st

from PIL import Image

def sideBar():
    with st.sidebar:
        logo = Image.open('images/logo.png')
        st.image(logo, width=200)

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
        
        st.markdown("---")
        st.markdown(
            '<h6>Made in &nbsp<img src="https://streamlit.io/images/brand/streamlit-mark-color.png" alt="Streamlit logo" height="16">&nbsp Twitter: <a href="https://twitter.com/datalakestudio">@datalakestudio</a></h6>',
            unsafe_allow_html=True,
        )