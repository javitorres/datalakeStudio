![image](https://github.com/javitorres/datalakeStudio/assets/4235424/462ac5ee-21a8-4a75-b3bc-cf90d36089b4)

# Datalake Studio
A Python, Streamlit, and DuckDB application to explore datasets using SQL, powered by the incredible DuckDB engine.

If you have ChatGPT credentials, you can use the SQL assistant, which will have context about the tables and their fields.
# Configuration

Install dependencies listed in requirements.txt:

```
pip install -r requirements.txt
```
Optional: Create file .streamlit/secrets.toml in your home directory for your credentials:

```
s3_access_key_id="XXXXXXXXXXXXXXXXXX"
s3_secret_access_key="XXXXXXXXXXXXXXXXXX"
openai_organization="XXXXXXXXXXXXXXXXXX"
openai_api_key="XXXXXXXXXXXXXXXXXX"
```

# How to start application
Run the following command:

```
streamlit run datalakeStudio.py
```

Or use this command if you want to load files from an S3 bucket:

```
streamlit run datalakeStudio.py -- YOUR_S3_BUCKET
```

# Usage

Enter the file name to load (CSV, Parquet, or JSON):

* Any local file: /fileFolder/file.csv
* Local folder: "/fileFolder/". This will load all CSV, Parquet, and JSON files in the folder and create one table for each file.
* A URL, for example: 
https://gist.githubusercontent.com/netj/8836201/raw/6f9306ad21398ea43cba4f7d537619d0e07d5ae3/iris.csv
* S3 file name. Press Enter and the script will search in your S3 bucket. Click on any suggestion to load the file


Click the load button to load the table(s) and quickly get insights about the loaded files:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/9e19f603-0926-4240-9a36-76a1176b40df)

View automatic distribution charts for cathegorical and numerical variables 

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/f1fc034b-1026-48b3-87e1-91a768a5032b)

If your data has geodata you can see them in a map directly:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/6cef3eff-9882-4731-9579-ec3dc237bc10)

Run your own SQL queries or ask ChatGPT to do it for you. ChatGPT has contextual information about the loaded tables and their fields:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/105c115b-f7ed-49de-801a-ca317628af08)

When finished you can download results as CSV or Excel:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/30acd76f-a2b3-489d-9290-e511ae94f6a8)

# Test online

You can test the application (only able to load files via HTTP) here: https://javitorres-datalakestudio-datalakestudio-km7ylm.streamlit.app/





