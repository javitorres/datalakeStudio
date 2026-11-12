// A dashboard is a declarative specification, never code: named SQL datasets, the widgets that aggregate
// them and the filters over their columns. The AI writes it, the app checks it here and draws it with its
// own components.
//
//   { title,
//     datasets: [{ id, sql, columns: { column: DUCKDB_TYPE } }],        columns are read from the database
//     filters:  [{ id, column, type, label, implicit }],                implicit: set by clicking a chart
//     widgets:  [{ id, type, title, dataset, dimension, measures: [{ column, agg, label }], columns,
//                  text, width, sort, limit }] }
import { cleanSql } from '../ai/prompts';
import { splitStatements } from '../data/sql';
import { uiType } from '../data/types';

export const WIDGET_TYPES = ['kpi', 'bar', 'horizontalBar', 'line', 'area', 'pie', 'histogram', 'table', 'text'];
// Widgets drawn as a chart of measures by a dimension; the user can switch among them
export const CHART_WIDGETS = ['bar', 'horizontalBar', 'line', 'area', 'pie'];
// Charts whose bars or slices filter the dashboard when clicked
export const CLICKABLE_WIDGETS = ['bar', 'horizontalBar', 'pie'];
export const AGGREGATIONS = ['count', 'countDistinct', 'sum', 'avg', 'min', 'max', 'median'];
const NUMERIC_AGGREGATIONS = ['sum', 'avg', 'median'];
export const FILTER_TYPES = ['select', 'range', 'dateRange'];
export const WIDTHS = [3, 4, 6, 8, 12];
const DEFAULT_WIDTH = { kpi: 3, table: 12, text: 12 };
export const MAX_DATASETS = 8;
export const MAX_WIDGETS = 24;
export const MAX_FILTERS = 8;
const MAX_MEASURES = 4;

const text = (value, limit = 200) => String(value ?? '').trim().slice(0, limit);

// Whether the SQL is one query, which is all a dataset can be
export function isSelect(sql) {
  const statements = splitStatements(sql);
  const code = (statements[0] || '').replace(/--[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '').trim();
  return statements.length === 1 && /^(select|with|from)\b/i.test(code);
}

// The specification with only what the app understands, and what is wrong in it (in English: the
// problems go back to the AI). Ids are given here: w1, w2... and f1, f2...
export function normalizeDashboard(raw) {
  const errors = [];
  const source = raw && typeof raw === 'object' ? raw : {};
  const list = (value, limit) => (Array.isArray(value) ? value.filter((item) => item && typeof item === 'object').slice(0, limit) : []);

  const datasets = [];
  for (const dataset of list(source.datasets, MAX_DATASETS)) {
    const id = text(dataset.id, 60);
    const sql = cleanSql(dataset.sql);
    if (!/^\w+$/.test(id) || datasets.some((d) => d.id === id)) {
      errors.push(`Dataset "${id}": the id must be a unique name of letters, digits and "_"`);
    } else if (!isSelect(sql)) {
      errors.push(`Dataset "${id}": the SQL must be a single SELECT statement`);
    } else {
      datasets.push({ id, sql });
    }
  }
  if (!datasets.length && !errors.length) errors.push('The dashboard needs at least one dataset');

  const widgets = [];
  list(source.widgets, MAX_WIDGETS).forEach((widget, index) => {
    const name = `Widget ${index + 1} (${text(widget.title, 60) || widget.type})`;
    if (!WIDGET_TYPES.includes(widget.type)) {
      errors.push(`${name}: unknown type "${widget.type}"`);
      return;
    }
    const type = widget.type;
    const clean = {
      type,
      title: text(widget.title),
      width: WIDTHS.includes(Number(widget.width)) ? Number(widget.width) : DEFAULT_WIDTH[type] || 6,
    };
    if (type === 'text') {
      clean.text = text(widget.text, 4000);
      if (clean.text || clean.title) widgets.push(clean);
      return;
    }
    clean.dataset = text(widget.dataset, 60);
    if (!datasets.some((d) => d.id === clean.dataset)) {
      // One dataset: it can only be that one
      if (datasets.length === 1) {
        clean.dataset = datasets[0].id;
      } else {
        errors.push(`${name}: unknown dataset "${clean.dataset}"`);
        return;
      }
    }
    clean.limit = Math.max(0, Math.round(Number(widget.limit)) || 0);
    if (type === 'table') {
      clean.columns = (Array.isArray(widget.columns) ? widget.columns : []).map((c) => text(c)).filter(Boolean);
    } else {
      if (type !== 'kpi') clean.dimension = text(widget.dimension);
      if (type !== 'histogram') {
        clean.measures = list(widget.measures, MAX_MEASURES)
          .filter((m) => AGGREGATIONS.includes(m.agg))
          .map((m) => ({ column: text(m.column) || '*', agg: m.agg, label: text(m.label, 80) }));
        if (!clean.measures.length) {
          errors.push(`${name}: it needs at least one measure (column and agg)`);
          return;
        }
        if (type === 'pie') clean.measures = clean.measures.slice(0, 1);
      }
      if (CHART_WIDGETS.includes(type)) {
        clean.sort = widget.sort === 'dimension' || (widget.sort !== 'value' && (type === 'line' || type === 'area'))
          ? 'dimension' : 'value';
      }
      if (type !== 'kpi' && !clean.dimension) {
        errors.push(`${name}: it needs a dimension column`);
        return;
      }
    }
    widgets.push(clean);
  });
  if (!widgets.length && !errors.length) errors.push('The dashboard needs at least one widget');

  const filters = [];
  for (const filter of list(source.filters, MAX_FILTERS)) {
    const column = text(filter.column);
    if (!column || filter.implicit || filters.some((f) => f.column === column)) continue;
    if (!FILTER_TYPES.includes(filter.type)) {
      errors.push(`Filter on "${column}": unknown type "${filter.type}"`);
      continue;
    }
    filters.push({ column, type: filter.type, label: text(filter.label, 80) || column });
  }

  widgets.forEach((widget, index) => { widget.id = `w${index + 1}`; });
  filters.forEach((filter, index) => { filter.id = `f${index + 1}`; });
  return { spec: { title: text(source.title), datasets, filters, widgets }, errors };
}

const datasetOf = (spec, id) => spec.datasets.find((dataset) => dataset.id === id);

// The datasets a filter applies to: the ones with its column
export function datasetsWith(spec, column) {
  return spec.datasets.filter((dataset) => dataset.columns && column in dataset.columns);
}

// What doesn't fit the columns of the datasets (once they are known)
function columnErrors(spec) {
  const errors = [];
  spec.widgets.forEach((widget, index) => {
    if (widget.type === 'text') return;
    const name = `Widget ${index + 1} (${widget.title || widget.type})`;
    const columns = datasetOf(spec, widget.dataset).columns;
    const known = Object.keys(columns).join(', ');
    const missing = (column) => {
      if (column in columns) return false;
      errors.push(`${name}: the dataset "${widget.dataset}" has no column "${column}". Its columns are: ${known}`);
      return true;
    };
    if (widget.dimension && !missing(widget.dimension) && widget.type === 'histogram'
        && uiType(columns[widget.dimension]) !== 'numeric') {
      errors.push(`${name}: a histogram needs a numeric column, "${widget.dimension}" is ${columns[widget.dimension]}`);
    }
    for (const measure of widget.measures || []) {
      if (measure.column === '*') {
        if (measure.agg !== 'count') errors.push(`${name}: column "*" can only be used with count`);
      } else if (!missing(measure.column) && NUMERIC_AGGREGATIONS.includes(measure.agg)
          && uiType(columns[measure.column]) !== 'numeric') {
        errors.push(`${name}: ${measure.agg} needs a numeric column, "${measure.column}" is ${columns[measure.column]}`);
      }
    }
    (widget.columns || []).forEach(missing);
  });
  for (const filter of spec.filters) {
    const [dataset] = datasetsWith(spec, filter.column);
    if (!dataset) {
      errors.push(`Filter on "${filter.column}": no dataset has that column`);
      continue;
    }
    const kind = uiType(dataset.columns[filter.column]);
    if (filter.type === 'range' && kind !== 'numeric') {
      errors.push(`Filter on "${filter.column}": a range filter needs a numeric column, it is ${dataset.columns[filter.column]}`);
    } else if (filter.type === 'dateRange' && kind !== 'temporal') {
      errors.push(`Filter on "${filter.column}": a dateRange filter needs a date or timestamp column, it is ${dataset.columns[filter.column]}`);
    }
  }
  return errors;
}

// Clicking a bar or a slice filters by its category: those charts get a filter on their dimension,
// shown only while it is set, unless the dashboard already has one
function withImplicitFilters(spec) {
  let next = 1;
  for (const widget of spec.widgets) {
    if (CLICKABLE_WIDGETS.includes(widget.type) && !spec.filters.some((f) => f.column === widget.dimension)) {
      spec.filters.push({ id: `x${next++}`, column: widget.dimension, type: 'select', label: widget.dimension, implicit: true });
    }
  }
  return spec;
}

// Checks a specification (the AI's answer, or a saved dashboard) against the database: every dataset
// must run and have the columns its widgets and filters use. Returns { spec, errors }; the spec can be
// drawn only when there are no errors.
export async function validateDashboard(engine, raw) {
  const { spec, errors } = normalizeDashboard(raw);
  if (errors.length) return { spec, errors };
  for (const dataset of spec.datasets) {
    try {
      const rows = await engine.query(`DESCRIBE SELECT * FROM (${dataset.sql}\n) AS s`);
      dataset.columns = Object.fromEntries(rows.map((row) => [row.column_name, row.column_type]));
    } catch (error) {
      errors.push(`Dataset "${dataset.id}": its SQL fails with: ${error.message}`);
    }
  }
  if (errors.length) return { spec, errors };
  errors.push(...columnErrors(spec));
  return { spec: withImplicitFilters(spec), errors };
}

// The specification as the AI wrote it, to ask for changes: no ids, column types or implicit filters
export function aiSpec(spec) {
  const pick = (object, keys) => Object.fromEntries(keys.filter((key) => object[key] !== undefined).map((key) => [key, object[key]]));
  return {
    title: spec.title,
    datasets: spec.datasets.map((dataset) => pick(dataset, ['id', 'sql'])),
    filters: spec.filters.filter((filter) => !filter.implicit).map((filter) => pick(filter, ['column', 'type', 'label'])),
    widgets: spec.widgets.map((widget) => pick(widget,
      ['type', 'title', 'dataset', 'dimension', 'measures', 'columns', 'text', 'width', 'sort', 'limit'])),
  };
}

// The name of a measure when it has no label: "avg fare", "count"
export function measureLabel(measure) {
  return measure.label || (measure.column === '*' ? measure.agg : `${measure.agg} ${measure.column}`);
}
