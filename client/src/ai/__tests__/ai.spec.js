import { http, HttpResponse } from 'msw'
import { server } from '../../test/msw/server'
import { setEngine } from '../../engine'
import { fakeEngine, schemaRows } from '../../test/fakeEngine'
import { capabilities } from '../../engine/engine'
import { aiReady, askSql, conversationTitle, explainResult, forgetAiKey, saveAiSettings, transcribe } from '..'
import { cleanSql, cleanTitle, describeSchema, sqlQuestion, toCsv, validChart } from '../prompts'

const OPENAI = 'https://api.openai.com/v1'

describe('prompts', () => {
  it('describes the tables as the backend does', () => {
    const schema = { iris: { species: 'VARCHAR', petal: 'DOUBLE' }, cars: { brand: 'VARCHAR' } }
    expect(describeSchema(schema)).toBe(
      "One of the tables is called 'iris' and has following fields:species (VARCHAR),petal (DOUBLE) "
      + "One of the tables is called 'cars' and has following fields:brand (VARCHAR)")
    expect(sqlQuestion({}, 'count rows')).toBe(' The query I need, for DuckDB is:count rows')
  })

  it('cleans the generated SQL', () => {
    expect(cleanSql('```sql\nSELECT 1;\n```')).toBe('SELECT 1')
  })

  it('writes the result as CSV, cut on a row boundary', () => {
    expect(toCsv(['zone', 'n'], [['Bronx, NY', '3'], ['say "hi"', '5']])).toBe('zone,n\n"Bronx, NY",3\n"say ""hi""",5')
    const rows = Array.from({ length: 500 }, (_, i) => [String(i), 'row ' + i])
    const csv = toCsv(['id', 'name'], rows, 1000)
    expect(csv.startsWith('id,name\n0,row 0\n1,row 1')).toBe(true)
    expect(csv.endsWith('\n(... more rows)')).toBe(true)
    expect(csv.length).toBeLessThanOrEqual(1000 + 20)
  })

  it('keeps only charts of columns in the result', () => {
    const columns = ['zone', 'trips', 'fare']
    expect(validChart({ type: 'pie', title: 'T', x: 'zone', y: ['trips', 'fare'] }, columns))
      .toEqual({ type: 'pie', title: 'T', x: 'zone', y: ['trips'] })
    expect(validChart({ type: 'none', title: '', x: '', y: [] }, columns)).toBeNull()
    expect(validChart({ type: 'bar', title: 'T', x: 'borough', y: ['trips'] }, columns)).toBeNull()
    expect(validChart({ type: 'radar', title: 'T', x: 'zone', y: ['trips'] }, columns)).toBeNull()
  })

  it('cleans the conversation titles', () => {
    expect(cleanTitle('"Viajes por barrio."', 'q')).toBe('Viajes por barrio')
    expect(cleanTitle('  ', 'x'.repeat(80))).toBe('x'.repeat(60))
  })
})

describe('own OpenAI key (browser engine)', () => {
  let requests

  beforeEach(() => {
    requests = []
    localStorage.clear()
    setEngine(fakeEngine({
      capabilities: capabilities({ ownAi: true }),
      query: () => schemaRows({ trips: { fare: 'DOUBLE', borough: 'VARCHAR' } }),
    }))
    server.use(
      http.post(`${OPENAI}/chat/completions`, async ({ request }) => {
        requests.push({ auth: request.headers.get('authorization'), body: await request.json() })
        return HttpResponse.json({ choices: [{ message: { content: '```sql\nSELECT borough FROM trips;\n```' } }] })
      }),
      http.post(`${OPENAI}/audio/transcriptions`, () => HttpResponse.text('you\n')),
    )
  })

  it('needs the key before asking', async () => {
    expect(aiReady()).toBe(false)
    await expect(askSql('boroughs')).rejects.toThrow('Add your OpenAI API key')
  })

  it('asks OpenAI with the key, the model and the schema', async () => {
    saveAiSettings({ key: ' sk-test ', model: 'gpt-test' })
    expect(aiReady()).toBe(true)
    expect(await askSql('list boroughs')).toBe('SELECT borough FROM trips')
    const [{ auth, body }] = requests
    expect(auth).toBe('Bearer sk-test')
    expect(body.model).toBe('gpt-test')
    expect(body.messages[1].content).toContain("'trips' and has following fields:fare (DOUBLE),borough (VARCHAR)")
    expect(body.messages[1].content).toContain('list boroughs')
    forgetAiKey()
    expect(aiReady()).toBe(false)
  })

  it('explains a result with a chart, and names conversations, in the app language', async () => {
    saveAiSettings({ key: 'sk-test' })
    server.use(http.post(`${OPENAI}/chat/completions`, async ({ request }) => {
      const body = await request.json()
      requests.push({ body })
      const content = body.response_format
        ? JSON.stringify({ answer: '**Queens** leads', chart: { type: 'pie', title: 'Trips', x: 'zone', y: ['trips', 'nope'] } })
        : '"Viajes por zona."'
      return HttpResponse.json({ choices: [{ message: { content } }] })
    }))
    const result = { columns: ['zone', 'trips'], rows: [['Bronx', '3'], ['Queens', '5']] }

    expect(await explainResult({ question: 'trips per zone', sql: 'SELECT 1', result, language: 'es' }))
      .toEqual({ answer: '**Queens** leads', chart: { type: 'pie', title: 'Trips', x: 'zone', y: ['trips'] } })
    expect(await conversationTitle('¿Cuántos viajes por zona?', 'es')).toBe('Viajes por zona')

    const [explain, title] = requests.map((r) => r.body)
    expect(explain.response_format.json_schema.strict).toBe(true)
    expect(explain.messages[0].content).toContain('Spanish from Spain')
    expect(explain.messages[1].content).toContain('zone,trips\nBronx,3\nQueens,5')
    expect(title.messages[0].content).toContain('Spanish from Spain')
  })

  it('treats a silent recording as empty', async () => {
    saveAiSettings({ key: 'sk-test' })
    expect(await transcribe(new Blob(['RIFF'], { type: 'audio/wav' }))).toBe('')
  })

  it('explains a request the browser could not read', async () => {
    saveAiSettings({ key: 'sk-bad' })
    server.use(http.post(`${OPENAI}/chat/completions`, () => HttpResponse.error()))
    await expect(askSql('x')).rejects.toThrow('check your API key and the model name')
  })

  it('shows the error OpenAI sends', async () => {
    saveAiSettings({ key: 'sk-bad' })
    server.use(http.post(`${OPENAI}/chat/completions`, () =>
      HttpResponse.json({ error: { message: 'Incorrect API key provided' } }, { status: 401 })))
    await expect(askSql('x')).rejects.toThrow('Incorrect API key provided')
  })
})
