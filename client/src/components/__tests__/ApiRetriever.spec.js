import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import ApiRetriever from '../ApiRetriever.vue'
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

describe('ApiRetriever', () => {
  it('searches services after selecting table and typing service name', async () => {
    let serviceCalls = 0
    server.use(
      http.get('http://localhost:8000/database/getTableSchema', () => {
        return HttpResponse.json({ id: 'INTEGER' }, { status: 200 })
      }),
      http.get('http://localhost:8000/apiRetriever/getServices', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('serviceName') === 'pet') {
          serviceCalls += 1
        }
        return HttpResponse.json(['petstore'], { status: 200 })
      })
    )

    const wrapper = mount(ApiRetriever, {
      props: { tables: ['iris'] },
      global: {
        stubs: {
          TableInspector: { template: '<div />' }
        }
      }
    })

    await wrapper.find('select#tableSelector').setValue('iris')
    await flushPromises()

    await wrapper.find('input#apiServiceName').setValue('pet')
    await wrapper.find('input#apiServiceName').trigger('input')
    await flushPromises()

    expect(serviceCalls).toBeGreaterThanOrEqual(1)
    expect(wrapper.text()).toContain('petstore')
  })

  it('runs enrichment and emits tableCreated', async () => {
    let enrichmentCalls = 0
    server.use(
      http.get('http://localhost:8000/database/getTableSchema', () => {
        return HttpResponse.json({ id: 'INTEGER' }, { status: 200 })
      }),
      http.post('http://localhost:8000/apiRetriever/runApiEnrichment', async ({ request }) => {
        const body = await request.json()
        if (body.tableName === 'iris' && body.newTableName === 'iris_enriched' && body.recordsToProcess === 10) {
          enrichmentCalls += 1
        }
        return HttpResponse.json({ ok: true }, { status: 200 })
      })
    )

    const wrapper = mount(ApiRetriever, {
      props: { tables: ['iris'] },
      global: {
        stubs: {
          TableInspector: { template: '<div />' }
        }
      }
    })

    await wrapper.find('select#tableSelector').setValue('iris')
    await flushPromises()

    await wrapper.find('input[placeholder="enrichedTable"]').setValue('iris_enriched')
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().trim() === 'Run').trigger('click')
    await flushPromises()

    expect(enrichmentCalls).toBe(1)
    expect(wrapper.emitted('tableCreated')).toBeTruthy()
  })
})
