import { http, HttpResponse } from 'msw'
import { server } from '../../test/msw/server'
import { setEngine } from '../../engine'
import { fakeEngine, schemaRows } from '../../test/fakeEngine'
import { capabilities } from '../../engine/engine'
import { aiReady, answer, askSql, forgetAiKey, saveAiSettings, transcribe } from '..'
import { cleanSql, describeSchema, resultQuestion, sqlQuestion } from '../prompts'

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

  it('sends at most 1000 characters of the result', () => {
    const rows = Array.from({ length: 500 }, (_, i) => ({ id: i, name: 'row ' + i }))
    const question = resultQuestion('how many?', 'SELECT *', rows)
    const csv = question.split('SQL result: ')[1].split('. Please')[0]
    expect(csv.startsWith('id,name\n0,row 0\n1,row 1')).toBe(true)
    expect(csv.length).toBeLessThanOrEqual(1000)
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
    expect(await answer('explain')).toContain('SELECT borough')
    forgetAiKey()
    expect(aiReady()).toBe(false)
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
