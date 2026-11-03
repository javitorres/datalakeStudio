import { DateUnit, Type } from 'apache-arrow';

// Turns an Arrow table into the plain rows every engine returns: numbers instead of BigInts (strings
// when they don't fit), dates as ISO strings without a time zone (DuckDB's TIMESTAMP has none) and
// nested values as plain arrays and objects
export function arrowToRows(table) {
  const converters = table.schema.fields.map((field) => [field.name, converterFor(field.type)]);
  const rows = [];
  for (let i = 0; i < table.numRows; i += 1) {
    const row = table.get(i);
    const plain = {};
    for (const [name, convert] of converters) plain[name] = convert(row[name]);
    rows.push(plain);
  }
  return rows;
}

function converterFor(type) {
  if (type.typeId === Type.Date || type.typeId === Type.Timestamp) {
    // DATE columns are days; timestamps arrive as millisecond dates (castTimestampToDate)
    const dateOnly = type.typeId === Type.Date && type.unit === DateUnit.DAY;
    return (value) => (value === null || value === undefined ? null : isoDate(value, dateOnly));
  }
  return plainValue;
}

function isoDate(value, dateOnly) {
  const iso = new Date(typeof value === 'bigint' ? Number(value) : value).toISOString();
  return dateOnly ? iso.slice(0, 10) : iso.replace('Z', '').replace(/\.000$/, '');
}

function plainValue(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === 'bigint') return Number.isSafeInteger(Number(value)) ? Number(value) : value.toString();
  if (typeof value !== 'object') return value;
  if (value instanceof Uint8Array) return `[${value.length} bytes]`;
  // Arrow vectors (lists) and struct rows
  if (typeof value.toArray === 'function') return Array.from(value.toArray(), plainValue);
  if (typeof value.toJSON === 'function') value = value.toJSON();
  return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, plainValue(v)]));
}
