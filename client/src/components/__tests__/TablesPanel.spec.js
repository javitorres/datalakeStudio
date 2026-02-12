import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import TablesPanel from '../TablesPanel.vue'
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

describe('TablesPanel', () => {
  it('emits deleteTable after selecting a table and confirming delete', async () => {
    const wrapper = mount(TablesPanel, {
      props: {
        tables: ['iris', 'cars']
      },
      global: {
        stubs: {
          TableInspector: { template: '<div />' }
        }
      }
    })

    await wrapper.findAll('button').find((b) => b.text().includes('iris')).trigger('click')
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().includes('Delete table')).trigger('click')
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().includes('Yes, delete it')).trigger('click')
    await flushPromises()

    expect(wrapper.emitted('deleteTable')).toBeTruthy()
    expect(wrapper.emitted('deleteTable')[0]).toEqual(['iris'])
  })

  it('downloads selected table in csv format', async () => {
    let exportCalls = 0
    server.use(
      http.get('http://localhost:8000/database/exportData', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('format') === 'csv' && url.searchParams.get('tableName') === 'iris') {
          exportCalls += 1
        }
        return HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, { status: 200 })
      })
    )

    const originalCreateObjectURL = window.URL.createObjectURL
    const originalAnchorClick = HTMLAnchorElement.prototype.click
    window.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
    HTMLAnchorElement.prototype.click = vi.fn()

    const wrapper = mount(TablesPanel, {
      props: {
        tables: ['iris']
      },
      global: {
        stubs: {
          TableInspector: { template: '<div />' }
        }
      }
    })

    await wrapper.findAll('button').find((b) => b.text().includes('iris')).trigger('click')
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().includes('Download data')).trigger('click')
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().trim().endsWith('CSV')).trigger('click')
    await flushPromises()

    expect(exportCalls).toBe(1)
    expect(window.URL.createObjectURL).toHaveBeenCalled()

    HTMLAnchorElement.prototype.click = originalAnchorClick
    window.URL.createObjectURL = originalCreateObjectURL
  })
})
