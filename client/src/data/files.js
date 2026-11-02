import { quoteIdent, quoteLiteral } from './sql';

// The DuckDB function that reads each kind of file (gzip-compressed CSV and JSON are read directly)
const READERS = [
  [/\.(csv|tsv|txt)(\.gz)?$/i, (path) => `read_csv_auto(${quoteLiteral(path)}, HEADER=TRUE, SAMPLE_SIZE=1000000)`],
  [/\.(parquet|pq)(\.gz)?$/i, (path) => `read_parquet(${quoteLiteral(path)})`],
  [/\.(json|ndjson|jsonl)(\.gz)?$/i, (path) => `read_json_auto(${quoteLiteral(path)}, maximum_object_size=60000000)`],
  [/\.(shp|geojson|gpkg|kml)$/i, (path) => `ST_Read(${quoteLiteral(path)})`],
];

export function isSupportedFile(path) {
  return READERS.some(([pattern]) => pattern.test(path));
}

// Geographic formats are read by the spatial extension
export function needsSpatial(path) {
  return /\.(shp|geojson|gpkg|kml)$/i.test(path);
}

// CREATE TABLE statement that loads a file (a URL, or a name the engine registered) into a table
export function loadFileSql(tableName, path) {
  const reader = READERS.find(([pattern]) => pattern.test(path.split('?')[0]));
  if (!reader) throw new Error('Unsupported file type: ' + path.split('/').pop());
  // CREATE OR REPLACE keeps the previous table if the new file fails
  return `CREATE OR REPLACE TABLE ${quoteIdent(tableName)} AS (SELECT * FROM ${reader[1](path)})`;
}

// The file to read inside an unpacked zip: a shapefile's .shp, otherwise the first data file
export function mainFileInZip(names) {
  return names.find((name) => /\.shp$/i.test(name)) || names.find(isSupportedFile) || null;
}
