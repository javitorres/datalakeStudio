// @vitest-environment node
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { createNodeEngine } from './nodeEngine'
import { dataExtent, mapCells, mapGeometries, mapPoints, parseBbox } from '../maps'

let engine

beforeAll(async () => {
  engine = await createNodeEngine()
  await engine.exec(`
    INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3;
    CREATE TABLE places AS SELECT * FROM (VALUES
      ('Sol', 40.4169, -3.7035, 10, 'a'), ('Retiro', 40.4153, -3.6845, 20, 'b'),
      ('Sagrada Familia', 41.4036, 2.1744, NULL, 'c'), ('Far away', 10.0, 10.0, 5, 'd')
    ) t(name, lat, lon, visitors, code);
    CREATE TABLE zones AS SELECT 'square' AS name, 7 AS visitors,
      ST_AsText(ST_Transform(ST_GeomFromText('POLYGON((-3.71 40.41, -3.69 40.41, -3.69 40.42, -3.71 40.42, -3.71 40.41))'),
        'EPSG:4326', 'EPSG:32630', always_xy := true)) AS wkt;`)
}, 120000)

afterAll(() => engine.close())

const SPAIN = '-19.3,26.5,7.8,44.5'

describe('maps', () => {
  it('checks the visible area', () => {
    expect(parseBbox('-10,30,5,45')).toEqual({ west: -10, south: 30, east: 5, north: 45 })
    expect(() => parseBbox('1,2,3')).toThrow('four finite numbers')
    expect(() => parseBbox('5,30,-10,45')).toThrow('outside valid')
  })

  it('returns the points inside the area, after the filter', async () => {
    const points = await mapPoints(engine, { table: 'places', latitudeField: 'lat', longitudeField: 'lon', fields: ['visitors'], bbox: SPAIN })
    expect(points.features.map((f) => f.geometry.coordinates)).toEqual([[-3.7035, 40.4169], [-3.6845, 40.4153], [2.1744, 41.4036]])
    expect(points.features[0].properties).toEqual({ visitors: 10 })
    const filtered = await mapPoints(engine, { table: 'places', latitudeField: 'lat', longitudeField: 'lon', bbox: SPAIN, filter: 'visitors > 15' })
    expect(filtered.features).toHaveLength(1)
  })

  it('aggregates rows into H3 cells', async () => {
    const { geojson, metadata } = await mapCells(engine, { table: 'places', latitudeField: 'lat', longitudeField: 'lon', fields: ['visitors'], level: 5, bbox: SPAIN })
    expect(metadata.records).toBe(2)
    const [madrid, barcelona] = geojson.features
    expect(madrid.properties).toMatchObject({ count: 2, visitors: 15 })
    expect(madrid.properties.h3_cell).toMatch(/^85[0-9a-f]+$/)
    expect(madrid.geometry.type).toBe('Polygon')
    expect(barcelona.properties.visitors).toBe(-1)
  })

  it('draws WKT geometries in lon/lat', async () => {
    const { geojson } = await mapGeometries(engine, { table: 'zones', geomField: 'wkt', fields: ['visitors'], bbox: SPAIN })
    expect(geojson.features).toHaveLength(1)
    const [lon, lat] = geojson.features[0].geometry.coordinates[0][0]
    expect(lon).toBeCloseTo(-3.71, 4)
    expect(lat).toBeCloseTo(40.41, 4)
    expect(geojson.features[0].properties).toEqual({ visitors: 7 })
  })

  it('finds the area where most of the data is', async () => {
    await engine.exec(`CREATE TABLE spread AS SELECT 40 + i / 100 AS lat, -4 + i / 100 AS lon FROM range(100) t(i)
      UNION ALL SELECT 0, 0`)
    const extent = await dataExtent(engine, { table: 'spread', latitudeField: 'lat', longitudeField: 'lon' })
    expect(extent.south).toBeGreaterThan(39.9)
    expect(extent.north).toBeLessThan(41)
    expect(extent.west).toBeGreaterThan(-4.1)
    const single = await dataExtent(engine, { table: 'places', latitudeField: 'lat', longitudeField: 'lon', filter: "name = 'Sol'" })
    expect(single.north - single.south).toBeCloseTo(0.02, 5)
    const zones = await dataExtent(engine, { table: 'zones', geomField: 'wkt' })
    expect(zones.west).toBeCloseTo(-3.71, 1)
    expect(zones.north).toBeCloseTo(40.42, 1)
    expect(await dataExtent(engine, { table: 'places', latitudeField: 'lat', longitudeField: 'lon', filter: 'false' })).toBeNull()
    expect(await dataExtent(engine, { table: 'places' })).toBeNull()
  })

  it('rejects unknown and non-numeric columns', async () => {
    await expect(mapPoints(engine, { table: 'places', latitudeField: 'lat', longitudeField: 'nope', bbox: SPAIN })).rejects.toThrow('Unknown columns: nope')
    await expect(mapCells(engine, { table: 'places', latitudeField: 'lat', longitudeField: 'lon', fields: ['code'], bbox: SPAIN })).rejects.toThrow('must be numeric: code')
    await expect(mapCells(engine, { table: 'missing', latitudeField: 'lat', longitudeField: 'lon', bbox: SPAIN })).rejects.toThrow('Unknown table')
  })
})
