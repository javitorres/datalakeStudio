import { getDatabaseSchema } from './tables';
import { quoteIdent } from './sql';
import { uiType } from './types';

// Map layers: points, H3 hexagons and geometries inside the visible area, as GeoJSON. The SQL builds
// the geometries (ST_AsGeoJSON), so both engines return the same features.

const MAX_POINTS = 100000;
const MAX_GEOMETRIES = 1000;
// Geometry columns are stored as WKT in this projection (UTM 30N), as the backend always assumed
export const DEFAULT_SOURCE_CRS = 'EPSG:32630';

// "west,south,east,north" (or an array) into checked numbers
export function parseBbox(bbox) {
  const values = (Array.isArray(bbox) ? bbox : String(bbox).split(',')).map(Number);
  if (values.length !== 4 || !values.every(Number.isFinite)) {
    throw new Error('bbox must contain four finite numbers');
  }
  const [west, south, east, north] = values;
  if (!(west >= -180 && west < east && east <= 180 && south >= -90 && south < north && north <= 90)) {
    throw new Error('bbox is outside valid longitude/latitude bounds');
  }
  return { west, south, east, north };
}

// Checks the columns exist (__lastQuery included) and that the aggregated ones are numeric
async function checkColumns(engine, table, columns, numericColumns = []) {
  const schema = (await getDatabaseSchema(engine, { includeHidden: true }))[table];
  if (!schema) throw new Error(`Unknown table: ${table}`);
  const missing = [...columns, ...numericColumns].filter((column) => column && !(column in schema));
  if (missing.length) throw new Error(`Unknown columns: ${missing.join(', ')}`);
  const notNumeric = numericColumns.filter((column) => uiType(schema[column]) !== 'numeric');
  if (notNumeric.length) throw new Error(`Aggregation columns must be numeric: ${notNumeric.join(', ')}`);
  return schema;
}

function insideBbox(latitudeField, longitudeField, { west, south, east, north }) {
  const lat = `TRY_CAST(${quoteIdent(latitudeField)} AS DOUBLE)`;
  const lon = `TRY_CAST(${quoteIdent(longitudeField)} AS DOUBLE)`;
  return `${lat} BETWEEN ${south} AND ${north} AND ${lon} BETWEEN ${west} AND ${east}`;
}

// The cross-filter predicate, appended to the WHERE clause
function andFilter(filter) {
  return filter && filter.trim() ? ` AND (${filter.trim()})` : '';
}

// One point per row (up to MAX_POINTS), with the numeric fields as properties
export async function mapPoints(engine, { table, latitudeField, longitudeField, fields = [], bbox, filter = '' }) {
  if (!latitudeField || !longitudeField) throw new Error('Latitude and longitude columns are required');
  const extra = fields.filter((field) => field !== latitudeField && field !== longitudeField);
  await checkColumns(engine, table, [latitudeField, longitudeField], extra);
  const sql = `
    SELECT round(TRY_CAST(${quoteIdent(latitudeField)} AS DOUBLE), 5) AS latitude,
           round(TRY_CAST(${quoteIdent(longitudeField)} AS DOUBLE), 5) AS longitude
           ${extra.map((field) => `, ${quoteIdent(field)}`).join('')}
    FROM ${quoteIdent(table)}
    WHERE ${insideBbox(latitudeField, longitudeField, parseBbox(bbox))}${andFilter(filter)}
    LIMIT ${MAX_POINTS}`;
  const rows = await engine.query(sql);
  return featureCollection(rows.map(({ latitude, longitude, ...properties }) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [longitude, latitude] },
    properties,
  })));
}

// Rows aggregated into H3 cells of the given level: count and the average of each numeric field
export async function mapCells(engine, { table, latitudeField, longitudeField, fields = [], level = 5, bbox, filter = '' }) {
  const h3Level = Number(level);
  if (!Number.isInteger(h3Level) || h3Level < 0 || h3Level > 15) throw new Error('H3 level must be between 0 and 15');
  await checkColumns(engine, table, [latitudeField, longitudeField], fields);
  await engine.loadExtension?.('h3');
  await engine.loadExtension?.('spatial');
  const lat = `TRY_CAST(${quoteIdent(latitudeField)} AS DOUBLE)`;
  const lon = `TRY_CAST(${quoteIdent(longitudeField)} AS DOUBLE)`;
  const sql = `
    SELECT h3_h3_to_string(h3_cell) AS h3_cell,
           ST_AsGeoJSON(ST_GeomFromText(h3_cell_to_boundary_wkt(h3_cell))) AS geometry,
           count(*) AS count
           ${fields.map((field) => `, avg(${quoteIdent(field)}) AS ${quoteIdent(field)}`).join('')}
    FROM (
      SELECT *, h3_latlng_to_cell(${lat}, ${lon}, ${h3Level}) AS h3_cell
      FROM ${quoteIdent(table)}
      WHERE ${insideBbox(latitudeField, longitudeField, parseBbox(bbox))}${andFilter(filter)}
    ) AS source_rows
    GROUP BY h3_cell
    ORDER BY count DESC`;
  return timed(() => engine.query(sql), (rows) => rows.map(({ geometry, ...properties }) =>
    feature(geometry, withDefaults(properties, ['count', ...fields]))));
}

// Rows with a geometry column (WKT text or GEOMETRY) inside the visible area, in lon/lat
export async function mapGeometries(engine, { table, geomField, fields = [], bbox, filter = '', sourceCrs = DEFAULT_SOURCE_CRS }) {
  const schema = await checkColumns(engine, table, [geomField], fields);
  await engine.loadExtension?.('spatial');
  const { west, south, east, north } = parseBbox(bbox);
  const column = quoteIdent(geomField);
  const source = /^GEOMETRY\b/i.test(schema[geomField]) ? column : `ST_GeomFromText(${column})`;
  // always_xy keeps lon/lat order (DuckDB 2.0 refuses the transform without it)
  const lonLat = `ST_Transform(${source}, '${sourceCrs}', 'EPSG:4326', always_xy := true)`;
  const sql = `
    SELECT ST_AsGeoJSON(${lonLat}) AS geometry
           ${fields.map((field) => `, ${quoteIdent(field)}`).join('')}
    FROM ${quoteIdent(table)}
    WHERE ${column} IS NOT NULL
      AND ST_Intersects(${lonLat}, ST_MakeEnvelope(${west}, ${south}, ${east}, ${north}))${andFilter(filter)}
    LIMIT ${MAX_GEOMETRIES}`;
  return timed(() => engine.query(sql), (rows) => rows.map(({ geometry, ...properties }) =>
    feature(geometry, withDefaults(properties, fields))));
}

// The area most rows fall in (2nd to 98th percentiles, so a few stray coordinates don't zoom the
// map out to the whole world): { west, south, east, north }, or null when there's nothing to show
export async function dataExtent(engine, { table, latitudeField, longitudeField, geomField, filter = '', sourceCrs = DEFAULT_SOURCE_CRS }) {
  let x;
  let y;
  let where;
  if (latitudeField && longitudeField) {
    await checkColumns(engine, table, [latitudeField, longitudeField]);
    y = `TRY_CAST(${quoteIdent(latitudeField)} AS DOUBLE)`;
    x = `TRY_CAST(${quoteIdent(longitudeField)} AS DOUBLE)`;
    where = `${y} BETWEEN -90 AND 90 AND ${x} BETWEEN -180 AND 180`;
  } else if (geomField) {
    const schema = await checkColumns(engine, table, [geomField]);
    await engine.loadExtension?.('spatial');
    const column = quoteIdent(geomField);
    const source = /^GEOMETRY\b/i.test(schema[geomField]) ? column : `ST_GeomFromText(${column})`;
    const center = `ST_Centroid(ST_Transform(${source}, '${sourceCrs}', 'EPSG:4326', always_xy := true))`;
    y = `ST_Y(${center})`;
    x = `ST_X(${center})`;
    where = `${column} IS NOT NULL`;
  } else {
    return null;
  }
  const [extent] = await engine.query(`
    SELECT quantile_cont(${x}, 0.02) AS west, quantile_cont(${y}, 0.02) AS south,
           quantile_cont(${x}, 0.98) AS east, quantile_cont(${y}, 0.98) AS north
    FROM ${quoteIdent(table)}
    WHERE ${where}${andFilter(filter)}`);
  if (!extent || ![extent.west, extent.south, extent.east, extent.north].every(Number.isFinite)) return null;
  // A single place: a small area around it
  const pad = (min, max) => (max - min < 0.01 ? [min - 0.01, max + 0.01] : [min, max]);
  const [west, east] = pad(extent.west, extent.east);
  const [south, north] = pad(extent.south, extent.north);
  return { west, south, east, north };
}

// The range a 3D layer's heights span for a property: from 0 when every value is positive (heights
// proportional to the values), else from the lowest value
export function heightRange(features, field) {
  const values = features.map((f) => Number(f.properties?.[field])).filter(Number.isFinite);
  if (!values.length) return { low: 0, high: 1 };
  const low = Math.min(0, ...values);
  const high = Math.max(...values);
  return { low, high: high > low ? high : low + 1 };
}

function feature(geometry, properties) {
  return { type: 'Feature', geometry: typeof geometry === 'string' ? JSON.parse(geometry) : geometry, properties };
}

function featureCollection(features) {
  return { type: 'FeatureCollection', features };
}

// Missing aggregates as -1 (the map's colour scales skip them), as the backend did
function withDefaults(properties, fields) {
  for (const field of fields) if (properties[field] === null || properties[field] === undefined) properties[field] = -1;
  return properties;
}

// Runs the query and returns the features with what the map shows about them
async function timed(run, toFeatures) {
  const start = performance.now();
  const rows = await run();
  const geojson = featureCollection(toFeatures(rows));
  return {
    geojson,
    metadata: {
      records: rows.length,
      objectSize: Math.round(JSON.stringify(geojson).length / 1024 / 1024 * 100) / 100,
      time: Math.round((performance.now() - start) / 10) / 100,
    },
  };
}
