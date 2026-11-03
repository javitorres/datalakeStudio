import { describe, expect, it } from 'vitest';
import { quoteIdent, quoteLiteral, splitStatements } from '../sql';
import { uiType } from '../types';

describe('sql helpers', () => {
  it('quotes names and values', () => {
    expect(quoteIdent('my "table"')).toBe('"my ""table"""');
    expect(quoteLiteral("it's")).toBe("'it''s'");
    expect(quoteLiteral(null)).toBe('NULL');
  });

  it('splits scripts on the semicolons outside strings and comments', () => {
    const script = `
      SELECT 'a;b', "c;d" FROM t; -- one; two
      /* block; comment */ SELECT $$x;y$$;
      ;
      -- only a comment;
    `;
    expect(splitStatements(script)).toEqual([
      `SELECT 'a;b', "c;d" FROM t`,
      `-- one; two\n      /* block; comment */ SELECT $$x;y$$`,
    ]);
    expect(splitStatements("SELECT 'it''s; fine'")).toEqual(["SELECT 'it''s; fine'"]);
  });
});

describe('uiType', () => {
  it('groups DuckDB types for the UI', () => {
    expect(['BIGINT', 'INTEGER', 'DOUBLE', 'DECIMAL(10,2)', 'FLOAT', 'HUGEINT', 'UBIGINT'].map(uiType))
      .toEqual(Array(7).fill('numeric'));
    expect(['DATE', 'TIMESTAMP', 'TIMESTAMP WITH TIME ZONE', 'TIME'].map(uiType)).toEqual(Array(4).fill('temporal'));
    expect(uiType('BOOLEAN')).toBe('boolean');
    expect(['VARCHAR', "ENUM('a', 'b')", 'UUID'].map(uiType)).toEqual(Array(3).fill('text'));
    expect(['INTEGER[]', 'STRUCT(a INTEGER)', 'GEOMETRY', 'BLOB', 'INTERVAL'].map(uiType)).toEqual(Array(5).fill('other'));
  });
});
