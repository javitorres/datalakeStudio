import streamlit as st

import services.duckDbService as db
import services.apiService as apiService
import pandas as pd

import json


def getFieldWithDotNotation(dict_obj, dot_notation):
    keys = dot_notation.split(".")
    for key in keys:
        dict_obj = dict_obj.get(key)
        if dict_obj is None:
            return None
    return dict_obj


def writeInParameters(methodInfo):
    inParameters = []
    if(methodInfo["method"]=="GET"):
        for param in methodInfo["parameters"]:
            type=None
            if ('type' in param):
                type=param["type"]
            elif ('schema' in param):
                type=param["schema"]["type"]
            else:
                type="unknown"
            if (type == "string"): icon="🔤"
            elif (type == "integer"): icon="🔢"
            elif (type == "boolean"): icon="🔘"
            elif (type == "array"): icon="[ ]"
            else: icon="🔳"
            print("param:" + str(param))
            if ("required" in param and param["required"] == True):
                st.markdown(icon + " **" + param["name"] + "** ")
            else:
                st.markdown(icon + " " + param["name"] + " :")
            st.markdown(apiService.getDescription(param))
            inParameters.append(param)
    elif(ses["methodInfo"]["method"]=="POST"):
        st.write(ses["methodInfo"]["requestBody"])
    else:
        st.write("Method not supported:" + ses["method"])
    
    return inParameters

def showTableScanMini(tableName):
    ses = st.session_state.sessionObject
    tableDf = db.runQuery("SELECT * FROM " + tableName + " LIMIT 1000")
    c1,c2 = st.columns([1, 7])
    if (tableDf is not None):
        with c1:
            st.write("Schema")
            st.write(tableDf.dtypes)
        with c2:
            st.write("Sample data (1000)")
            st.write(tableDf.head(1000))

def apiTool(ses):
    with st.expander("**Get data from external API** 🌐", expanded=False):
        tableTmp=None
        c1, c2 = st.columns((1, 1))
        ###### File Section
        with c1:
            st.markdown("**Table selection**")
            tableList = db.getTableList()
            if (tableList is not None):
                tableTmp = st.selectbox(label="Select table from list", options = tableList, key="tableForEnrichment")
                #tableTmp = st.session_state.tableForEnrichment
                showTableScanMini(tableTmp)

        ###### API Section
        with c2:
            st.markdown("**Connect dataset with API** 🧩")
            apiMenu = st.radio(
                "Configure the process...",
                ('...by searching the API', '...by writing directly the API URL'), key="apiMenu")
            environment="pro"
            if (apiMenu == '...by searching the API'):
                st.text_input("Service name", key="service_name")
                if (st.button("Search service")):
                    ses["services"] = ses["service"] = ses["methods"] = ses["method"] = ses["methodInfo"] = None
                    with st.spinner('Searching...'):
                        ses["services"] = apiService.getRepositories(st.session_state.service_name)

                if (ses["services"] is not None):
                    ses["service"] = st.selectbox(label="Select service", options = ses["services"], key="service")

                if (ses["service"] != None):
                    st.text_input("Method name", key="method_name")

                    if (st.button("Search methods")):
                        with st.spinner('Searching...'):
                            ses["methods"] = apiService.getRepositoryMethodList(ses["service"], st.session_state.method_name, environment, st.secrets["api_domain"], st.secrets["api_context"])
                            if (ses["methods"] is None or len(ses["methods"])==0):
                                st.write("Could not load any method")
                    
                    if (ses["methods"] is not None and len(ses["methods"])>0):
                        ses["method"] = st.selectbox(label="Select method", options = ses["methods"], key="method")

                    if (ses["method"] is not None):
                        with st.spinner('Loading method...'):
                            ses["methodInfo"] = apiService.getMethodInfo(ses["service"], ses["method"], environment, st.secrets["api_domain"], st.secrets["api_context"])
                    
                    if (ses["methodInfo"] is not None):
                        st.markdown("**Description**")
                        print("methodInfo:" + str(ses["methodInfo"]))
                        st.write(ses["methodInfo"]["summary"])

                        c1, c2 = st.columns((1, 1))
                        with c1:
                            st.markdown("**Input parameters**")
                            ses["inParameters"] = writeInParameters(ses["methodInfo"])
                            print("methodInfo1:" + str(ses["methodInfo"]))
                            
                        
                        with c2:
                            st.markdown("**Response**")
                            st.write(ses["methodInfo"]["responses"])
            elif (apiMenu == '...by writing directly the API URL'):
                st.write("Write here an API request example with query parameters for GET methods or empty for POST methods")
                st.text_input("API URL", key="manualApiUrl")

                if (st.button("Analyze URL")):
                    ses["services"] = ses["service"] = ses["methods"] = ses["method"] = ses["methodInfo"] = None
                    ses["methodInfo"] = apiService.getMethodInfoFromExample(st.session_state.manualApiUrl)
                    print("methodInfo2:" + str(ses["methodInfo"]))


        dfFields = db.getTableDescription(tableTmp)
        if (dfFields is not None and ses["methodInfo"] is not None):
            c1, c2, c3 = st.columns((1, 1, 1))
            tableDf = db.runQuery("SELECT * FROM " + tableTmp + " LIMIT 1")
            with c1:
                st.markdown("**Field mapping** 🔀")
                if(ses["methodInfo"]["method"]=="GET"):
                    dfFields.insert(0, "--")
                    st.write("Select the field to map with the API parameter")
                    for param in ses["methodInfo"]["parameters"]:                            
                        st.selectbox(label=param["name"], options = dfFields, key="pair_" + param["name"])
                    
                    if (tableDf is not None):
                        for index, row in tableDf.iterrows():
                            queryString=""
                            for param in ses["methodInfo"]["parameters"]:
                                if (st.session_state["pair_" + param["name"]]!="--"):
                                    fileValue = row[st.session_state["pair_" + param["name"]]]
                                    queryString += "&" + param["name"] + "=" + str(fileValue)
                elif(ses["methodInfo"]["method"]=="POST"):
                    st.write("Write the JSON body to send to the API, use the fields from the table with the format ${field_name}")
                    st.text_area("JSON body", key="jsonBody", height=400)

            with c2:
                st.markdown("**Api response example** 🔗")
                
                if(ses["methodInfo"]["method"]=="GET"):
                    print("queryString:" + queryString)
                    if (ses["methodInfo"]["origin"] == "SWAGGER"):
                        #url = "http://" + ses["service"] + "." + environment + "." + st.secrets["api_domain"] + ses["method"] + "?" + queryString
                        url = ses["methodInfo"]["url"] + "?" + queryString
                    elif (ses["methodInfo"]["origin"] == "EXAMPLE"):
                        url = ses["methodInfo"]["url"] + "?" + queryString
                    st.write("Response for 1st record:" + url)
                    r = apiService.getApi(url)
                    if (r is not None):
                        if (r.status_code != 200):
                            st.write("Error calling API: " + str(r.status_code))
                        else:
                            jsonString = json.dumps(r.json(), indent=4)
                            st.text_area("Response", value=jsonString, height=400)
                elif(ses["methodInfo"]["method"]=="POST"):
                    if (ses["methodInfo"]["origin"] == "SWAGGER"):
                        url = "http://" + ses["service"] + "." + environment + "." + st.secrets["api_domain"] + ses["method"]
                    elif (ses["methodInfo"]["origin"] == "EXAMPLE"):
                        url = st.session_state.manualApiUrl
                    st.write("Response for 1st record:" + url)
                    print("Test query:" + url)
                    bodyTemplate = st.session_state.jsonBody
                    # Replace ${field_name} with the value from the table
                    for col in dfFields:
                        bodyTemplate = bodyTemplate.replace("${"+col+"}", str(tableDf[col].iloc[0]))
                    st.text_area("Body", bodyTemplate, height=400)

                    r = apiService.postApi(url, bodyTemplate)
                    if (r is not None):
                        if (r.status_code != 200):
                            st.write("Error calling API: " + str(r.status_code))
                        else:
                            jsonString = json.dumps(r.json(), indent=4)
                            st.text_area("Response", value=jsonString, height=400)

                
            with c3:
                st.markdown("**Extract Fields** 🎯")
                st.write("Write field to load, example \: data.catastro.localizacion.seccionCensal. If the field is empty the whole response will be loaded in RESPONSE_JSON field")
                c1, c2 = st.columns((1, 1))
                with c1:
                    st.text_input(label="JSON field", key="jsonField", label_visibility='visible')
                with c2:
                    st.text_input(label="Table new field", key="newField", label_visibility='visible')

                if (st.button("Add")):
                    ses["fieldsToLoad"] = [field for field in ses["fieldsToLoad"] if field["jsonField"] != st.session_state.jsonField]
                    exampleValue = str(getFieldWithDotNotation(r.json(), st.session_state.jsonField ))
                    ses["fieldsToLoad"].append({"jsonField":st.session_state.jsonField, "newField":st.session_state.newField, "exampleValue":exampleValue})
                if (st.button("Delete all mappings")):
                    ses["fieldsToLoad"] = []

                if (ses["fieldsToLoad"] is not None and ses["fieldsToLoad"]!=[]):
                    st.write("Fields to load")
                    dfNewFields = pd.DataFrame(ses["fieldsToLoad"])
                    st.write(dfNewFields)

            c1, c2 = st.columns((2, 6))
            
            with c1:
                recordsToProcess = st.text_input(label="Select how many rows to process, empty for all ", key="recordsToProcess")
                
                if (st.button("Generate")):
                    my_bar = st.progress(0, text="Processing file...")

                    print("Button pressed")
                    ses["tableDfNew"] = None
                    query = "SELECT * FROM " + tableTmp
                    if (recordsToProcess is not None and recordsToProcess != ""):
                        query = "SELECT * FROM " + tableTmp + " LIMIT " + recordsToProcess
                                       
                    ses["tableDfNew"] = db.runQuery(query)
                    
                    print("Processing line:" + str(ses["methodInfo"]))
                    if (ses["tableDfNew"] is not None):
                        # For each row in the table
                        for index, row in ses["tableDfNew"].iterrows():
                            
                            queryString=""
                            if (ses["methodInfo"]["parameters"] is not None):
                                for param in ses["methodInfo"]["parameters"]:
                                    if (st.session_state["pair_" + param["name"]]!="--"):
                                        fileValue = row[st.session_state["pair_" + param["name"]]]
                                        queryString += "&" + param["name"] + "=" + str(fileValue)

                            if(ses["methodInfo"]["method"]=="GET"):
                                #url = "http://" + ses["service"] + "." + environment + "." + st.secrets["api_domain"] + ses["method"] + "?" + queryString
                                url = ses["methodInfo"]["url"] + "?" + queryString
                                r = apiService.getApi(url)
                            elif(ses["methodInfo"]["method"]=="POST"):
                                if (ses["methodInfo"]["origin"] == "SWAGGER"):
                                    url = "http://" + ses["service"] + "." + environment + "." + st.secrets["api_domain"] + ses["method"]
                                elif (ses["methodInfo"]["origin"] == "EXAMPLE"):
                                    url = st.session_state.manualApiUrl
                                
                                bodyTemplate = st.session_state.jsonBody
                                for col in dfFields:
                                    bodyTemplate = bodyTemplate.replace("${"+col+"}", str(row[col]))

                                r = apiService.postApi(url, bodyTemplate)
                                if (r is not None):
                                    if (r.status_code != 200):
                                        print("Error calling API: " + str(r.status_code))
                                    else:
                                        jsonString = json.dumps(r.json(), indent=4)

                            percent_complete = int((index+1) / len(ses["tableDfNew"]) * 100)
                            my_bar.progress(percent_complete, text="Processing file..." + str(percent_complete) + "%" + " (" + str(index+1) + "/" + str(len(ses["tableDfNew"])) + ")")
                            
                            if (ses["fieldsToLoad"] is not None):
                                if (r is not None):
                                    if (ses["fieldsToLoad"]==[]):
                                        ses["tableDfNew"].loc[index, "RESPONSE_STATUS"] = str(r.status_code)
                                        ses["tableDfNew"].loc[index, "RESPONSE_JSON"] = r.content.decode('utf-8')
                                    else:
                                        for field in ses["fieldsToLoad"]:
                                            value = getFieldWithDotNotation(r.json(), field["jsonField"])
                                            ses["tableDfNew"].loc[index, field["newField"]] = value

            if (ses["tableDfNew"] is not None):
                st.write("Result (max 100 rows))")
                st.write(ses["tableDfNew"].head(1000))
                if (st.button("Download file")):
                    st.write("Download table")
                    file_type = st.radio("Doanload as:", ("CSV", "Excel"), horizontal=True, label_visibility="collapsed")
                    if file_type == "CSV":
                        file = ses["tableDfNew"].to_csv().encode('utf-8')
                        st.download_button("Download dataframe", file, "report.csv", "text/csv", use_container_width=True)
                    elif file_type == "Excel":
                        file = convert_excel(ses["tableDfNew"])
                        st.download_button("Download dataframe", file, "report.xlsx", use_container_width=True)
                
                st.write("Save as a new table")
                tableName = st.text_input('Table name', 'table', key='newTableName')
                if (tableName != ""):
                    if (st.button("Save", key="saveTable")):
                        dfNew = ses["tableDfNew"]
                        db.saveDfAsTable("dfNew", tableName)
                        st.write("Table saved")
                        st.experimental_rerun()