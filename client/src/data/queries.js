import { quoteLiteral } from './sql';

// Saved SQL queries, kept in the __queries table of the active database (same layout as the
// backend's queriesService, so the published API endpoints can still find them)

async function ensureQueriesTable(engine) {
  await engine.exec(`
    CREATE TABLE IF NOT EXISTS __queries (id_query INTEGER PRIMARY KEY, name VARCHAR, query VARCHAR, description VARCHAR);
    CREATE SEQUENCE IF NOT EXISTS seq_id_query START 1;`);
}

export async function saveQuery(engine, { name, query, description }) {
  await ensureQueriesTable(engine);
  await engine.exec(`
    INSERT INTO __queries (id_query, name, query, description)
    VALUES (nextval('seq_id_query'), ${quoteLiteral(name)}, ${quoteLiteral(query)}, ${quoteLiteral(description)})`);
}

// Saved queries whose name or description contains the text (case-insensitive)
export async function searchQueries(engine, text = '') {
  await ensureQueriesTable(engine);
  const term = quoteLiteral('%' + String(text || '').toLowerCase() + '%');
  return engine.query(`
    SELECT * FROM __queries
    WHERE LOWER(name) LIKE ${term} OR LOWER(description) LIKE ${term}
    ORDER BY id_query`);
}

export async function deleteQuery(engine, idQuery) {
  await ensureQueriesTable(engine);
  await engine.exec(`DELETE FROM __queries WHERE id_query = ${Number(idQuery)}`);
}
