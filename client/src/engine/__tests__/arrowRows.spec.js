import { DateDay, DateMillisecond, Field, Int64, Int32, List, Schema, Table, TimestampMillisecond, Utf8, vectorFromArray } from 'apache-arrow'
import { arrowToRows } from '../arrowRows'

describe('arrowToRows', () => {
  it('turns Arrow values into plain JSON-friendly values', () => {
    const at = Date.UTC(2024, 0, 2, 18, 12, 29)
    const table = new Table({
      n: vectorFromArray([1n, 2n ** 60n, null], new Int64()),
      s: vectorFromArray(['a', null, 'c'], new Utf8()),
      day: vectorFromArray([new Date(Date.UTC(2024, 0, 2)), null, null], new DateDay()),
      ms: vectorFromArray([new Date(at), null, null], new DateMillisecond()),
      ts: vectorFromArray([at, null, null], new TimestampMillisecond()),
      l: vectorFromArray([[1, 2], [], null], new List(new Field('item', new Int32(), true))),
    })

    expect(arrowToRows(table)).toEqual([
      { n: 1, s: 'a', day: '2024-01-02', ms: '2024-01-02T18:12:29', ts: '2024-01-02T18:12:29', l: [1, 2] },
      { n: '1152921504606846976', s: null, day: null, ms: null, ts: null, l: [] },
      { n: null, s: 'c', day: null, ms: null, ts: null, l: null },
    ])
  })

  it('returns no rows for an empty result', () => {
    expect(arrowToRows(new Table(new Schema([new Field('x', new Int32())])))).toEqual([])
  })
})
