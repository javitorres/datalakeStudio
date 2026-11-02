import { http, HttpResponse } from 'msw'
import { tableFromArrays, tableToIPC } from 'apache-arrow'
import { RemoteEngine } from '../RemoteEngine'
import { server } from '../../test/msw/server'

const CONNECTOR = 'http://localhost:8000/database/restConnector'

describe('RemoteEngine', () => {
  it('runs queries through the backend restConnector', async () => {
    const bodies = []
    server.use(http.post(CONNECTOR, async ({ request }) => {
      const body = await request.json()
      bodies.push(body)
      if (body.type === 'json') return HttpResponse.json([{ n: 1 }])
      if (body.type === 'arrow') {
        return HttpResponse.arrayBuffer(tableToIPC(tableFromArrays({ n: Int32Array.from([7, 8]) }), 'stream'))
      }
      return HttpResponse.json({ status: 'ok' })
    }))

    const engine = new RemoteEngine()
    expect(await engine.query('SELECT 1 AS n')).toEqual([{ n: 1 }])
    const table = await engine.queryArrow('SELECT n')
    expect(table.getChild('n').toArray()).toEqual(Int32Array.from([7, 8]))
    await engine.exec('CREATE TABLE t (n INT)')
    expect(bodies).toEqual([
      { type: 'json', sql: 'SELECT 1 AS n' },
      { type: 'arrow', sql: 'SELECT n' },
      { type: 'exec', sql: 'CREATE TABLE t (n INT)' },
    ])
  })

  it('throws the backend error message', async () => {
    server.use(http.post(CONNECTOR, async ({ request }) => {
      const body = await request.json()
      if (body.type === 'arrow') return new HttpResponse('Catalog Error: Table x does not exist', { status: 500 })
      return HttpResponse.json({ status: 'error', message: 'Parser Error: syntax error' }, { status: 500 })
    }))

    const engine = new RemoteEngine()
    await expect(engine.query('SELEC')).rejects.toThrow('Parser Error: syntax error')
    await expect(engine.queryArrow('SELECT * FROM x')).rejects.toThrow('Catalog Error: Table x does not exist')
  })

  it('lists databases with the active one from the backend header', async () => {
    server.use(http.get('http://localhost:8000/database/getDatabaseList', () => HttpResponse.json(
      ['a.db', 'b.db'], { headers: { 'X-Current-Database': 'b.db', 'Access-Control-Expose-Headers': 'X-Current-Database' } })))

    expect(await new RemoteEngine().listDatabases()).toEqual({ databases: ['a.db', 'b.db'], current: 'b.db' })
  })
})
