import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import QueryPanel from '../QueryPanel.vue'
import { server } from '../../test/msw/server'

vi.mock('vue-codemirror', () => ({
  Codemirror: {
    name: 'Codemirror',
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

describe('QueryPanel', () => {
  it('runs the main query against backend', async () => {
    let runQueryCalls = 0
    server.use(
      http.post('http://localhost:8000/database/runQuery', async ({ request }) => {
        const body = await request.json()
        if (body.query === 'SELECT * FROM iris') {
          runQueryCalls += 1
        }
        return HttpResponse.json([{ id: 1 }], { status: 200 })
      })
    )

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

    expect(runQueryCalls).toBe(1)
    expect(wrapper.find('[data-test="table-inspector"]').exists()).toBe(true)
  })

  it('creates table from query and emits tableCreated', async () => {
    let runQueryCalls = 0
    let createTableCalls = 0
    server.use(
      http.post('http://localhost:8000/database/runQuery', async ({ request }) => {
        const body = await request.json()
        if (body.query === 'SELECT * FROM iris') {
          runQueryCalls += 1
        }
        return HttpResponse.json([{ id: 1 }], { status: 200 })
      }),
      http.get('http://localhost:8000/database/createTableFromQuery', ({ request }) => {
        const url = new URL(request.url)
        if (
          url.searchParams.get('query') === 'SELECT * FROM iris' &&
          url.searchParams.get('tableName') === 'iris_copy'
        ) {
          createTableCalls += 1
        }
        return HttpResponse.json({ ok: true }, { status: 200 })
      })
    )

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

    expect(runQueryCalls).toBe(1)
    expect(createTableCalls).toBe(1)
    expect(wrapper.emitted('tableCreated')).toBeTruthy()
  })
})
