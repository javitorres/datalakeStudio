<div align="center">
<img src="https://github.com/javitorres/datalakeStudio/assets/4235424/462ac5ee-21a8-4a75-b3bc-cf90d36089b4" height="200">
</div>

<p align="center">
    <img src="https://img.shields.io/badge/Version-1.0.0-red" alt="Latest Release">
    <img src="https://img.shields.io/badge/Vue-3.3.4-blue" alt="Vue3">
    <img src="https://img.shields.io/badge/DuckDB-0.9.2-yellow" alt="DuckDB">
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

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/6954818b-94f6-4438-b7b7-012f42edeb63)

## Table explorer

Inspect loaded data. Export data to CSV or Parquet

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/6994281c-d59a-4962-8337-6248239ec35f)

Get data profile

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/34a260d5-396a-4e08-a782-e26f0067e75f)

Use crossfilter to play with your data

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/2e08c714-7f03-4610-9e92-7151fd42cf7b)


## Query panel

Query your data and generate new tables. Save or load your queries. Use ChatGPT to create new queries

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/1ae4eb9a-15db-4f4b-b6c6-170635cdd2d1)


# Load data from APIs

Enrich your datasets calling external APIs

# Load data from remote databases

Explore your external databases and load data into Datalake Studio for local analysis

# Talk to ChatGPT 
Talk to explore your data (experimental)

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/e3913bb0-5741-4cac-b702-ad30f37d5fa5)







