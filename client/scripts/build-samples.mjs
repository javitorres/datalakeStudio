// Builds the sample datasets the public app offers to newcomers (node scripts/build-samples.mjs).
// They are served by the app itself (public/samples), so the browser loads them without CORS and
// without third parties. They come from the NYC Taxi & Limousine Commission's open data.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DuckDBInstance } from '@duckdb/node-api';

const OUT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'public', 'samples');
const TRIPS_URL = 'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet';
const ZONES_URL = 'https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip';
const TAXI = path.join(OUT, 'nyc_taxi_2024_01.parquet');
const SAMPLE_ROWS = 200000;

if (fs.existsSync(TAXI) && !process.argv.includes('--force')) {
  console.log(`${path.relative(process.cwd(), TAXI)} already exists (--force rebuilds it)`);
  process.exit(0);
}

fs.mkdirSync(OUT, { recursive: true });
const zip = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'samples-')), 'taxi_zones.zip');
fs.writeFileSync(zip, Buffer.from(await (await fetch(ZONES_URL)).arrayBuffer()));

const db = await DuckDBInstance.create(':memory:');
const con = await db.connect();
await con.run(`
  INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs;
  CREATE TABLE zones AS
    SELECT LocationID, zone, borough, round(ST_Y(c), 5) AS lat, round(ST_X(c), 5) AS lon
    FROM (SELECT *, ST_Transform(ST_Centroid(geom), 'EPSG:2263', 'EPSG:4326', always_xy := true) AS c
          FROM ST_Read('/vsizip/${zip}/taxi_zones/taxi_zones.shp'));
  -- A reproducible sample of the month, each trip with its pickup and drop-off zones
  COPY (
    SELECT t.tpep_pickup_datetime AS pickup_time, t.tpep_dropoff_datetime AS dropoff_time,
           t.passenger_count, t.trip_distance, t.fare_amount, t.tip_amount, t.total_amount,
           CASE t.payment_type WHEN 1 THEN 'Credit card' WHEN 2 THEN 'Cash' WHEN 3 THEN 'No charge'
                               WHEN 4 THEN 'Dispute' ELSE 'Other' END AS payment,
           pu.zone AS pickup_zone, pu.borough AS pickup_borough, pu.lat AS pickup_lat, pu.lon AS pickup_lon,
           dz.zone AS dropoff_zone, dz.borough AS dropoff_borough
    FROM (SELECT * FROM read_parquet('${TRIPS_URL}')
          WHERE tpep_pickup_datetime >= '2024-01-01' AND tpep_pickup_datetime < '2024-02-01'
          USING SAMPLE reservoir(${SAMPLE_ROWS} ROWS) REPEATABLE (42)) t
    JOIN zones pu ON t.PULocationID = pu.LocationID
    JOIN zones dz ON t.DOLocationID = dz.LocationID
    ORDER BY pickup_time
  ) TO '${TAXI}' (FORMAT PARQUET, COMPRESSION ZSTD);`);
const rows = await con.runAndReadAll(`SELECT count(*)::INT AS n FROM '${TAXI}'`);
console.log(`${path.relative(process.cwd(), TAXI)}: ${rows.getRowObjects()[0].n} trips, ${(fs.statSync(TAXI).size / 1024 / 1024).toFixed(1)} MB`);
