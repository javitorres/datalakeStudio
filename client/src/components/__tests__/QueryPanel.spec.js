import { flushPromises, mount } from '@vue/test-utils'
import { CompletionContext } from '@codemirror/autocomplete'
import { EditorState } from '@codemirror/state'
import QueryPanel from '../QueryPanel.vue'
import MapH3 from '../MapH3.vue'
import { setEngine } from '../../engine'
import { fakeEngine, schemaRows } from '../../test/fakeEngine'

vi.mock('vue-codemirror', () => ({
  Codemirror: {
    name: 'Codemirror',
    props: ['extensions'],
    template: '<div data-test="codemirror"></div>'
  }
}))

vi.mock('vue3-toastify', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
    POSITION: { BOTTOM_RIGHT: 'bottom-right' },
    promise: (p) => p
  }
}))

async function completionOptions(extensions, doc, pos = doc.length) {
  const state = EditorState.create({ doc, extensions })
  const sources = state.languageDataAt('autocomplete', pos)
  const results = await Promise.all(
    sources.map((source) => source(new CompletionContext(state, pos, true)))
  )
  return results.flatMap((result) => result?.options || [])
}

describe('QueryPanel', () => {
  let engine
  const ranQueries = []

  function useSchema(schema) {
    engine = fakeEngine({
      query: () => (typeof schema === 'function' ? schema() : schemaRows(schema)),
      runUserQuery: async (sql) => { ranQueries.push(sql) },
    })
    setEngine(engine)
  }

  beforeEach(() => {
    ranQueries.length = 0
    useSchema({ iris: { id: 'INTEGER', species: 'VARCHAR', sepal_length: 'DOUBLE' } })
  })

  it('runs the main query on the engine', async () => {

    const wrapper = mount(QueryPanel, {
      props: { tables: ['iris'] },
      global: {
        stubs: {
          TableInspector: { template: '<div data-test="table-inspector"></div>' }
        }
      }
    })

    const runButton = wrapper.findAll('button').find((b) => b.text().includes('Run Query'))
    await runButton.trigger('click')
    await flushPromises()

    expect(ranQueries).toEqual(['SELECT * FROM iris'])
    expect(wrapper.find('[data-test="table-inspector"]').exists()).toBe(true)
  })

  it('creates table from query and emits tableCreated', async () => {

    const wrapper = mount(QueryPanel, {
      props: { tables: ['iris'] },
      global: {
        stubs: {
          TableInspector: { template: '<div />' }
        }
      }
    })

    await wrapper.findAll('button').find((b) => b.text().includes('Run Query')).trigger('click')
    await flushPromises()

    await wrapper.findAll('a').find((a) => a.text().includes('New table')).trigger('click')
    await flushPromises()

    await wrapper.find('input#tableNameInput').setValue('iris_copy')
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().includes('Create table')).trigger('click')
    await flushPromises()

    expect(ranQueries).toEqual(['SELECT * FROM iris'])
    expect(engine.calls.exec).toEqual(['CREATE OR REPLACE TABLE "iris_copy" AS (SELECT * FROM iris)'])
    expect(wrapper.emitted('tableCreated')).toBeTruthy()
  })

  it('loads and reloads the completion schema when tables change', async () => {
    let schemaCalls = 0
    useSchema(() => {
      schemaCalls += 1
      return schemaRows(schemaCalls === 1 ? { iris: { id: 'INTEGER' } } : { orders: { total: 'DOUBLE' } })
    })

    const wrapper = mount(QueryPanel, { props: { tables: ['iris'] } })
    await flushPromises()
    expect(wrapper.text()).toContain('1 table indexed')

    await wrapper.setProps({ tables: ['orders'] })
    await flushPromises()
    expect(schemaCalls).toBe(2)
    expect(wrapper.text()).toContain('1 table indexed')

    const extensions = wrapper.findComponent({ name: 'Codemirror' }).props('extensions')
    const options = await completionOptions(extensions, 'SELECT orders.')
    expect(options).toContainEqual(expect.objectContaining({
      label: 'total', type: 'property', detail: 'DOUBLE'
    }))
  })

  it('offers tables, qualified columns, aliases and quoted identifiers', async () => {
    useSchema({
      iris: { id: 'INTEGER', 'sepal length': 'DOUBLE' },
      'sales data': { 'order total': 'DECIMAL(10,2)' }
    })

    const wrapper = mount(QueryPanel, { props: { tables: ['iris', 'sales data'] } })
    await flushPromises()
    const extensions = wrapper.findComponent({ name: 'Codemirror' }).props('extensions')

    const fromOptions = await completionOptions(extensions, 'SELECT * FROM sa')
    expect(fromOptions).toContainEqual(expect.objectContaining({
      label: 'sales data', apply: '"sales data"'
    }))

    const joinOptions = await completionOptions(extensions, 'SELECT * FROM iris JOIN sa')
    expect(joinOptions.some((option) => option.label === 'sales data')).toBe(true)

    const tableOptions = await completionOptions(extensions, 'SELECT iris.')
    expect(tableOptions).toContainEqual(expect.objectContaining({
      label: 'sepal length', apply: '"sepal length"', detail: 'DOUBLE'
    }))

    const aliasQuery = 'SELECT i. FROM iris AS i'
    const aliasOptions = await completionOptions(extensions, aliasQuery, 'SELECT i.'.length)
    expect(aliasOptions.some((option) => option.label === 'id')).toBe(true)
  })

  it('keeps SQL keyword completion available when schema loading fails', async () => {
    useSchema(() => { throw new Error('Database closed') })

    const wrapper = mount(QueryPanel, { props: { tables: ['iris'] } })
    await flushPromises()

    expect(wrapper.text()).toContain('Autocomplete unavailable')
    expect(wrapper.findComponent({ name: 'Codemirror' }).exists()).toBe(true)
    const extensions = wrapper.findComponent({ name: 'Codemirror' }).props('extensions')
    const options = await completionOptions(extensions, 'SEL')
    expect(options.some((option) => option.label === 'SELECT')).toBe(true)
  })

  describe('map helpers', () => {
    it('detects coordinate and numeric fields without confusing population with latitude', () => {
      const context = {
        schema: { population: 'BIGINT', lat_coord: 'DOUBLE', longitude: 'DECIMAL(9,6)', name: 'VARCHAR' },
        selectedFields: ['population', 'lat_coord', 'longitude', 'name'],
        numericFields: [],
        selectedFieldForH3: null,
        selectedFieldForPoints: null,
        latitudeField: null,
        longitudeField: null,
        geomField: null
      }

      MapH3.methods.setNumericFields.call(context)
      MapH3.methods.guessLatitudeLongitude.call(context)

      expect(context.numericFields).toEqual(['population', 'lat_coord', 'longitude'])
      expect(context.latitudeField).toBe('lat_coord')
      expect(context.longitudeField).toBe('longitude')
      expect(context.selectedFieldForH3).toBe('population')
    })

    it('calculates finite percentiles and histograms for zero and string values', () => {
      const geojson = { features: [
        { properties: { value: '0' } },
        { properties: { value: 0 } },
        { properties: { value: '10' } },
        { properties: { value: null } }
      ] }

      const result = MapH3.methods.getPercentiles.call({}, geojson, 'value')
      expect(result.p0).toBe(0)
      expect(result.p100).toBe(10)
      expect(result.histogram.reduce((sum, count) => sum + count, 0)).toBe(3)
      expect(result.percentiles.every(Number.isFinite)).toBe(true)
      expect(MapH3.methods.getPercentiles.call({}, { features: [] }, 'value')).toBeNull()
    })

    it('escapes popup values and handles degenerate ranges', () => {
      expect(MapH3.methods.escapeHtml('<img onerror="x">')).toBe('&lt;img onerror=&quot;x&quot;&gt;')
      expect(MapH3.methods.highlightStyle(5, 5, 5, 5)).toEqual({ left: '0%', width: '100%' })
    })
  })
})
