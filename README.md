# datalakeStudio
Python+Streamlit application to explore datasets using SQL. It uses the incredible Duckdb engine.

If you have ChatGPT credentials you can use the SQL assistant who will have context about the tables and its fields

# Configuration

Create file .streamlit/secrets.toml in your home for your credentials:

s3_access_key_id="XXXXXXXXXXXXXXXXXX"
s3_secret_access_key="XXXXXXXXXXXXXXXXXX"
openai_organization="XXXXXXXXXXXXXXXXXX"
openai_api_key="XXXXXXXXXXXXXXXXXX"

# How to start application
Run following command:
```
streamlit run datalakeStudio.py -- YOUR_S3_BUCKET
```

# Usage

Write the file name to load (CSV, parquet or JSON):

* Any local a file: /fileFolder/file.csv
* Local folder: "/fileFolder/". Load all csv, parquet and json files in the folder and create one table for each file
* A URL, for example: https://gist.githubusercontent.com/netj/8836201/raw/6f9306ad21398ea43cba4f7d537619d0e07d5ae3/iris.csv
* S3 file name. Press Enter and script will search in your S3 bucket. Click on any suggestion to load


Click load button to load the table/s

Now you can run any SQL expression on the loaded tables. You can use ChatGPT assistant on the right to help you to write the SQL queries.

Click on "Run Query" and you'll see below the resulting dataset and analysis.







