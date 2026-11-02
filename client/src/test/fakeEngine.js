import { capabilities } from '../engine/engine';

// An engine for component tests: it records the SQL it gets and answers queries with `query(sql)`.
// Pass any other engine method (runUserQuery, exportTable...) to override it.
export function fakeEngine({ query = () => [], exec = () => {}, ...methods } = {}) {
  const calls = { query: [], exec: [] };
  return {
    mode: 'remote',
    capabilities: capabilities({
      s3: true, remoteDb: true, publishApi: true, auth: true, serverAi: true, serverPath: true,
      h3: true, spatial: true, persistent: true,
    }),
    calls,
    async query(sql) {
      calls.query.push(sql);
      return query(sql);
    },
    async exec(sql) {
      calls.exec.push(sql);
      return exec(sql);
    },
    ...methods,
  };
}

// What `SHOW TABLES` returns for these table names
export function showTables(names) {
  return names.map((name) => ({ name }));
}

// What information_schema.columns returns for a { table: { column: type } } schema
export function schemaRows(schema) {
  return Object.entries(schema).flatMap(([table, columns]) =>
    Object.entries(columns).map(([column, type]) => ({ table_name: table, column_name: column, data_type: type })));
}
