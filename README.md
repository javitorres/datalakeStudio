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
npm run dev
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
# Necessary for DuckDB to work with S3
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

