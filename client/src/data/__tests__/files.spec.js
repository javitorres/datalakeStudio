import { describe, expect, it } from 'vitest'
import { isSupportedFile, loadFileSql, mainFileInZip, needsSpatial } from '../files'

describe('files', () => {
  it('reads each kind of file with its DuckDB function', () => {
    expect(loadFileSql('iris', 'https://example.com/iris.csv?raw=1'))
      .toBe(`CREATE OR REPLACE TABLE "iris" AS (SELECT * FROM read_csv_auto('https://example.com/iris.csv?raw=1', HEADER=TRUE, SAMPLE_SIZE=1000000))`)
    expect(loadFileSql('t', 'trips.parquet')).toContain(`read_parquet('trips.parquet')`)
    expect(loadFileSql('t', 'events.json.gz')).toContain(`read_json_auto('events.json.gz', maximum_object_size=60000000)`)
    expect(loadFileSql('t', "it's.geojson")).toContain(`ST_Read('it''s.geojson')`)
    expect(() => loadFileSql('t', 'notes.docx')).toThrow('Unsupported file type: notes.docx')
  })

  it('knows which files need the spatial extension', () => {
    expect(needsSpatial('zones/taxi_zones.shp')).toBe(true)
    expect(needsSpatial('iris.csv')).toBe(false)
    expect(isSupportedFile('data.tsv')).toBe(true)
  })

  it('picks the file to read inside a zip', () => {
    expect(mainFileInZip(['z/zones.dbf', 'z/zones.shx', 'z/zones.shp', 'z/zones.prj'])).toBe('z/zones.shp')
    expect(mainFileInZip(['readme.txt', 'data.parquet'])).toBe('readme.txt')
    expect(mainFileInZip(['image.png'])).toBeNull()
  })
})
