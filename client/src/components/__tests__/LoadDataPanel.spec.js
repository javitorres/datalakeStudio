import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import LoadDataPanel from '../LoadDataPanel.vue'
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

describe('LoadDataPanel', () => {
  it('searches S3 and lets user pick a suggested file', async () => {
    let searchCalls = 0
    server.use(
      http.get('http://localhost:8000/s3/s3Search', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('bucket') === 'bucket' && url.searchParams.get('fileName') === 'path') {
          searchCalls += 1
        }
        return HttpResponse.json({ results: ['s3://bucket/path.csv'] })
      })
    )

    const wrapper = mount(LoadDataPanel)

    await wrapper.findAll('a').find((a) => a.text().includes('Load from S3')).trigger('click')

    const [bucketInput, fileInput] = wrapper.findAll('input').filter((i) => i.attributes('id') === 'bucket' || i.attributes('id') === 'fileInput')
    await bucketInput.setValue('bucket')
    await fileInput.setValue('path')
    await fileInput.trigger('input')
    await flushPromises()

    expect(searchCalls).toBeGreaterThanOrEqual(1)

    const suggestion = wrapper.findAll('button').find((b) => b.text().includes('s3://bucket/path.csv'))
    expect(suggestion).toBeTruthy()

    await suggestion.trigger('click')
    await flushPromises()

    expect(wrapper.find('input#fileInput').element.value).toBe('s3://bucket/path.csv')
  })

  it('does not call S3 search for inputs shorter than 3 chars', async () => {
    let searchCalls = 0
    server.use(
      http.get('http://localhost:8000/s3/s3Search', () => {
        searchCalls += 1
        return HttpResponse.json({ results: [] })
      })
    )

    const wrapper = mount(LoadDataPanel)

    await wrapper.findAll('a').find((a) => a.text().includes('Load from S3')).trigger('click')

    const fileInput = wrapper.find('input#fileInput')
    await fileInput.setValue('ab')
    await fileInput.trigger('input')
    await flushPromises()

    expect(searchCalls).toBe(0)
  })

  it('loads file from URL and emits tableCreated', async () => {
    let loadCalls = 0
    server.use(
      http.get('http://localhost:8000/database/loadFile', ({ request }) => {
        const url = new URL(request.url)
        if (
          url.searchParams.get('tableName') === 'my_table' &&
          url.searchParams.get('fileName') === 'https://example.com/data.csv'
        ) {
          loadCalls += 1
        }
        return HttpResponse.json({ ok: true }, { status: 200 })
      })
    )

    const wrapper = mount(LoadDataPanel)

    await wrapper.findAll('a').find((a) => a.text().includes('Load from URL')).trigger('click')
    await flushPromises()

    await wrapper.find('input#fileInputUrl').setValue('https://example.com/data.csv')
    await wrapper.find('input#tableNameInputUrl').setValue('my_table')
    await flushPromises()

    const loadButton = wrapper.findAll('button').find((b) => b.text().includes('Load file'))
    await loadButton.trigger('click')
    await flushPromises()

    expect(loadCalls).toBe(1)
    expect(wrapper.emitted('tableCreated')).toBeTruthy()
  })
})
