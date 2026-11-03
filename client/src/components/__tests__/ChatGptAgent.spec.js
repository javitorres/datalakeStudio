import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import ChatGptAgent from '../ChatGptAgent.vue'
import { server } from '../../test/msw/server'

const API = 'http://localhost:8000'

// The conversations saved on the server, in memory
let saved

const summary = (conversation) => Object.fromEntries(Object.entries(conversation).filter(([key]) => key !== 'messages'))

function serveConversations() {
  server.use(
    http.get(`${API}/conversations`, () => HttpResponse.json(Object.values(saved).map(summary))),
    http.get(`${API}/conversations/:id`, ({ params }) => HttpResponse.json(saved[params.id])),
    http.put(`${API}/conversations/:id`, async ({ params, request }) => {
      saved[params.id] = { id: params.id, ...(await request.json()), database: 'test', updated: Date.now() / 1000 }
      return HttpResponse.json(summary(saved[params.id]))
    }),
    http.patch(`${API}/conversations/:id`, async ({ params, request }) => {
      saved[params.id].title = (await request.json()).title
      return HttpResponse.json({ id: params.id, title: saved[params.id].title })
    }),
    http.delete(`${API}/conversations/:id`, ({ params }) => {
      delete saved[params.id]
      return HttpResponse.json({ status: 'ok' })
    }),
    http.get(`${API}/gpt/conversationTitle`, () => HttpResponse.json({ title: 'Petal length by species' })),
  )
}

// vue-echarts needs a canvas: the stub keeps the option it gets
const ChartStub = { name: 'ChartStub', props: ['option'], template: '<div class="chart-stub"></div>' }

function mountAgent(tables = ['iris']) {
  return mount(ChatGptAgent, {
    props: { tables },
    global: { stubs: { RecorderWidget: true, echarts: ChartStub } },
  })
}

describe('ChatGptAgent', () => {
  beforeAll(() => {
    // jsdom has no layout: scrolling the feed is a no-op
    Element.prototype.scrollTo = () => {}
  })

  beforeEach(() => {
    saved = {}
    serveConversations()
  })

  it('suggests questions about the user tables', () => {
    const wrapper = mountAgent(['__lastQuery', 'trips'])

    const suggestions = wrapper.findAll('.assistant-suggestion').map((b) => b.text())
    expect(suggestions).toContain('How many rows does trips have?')
    expect(suggestions.join(' ')).not.toContain('__lastQuery')
  })

  it('answers a question with the SQL, its result and the explanation, without speaking by default', async () => {
    const calls = []
    server.use(
      http.get(`${API}/gpt/askGPT`, ({ request }) => {
        calls.push(new URL(request.url).searchParams.get('question'))
        return HttpResponse.json('SELECT species, avg(petal_length) AS avg_len FROM iris GROUP BY species')
      }),
      http.post(`${API}/database/runQuery`, () => new HttpResponse(
        'species,avg_len\nIris-setosa,1.464\n"Iris, virginica",5.552\n', { headers: { 'Content-Type': 'text/csv' } })),
      http.post(`${API}/gpt/explainResult`, async ({ request }) => {
        calls.push((await request.json()).language)
        return HttpResponse.json({ answer: 'The longest petals:\n\n- **Iris virginica**: 5.552\n- <b>setosa</b>: 1.464', chart: null })
      }),
      http.get(`${API}/gpt/text2speech`, () => {
        calls.push('tts')
        return new HttpResponse('mp3')
      }),
    )
    const wrapper = mountAgent()

    await wrapper.find('textarea').setValue('Average petal length per species?')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(calls).toEqual(['Average petal length per species?', 'en'])
    expect(wrapper.find('.user-bubble').text()).toBe('Average petal length per species?')
    expect(wrapper.find('.assistant-sql pre').text()).toContain('GROUP BY species')
    expect(wrapper.findAll('.assistant-result th').map((th) => th.text())).toEqual(['species', 'avg_len'])
    expect(wrapper.findAll('.assistant-result tbody tr')[1].text()).toContain('Iris, virginica')
    expect(wrapper.find('.assistant-result-foot').text()).toBe('2 rows')
    const answer = wrapper.find('.assistant-text')
    expect(answer.find('strong').text()).toBe('Iris virginica')
    expect(answer.findAll('li')).toHaveLength(2)
    // Markdown is rendered, HTML in the answer is not
    expect(answer.find('b').exists()).toBe(false)
    expect(answer.text()).toContain('<b>setosa</b>')
    expect(wrapper.find('textarea').element.value).toBe('')
  })

  it('saves a new conversation with an AI title, and renames and deletes it', async () => {
    server.use(
      http.get(`${API}/gpt/askGPT`, () => HttpResponse.json('SELECT 1 AS n')),
      http.post(`${API}/database/runQuery`, () => new HttpResponse('n\n1\n', { headers: { 'Content-Type': 'text/csv' } })),
      http.post(`${API}/gpt/explainResult`, () => HttpResponse.json({ answer: 'One', chart: null })),
    )
    const wrapper = mountAgent()
    await flushPromises()
    expect(wrapper.find('.assistant-history-note').text()).toBe('Your conversations will appear here.')

    await wrapper.find('textarea').setValue('How long are the petals of each species?')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const [conversation] = Object.values(saved)
    expect(conversation.title).toBe('Petal length by species')
    expect(conversation.messages).toEqual([
      { role: 'user', text: 'How long are the petals of each species?' },
      { role: 'assistant', sql: 'SELECT 1 AS n', result: { columns: ['n'], rows: [['1']] }, text: 'One' },
    ])
    expect(wrapper.find('.assistant-history-group').text()).toBe('Today')
    expect(wrapper.find('.assistant-history-item.is-active').text()).toContain('Petal length by species')
    expect(wrapper.find('.assistant-bar-name').text()).toBe('Petal length by species')

    await wrapper.find('.assistant-history-action[title="Rename"]').trigger('click')
    await wrapper.find('.assistant-history-rename').setValue('  Iris petals ')
    await wrapper.find('.assistant-history-rename').trigger('keydown', { key: 'Enter' })
    await flushPromises()
    expect(saved[conversation.id].title).toBe('Iris petals')
    expect(wrapper.find('.assistant-history-open').text()).toBe('Iris petals')

    await wrapper.find('.assistant-history-action[title="Delete"]').trigger('click')
    await wrapper.find('.assistant-history-action.is-danger').trigger('click')
    await flushPromises()
    expect(saved).toEqual({})
    expect(wrapper.find('.assistant-history-item').exists()).toBe(false)
    expect(wrapper.find('.user-bubble').exists()).toBe(false)
  })

  it('draws the chart the AI chose, and switches its type', async () => {
    server.use(
      http.get(`${API}/gpt/askGPT`, () => HttpResponse.json('SELECT zone, trips, fare FROM t')),
      http.post(`${API}/database/runQuery`, () => new HttpResponse(
        'zone,trips,fare\nBronx,3,10.5\nQueens,5,12\n', { headers: { 'Content-Type': 'text/csv' } })),
      http.post(`${API}/gpt/explainResult`, () => HttpResponse.json({
        answer: 'Queens leads', chart: { type: 'pie', title: 'Trips per zone', x: 'zone', y: ['trips'] },
      })),
    )
    const wrapper = mountAgent()
    await wrapper.find('textarea').setValue('Pie chart of trips per zone')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.assistant-chart-title').text()).toBe('Trips per zone')
    const chart = () => wrapper.findComponent(ChartStub).props('option')
    expect(chart().series[0].type).toBe('pie')
    expect(chart().series[0].data).toEqual([{ name: 'Queens', value: 5 }, { name: 'Bronx', value: 3 }])

    await wrapper.find('.assistant-chart-types [title="Horizontal bars"]').trigger('click')
    await flushPromises()
    expect(chart().series[0]).toMatchObject({ type: 'bar', name: 'trips', data: [3, 5] })
    expect(chart().yAxis).toMatchObject({ type: 'category', data: ['Bronx', 'Queens'] })
    // The chart is saved with the conversation, with the type the user chose
    expect(Object.values(saved)[0].messages[1].chart).toEqual({ type: 'horizontalBar', title: 'Trips per zone', x: 'zone', y: ['trips'] })
  })

  it('lists the saved conversations by date and reopens one', async () => {
    const now = Date.now() / 1000
    saved = {
      'conv-old00001': { id: 'conv-old00001', title: 'Old one', updated: now - 30 * 24 * 3600, messages: [] },
      'conv-new00001': {
        id: 'conv-new00001', title: 'Trips per zone', updated: now,
        messages: [{ role: 'user', text: 'Trips per zone?' }, { role: 'assistant', sql: 'SELECT 2', text: '**Two** zones' }],
      },
    }
    const wrapper = mountAgent()
    await flushPromises()

    expect(wrapper.findAll('.assistant-history-group').map((h) => h.text())).toEqual(['Today', 'Older'])

    await wrapper.find('input[type="search"]').setValue('trips')
    expect(wrapper.findAll('.assistant-history-open').map((b) => b.text())).toEqual(['Trips per zone'])

    await wrapper.find('.assistant-history-open').trigger('click')
    await flushPromises()
    expect(wrapper.find('.user-bubble').text()).toBe('Trips per zone?')
    expect(wrapper.find('.assistant-sql pre').text()).toBe('SELECT 2')
    expect(wrapper.find('.assistant-text strong').text()).toBe('Two')

    await wrapper.find('.assistant-new').trigger('click')
    expect(wrapper.find('.assistant-suggestion').exists()).toBe(true)
    expect(wrapper.find('.assistant-history-item.is-active').exists()).toBe(false)
  })

  it('shows a failed query in the conversation', async () => {
    server.use(
      http.get(`${API}/gpt/askGPT`, () => HttpResponse.json('SELECT * FROM nope')),
      http.post(`${API}/database/runQuery`, () => HttpResponse.json(
        { status: 'error', message: 'Table nope does not exist' }, { status: 400 })),
    )
    const wrapper = mountAgent()

    await wrapper.find('textarea').setValue('broken question')
    await wrapper.find('textarea').trigger('keydown', { key: 'Enter' })
    await flushPromises()

    expect(wrapper.find('.assistant-error').text()).toContain('Table nope does not exist')
    expect(wrapper.find('.assistant-status').exists()).toBe(false)
    expect(wrapper.find('.assistant-send').attributes('disabled')).toBeDefined()   // empty draft, not busy
  })
})
