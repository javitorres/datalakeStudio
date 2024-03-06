#!/bin/bash
duckdb data/datalakeStudio.db -s "EXPORT database 'datalakeStudio_vacuum' (FORMAT PARQUET)"
#mv data/datalakeStudio.db data/datalakeStudio.db.bak 
#duckdb data/datalakeStudio.db -s "IMPORT database 'datalakeStudio_vacuum'"