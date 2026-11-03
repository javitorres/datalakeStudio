// How the UI treats a DuckDB column type: which charts, map fields and statistics it gets.
//   numeric  | temporal | boolean | text | other (lists, structs, blobs, geometries...)
const NUMERIC = /^(TINYINT|SMALLINT|INTEGER|INT|INT\d+|BIGINT|HUGEINT|UTINYINT|USMALLINT|UINTEGER|UBIGINT|UHUGEINT|FLOAT|FLOAT\d*|REAL|DOUBLE|DECIMAL|NUMERIC)\b/;
const TEMPORAL = /^(DATE|TIME|TIMESTAMP|DATETIME)/;
const TEXT = /^(VARCHAR|CHAR|BPCHAR|TEXT|STRING|ENUM|UUID)\b/;

export function uiType(columnType) {
  const type = String(columnType || '').trim().toUpperCase();
  // Nested types end in [] or are written as STRUCT(...), MAP(...)
  if (/\[\d*\]$/.test(type)) return 'other';
  if (NUMERIC.test(type)) return 'numeric';
  if (TEMPORAL.test(type)) return 'temporal';
  if (type === 'BOOLEAN' || type === 'BOOL') return 'boolean';
  if (TEXT.test(type)) return 'text';
  return 'other';
}
