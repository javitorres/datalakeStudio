<div align="center">
<img src="https://github.com/javitorres/datalakeStudio/assets/4235424/462ac5ee-21a8-4a75-b3bc-cf90d36089b4" height="200">
<br/>
<img src="https://github.com/javitorres/datalakeStudio/assets/4235424/3306a67f-91d3-4427-8214-96f8a1f02eb1" width=60% height=auto>
<br/><br/>
</div>

<p align="center">
    <img src="https://img.shields.io/badge/Version-1.0.0-red" alt="Version">
    <img src="https://img.shields.io/badge/Vue-3.4-blue" alt="Vue 3">
    <img src="https://img.shields.io/badge/FastAPI-0.108-009688" alt="FastAPI">
    <img src="https://img.shields.io/badge/DuckDB-1.5.4-yellow" alt="DuckDB">
    <img src="https://img.shields.io/badge/License-GPLv3-green" alt="License: GPL v3">
</p>

# Datalake Studio

**From raw data to ready-to-use APIs.** Datalake Studio is an open-source data
workspace: load data from anywhere, explore millions of rows with DuckDB, query
with SQL or an AI assistant, visualise it on charts and maps, and publish any
query as a live REST API — all from a single tool that runs on your machine.

Built with **Vue 3** (frontend), **FastAPI** (backend) and **DuckDB** (engine).

![Datalake Studio overview](https://github.com/javitorres/datalakeStudio/assets/4235424/786276af-5d2e-43a5-9f14-e56e7456e3ea)

## Table of contents

- [Key features](#key-features)
- [Quick start (Docker)](#quick-start-docker)
- [Running without Docker](#running-without-docker)
- [Configuration](#configuration)
- [Tests](#tests)
- [Usage](#usage)
- [License](#license)

## Key features

- **Fast on big data** — Built on top of [DuckDB](https://duckdb.org/), a
  high-performance embedded OLAP engine designed to handle large datasets, ideal
  for exploration and analysis.
- **Load from anywhere** — Upload from your computer, pull from a URL, browse an
  Amazon S3 bucket, or import directly from PostgreSQL databases.
- **Many formats** — CSV, TSV, Parquet, JSON and Shapefile, with no tedious
  conversions.
- **Visualise your data** — Automatic charts, interactive cross-filters, and
  geospatial maps with point and H3 hexagon aggregations.
- **AI SQL assistant** — With OpenAI credentials, describe what you need in plain
  language and get DuckDB SQL that already knows your tables and fields.
- **Enrich from remote APIs** — Augment your datasets by calling external APIs.
- **Publish as an API** — Turn any saved query into a parameterised REST endpoint
  and share live data with other applications.
- **Multi-user** — Optional login with username/password or "Sign in with
  Google", each user with their own workspace.

## Quick start (Docker)

The fastest way to run the whole stack (frontend + backend).

**Prerequisites:** Docker and Docker Compose. Ports **8080** and **8000** must be
free on your machine.

```bash
docker-compose up --build
```

Then open **http://localhost:8080/** in your browser. The backend API runs on
**http://localhost:8000/**.

Datalake Studio works out of the box for local files and URLs. To enable S3,
PostgreSQL, the AI assistant or maps, add a `server/secrets.yml` file (see
[Configuration](#configuration)). Docker Compose also mounts your `~/.aws`
credentials into the backend for AWS access.

### Without Compose

Build and run each image separately:

```bash
# Backend
docker build -t datalakestudio-backend ./server
docker run --name datalakestudio-backend -p 8000:8000 datalakestudio-backend

# Frontend
docker build -t datalakestudio-frontend ./client
docker run --name datalakestudio-frontend -p 8080:8080 datalakestudio-frontend
```

## Running without Docker

### Server

From the `server/` folder:

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

Requires **Python 3.10+** (DuckDB 1.5+ needs it). Exit the virtualenv with
`deactivate`.

### Client

From the `client/` folder:

```bash
npm install
npm run dev -- --port 8080
```

Then open **http://localhost:8080/**.

By default the client talks to the backend at `http://localhost:8000`. To point
it elsewhere, create a `client/.env` file:

```bash
VITE_API_URL=https://your-backend-host      # e.g. behind a reverse proxy
# or, individually:
# VITE_API_HOST=http://localhost
# VITE_API_PORT=8000
# VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

## Configuration

### `server/config.yml`

Server behaviour. Example:

```yaml
port: 8000
databasesFolder: "data"          # where per-user databases are stored
defaultDatabase: "datalakeStudio.db"
downloadFolder: "temp"           # temp folder for uploads and exports
authEnabled: false               # true = require login; false = anonymous "default" user
allowedOrigins:                  # CORS origins for app endpoints (not /api/*)
  - "http://localhost:8080"
```

### `server/secrets.yml`

Credentials and optional integrations. Copy the template and fill in what you
need — everything is optional depending on the features you use:

```bash
cp server/secrets.yml.template server/secrets.yml
```

It covers S3 access, OpenAI (AI assistant), the API search domain, the PostgreSQL
`pgpass` file, a Mapbox token (maps), Google OAuth and SMTP (email verification /
password recovery). If you enable `authEnabled`, also set a strong `jwt_secret`.

> **Never commit `secrets.yml` or `.pgpass`.** They are already in `.gitignore`,
> and a pre-commit hook in `.githooks/` blocks accidental secret commits — enable
> it with `git config core.hooksPath .githooks`.

### Remote databases (`.pgpass`)

To use remote PostgreSQL databases, point `pgpass_file` at a file with one line
per connection:

```
hostname:port:database:username:password
```

## Tests

```bash
# Backend (from server/, with the virtualenv active)
python -m pytest -q

# Frontend (from client/)
npm run test:run
```

## Usage

### Load data

Load from your local filesystem, any URL, or S3. Try this example dataset:
`https://raw.githubusercontent.com/javitorres/GenericCross/main/public/data/iris.csv`

![Load data](https://github.com/javitorres/datalakeStudio/assets/4235424/6954818b-94f6-4438-b7b7-012f42edeb63)

### Table explorer

Inspect loaded data and export it to CSV or Parquet.

![Table explorer](https://github.com/javitorres/datalakeStudio/assets/4235424/5625c1e9-a399-4089-acd1-73381174089c)

Get a data profile:

![Data profile](https://github.com/javitorres/datalakeStudio/assets/4235424/959a1fae-2740-488e-b9ac-5e3c8079e8dd)

Or use cross-filters to explore interactively:

![Cross-filter](https://github.com/javitorres/datalakeStudio/assets/4235424/392f50f8-6d8d-4a4f-a1fa-9e70c7fc652b)

If your data has spatial information, view it on a map:

![Map view](https://github.com/user-attachments/assets/cc91394c-1f4a-4b3b-9065-983b6efd3764)

<img width="1239" alt="Map points" src="https://github.com/user-attachments/assets/5be35c2f-72ba-4678-a36f-4c2cab45046b">

<img width="1251" alt="H3 aggregation" src="https://github.com/user-attachments/assets/641c757a-c228-4f1d-9ad0-5c1d72554a99">

### Query panel

Query your data and generate new tables. Save and load queries, or ask the AI
assistant to write SQL for you.

![Query panel](https://github.com/javitorres/datalakeStudio/assets/4235424/13de8f41-e002-4f2a-811b-a64a3fdeca19)

### Enrich from APIs

Enrich your datasets by calling external APIs:

![API enrichment](https://github.com/javitorres/datalakeStudio/assets/4235424/8a81495b-0e40-4829-af9e-f1081f871bb9)

Resulting table:

![Enriched table](https://github.com/javitorres/datalakeStudio/assets/4235424/d367ddfa-089d-4670-8277-0693899b50cd)

### Load from remote databases

Explore external databases and load data into Datalake Studio for local analysis:

![Remote databases](https://github.com/javitorres/datalakeStudio/assets/4235424/948a0165-a908-43ce-b195-cdd17839f45e)

### Expose your data via API

Publish endpoints that serve your data with parameterised queries:

![Publish API](https://github.com/javitorres/datalakeStudio/assets/4235424/34537cf8-c59c-4167-940c-3c07a71e2cc5)

Keep control of the endpoints you publish:

![Manage endpoints](https://github.com/javitorres/datalakeStudio/assets/4235424/32ee7182-228c-4130-8ce7-482e464c3c0d)

### Explore your S3 buckets

Navigate your S3 buckets and add descriptions:

![S3 explorer](https://github.com/javitorres/datalakeStudio/assets/4235424/cd63c467-7cee-4fdc-8c9d-705372e8387e)

Preview files or load them into Datalake Studio:

![S3 preview](https://github.com/javitorres/datalakeStudio/assets/4235424/16c1f44a-52a0-4593-9c42-4f687fe315b1)

### Talk to ChatGPT

Explore your data conversationally (experimental):

![ChatGPT](https://github.com/javitorres/datalakeStudio/assets/4235424/e3913bb0-5741-4cac-b702-ad30f37d5fa5)

## License

Distributed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE)
for details.
