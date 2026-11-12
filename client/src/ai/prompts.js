// The prompts of the AI assistant, the same ones the backend sends (services/chatGPTService.py)

export const SQL_SYSTEM_PROMPT = `You are a SQL assistant, you only have to answer with SQL queries, no other text, only SQL.
Use exactly the table names provided. If the user asks for a chart, write the query that returns its data: a column for the
labels or the x axis and the numeric columns to plot, ordered so that it reads well. Don't put any other text that are not in the question or any other text that could break de SQL
syntax. Don't use any other character or context than the query itself. For example, don't include \`\`\`sql header in the response`;

export const DATA_SYSTEM_PROMPT = `You are a data assistant, you have to read the user question and the data provided and return a response
to help the user. You can use any text, but you have to return a response that is useful for the user.`;

export const RESULT_SYSTEM_PROMPT = `You are a data assistant. Read the user question, the SQL that answered it and its result (CSV), and
answer the question using that data, in Markdown.
Also choose a chart for the result in "chart":
- When the user asks for a chart, use the type they ask for (pie, bar, horizontalBar, line, area or scatter) or the best one.
- When they don't, propose one only if it clearly helps: several rows with a label and a numeric column. Otherwise type is "none".
- x is the column with the labels or the x axis, y the numeric columns to plot. Use exact column names from the CSV header.
- pie takes one y column; scatter takes a numeric x.
Don't describe the chart in the answer: the app draws it below.`;

export const TITLE_SYSTEM_PROMPT = `Give a short title, of 2 to 6 words, to a conversation that starts with the user question below.
Answer only with the title: no quotes, no final period, no prefix.`;

// The app languages, as the backend names them to the model
export const LANGUAGES = { en: 'English', es: 'Spanish from Spain' };
export const TITLE_LIMIT = 60;
// CSV characters sent to explain a result: fewer characters, fewer tokens
export const RESULT_CSV_LIMIT = 20000;

export const CHART_TYPES = ['none', 'pie', 'bar', 'horizontalBar', 'line', 'area', 'scatter'];
// The answer and the chart, as a JSON schema the model must follow
export const RESULT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['answer', 'chart'],
  properties: {
    answer: { type: 'string' },
    chart: {
      type: 'object', additionalProperties: false, required: ['type', 'title', 'x', 'y'],
      properties: {
        type: { type: 'string', enum: CHART_TYPES },
        title: { type: 'string' },
        x: { type: 'string' },
        y: { type: 'array', items: { type: 'string' } },
      },
    },
  },
};

// "Always answer in ..." for the app language, nothing for an unknown one
export function inLanguage(language, what = 'answer') {
  return LANGUAGES[language] ? `\nAlways ${what} in ${LANGUAGES[language]}.` : '';
}

// The tables and their columns, as the backend describes them to the model
export function describeSchema(schema) {
  return Object.entries(schema)
    .map(([table, columns]) => `One of the tables is called '${table}' and has following fields:`
      + Object.entries(columns).map(([column, type]) => `${column} (${type})`).join(','))
    .join(' ');
}

export function sqlQuestion(schema, question) {
  const tables = describeSchema(schema);
  return (tables ? ` You have the following tables: ${tables}.` : '') + ` The query I need, for DuckDB is:${question}`;
}

// Without code fences or a trailing semicolon, so the answer can run as it is
export function cleanSql(answer) {
  const sql = String(answer || '').replaceAll('```sql', '').replaceAll('```', '').trim();
  return sql.endsWith(';') ? sql.slice(0, -1).trim() : sql;
}

// A CSV field, quoted when it has to be (RFC 4180)
function csvField(value) {
  const text = value == null ? '' : String(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

// A result as CSV, header first, cut at `limit` characters on a row boundary
export function toCsv(columns, rows, limit = RESULT_CSV_LIMIT) {
  let csv = columns.map(csvField).join(',');
  for (const row of rows) {
    const line = '\n' + row.map(csvField).join(',');
    if (csv.length + line.length > limit) return csv + '\n(... more rows)';
    csv += line;
  }
  return csv;
}

export function resultRequest(question, sql, csv) {
  return `User question: ${question}\n\nSQL:\n${sql}\n\nResult (CSV):\n${csv}`;
}

// The chart the AI chose, if it plots columns of the result
export function validChart(chart, columns) {
  if (!chart || typeof chart !== 'object' || !CHART_TYPES.slice(1).includes(chart.type)) return null;
  let y = (chart.y || []).filter((column) => columns.includes(column));
  if (!columns.includes(chart.x) || !y.length) return null;
  if (chart.type === 'pie') y = y.slice(0, 1);
  return { type: chart.type, title: String(chart.title || ''), x: chart.x, y };
}

// The model's title without quotes or a final period, else the question itself
export function cleanTitle(title, question) {
  const clean = String(title || '').trim().replace(/^["'«“]+|["'»”]+$/g, '').replace(/\.+$/, '').trim();
  return (clean || question).slice(0, TITLE_LIMIT).trim();
}

// The dashboards the AI designs: the same text as DASHBOARD_INSTRUCTIONS in services/chatGPTService.py
export const DASHBOARD_SYSTEM_PROMPT = `You design data dashboards for Datalake Studio. From the user's tables and their instruction, answer with a
dashboard specification in JSON. The app runs the SQL on DuckDB and draws the widgets itself.
- datasets: named DuckDB SELECT queries with the rows the widgets aggregate. Keep them simple: usually "SELECT * FROM table",
  adding the computed columns the widgets need (date_trunc('month', ts) AS month, CASE buckets...). Don't aggregate in a
  dataset: the widgets aggregate. One statement each, no trailing semicolon. Use exactly the table and column names given.
- widgets, in reading order, on a 12-column grid (width 3, 4, 6, 8 or 12):
  - kpi: one to four headline numbers (measures), no dimension.
  - bar, horizontalBar, pie: measures grouped by a categorical dimension.
  - line, area: measures along an ordered dimension (dates, numbers), with sort "dimension".
  - histogram: the distribution of the numeric column in dimension.
  - table: rows of the dataset; columns lists the ones to show (empty for all).
  - text: a short Markdown note in text.
  - measures: column, agg (count, countDistinct, sum, avg, min, max or median) and a short label. Column "*" with count
    counts the rows.
  - sort: "value" (largest first) or "dimension". limit: maximum groups or rows (0 for the default).
  - Fields a widget doesn't use: empty string, empty array or 0.
- filters: controls that filter every dataset that has that column: select (categories), range (numbers) or dateRange
  (dates and timestamps). Add the 2 to 4 most useful ones. The user can also click bars and pie slices to filter by them.
Start with the KPIs, then the charts: 5 to 9 widgets unless asked otherwise. When there is a current dashboard, apply the
instruction to it and return the whole updated specification, keeping what the user didn't ask to change.
summary: one or two sentences telling the user what you built or changed.`;

const object = (properties) => ({ type: 'object', additionalProperties: false, required: Object.keys(properties), properties });
const string = { type: 'string' };
// The dashboard specification, as a JSON schema the model must follow
export const DASHBOARD_SCHEMA = object({
  title: string,
  summary: string,
  datasets: { type: 'array', items: object({ id: string, sql: string }) },
  filters: { type: 'array', items: object({ column: string, type: { type: 'string', enum: ['select', 'range', 'dateRange'] }, label: string }) },
  widgets: {
    type: 'array',
    items: object({
      type: { type: 'string', enum: ['kpi', 'bar', 'horizontalBar', 'line', 'area', 'pie', 'histogram', 'table', 'text'] },
      title: string,
      dataset: string,
      dimension: string,
      measures: {
        type: 'array',
        items: object({ column: string, agg: { type: 'string', enum: ['count', 'countDistinct', 'sum', 'avg', 'min', 'max', 'median'] }, label: string }),
      },
      columns: { type: 'array', items: string },
      text: string,
      width: { type: 'integer', enum: [3, 4, 6, 8, 12] },
      sort: { type: 'string', enum: ['value', 'dimension'] },
      limit: { type: 'integer' },
    }),
  },
});

// What the model is asked: the tables, the dashboard to change (if any), the instruction and, on a
// retry, its previous answer with what was wrong in it
export function dashboardRequest(schema, { instruction, current, previous, errors }) {
  const tables = describeSchema(schema);
  let request = tables ? `You have the following tables: ${tables}.\n\n` : '';
  if (current) request += `Current dashboard:\n${current}\n\n`;
  request += `Instruction: ${instruction}`;
  if (errors?.length) {
    request += `\n\nYour previous answer was:\n${previous || ''}\n\nIt had these problems, fix them:\n`
      + errors.map((error) => `- ${error}`).join('\n');
  }
  return request;
}
