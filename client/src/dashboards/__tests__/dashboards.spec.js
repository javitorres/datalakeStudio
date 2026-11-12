// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { createNodeEngine } from '../../data/__tests__/nodeEngine';
import { filterInfoSql, publishedQueries, widgetSql } from '../compile';
import { aiSpec, isSelect, normalizeDashboard, validateDashboard } from '../spec';

// What the AI answers: no ids, and every field of every widget
const widget = (fields) => ({ title: '', dataset: 'trips', dimension: '', measures: [], columns: [], text: '', width: 6, sort: 'value', limit: 0, ...fields });
const RAW = {
  title: 'Taxi trips',
  summary: 'An overview of the trips',
  datasets: [{ id: 'trips', sql: "SELECT *, date_trunc('month', pickup) AS month FROM trips -- every trip" }],
  filters: [
    { column: 'borough', type: 'select', label: 'Borough' },
    { column: 'fare', type: 'range', label: 'Fare' },
    { column: 'pickup', type: 'dateRange', label: 'Pickup' },
  ],
  widgets: [
    widget({ type: 'kpi', title: 'Totals', measures: [{ column: '*', agg: 'count', label: 'Trips' }, { column: 'fare', agg: 'avg', label: '' }], width: 3 }),
    widget({ type: 'bar', title: 'Trips by borough', dimension: 'borough', measures: [{ column: '*', agg: 'count', label: 'Trips' }] }),
    widget({ type: 'pie', title: 'Fare by payment', dimension: 'payment', measures: [{ column: 'fare', agg: 'sum', label: 'Fare' }, { column: 'fare', agg: 'max', label: 'Max' }] }),
    widget({ type: 'line', title: 'Trips per month', dimension: 'month', measures: [{ column: '*', agg: 'count', label: 'Trips' }], sort: 'value' }),
    widget({ type: 'histogram', title: 'Fares', dimension: 'fare' }),
    widget({ type: 'table', title: 'Trips', columns: ['borough', 'fare'], limit: 2, width: 12 }),
    widget({ type: 'text', title: 'Notes', text: '**Fares** in dollars', dataset: '' }),
  ],
};

// The server binds each {placeholder} as a parameter: here its value is written in
function bind(template, values) {
  const literal = (value) => (value == null ? 'NULL'
    : Array.isArray(value) ? `[${value.map((v) => `'${v}'`).join(', ')}]`
      : typeof value === 'number' ? String(value) : `'${value}'`);
  return template.replace(/\{(\w+)\}/g, (_, name) => literal(values[name]));
}

let engine;

beforeEach(async () => {
  engine = await createNodeEngine();
  await engine.exec(`
    CREATE TABLE trips AS SELECT * FROM (VALUES
      ('Bronx', 'card', 10.0, TIMESTAMP '2024-01-05 08:00:00'), ('Bronx', 'cash', 20.0, TIMESTAMP '2024-01-20 09:30:00'),
      ('Queens', 'card', 30.0, TIMESTAMP '2024-02-03 10:00:00'), ('Queens', 'card', 40.0, TIMESTAMP '2024-02-10 23:59:00'),
      ('Queens', 'cash', 50.0, TIMESTAMP '2024-03-01 12:00:00'), ('O''Hare', 'card', 60.0, TIMESTAMP '2024-03-15 18:00:00'))
      t(borough, payment, fare, pickup);`);
});

afterEach(() => engine.close());

describe('dashboard specification', () => {
  it('accepts only single queries as datasets', () => {
    expect(isSelect('SELECT 1')).toBe(true);
    expect(isSelect('-- all\nWITH a AS (SELECT 1) SELECT * FROM a;')).toBe(true);
    expect(isSelect("SELECT ';' AS semicolon")).toBe(true);
    for (const sql of ['DROP TABLE trips', 'SELECT 1; DROP TABLE trips', 'COPY trips TO \'x.csv\'', '', 'ATTACH \'x.db\'']) {
      expect(isSelect(sql), sql).toBe(false);
    }
  });

  it('keeps what the app understands, with ids and defaults', () => {
    const { spec, errors } = normalizeDashboard(RAW);

    expect(errors).toEqual([]);
    expect(spec.widgets.map((w) => w.id)).toEqual(['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7']);
    expect(spec.filters.map((f) => f.id)).toEqual(['f1', 'f2', 'f3']);
    // A pie has one measure, a line is read along its dimension, and unused fields are dropped
    expect(spec.widgets[2].measures).toHaveLength(1);
    expect(spec.widgets[3].sort).toBe('value');
    expect(normalizeDashboard({ ...RAW, widgets: [widget({ type: 'line', dimension: 'month', measures: RAW.widgets[3].measures, sort: '' })] })
      .spec.widgets[0].sort).toBe('dimension');
    expect(spec.widgets[6]).toEqual({ id: 'w7', type: 'text', title: 'Notes', width: 6, text: '**Fares** in dollars' });
    expect(spec.widgets[0]).not.toHaveProperty('dimension');
    expect(spec).not.toHaveProperty('summary');
  });

  it('reports what the AI got wrong, for it to fix', () => {
    const { errors } = normalizeDashboard({
      datasets: [{ id: 'a', sql: 'SELECT 1' }, { id: 'b', sql: 'DELETE FROM trips' }, { id: 'c d', sql: 'SELECT 1' }, { id: 'e', sql: 'SELECT 2' }],
      filters: [{ column: 'x', type: 'slider', label: '' }],
      widgets: [
        { type: 'gauge', title: 'G' },
        widget({ type: 'bar', title: 'No measures', dataset: 'a', dimension: 'x' }),
        widget({ type: 'bar', title: 'No dimension', dataset: 'a', measures: [{ column: '*', agg: 'count', label: '' }] }),
        widget({ type: 'kpi', title: 'Lost', dataset: 'zzz', measures: [{ column: '*', agg: 'count', label: '' }] }),
      ],
    });

    expect(errors).toHaveLength(7);
    expect(errors.join('\n')).toMatch(/Dataset "b": the SQL must be a single SELECT/);
    expect(errors.join('\n')).toMatch(/unknown type "gauge"[\s\S]*at least one measure[\s\S]*needs a dimension[\s\S]*unknown dataset "zzz"/);
    expect(normalizeDashboard(null).errors).toEqual(['The dashboard needs at least one dataset']);
  });

  it('checks the columns against the database', async () => {
    const { spec, errors } = await validateDashboard(engine, RAW);

    expect(errors).toEqual([]);
    expect(spec.datasets[0].columns).toMatchObject({ borough: 'VARCHAR', fare: 'DECIMAL(3,1)', month: 'TIMESTAMP' });
    // Clicking the pie filters by payment, which has no filter of its own; borough already has one
    expect(spec.filters.filter((f) => f.implicit)).toEqual([{ id: 'x1', column: 'payment', type: 'select', label: 'payment', implicit: true }]);

    const broken = await validateDashboard(engine, {
      ...RAW,
      filters: [{ column: 'borough', type: 'range', label: '' }, { column: 'fare', type: 'dateRange', label: '' }, { column: 'nope', type: 'select', label: '' }],
      widgets: [
        widget({ type: 'bar', title: 'B', dimension: 'zone', measures: [{ column: 'borough', agg: 'sum', label: '' }, { column: '*', agg: 'avg', label: '' }] }),
        widget({ type: 'histogram', title: 'H', dimension: 'borough' }),
        widget({ type: 'table', title: 'T', columns: ['tip'] }),
      ],
    });
    expect(broken.errors).toHaveLength(8);
    expect(broken.errors[0]).toContain('has no column "zone". Its columns are: borough, payment, fare, pickup, month');
    expect(broken.errors.join('\n')).toMatch(/sum needs a numeric column[\s\S]*"\*" can only be used with count[\s\S]*histogram needs a numeric/);

    const failing = await validateDashboard(engine, { ...RAW, datasets: [{ id: 'trips', sql: 'SELECT * FROM no_such_table' }] });
    expect(failing.errors).toHaveLength(1);
    expect(failing.errors[0]).toMatch(/Dataset "trips": its SQL fails with: .*no_such_table/);
  });

  it('goes back to the AI without what the app added', async () => {
    const { spec } = await validateDashboard(engine, RAW);
    const sent = aiSpec(spec);

    expect(sent.filters).toEqual(RAW.filters);
    expect(sent.datasets).toEqual([{ id: 'trips', sql: RAW.datasets[0].sql }]);
    expect(sent.widgets[1]).toEqual({
      type: 'bar', title: 'Trips by borough', dataset: 'trips', dimension: 'borough',
      measures: [{ column: '*', agg: 'count', label: 'Trips' }], width: 6, sort: 'value', limit: 0,
    });
    // The same dashboard when it is checked again
    expect((await validateDashboard(engine, sent)).spec).toEqual(spec);
  });
});

describe('dashboard queries', () => {
  let spec;
  const run = (id, state) => engine.query(widgetSql(spec, spec.widgets.find((w) => w.id === id), state));

  beforeEach(async () => {
    spec = (await validateDashboard(engine, RAW)).spec;
  });

  it('aggregates each kind of widget', async () => {
    expect(await run('w1')).toEqual([{ m0: 6, m1: 35 }]);
    expect(await run('w2')).toEqual([{ x: 'Queens', m0: 3 }, { x: 'Bronx', m0: 2 }, { x: "O'Hare", m0: 1 }]);
    expect(await run('w3')).toEqual([{ x: 'card', m0: 140 }, { x: 'cash', m0: 70 }]);
    expect((await run('w4')).map((row) => [row.x.slice(0, 7), row.m0])).toEqual([['2024-01', 2], ['2024-02', 2], ['2024-03', 2]]);
    const bins = await run('w5');
    expect(bins.reduce((sum, bin) => sum + bin.m0, 0)).toBe(6);
    expect([bins[0].x0, bins.at(-1).x1]).toEqual([10, 60]);
    expect(await run('w6')).toEqual([{ borough: 'Bronx', fare: 10 }, { borough: 'Bronx', fare: 20 }]);
    expect(widgetSql(spec, spec.widgets[6])).toBeNull();
  });

  it('filters by the values of the user, written in as literals', async () => {
    expect(await run('w1', { f1: ["O'Hare", 'Bronx'] })).toEqual([{ m0: 3, m1: 30 }]);
    expect(await run('w1', { f2: [30, 50] })).toEqual([{ m0: 3, m1: 40 }]);
    expect(await run('w1', { f2: [null, 20] })).toEqual([{ m0: 2, m1: 15 }]);
    // Both days of a date range are included
    expect(await run('w1', { f3: ['2024-01-20', '2024-02-10'] })).toEqual([{ m0: 3, m1: 30 }]);
    expect(await run('w1', { f1: ['Queens'], f2: [45, null], x1: ['cash'] })).toEqual([{ m0: 1, m1: 50 }]);
    // Values that are not what the filter takes don't filter, and never reach the SQL
    expect(await run('w1', { f1: [], f2: ['1 OR 1=1', ''], f3: ["x' OR true --", null] })).toEqual([{ m0: 6, m1: 35 }]);
    expect(await run('w1', { f1: ["x') OR true --"] })).toEqual([{ m0: 0, m1: null }]);
  });

  it('keeps every category of a chart that filters by its own dimension', async () => {
    const state = { f1: ['Queens'] };

    expect((await run('w2', state)).map((row) => row.x)).toEqual(['Queens', 'Bronx', "O'Hare"]);
    expect(await run('w3', state)).toEqual([{ x: 'card', m0: 70 }, { x: 'cash', m0: 50 }]);
  });

  it('tells a filter control what to offer', async () => {
    const info = (id) => engine.query(filterInfoSql(spec, spec.filters.find((f) => f.id === id)));

    expect(await info('f1')).toEqual([{ value: 'Queens', n: 3 }, { value: 'Bronx', n: 2 }, { value: "O'Hare", n: 1 }]);
    expect(await info('f2')).toEqual([{ min: 10, max: 60 }]);
    expect(await info('f3')).toEqual([{ min: '2024-01-05', max: '2024-03-15' }]);
  });

  it('publishes templates that give the same rows once the server binds the values', async () => {
    const queries = publishedQueries(spec);
    const open = { f1: null, f2_min: null, f2_max: null, f3_from: null, f3_to: null, x1: null };

    // Every widget with data and every control, never the text or the click filters
    expect(Object.keys(queries)).toEqual(['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'f1', 'f2', 'f3']);
    for (const [id, template] of Object.entries(queries)) {
      expect(isSelect(template), id).toBe(true);
      expect(template).not.toMatch(/'[^']*\{\w+\}[^']*'/);
    }
    const published = async (id, values) => engine.query(bind(queries[id], { ...open, ...values }));
    for (const id of ['w1', 'w2', 'w3', 'w4', 'w5', 'w6']) {
      expect(await published(id, {}), id).toEqual(await run(id, {}));
    }
    expect(await published('w1', { f1: ['Queens'], f2_min: 35, x1: ['cash'] })).toEqual(await run('w1', { f1: ['Queens'], f2: [35, null], x1: ['cash'] }));
    expect(await published('w1', { f3_from: '2024-01-20', f3_to: '2024-02-10' })).toEqual([{ m0: 3, m1: 30 }]);
    expect(await published('w2', { f1: ['Queens'] })).toEqual(await run('w2', { f1: ['Queens'] }));
    expect(await published('w3', { f1: ['Queens'] })).toEqual(await run('w3', { f1: ['Queens'] }));
  });
});
