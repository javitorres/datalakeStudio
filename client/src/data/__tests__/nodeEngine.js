import { DuckDBInstance } from '@duckdb/node-api';

// An engine on DuckDB for Node, so the data layer's SQL is tested against a real database
export async function createNodeEngine() {
  const instance = await DuckDBInstance.create(':memory:');
  const connection = await instance.connect();
  return {
    mode: 'test',
    capabilities: {},
    async query(sql) {
      const reader = await connection.runAndReadAll(sql);
      return reader.getRowObjectsJS().map(plainRow);
    },
    async exec(sql) {
      const extracted = await connection.extractStatements(sql);
      for (let i = 0; i < extracted.count; i += 1) {
        const prepared = await extracted.prepare(i);
        await prepared.run();
      }
    },
    close() {
      connection.closeSync();
    },
  };
}

// The values the engines return: BigInts as numbers and dates as ISO strings
function plainRow(row) {
  return Object.fromEntries(Object.entries(row).map(([key, value]) => {
    if (typeof value === 'bigint') return [key, Number(value)];
    if (value instanceof Date) return [key, value.toISOString()];
    return [key, value];
  }));
}
