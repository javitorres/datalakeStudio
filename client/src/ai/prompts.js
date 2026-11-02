// The prompts of the AI assistant, the same ones the backend sends (services/chatGPTService.py)

export const SQL_SYSTEM_PROMPT = `You are a SQL assistant, you only have to answer with SQL queries, no other text, only SQL.
Use exactly the table names provided. Don't put any other text that are not in the question or any other text that could break de SQL
syntax. Don't use any other character or context than the query itself. For example, don't include \`\`\`sql header in the response`;

export const DATA_SYSTEM_PROMPT = `You are a data assistant, you have to read the user question and the data provided and return a response
to help the user. You can use any text, but you have to return a response that is useful for the user.`;

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

// What the chat sends to explain a result: the question, the SQL and the first rows (at most `limit`
// characters, as the backend accepted)
export function resultQuestion(question, sql, rows, limit = 1000) {
  const columns = rows.length ? Object.keys(rows[0]) : [];
  let csv = columns.join(',');
  for (const row of rows) {
    const line = '\n' + columns.map((column) => row[column]).join(',');
    if (csv.length + line.length > limit) break;
    csv += line;
  }
  return `User question is: ${question} and ChatGPT answer is: ${sql} and SQL result: ${csv}. `
    + 'Please give me a verbalized answer to the questoin using the provided data';
}
