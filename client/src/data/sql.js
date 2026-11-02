// Small SQL helpers shared by every data module. Engines take plain SQL strings (no bound
// parameters), so every value or name written into a query goes through these.

export function quoteIdent(name) {
  return '"' + String(name).replaceAll('"', '""') + '"';
}

export function quoteLiteral(value) {
  if (value === null || value === undefined) return 'NULL';
  return "'" + String(value).replaceAll("'", "''") + "'";
}

// Splits a script into statements on the semicolons that are outside strings, quoted identifiers,
// dollar-quoted strings and comments. Empty statements are dropped.
export function splitStatements(script) {
  const statements = [];
  let current = '';
  let i = 0;
  while (i < script.length) {
    const ch = script[i];
    const next = script[i + 1];
    if (ch === "'" || ch === '"') {
      const end = closingQuote(script, i, ch);
      current += script.slice(i, end);
      i = end;
    } else if (ch === '-' && next === '-') {
      const end = script.indexOf('\n', i);
      const stop = end === -1 ? script.length : end;
      current += script.slice(i, stop);
      i = stop;
    } else if (ch === '/' && next === '*') {
      const end = script.indexOf('*/', i + 2);
      const stop = end === -1 ? script.length : end + 2;
      current += script.slice(i, stop);
      i = stop;
    } else if (ch === '$' && /^\$[A-Za-z_]*\$/.test(script.slice(i))) {
      const tag = script.slice(i).match(/^\$[A-Za-z_]*\$/)[0];
      const end = script.indexOf(tag, i + tag.length);
      const stop = end === -1 ? script.length : end + tag.length;
      current += script.slice(i, stop);
      i = stop;
    } else if (ch === ';') {
      statements.push(current);
      current = '';
      i += 1;
    } else {
      current += ch;
      i += 1;
    }
  }
  statements.push(current);
  return statements.map((s) => s.trim()).filter((s) => s && !isOnlyComments(s));
}

// Index just past the quote that closes the one at `start` (a doubled quote is an escaped one)
function closingQuote(script, start, quote) {
  let i = start + 1;
  while (i < script.length) {
    if (script[i] === quote) {
      if (script[i + 1] === quote) {
        i += 2;
        continue;
      }
      return i + 1;
    }
    i += 1;
  }
  return script.length;
}

function isOnlyComments(statement) {
  return statement.replace(/--[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '').trim() === '';
}
