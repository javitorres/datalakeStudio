<div align="center">
<img src="https://github.com/javitorres/datalakeStudio/assets/4235424/462ac5ee-21a8-4a75-b3bc-cf90d36089b4" height="200">
<br/>
<img src="https://github.com/javitorres/datalakeStudio/assets/4235424/3306a67f-91d3-4427-8214-96f8a1f02eb1" width=60% height=auto>
<br/><br/>
    
</div>

<p align="center">
    <img src="https://img.shields.io/badge/Version-1.0.0-red" alt="Latest Release">
    <img src="https://img.shields.io/badge/Vue-3.3.4-blue" alt="Vue3">
    <img src="https://img.shields.io/badge/DuckDB-0.9.2-yellow" alt="DuckDB">
    <img src="https://img.shields.io/badge/OpenAI-1.6.1-green" alt="OpenAI">
</p>

# Datalake Studio

Datalake Studio is an enhanced Data Exploration and Management tool

## Key Features of Datalake Studio:

<b>Quick for big data:</b> Datalake Studio is built on top of DuckDB, a high-performance, embedded SQL OLAP database management system. DuckDB is designed to handle large datasets, making it ideal for data exploration and analysis.

<b>Versatile Data Loading Options:</b> Users can effortlessly upload data from a several sources: directly from local computer, via a URL, or from an Amazon S3 bucket. Additionally, it supports direct data downloads from PostgreSQL databases, enhancing its utility for database administrators and data analysts.

<b>Several data formats and origins:</b> Embracing a wide range of data formats, the platform is compatible with CSV, TSV, and Shapefile formats. This flexibility ensures that users can work with their preferred data types without the need for tedious conversions.

<b>ChatGPT Integration with SQL Assistants:</b> Users with ChatGPT credentials can use the power of SQL assistants. These assistants provide contextual understanding about tables and their fields, making data manipulation and query formulation more intuitive and efficient.

<b>Enhancement through Remote APIs:</b> Users have the ability to enrich their data by integrating information from remote APIs.

<b>API Exposure for Data Sharing:</b> After completing data transformation processes, users can expose their data through APIs. This feature allows for easy sharing and collaboration, making Datalake Studio not just a tool for data exploration, but also a platform for data distribution.

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/786276af-5d2e-43a5-9f14-e56e7456e3ea)


# Project build with Docker

```
docker-compose up --build
```

Open http://localhost:8080/ in your browser.

# Project build without Docker

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

Also, docker-compose will get the credentials in .aws for AWS access.

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

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/5625c1e9-a399-4089-acd1-73381174089c)

Get data profile

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/959a1fae-2740-488e-b9ac-5e3c8079e8dd)

or use crossfilter to play with your data

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/392f50f8-6d8d-4a4f-a1fa-9e70c7fc652b)


## Query panel

Query your data and generate new tables. Save or load your queries. Use ChatGPT to create new queries

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/13de8f41-e002-4f2a-811b-a64a3fdeca19)

# Load data from APIs

Enrich your datasets calling external APIs

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/8a81495b-0e40-4829-af9e-f1081f871bb9)

New table:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/d367ddfa-089d-4670-8277-0693899b50cd)


# Load data from remote databases

Explore your external databases and load data into Datalake Studio for local analysis

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/948a0165-a908-43ce-b195-cdd17839f45e)


# Expose your data via API

Publish endpoints serving your data with parametrized queries:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/34537cf8-c59c-4167-940c-3c07a71e2cc5)

Keep control of endpoints published:

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/32ee7182-228c-4130-8ce7-482e464c3c0d)

# Explore your S3 buckets

Move in your S3 buckets and write descriptions

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/cd63c467-7cee-4fdc-8c9d-705372e8387e)

Preview files or load them into DatalaleStudio

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/16c1f44a-52a0-4593-9c42-4f687fe315b1)


# Talk to ChatGPT 
Talk to explore your data (experimental)

![image](https://github.com/javitorres/datalakeStudio/assets/4235424/e3913bb0-5741-4cac-b702-ad30f37d5fa5)







