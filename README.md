<div align="center">
<img src="https://github.com/javitorres/datalakeStudio/assets/4235424/462ac5ee-21a8-4a75-b3bc-cf90d36089b4" height="200">
</div>

<p align="center">
    <img src="https://img.shields.io/badge/Version-1.0.0-red" alt="Latest Release">
    <img src="https://img.shields.io/badge/DuckDB-0.9.0-yellow" alt="DuckDB">
    <img src="https://img.shields.io/badge/OpenAI-0.27.6-green" alt="OpenAI">
</p>


# Datalake Studio
Datalake Studio is a Python/HTML/Javascript application to explore datasets. You can explore your datafiles using the incredible DuckDB engine. 

You can load files directly from your computer, from a URL, or from an S3 bucket. You also can download data from your PostgreSQL Databases

If you have ChatGPT credentials, you can use the SQL assistant, which will have context about the tables and their fields.

Frontend is built with Vue.js and backend with Python Flask.


# Project build with Docker


```
docker-compose up --build
```

Open http://localhost:8080/ in your browser.

# Project build and without Docker

## Server

Inside server folder run:
```
pip3 install -r requirements.txt
python3 server.py
```

## Client

Inside the client folder of the project, run these commands to build the Vue UI project:

```
npm install
npm run dev -- --port 8080
```

Open http://localhost:8080/ in your browser.

# Configuration files

## Server

Inside server folder create a file named config.yml. Example:

```
port: 8000
database: "data/datalakeStudio.db"
```

And another file named secrets.yml with properties:

```
# Optional for DuckDB to work with S3, if not defined, user aws credentials will be loaded through the AWS Default Credentials Provider Chain
s3_access_key_id: "YOUR_S3_ACCESS_KEY_ID"
s3_secret_access_key: "YOUR_S3_SECRET_ACCESS_KEY"

# For OpenAI
openai_organization: "YOUR_OPENAI_ORGANIZATION"
openai_api_key: "YOUR_OPENAI_API_KEY"

# For API search
api_domain: "YOUR_API_DOMAIN"
api_context: "YOUR_API_CONTEXT"

# Database connections
pgpass_file: "YOUR_PG_PASS_FILE"

```

Also, docker-compose will get the credentials in .aws for AWS access
If you want to use remote database, copy your pgpass file to the server folder. pgpass is a file with the following format:


```
hostname:port:database:username:password
```
# Usage

## Load data

You can load data from local filesystem, from any URL or from S3. 
Try to load this example: https://raw.githubusercontent.com/javitorres/GenericCross/main/public/data/iris.csv

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/60c9761f-8f2f-42ee-819d-4b315566e57d)

## Table explorer

Inspect data and profile loaded data

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/5301e4ca-d2ae-4d34-a417-dbb946edbe55)

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/592bc7d9-45da-4e29-a02c-a35470124a11)

## Query panel

Query your data and generate new tables.

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/f5341884-f7a0-478d-98bb-8ee9a549adfd)

Use GPT assistant to generate SQL

Explore your data using automatic and interactive charts:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/a8e888f6-e3c8-4f5c-9923-262b1cb620fd)




# Shape files
https://duckdb.org/2023/04/28/spatial.html







