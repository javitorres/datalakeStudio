// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { createNodeEngine } from './nodeEngine';
import {
  createTableFromQuery, dropTable, getDatabaseSchema, getTableSchema, listTables, profile, renameTable,
  rowCount, runUserQuery, sample,
} from '../tables';
import { deleteQuery, saveQuery, searchQueries } from '../queries';

let engine;

beforeEach(async () => {
  engine = await createNodeEngine();
  await engine.exec(`
    CREATE TABLE iris AS SELECT * FROM (VALUES
      (5.1, 3.5, 'setosa', 1), (4.9, 3.0, 'setosa', 2), (7.0, 3.2, 'versicolor', 3),
      (6.4, 3.2, 'versicolor', 4), (6.3, 3.3, 'virginica', 5)) t(sepal_length, sepal_width, species, id);
    CREATE TABLE "odd ""name""" AS SELECT 1 AS "a column";
    CREATE TABLE __hidden AS SELECT 1 AS x;
    CREATE TABLE cube_index_abc AS SELECT 1 AS x;`);
});

afterEach(() => engine.close());

describe('tables', () => {
  it('lists the tables without the app ones', async () => {
    expect((await listTables(engine)).sort()).toEqual(['iris', 'odd "name"']);
  });

  it('describes the columns of a table and of the whole database', async () => {
    expect(await getTableSchema(engine, 'iris')).toEqual({
      sepal_length: 'DECIMAL(2,1)', sepal_width: 'DECIMAL(2,1)', species: 'VARCHAR', id: 'INTEGER',
    });
    const schema = await getDatabaseSchema(engine);
    expect(Object.keys(schema).sort()).toEqual(['iris', 'odd "name"']);
    expect(Object.keys(schema.iris)).toEqual(['sepal_length', 'sepal_width', 'species', 'id']);
    expect(Object.keys(await getDatabaseSchema(engine, { includeHidden: true }))).toContain('__hidden');
  });

  it('counts rows and quotes odd table names', async () => {
    expect(await rowCount(engine, 'iris')).toBe(5);
    expect(await rowCount(engine, 'odd "name"')).toBe(1);
  });

  it('samples the first, last and random rows, after a filter', async () => {
    expect((await sample(engine, 'iris', { records: 2 })).map((r) => r.id)).toEqual([1, 2]);
    expect((await sample(engine, 'iris', { type: 'Last', records: 2 })).map((r) => r.id)).toEqual([4, 5]);
    expect(await sample(engine, 'iris', { type: 'Shuffle', records: 3 })).toHaveLength(3);
    expect(await sample(engine, 'iris', { records: 0 })).toHaveLength(5);
    const filtered = await sample(engine, 'iris', { type: 'Last', records: 1, filter: "species = 'setosa'" });
    expect(filtered.map((r) => r.id)).toEqual([2]);
  });

  it('profiles the numeric columns, one row per statistic', async () => {
    const rows = await profile(engine, 'iris');
    expect(rows.map((r) => r.statistic)).toEqual(['count', 'mean', 'std', 'min', 'p25', 'p50', 'p75', 'max']);
    expect(Object.keys(rows[0])).toEqual(['statistic', 'sepal_length', 'sepal_width', 'id']);
    expect(rows[0].id).toBe(5);
    expect(rows[1].id).toBe(3);
    expect(rows[7].sepal_length).toBe(7);
  });

  it('creates, renames and drops tables', async () => {
    await createTableFromQuery(engine, 'setosa', "SELECT * FROM iris WHERE species = 'setosa'");
    expect(await rowCount(engine, 'setosa')).toBe(2);
    await renameTable(engine, 'setosa', 'only_setosa');
    expect(await listTables(engine)).toContain('only_setosa');
    await expect(renameTable(engine, 'only_setosa', '1bad name')).rejects.toThrow('Invalid name');
    await dropTable(engine, 'only_setosa');
    expect(await listTables(engine)).not.toContain('only_setosa');
  });

  it('keeps the last statement of a script as __lastQuery', async () => {
    await runUserQuery(engine, `
      -- a comment; with a semicolon
      CREATE TABLE tmp AS SELECT 'a;b' AS s;
      SELECT s, 42 AS n FROM tmp;`);
    expect(await sample(engine, '__lastQuery')).toEqual([{ s: 'a;b', n: 42 }]);
    expect(await getTableSchema(engine, '__lastQuery')).toEqual({ s: 'VARCHAR', n: 'INTEGER' });
    expect(await listTables(engine)).not.toContain('__lastQuery');
    await expect(runUserQuery(engine, ' ; -- nothing')).rejects.toThrow('empty');
  });

  it('uses the engine own runUserQuery when it has one', async () => {
    const calls = [];
    await runUserQuery({ runUserQuery: (sql) => calls.push(sql) }, 'SELECT 1');
    expect(calls).toEqual(['SELECT 1']);
  });
});

describe('saved queries', () => {
  it('saves, searches and deletes queries', async () => {
    await saveQuery(engine, { name: "Iris 'all'", query: 'SELECT * FROM iris', description: 'Every flower' });
    await saveQuery(engine, { name: 'Setosa', query: "SELECT * FROM iris WHERE species = 'setosa'", description: '' });
    expect((await searchQueries(engine, '')).map((q) => q.name)).toEqual(["Iris 'all'", 'Setosa']);
    const [found] = await searchQueries(engine, 'FLOWER');
    expect(found).toMatchObject({ id_query: 1, query: 'SELECT * FROM iris' });
    await deleteQuery(engine, found.id_query);
    expect((await searchQueries(engine)).map((q) => q.name)).toEqual(['Setosa']);
  });
});
