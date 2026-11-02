import { flushPromises, mount } from '@vue/test-utils'
import DatalakeStudio from '../DatalakeStudio.vue'
import { setEngine } from '../../engine'
import { fakeEngine, showTables } from '../../test/fakeEngine'

vi.mock('vue3-toastify', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
    POSITION: { BOTTOM_RIGHT: 'bottom-right' },
    promise: (p) => p
  }
}))

function useTablesEngine() {
  const engine = fakeEngine({ query: () => showTables(['iris', 'cars']) })
  setEngine(engine)
  return engine
}

function tablesListed(engine) {
  return engine.calls.query.filter((sql) => sql === 'SHOW TABLES').length
}

describe('DatalakeStudio', () => {
  it('loads tables on mount and switches to ChangeDatabase from menu', async () => {
    const engine = useTablesEngine()

    const wrapper = mount(DatalakeStudio, {
      global: {
        stubs: {
          Welcome: { template: '<div data-test="welcome">Welcome</div>' },
          ChangeDatabase: { template: '<div data-test="change-db">Change DB</div>' },
          LoadDataPanel: true,
          RemoteDbPanel: true,
          TablesPanel: true,
          QueryPanel: true,
          ApiRetriever: true,
          ApiServer: true,
          ChatGptAgent: true,
          S3Explorer: true
        }
      }
    })

    await flushPromises()

    expect(tablesListed(engine)).toBe(1)
    expect(wrapper.find('[data-test="welcome"]').exists()).toBe(true)

    await wrapper.find('a[title="Change database"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="change-db"]').exists()).toBe(true)
  })

  it('switches to ShowTables and Queries passing current tables as props', async () => {
    useTablesEngine()

    const wrapper = mount(DatalakeStudio, {
      global: {
        stubs: {
          Welcome: { template: '<div data-test="welcome">Welcome</div>' },
          ChangeDatabase: true,
          LoadDataPanel: true,
          RemoteDbPanel: true,
          ApiRetriever: true,
          ApiServer: true,
          ChatGptAgent: true,
          S3Explorer: true,
          TablesPanel: {
            props: ['tables'],
            template: '<div data-test="tables-panel">{{ tables.join(",") }}</div>'
          },
          QueryPanel: {
            props: ['tables'],
            template: '<div data-test="query-panel">{{ tables.join(",") }}</div>'
          }
        }
      }
    })

    await flushPromises()

    await wrapper.find('a[title="Show tables"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-test="tables-panel"]').text()).toContain('iris,cars')

    await wrapper.find('a[title="Queries"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-test="query-panel"]').text()).toContain('iris,cars')
  })

  it('refreshes table list when LoadDataPanel emits tableCreated', async () => {
    const engine = useTablesEngine()

    const wrapper = mount(DatalakeStudio, {
      global: {
        stubs: {
          Welcome: true,
          ChangeDatabase: true,
          RemoteDbPanel: true,
          TablesPanel: true,
          QueryPanel: true,
          ApiRetriever: true,
          ApiServer: true,
          ChatGptAgent: true,
          S3Explorer: true,
          LoadDataPanel: {
            emits: ['tableCreated'],
            template: '<button data-test="emit-created" @click="$emit(\'tableCreated\')">Emit</button>'
          }
        }
      }
    })

    await flushPromises()
    expect(tablesListed(engine)).toBe(1)

    await wrapper.find('a[title="Load data from files"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-test="emit-created"]').trigger('click')
    await flushPromises()

    expect(tablesListed(engine)).toBe(2)
  })

  it('refreshes table list when ChangeDatabase emits changedDatabase', async () => {
    const engine = useTablesEngine()

    const wrapper = mount(DatalakeStudio, {
      global: {
        stubs: {
          Welcome: true,
          LoadDataPanel: true,
          RemoteDbPanel: true,
          TablesPanel: true,
          QueryPanel: true,
          ApiRetriever: true,
          ApiServer: true,
          ChatGptAgent: true,
          S3Explorer: true,
          ChangeDatabase: {
            emits: ['changedDatabase'],
            template: '<button data-test="emit-db" @click="$emit(\'changedDatabase\', \'main.db\')">Emit</button>'
          }
        }
      }
    })

    await flushPromises()
    expect(tablesListed(engine)).toBe(1)

    await wrapper.find('a[title="Change database"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-test="emit-db"]').trigger('click')
    await flushPromises()

    expect(tablesListed(engine)).toBe(2)
  })

  it('drops the table when TablesPanel emits deleteTable and reloads tables', async () => {
    const engine = useTablesEngine()

    const wrapper = mount(DatalakeStudio, {
      global: {
        stubs: {
          Welcome: true,
          ChangeDatabase: true,
          LoadDataPanel: true,
          RemoteDbPanel: true,
          QueryPanel: true,
          ApiRetriever: true,
          ApiServer: true,
          ChatGptAgent: true,
          S3Explorer: true,
          TablesPanel: {
            emits: ['deleteTable'],
            template: '<button data-test="emit-delete" @click="$emit(\'deleteTable\', \'iris\')">Emit</button>'
          }
        }
      }
    })

    await flushPromises()

    await wrapper.find('a[title="Show tables"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-test="emit-delete"]').trigger('click')
    await flushPromises()

    expect(engine.calls.exec).toEqual(['DROP TABLE IF EXISTS "iris"'])
    expect(tablesListed(engine)).toBeGreaterThanOrEqual(2)
  })
})
