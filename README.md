<div align="center">
<img src="https://github.com/javitorres/datalakeStudio/assets/4235424/462ac5ee-21a8-4a75-b3bc-cf90d36089b4" height="200">
</div>

<p align="center">
    <img src="https://img.shields.io/badge/Version-0.1.0-red" alt="Latest Release">
    <img src="https://img.shields.io/badge/DuckDB-0.8.0-yellow" alt="DuckDB">
    <img src="https://img.shields.io/badge/Streamlit-1.21.0-blueviolet" alt="Streamlit">
    <img src="https://img.shields.io/badge/OpenAI-0.27.6-green" alt="OpenAI">
</p>


# Datalake Studio
Datalake Studio is a very simple Python application to explore datasets using SQL, powered by the incredible DuckDB engine and the fantastic framework Streamlit. It also uses the DataProfiler library to get insights about the loaded data.

You can load files directly from your computer, from a URL, or from an S3 bucket. Now you also can download data from a PostgreSQL Database and retrieve data from an external URL

[DatalakeStudioSubs.webm](https://github.com/javitorres/datalakeStudio/assets/4235424/e4396cfb-297a-4ce4-bf8d-f751d0b9dbd0)

If you have ChatGPT credentials, you can use the SQL assistant, which will have context about the tables and their fields.

# Configuration

Install dependencies listed in requirements.txt:

```
pip install -r requirements.txt
```
Optional: Create file .streamlit/secrets.toml in your home directory for your credentials and other configuration details:

```
# S3
s3_access_key_id="XXXXXXXXXXXXXXXXXX"
s3_secret_access_key="XXXXXXXXXXXXXXXXXX"

# ChatGPT
openai_organization="XXXXXXXXXXXXXXXXXX"
openai_api_key="XXXXXXXXXXXXXXXXXX"

# API search
api_domain="yourdomain.com"
api_context="yourApiServiceContext"

# Database connection file
pgpass_file="pathToYour/.pgpass"
```


# Start application
Run the following command:

```
streamlit run datalakeStudio.py
```

Or use this command if you want to load files from an S3 bucket:

```
streamlit run datalakeStudio.py -- YOUR_S3_BUCKET
```

# Dockerfile

If you prefer to use Docker, you can build the image with the following command:

```
docker build -t datalakestudio .
```

And run it with:

```
docker run -p 8080:8501 --name datalakestudio datalakestudio
```

Then open your browser at http://localhost:8080

To run the container with your own credentials, edit the file secrets.toml.template in your home directory with the following content:

```
s3_access_key_id="PUT_HERE_YOUR_S3_ACCESS_KEY_ID"
s3_secret_access_key="PUT_HERE_YOUR_SECRET_ACCESS_KEY"
openai_organization="PUT_HERE_YOUR_OPENAI_ORGANIZATION_ID"
openai_api_key="PUT_HERE_YOUR_OPENAI_API_KEY"
```

or run with the following command to use your AWS credentials:

```
docker run -p 8080:8501 -v ~/.aws:/root/.aws --name datalakestudio datalakestudio
```

Then rebuild the image with the first command ahead.

Or if you prefer, after editing config files, all together:
```
docker build -t datalakestudio . && docker run -v ~/.aws:/root/.aws -e BUCKET_NAME=YOUR_BUCKET -p 8080:8501 --name datalakestudio datalakestudio
```

To stop the container simply run:

```
docker stop datalakestudio
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

When finished you can download results as CSV:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/30acd76f-a2b3-489d-9290-e511ae94f6a8)

# Load data from a PostgreSQL database

Connect to your databases adding the path to your DBeaver config file or any file with rows like this:

```
host:port:database:user:pass
```

Add the path to your config file in .streamlit/secrets.toml:

```
pgpass_file="pathToYour/.pgpass"
```
Then you can search and load data with a query

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/823ca136-0c39-4956-abfe-18ab736bda5c)



# Load data from an external URL

Now you can add columns from an external URL using GET or POST http requests and using columns of your dataset as parameters

[output.webm](https://github.com/javitorres/datalakeStudio/assets/4235424/a57d2377-7513-499b-8b84-bf1e4875f5a8)


# Test online

You can test the application (only able to load files via HTTP) here: https://javitorres-datalakestudio-datalakestudio-km7ylm.streamlit.app/





