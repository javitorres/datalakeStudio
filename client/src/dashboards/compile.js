// The SQL of a dashboard's widgets and filters, written here once for the two places it runs:
// - on the user's own engine, with the filter values as literals (`state`: { filter id: value });
// - on the server for a published dashboard, as a template with a {placeholder} per filter value
//   (`state` null). Viewers send only values, which the server binds as parameters.
// A filter value is a list of strings (select) or a [low, high] pair (range, dateRange), null when open.
import { quoteIdent, quoteLiteral } from '../data/sql';
import { CLICKABLE_WIDGETS } from './spec';

const DEFAULT_LIMIT = { bar: 30, horizontalBar: 20, pie: 12, line: 500, area: 500, table: 100 };
const MAX_LIMIT = 1000;
export const HISTOGRAM_BINS = 30;
// Values a select filter offers
export const FILTER_OPTIONS = 200;

const AGGREGATES = {
  count: (c) => `count(${c})`,
  countDistinct: (c) => `count(DISTINCT ${c})`,
  sum: (c) => `sum(${c})`,
  avg: (c) => `avg(${c})`,
  min: (c) => `min(${c})`,
  max: (c) => `max(${c})`,
  median: (c) => `median(${c})`,
};

function measureSql(measure) {
  return AGGREGATES[measure.agg](measure.column === '*' ? '*' : quoteIdent(measure.column));
}

const isDate = (value) => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value);
const isNumber = (value) => value !== null && value !== '' && Number.isFinite(Number(value));

// The conditions of a filter: with its values written in, or as a template
function filterConditions(filter, state) {
  const column = quoteIdent(filter.column);
  const template = state === null;
  const value = template ? null : state[filter.id];
  if (filter.type === 'select') {
    if (template) {
      return [`({${filter.id}}::VARCHAR[] IS NULL OR CAST(${column} AS VARCHAR) IN (SELECT unnest({${filter.id}}::VARCHAR[])))`];
    }
    return Array.isArray(value) && value.length
      ? [`CAST(${column} AS VARCHAR) IN (${value.map(quoteLiteral).join(', ')})`] : [];
  }
  const [low, high] = Array.isArray(value) ? value : [];
  if (filter.type === 'range') {
    if (template) {
      return [`({${filter.id}_min}::DOUBLE IS NULL OR ${column} >= {${filter.id}_min}::DOUBLE)`,
        `({${filter.id}_max}::DOUBLE IS NULL OR ${column} <= {${filter.id}_max}::DOUBLE)`];
    }
    return [isNumber(low) && `${column} >= ${Number(low)}`, isNumber(high) && `${column} <= ${Number(high)}`].filter(Boolean);
  }
  // dateRange: both days included
  if (template) {
    return [`({${filter.id}_from}::TIMESTAMP IS NULL OR ${column} >= {${filter.id}_from}::TIMESTAMP)`,
      `({${filter.id}_to}::TIMESTAMP IS NULL OR ${column} < {${filter.id}_to}::TIMESTAMP + INTERVAL 1 DAY)`];
  }
  return [isDate(low) && `${column} >= TIMESTAMP ${quoteLiteral(low)}`,
    isDate(high) && `${column} < TIMESTAMP ${quoteLiteral(high)} + INTERVAL 1 DAY`].filter(Boolean);
}

// "WITH d AS (the dataset's rows after the filters)". A filter applies to the datasets that have its
// column; `except` leaves out the filters on one column.
function filtered(spec, datasetId, state, except) {
  const dataset = spec.datasets.find((d) => d.id === datasetId);
  const conditions = spec.filters
    .filter((filter) => filter.column !== except && dataset.columns && filter.column in dataset.columns)
    .flatMap((filter) => filterConditions(filter, state));
  const where = conditions.length ? ` WHERE ${conditions.join(' AND ')}` : '';
  // The line break closes a trailing "--" comment of the dataset's SQL
  return `WITH d AS (SELECT * FROM (${dataset.sql}\n) AS s${where})`;
}

function limitOf(widget) {
  return Math.min(widget.limit || DEFAULT_LIMIT[widget.type] || 100, MAX_LIMIT);
}

// The query of a widget. Its rows are:
//   kpi          one row { m0, m1... }, a column per measure
//   charts       { x, m0, m1... } per group, x as text
//   histogram    { x0, x1, m0 } per bin
//   table        the dataset's rows
export function widgetSql(spec, widget, state = {}) {
  if (widget.type === 'text') return null;
  // A chart that filters by its own dimension keeps showing every category
  const base = filtered(spec, widget.dataset, state, CLICKABLE_WIDGETS.includes(widget.type) ? widget.dimension : null);
  if (widget.type === 'table') {
    const columns = widget.columns?.length ? widget.columns.map(quoteIdent).join(', ') : '*';
    return `${base} SELECT ${columns} FROM d LIMIT ${limitOf(widget)}`;
  }
  if (widget.type === 'histogram') {
    const column = `${quoteIdent(widget.dimension)}::DOUBLE`;
    const bins = HISTOGRAM_BINS;
    // Between the 0.5% and 99.5% quantiles: a few extreme values would leave every row in one bin
    return `${base}, r AS (SELECT approx_quantile(${column}, 0.005) AS mn, approx_quantile(${column}, 0.995) AS mx FROM d) `
      + `SELECT any_value(mn) + (any_value(mx) - any_value(mn)) * b / ${bins} AS x0, `
      + `any_value(mn) + (any_value(mx) - any_value(mn)) * (b + 1) / ${bins} AS x1, count(*) AS m0 `
      + `FROM (SELECT least(coalesce(floor((${column} - mn) / nullif(mx - mn, 0) * ${bins}), 0), ${bins - 1})::INTEGER AS b, mn, mx `
      + `FROM d, r WHERE ${column} BETWEEN mn AND mx) GROUP BY b ORDER BY b`;
  }
  const measures = widget.measures.map((measure, index) => `${measureSql(measure)} AS m${index}`).join(', ');
  if (widget.type === 'kpi') return `${base} SELECT ${measures} FROM d`;
  const dimension = quoteIdent(widget.dimension);
  const order = widget.sort === 'dimension' ? dimension : `m0 DESC NULLS LAST, ${dimension}`;
  return `${base} SELECT CAST(${dimension} AS VARCHAR) AS x, ${measures} FROM d GROUP BY ${dimension} `
    + `ORDER BY ${order} LIMIT ${limitOf(widget)}`;
}

// What a filter control needs: the values to choose from ({ value, n } per category) or the
// extremes of its column (one row { min, max }). From the first dataset that has the column.
export function filterInfoSql(spec, filter) {
  const dataset = spec.datasets.find((d) => d.columns && filter.column in d.columns);
  const column = quoteIdent(filter.column);
  const from = `FROM (${dataset.sql}\n) AS s`;
  if (filter.type === 'select') {
    return `SELECT CAST(${column} AS VARCHAR) AS value, count(*) AS n ${from} WHERE ${column} IS NOT NULL `
      + `GROUP BY 1 ORDER BY n DESC, 1 LIMIT ${FILTER_OPTIONS}`;
  }
  if (filter.type === 'range') return `SELECT min(${column})::DOUBLE AS min, max(${column})::DOUBLE AS max ${from}`;
  return `SELECT CAST(CAST(min(${column}) AS DATE) AS VARCHAR) AS min, CAST(CAST(max(${column}) AS DATE) AS VARCHAR) AS max ${from}`;
}

// The queries a published dashboard runs on the server: { widget or filter id: SQL template }
export function publishedQueries(spec) {
  const queries = {};
  for (const widget of spec.widgets) {
    if (widget.type !== 'text') queries[widget.id] = widgetSql(spec, widget, null);
  }
  for (const filter of spec.filters) {
    if (!filter.implicit) queries[filter.id] = filterInfoSql(spec, filter);
  }
  return queries;
}
