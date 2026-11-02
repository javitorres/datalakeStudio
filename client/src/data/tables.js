import { quoteIdent, splitStatements } from './sql';
import { uiType } from './types';

// The app's own tables (saved queries, endpoints, the last query result, Mosaic's cube indexes)
export function isHiddenTable(name) {
  return name.startsWith('__') || name.startsWith('cube_index_');
}

export async function listTables(engine) {
  const rows = await engine.query('SHOW TABLES');
  return rows.map((row) => row.name).filter((name) => !isHiddenTable(name));
}

// { table: { column: DUCKDB_TYPE } } in column order, for SQL autocompletion and the AI prompt
export async function getDatabaseSchema(engine, { includeHidden = false } = {}) {
  const rows = await engine.query(`
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'main'
    ORDER BY table_name, ordinal_position`);
  const schema = {};
  for (const { table_name: table, column_name: column, data_type: type } of rows) {
    if (!includeHidden && isHiddenTable(table)) continue;
    (schema[table] ||= {})[column] = type;
  }
  return schema;
}

// { column: DUCKDB_TYPE } in column order. Works on views too, such as __lastQuery.
export async function getTableSchema(engine, tableName) {
  const rows = await engine.query(`DESCRIBE ${quoteIdent(tableName)}`);
  return Object.fromEntries(rows.map((row) => [row.column_name, row.column_type]));
}

export async function rowCount(engine, tableName) {
  const rows = await engine.query(`SELECT COUNT(*) AS total FROM ${quoteIdent(tableName)}`);
  return Number(rows[0]?.total ?? 0);
}

// The first, last or random `records` rows (all of them with records = 0), after an optional SQL
// predicate (the cross-filter)
export async function sample(engine, tableName, { type = 'First', records = 1000, filter = '' } = {}) {
  const table = quoteIdent(tableName);
  const where = filter && filter.trim() ? ` WHERE (${filter.trim()})` : '';
  const n = Number(records) || 0;
  let sql = `SELECT ${await readableColumns(engine, tableName)} FROM ${table}${where}`;
  if (n && type === 'Shuffle') {
    // Sample the filtered rows: USING SAMPLE on the table itself samples before the WHERE
    sql = `SELECT * FROM (${sql}) USING SAMPLE ${n} ROWS`;
  } else if (n && type === 'Last') {
    // The last rows in their original order (views have no rowid to sort by)
    sql += ` OFFSET (SELECT greatest(count(*) - ${n}, 0) FROM ${table}${where})`;
  } else if (n) {
    sql += ` LIMIT ${n}`;
  }
  return engine.query(sql);
}

// Geometries are binary: show them as WKT text
async function readableColumns(engine, tableName) {
  const geometries = Object.entries(await getTableSchema(engine, tableName))
    .filter(([, type]) => /^GEOMETRY\b/i.test(type))
    .map(([name]) => `ST_AsText(${quoteIdent(name)}) AS ${quoteIdent(name)}`);
  return geometries.length ? `* REPLACE (${geometries.join(', ')})` : '*';
}

// count, mean, std, min, quartiles and max of every numeric column, one row per statistic
export async function profile(engine, tableName) {
  const columns = Object.entries(await getTableSchema(engine, tableName))
    .filter(([, type]) => uiType(type) === 'numeric')
    .map(([name]) => quoteIdent(name));
  if (!columns.length) return [];
  const table = quoteIdent(tableName);
  const statistics = [
    ['count', (c) => `COUNT(${c})`],
    ['mean', (c) => `AVG(${c})`],
    ['std', (c) => `STDDEV(${c})`],
    ['min', (c) => `MIN(${c})`],
    ['p25', (c) => `PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ${c})`],
    ['p50', (c) => `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ${c})`],
    ['p75', (c) => `PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ${c})`],
    ['max', (c) => `MAX(${c})`],
  ];
  const sql = statistics.map(([name, aggregate], index) =>
    `SELECT ${index} AS _order, '${name}' AS statistic, `
    + columns.map((c) => `${aggregate(c)}::DOUBLE AS ${c}`).join(', ')
    + ` FROM ${table}`).join(' UNION ALL ');
  const rows = await engine.query(`SELECT * EXCLUDE (_order) FROM (${sql}) ORDER BY _order`);
  return rows;
}

export async function createTableFromQuery(engine, tableName, query) {
  // Replaces the table only once the query has worked (and the query may read that same table)
  await engine.exec(`CREATE OR REPLACE TABLE ${quoteIdent(tableName)} AS (${query})`);
}

export async function dropTable(engine, tableName) {
  await engine.exec(`DROP TABLE IF EXISTS ${quoteIdent(tableName)}`);
}

export const VALID_TABLE_NAME = /^[A-Za-z_][A-Za-z0-9_]*$/;

export async function renameTable(engine, tableName, newName) {
  if (!VALID_TABLE_NAME.test(newName)) {
    throw new Error("Invalid name. Use letters, numbers and underscores, and don't start with a number.");
  }
  await engine.exec(`ALTER TABLE ${quoteIdent(tableName)} RENAME TO ${quoteIdent(newName)}`);
}

// Runs a SQL workspace script and keeps the result of its last statement as the temporary view
// __lastQuery, which the explorer, charts and maps then read like any other table
export async function runUserQuery(engine, script) {
  if (engine.runUserQuery) return engine.runUserQuery(script);
  const statements = splitStatements(script);
  if (!statements.length) throw new Error('The query is empty');
  const last = statements.pop();
  for (const statement of statements) await engine.exec(statement);
  try {
    await engine.exec(`CREATE OR REPLACE TEMP TABLE __lastQueryData AS ${last}`);
  } catch (error) {
    // Not a query (PRAGMA, EXPLAIN, SET...): run it as it is and keep what it returns. A real syntax
    // error is reported again by running the statement.
    if (!/Parser Error/i.test(error.message) || !engine.materialize) throw error;
    await engine.materialize(last, '__lastQueryData');
  }
  await engine.exec('CREATE OR REPLACE TEMP VIEW __lastQuery AS SELECT * FROM __lastQueryData');
}
