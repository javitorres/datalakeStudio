import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import DatalakeStudio from '../DatalakeStudio.vue'
import { server } from '../../test/msw/server'

vi.mock('vue3-toastify', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
    POSITION: { BOTTOM_RIGHT: 'bottom-right' },
    promise: (p) => p
  }
}))

describe('DatalakeStudio', () => {
  it('loads tables on mount and switches to ChangeDatabase from menu', async () => {
    let getTablesCalls = 0
    server.use(
      http.get('http://localhost:8000/database/getTables', () => {
        getTablesCalls += 1
        return HttpResponse.json(['iris', 'cars'])
      })
    )

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

    expect(getTablesCalls).toBe(1)
    expect(wrapper.find('[data-test="welcome"]').exists()).toBe(true)

    await wrapper.find('a[title="Change database"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="change-db"]').exists()).toBe(true)
  })

  it('switches to ShowTables and Queries passing current tables as props', async () => {
    server.use(
      http.get('http://localhost:8000/database/getTables', () => {
        return HttpResponse.json(['iris', 'cars'])
      })
    )

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
    let getTablesCalls = 0
    server.use(
      http.get('http://localhost:8000/database/getTables', () => {
        getTablesCalls += 1
        return HttpResponse.json(['iris', 'cars'])
      })
    )

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
    expect(getTablesCalls).toBe(1)

    await wrapper.find('a[title="Load data from files"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-test="emit-created"]').trigger('click')
    await flushPromises()

    expect(getTablesCalls).toBe(2)
  })

  it('refreshes table list when ChangeDatabase emits changedDatabase', async () => {
    let getTablesCalls = 0
    server.use(
      http.get('http://localhost:8000/database/getTables', () => {
        getTablesCalls += 1
        return HttpResponse.json(['iris', 'cars'])
      })
    )

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
    expect(getTablesCalls).toBe(1)

    await wrapper.find('a[title="Change database"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-test="emit-db"]').trigger('click')
    await flushPromises()

    expect(getTablesCalls).toBe(2)
  })

  it('calls delete endpoint when TablesPanel emits deleteTable and reloads tables', async () => {
    let getTablesCalls = 0
    let deleteCalls = 0
    server.use(
      http.get('http://localhost:8000/database/getTables', () => {
        getTablesCalls += 1
        return HttpResponse.json(['iris', 'cars'])
      }),
      http.get('http://localhost:8000/database/deleteTable', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('tableName') === 'iris') {
          deleteCalls += 1
        }
        return HttpResponse.json({ ok: true }, { status: 200 })
      })
    )

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

    expect(deleteCalls).toBe(1)
    expect(getTablesCalls).toBeGreaterThanOrEqual(2)
  })
})
