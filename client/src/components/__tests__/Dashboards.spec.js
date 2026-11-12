import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import DashboardsPanel from '../DashboardsPanel.vue'
import DashboardView from '../DashboardView.vue'
import PublishedDashboard from '../PublishedDashboard.vue'
import { server } from '../../test/msw/server'
import { setEngine } from '../../engine'
import { fakeEngine, schemaRows } from '../../test/fakeEngine'
import { capabilities } from '../../engine/engine'
import { saveAiSettings } from '../../ai'
import { publishedPathFromHash } from '../../lib/dashboards'

const API = 'http://localhost:8000'
const OPENAI = 'https://api.openai.com/v1'

// What the AI answers for "trips by borough"
const ANSWER = {
  title: 'Trips by borough',
  summary: 'Indicators and a chart of the trips per borough.',
  datasets: [{ id: 'trips', sql: 'SELECT * FROM trips' }],
  filters: [{ column: 'fare', type: 'range', label: 'Fare' }],
  widgets: [
    { type: 'kpi', title: 'Totals', dataset: 'trips', dimension: '', measures: [{ column: '*', agg: 'count', label: 'Trips' }], columns: [], text: '', width: 3, sort: 'value', limit: 0 },
    { type: 'bar', title: 'By borough', dataset: 'trips', dimension: 'borough', measures: [{ column: 'fare', agg: 'avg', label: 'Average fare' }], columns: [], text: '', width: 6, sort: 'value', limit: 0 },
  ],
}
// The same dashboard once the app has checked it
const SPEC = {
  title: 'Trips by borough',
  datasets: [{ id: 'trips', sql: 'SELECT * FROM trips', columns: { borough: 'VARCHAR', fare: 'DOUBLE' } }],
  filters: [
    { id: 'f1', column: 'fare', type: 'range', label: 'Fare' },
    { id: 'f2', column: 'borough', type: 'select', label: 'Borough' },
  ],
  widgets: [
    { id: 'w1', type: 'kpi', title: 'Totals', width: 3, dataset: 'trips', limit: 0, measures: [{ column: '*', agg: 'count', label: 'Trips' }] },
    { id: 'w2', type: 'bar', title: 'By borough', width: 6, dataset: 'trips', limit: 0, dimension: 'borough', sort: 'value', measures: [{ column: 'fare', agg: 'avg', label: 'Average fare' }] },
    { id: 'w3', type: 'table', title: 'Rows', width: 12, dataset: 'trips', limit: 0, columns: [] },
    { id: 'w4', type: 'text', title: 'Notes', width: 12, text: '**Fares** in <b>dollars</b>' },
  ],
}

// An engine with a table trips(borough, fare): it answers the queries of the dashboards
function tripsEngine(options = {}) {
  const engine = fakeEngine({
    query: (sql) => {
      if (sql.includes('information_schema')) return schemaRows({ trips: { borough: 'VARCHAR', fare: 'DOUBLE' } })
      if (sql.startsWith('DESCRIBE')) {
        if (sql.includes('no_such_table')) throw new Error('Table no_such_table does not exist')
        return [{ column_name: 'borough', column_type: 'VARCHAR' }, { column_name: 'fare', column_type: 'DOUBLE' }]
      }
      if (sql.includes('AS value')) return [{ value: 'Queens', n: 3 }, { value: 'Bronx', n: 2 }]
      if (sql.includes('AS min')) return [{ min: 2.5, max: 80 }]
      if (sql.includes('AS x,')) return [{ x: 'Queens', m0: 31.5 }, { x: 'Bronx', m0: 12 }]
      if (sql.includes('count(*) AS m0 FROM d')) return [{ m0: sql.includes('WHERE') ? 2 : 1234567 }]
      return [{ borough: 'Queens', fare: 31.5 }]
    },
    ...options,
  })
  setEngine(engine)
  return engine
}

// vue-echarts needs a canvas: the stub keeps the option it gets
const ChartStub = { name: 'ChartStub', props: ['option'], emits: ['click'], template: '<div class="chart-stub"></div>' }
const stubs = { echarts: ChartStub }

describe('DashboardView', () => {
  const mountView = (source, props = {}) => mount(DashboardView, { props: { spec: JSON.parse(JSON.stringify(SPEC)), source, ...props }, global: { stubs } })
  // A source that records what it is asked
  function recordingSource() {
    const calls = []
    return {
      calls,
      widget: async (widget, state) => {
        calls.push([widget.id, JSON.parse(JSON.stringify(state))])
        if (widget.id === 'w1') return [{ m0: 1234567 }]
        if (widget.id === 'w2') return [{ x: 'Queens', m0: 31.5 }, { x: 'Bronx', m0: 12 }]
        return [{ borough: 'Queens', fare: 31.5 }]
      },
      filter: async (filter) => (filter.type === 'select' ? [{ value: 'Queens', n: 3 }, { value: 'Bronx', n: 2 }] : [{ min: 2.5, max: 80 }]),
    }
  }

  it('draws every kind of widget from the rows of its source', async () => {
    const wrapper = mountView(recordingSource())
    await flushPromises()

    expect(wrapper.find('[data-widget="w1"] .dash-kpi-value').text()).toBe('1.2M')
    expect(wrapper.find('[data-widget="w1"] .dash-kpi-label').text()).toBe('Trips')
    const chart = wrapper.findComponent(ChartStub).props('option')
    expect(chart.xAxis.data).toEqual(['Queens', 'Bronx'])
    expect(chart.series[0]).toMatchObject({ name: 'Average fare', type: 'bar', data: [31.5, 12] })
    expect(wrapper.findAll('[data-widget="w3"] th').map((th) => th.text())).toEqual(['borough', 'fare'])
    // Markdown is rendered, HTML in it is not
    const note = wrapper.find('[data-widget="w4"] .dash-text')
    expect(note.find('strong').text()).toBe('Fares')
    expect(note.find('b').exists()).toBe(false)
    // A viewer has no tools to change the widgets
    expect(wrapper.find('.dash-tools').exists()).toBe(false)
  })

  it('asks for the rows again with the filters the user sets', async () => {
    vi.useFakeTimers()
    const source = recordingSource()
    const wrapper = mountView(source)
    await flushPromises()
    source.calls.length = 0

    expect(wrapper.find('[data-filter="f1"] input').attributes('placeholder')).toBe('2.5')
    await wrapper.find('[data-filter="f1"] input').setValue('10')
    await wrapper.findAll('[data-filter="f2"] input')[1].setValue(true)
    await vi.runAllTimersAsync()
    vi.useRealTimers()
    await flushPromises()

    expect(source.calls).toEqual(['w1', 'w2', 'w3'].map((id) => [id, { f1: [10, null], f2: ['Bronx'] }]))
    expect(wrapper.find('[data-filter="f2"] .dash-count').text()).toBe('1')

    await wrapper.find('.dash-clear').trigger('click')
    expect(wrapper.find('.dash-clear').exists()).toBe(false)
  })

  it('filters by a category when its bar is clicked', async () => {
    const source = recordingSource()
    const wrapper = mountView(source)
    await flushPromises()

    wrapper.findComponent(ChartStub).vm.$emit('click', { name: 'Queens' })
    await flushPromises()

    expect(wrapper.find('[data-filter="f2"] .dash-count').text()).toBe('1')
    // The chart keeps its bars, with the ones not chosen dimmed
    const [queens, bronx] = wrapper.findComponent(ChartStub).props('option').series[0].data
    expect([queens.itemStyle.opacity, bronx.itemStyle.opacity]).toEqual([1, 0.3])
  })

  it('shows the error of a widget without breaking the others', async () => {
    const source = recordingSource()
    const widget = source.widget
    source.widget = (w, state) => (w.id === 'w3' ? Promise.reject(new Error('Catalog Error: no trips')) : widget(w, state))
    const wrapper = mountView(source)
    await flushPromises()

    expect(wrapper.find('[data-widget="w3"] .dash-error').text()).toContain('Catalog Error: no trips')
    expect(wrapper.find('[data-widget="w1"] .dash-kpi-value').exists()).toBe(true)
  })

  it('lets the author change and remove widgets', async () => {
    const wrapper = mountView(recordingSource(), { editable: true })
    await flushPromises()

    await wrapper.find('[data-widget="w2"] .dash-tool[title="Pie"]').trigger('click')
    await wrapper.find('[data-widget="w1"] .dash-width').setValue('4')
    await wrapper.find('[data-widget="w3"] .dash-tool.is-danger').trigger('click')

    expect(wrapper.emitted('change').map(([widget, changes]) => [widget.id, changes])).toEqual([['w2', { type: 'pie' }], ['w1', { width: 4 }]])
    expect(wrapper.emitted('remove')[0][0].id).toBe('w3')
  })
})

describe('DashboardsPanel on the server', () => {
  // The dashboards saved on the server, in memory, and what the assistant was asked
  let saved
  let asked
  const summary = ({ spec, history, ...dashboard }) => dashboard // eslint-disable-line no-unused-vars

  beforeEach(() => {
    saved = {}
    asked = []
    tripsEngine()
    server.use(
      http.get(`${API}/dashboards`, () => HttpResponse.json(Object.values(saved).map(summary))),
      http.get(`${API}/dashboards/:id`, ({ params }) => HttpResponse.json(saved[params.id])),
      http.put(`${API}/dashboards/:id`, async ({ params, request }) => {
        saved[params.id] = { published: null, ...saved[params.id], id: params.id, ...(await request.json()), database: 'taxis', updated: 100 }
        return HttpResponse.json(summary(saved[params.id]))
      }),
      http.delete(`${API}/dashboards/:id`, ({ params }) => {
        delete saved[params.id]
        return HttpResponse.json({ status: 'ok' })
      }),
      http.get(`${API}/d`, () => HttpResponse.json([
        { path: 'sales/overview', title: 'Sales', owner: 'bob@example.com' },
        { path: 'mine', title: 'Mine', owner: 'alice@example.com' },
      ])),
      http.post(`${API}/gpt/dashboard`, async ({ request }) => {
        asked.push(await request.json())
        return HttpResponse.json(ANSWER)
      }),
    )
  })

  const mountPanel = () => mount(DashboardsPanel, { props: { tables: ['trips'], username: 'alice@example.com' }, global: { stubs } })

  async function build(wrapper, instruction) {
    await wrapper.find('textarea').setValue(instruction)
    await wrapper.find('form.boards-composer').trigger('submit')
    await flushPromises()
  }

  it('builds a dashboard from an instruction, draws it and saves it', async () => {
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.findAll('.boards-suggestion')[0].text()).toContain('trips')
    // What other users published, not the user's own
    expect(wrapper.findAll('.boards-shared').map((a) => a.attributes('href'))).toEqual([`${window.location.origin}/#/d/sales/overview`])

    await build(wrapper, 'trips by borough')

    expect(asked).toEqual([{ instruction: 'trips by borough', current: null, previous: null, errors: [], language: 'en' }])
    expect(wrapper.find('.boards-title').element.value).toBe('Trips by borough')
    expect(wrapper.find('[data-widget="w1"] .dash-kpi-value').text()).toBe('1.2M')
    expect(wrapper.find('[data-widget="w2"] h3').text()).toBe('By borough')
    expect(wrapper.find('.boards-log').text()).toContain('Indicators and a chart of the trips per borough.')
    const [stored] = Object.values(saved)
    expect(stored.title).toBe('Trips by borough')
    expect(stored.spec.widgets.map((w) => w.id)).toEqual(['w1', 'w2'])
    expect(stored.history.map((entry) => entry.role)).toEqual(['user', 'assistant'])
    expect(wrapper.find('.boards-item.is-active').text()).toBe('Trips by borough')
    expect(wrapper.find('.boards-state').text()).toBe('Saved')
  })

  it('sends the current dashboard to change it, and what was wrong for the AI to fix', async () => {
    const wrapper = mountPanel()
    await build(wrapper, 'trips by borough')
    asked = []
    let answers = 0
    server.use(http.post(`${API}/gpt/dashboard`, async ({ request }) => {
      asked.push(await request.json())
      answers += 1
      // The first answer plots a column that isn't there
      const widgets = answers === 1 ? [{ ...ANSWER.widgets[1], dimension: 'zone' }] : [ANSWER.widgets[0]]
      return HttpResponse.json({ ...ANSWER, summary: 'Only the totals now.', widgets })
    }))

    await build(wrapper, 'leave only the totals')

    expect(asked).toHaveLength(2)
    const current = JSON.parse(asked[0].current)
    expect(current.widgets.map((w) => w.title)).toEqual(['Totals', 'By borough'])
    expect(current.widgets[0]).not.toHaveProperty('id')
    expect(current.datasets[0]).toEqual({ id: 'trips', sql: 'SELECT * FROM trips' })
    expect(asked[1].errors[0]).toContain('has no column "zone". Its columns are: borough, fare')
    expect(JSON.parse(asked[1].previous).widgets[0].dimension).toBe('zone')
    expect(wrapper.findAll('.dash-widget')).toHaveLength(1)
    expect(Object.values(saved)[0].spec.widgets).toHaveLength(1)
  })

  it('keeps the dashboard when the AI cannot fix its answer', async () => {
    const wrapper = mountPanel()
    await build(wrapper, 'trips by borough')
    server.use(http.post(`${API}/gpt/dashboard`, () =>
      HttpResponse.json({ ...ANSWER, datasets: [{ id: 'trips', sql: 'SELECT * FROM no_such_table' }] })))

    await build(wrapper, 'use another table')

    expect(wrapper.find('.boards-log .text-danger').text()).toContain("couldn't build a valid dashboard")
    expect(wrapper.find('.boards-log .text-danger').text()).toContain('no_such_table')
    expect(wrapper.findAll('.dash-widget')).toHaveLength(2)
  })

  it('shows the error of the assistant', async () => {
    server.use(http.post(`${API}/gpt/dashboard`, () =>
      HttpResponse.json({ status: 'error', message: 'The AI assistant needs an OpenAI API key' }, { status: 503 })))
    const wrapper = mountPanel()

    await build(wrapper, 'trips by borough')

    expect(wrapper.find('.boards-log .text-danger').text()).toContain('needs an OpenAI API key')
    expect(wrapper.find('.dash-widget').exists()).toBe(false)
    expect(saved).toEqual({})
  })

  it('publishes it under a path with the SQL of its widgets, and unpublishes it', async () => {
    let sent
    server.use(
      http.put(`${API}/dashboards/:id/publish`, async ({ params, request }) => {
        sent = await request.json()
        if (sent.path === 'taken') return HttpResponse.json({ status: 'error', message: 'The path taken is already used by another dashboard' }, { status: 409 })
        saved[params.id].published = { path: sent.path.toLowerCase(), updated: 100 }
        return HttpResponse.json(summary(saved[params.id]))
      }),
      http.delete(`${API}/dashboards/:id/publish`, ({ params }) => {
        saved[params.id].published = null
        return HttpResponse.json(summary(saved[params.id]))
      }),
    )
    const wrapper = mountPanel()
    await build(wrapper, 'trips by borough')

    await wrapper.find('.boards-chip').trigger('click')
    await wrapper.find('.boards-path input').setValue('taken')
    await wrapper.find('form.boards-publish').trigger('submit')
    await flushPromises()
    expect(wrapper.find('.boards-publish-note.text-danger').text()).toContain('already used by another dashboard')

    await wrapper.find('.boards-path input').setValue('Taxis/By_Borough')
    expect(wrapper.find('form.boards-publish button[type="submit"]').element.disabled).toBe(false)
    await wrapper.find('form.boards-publish').trigger('submit')
    await flushPromises()

    expect(sent.path).toBe('Taxis/By_Borough')
    // A query per widget and filter control, with placeholders for the values of the viewers
    expect(Object.keys(sent.queries)).toEqual(['w1', 'w2', 'f1'])
    expect(sent.queries.w1).toContain('({f1_min}::DOUBLE IS NULL OR "fare" >= {f1_min}::DOUBLE)')
    expect(sent.queries.w1).toContain('{x1}::VARCHAR[]')
    expect(wrapper.find('.boards-path input').element.value).toBe('taxis/by_borough')
    expect(wrapper.find('.boards-publish a').attributes('href')).toBe(`${window.location.origin}/#/d/taxis/by_borough`)
    expect(wrapper.find('.boards-publish-note').text()).toBe('The published version is up to date')
    expect(wrapper.find('.boards-open .bi-broadcast').exists()).toBe(true)

    await wrapper.find('.boards-publish .btn-danger').trigger('click')
    await flushPromises()
    expect(wrapper.find('.boards-open .bi-broadcast').exists()).toBe(false)
  })

  it('reopens a saved dashboard, and tells when it no longer fits the database', async () => {
    saved = {
      'dash-good1': { id: 'dash-good1', title: 'Good', database: 'taxis', updated: 2, published: null, spec: SPEC, history: [] },
      'dash-lost1': {
        id: 'dash-lost1', title: 'Lost', database: 'sales', updated: 1, published: null, history: [],
        spec: { ...SPEC, datasets: [{ id: 'trips', sql: 'SELECT * FROM no_such_table' }] },
      },
    }
    const wrapper = mountPanel()
    await flushPromises()

    await wrapper.findAll('.boards-open')[0].trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.dash-widget')).toHaveLength(4)

    await wrapper.findAll('.boards-open')[1].trigger('click')
    await flushPromises()
    expect(wrapper.find('.boards-broken').text()).toContain('no_such_table')
    expect(wrapper.find('.boards-broken').text()).toContain('sales')
    expect(wrapper.find('.dash-widget').exists()).toBe(false)

    // Deleting asks first
    await wrapper.findAll('.boards-item')[1].find('.boards-action').trigger('click')
    await wrapper.find('.boards-action.is-danger').trigger('click')
    await flushPromises()
    expect(Object.keys(saved)).toEqual(['dash-good1'])
    expect(wrapper.find('.boards-empty').exists()).toBe(true)
  })
})

describe('DashboardsPanel in the browser', () => {
  let requests

  beforeEach(() => {
    localStorage.clear()
    requests = []
    tripsEngine({ mode: 'local', capabilities: capabilities({ ownAi: true }), databaseName: 'datalakeStudio.db' })
    server.use(http.post(`${OPENAI}/chat/completions`, async ({ request }) => {
      requests.push(await request.json())
      return HttpResponse.json({ choices: [{ message: { content: JSON.stringify(ANSWER) } }] })
    }))
  })

  it('needs the key of the user, sends only the schema and keeps the dashboard in this browser', async () => {
    const wrapper = mount(DashboardsPanel, { props: { tables: ['trips'] }, global: { stubs } })
    await flushPromises()
    expect(wrapper.find('textarea').attributes('disabled')).toBeDefined()
    // Nothing to publish without a server
    expect(wrapper.find('.boards-chip').exists()).toBe(false)

    saveAiSettings({ key: 'sk-test', model: 'gpt-test' })
    await wrapper.findComponent({ name: 'AiKeySettings' }).vm.$emit('change')
    await wrapper.find('textarea').setValue('viajes por barrio')
    await wrapper.find('form.boards-composer').trigger('submit')
    await flushPromises()

    const [request] = requests
    expect(request.response_format.json_schema).toMatchObject({ name: 'dashboard', strict: true })
    expect(request.messages[1].content).toContain("'trips' and has following fields:borough (VARCHAR),fare (DOUBLE)")
    expect(request.messages[1].content).toContain('Instruction: viajes por barrio')
    expect(wrapper.find('[data-widget="w2"] h3').text()).toBe('By borough')
    expect(wrapper.find('.boards-local').exists()).toBe(true)
    const [stored] = Object.values(JSON.parse(localStorage.getItem('datalakeStudio.dashboards')))
    expect(stored).toMatchObject({ title: 'Trips by borough', database: 'datalakeStudio.db', published: null })

    // It is there the next time the app opens
    const again = mount(DashboardsPanel, { props: { tables: ['trips'] }, global: { stubs } })
    await flushPromises()
    await again.find('.boards-open').trigger('click')
    await flushPromises()
    expect(again.findAll('.dash-widget')).toHaveLength(2)
  })
})

describe('PublishedDashboard', () => {
  it('reads the path of a published dashboard from the address', () => {
    expect(publishedPathFromHash('#/d/iris/flower_analysis')).toBe('iris/flower_analysis')
    expect(publishedPathFromHash('#/d/sales/')).toBe('sales')
    for (const hash of ['', '#/', '#/d/', '#/dashboards/x', '#/d/../users', '#/d/a?b=1']) {
      expect(publishedPathFromHash(hash), hash).toBeNull()
    }
  })

  it('shows the dashboard of another user with the rows the server gives, sending only filter values', async () => {
    const asked = []
    const { datasets, ...rest } = SPEC
    server.use(
      http.get(`${API}/d/taxis/by_borough`, () => HttpResponse.json({
        path: 'taxis/by_borough', title: 'Trips by borough', owner: 'alice@example.com', published: 100,
        spec: { ...rest, datasets: datasets.map(({ sql, ...dataset }) => dataset) }, // eslint-disable-line no-unused-vars
      })),
      http.post(`${API}/d/taxis/by_borough`, async ({ request }) => {
        const body = await request.json()
        asked.push(body)
        if (body.query === 'w1') return HttpResponse.json([{ m0: 42 }])
        if (body.query === 'w2') return HttpResponse.json([{ x: 'Queens', m0: 31.5 }])
        if (body.query === 'f2') return HttpResponse.json([{ value: 'Queens', n: 3 }])
        return HttpResponse.json(body.query === 'f1' ? [{ min: 1, max: 9 }] : [{ borough: 'Queens', fare: 31.5 }])
      }),
    )
    const wrapper = mount(PublishedDashboard, { props: { path: 'taxis/by_borough' }, global: { stubs } })
    await flushPromises()

    expect(wrapper.find('h1').text()).toBe('Trips by borough')
    expect(wrapper.find('.published-heading p').text()).toContain('alice@example.com')
    expect(wrapper.find('[data-widget="w1"] .dash-kpi-value').text()).toBe('42')
    expect(asked.map((body) => body.query).sort()).toEqual(['f1', 'f2', 'w1', 'w2', 'w3'])
    expect(asked.every((body) => !('sql' in body) && JSON.stringify(body.filters) === '{}')).toBe(true)
  })

  it('tells when nothing is published at the path', async () => {
    server.use(http.get(`${API}/d/gone`, () => HttpResponse.json({ status: 'error', message: 'Dashboard gone not found' }, { status: 404 })))
    const wrapper = mount(PublishedDashboard, { props: { path: 'gone' }, global: { stubs } })
    await flushPromises()

    expect(wrapper.find('.published-message h2').text()).toBe('There is no dashboard published at gone')
  })
})
