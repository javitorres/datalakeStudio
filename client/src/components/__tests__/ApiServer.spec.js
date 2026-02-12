import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import ApiServer from '../ApiServer.vue'
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

describe('ApiServer', () => {
  it('loads endpoint details from backend when clicking Edit', async () => {
    let getEndpointCalls = 0
    server.use(
      http.get('http://localhost:8000/apiserver/listEndpoints', () => {
        return HttpResponse.json([{
          id_endpoint: 2,
          id_query: 11,
          endpoint: 'carsByBrand',
          description: 'From list',
          query: 'SELECT 1',
          parameters: '[]',
          queryStringTest: '?brand=FORD',
          status: 'DEV'
        }], { status: 200 })
      }),
      http.get('http://localhost:8000/apiserver/getEndpoint', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('id_endpoint') === '2') {
          getEndpointCalls += 1
        }
        return HttpResponse.json({
          id_endpoint: 2,
          id_query: 11,
          endpoint: 'carsByBrand',
          description: 'Loaded from backend',
          query: 'SELECT * FROM cars WHERE brand = {brand}',
          parameters: '[{"name":"brand","exampleValue":"FORD"}]',
          queryStringTest: '?brand=FORD',
          status: 'DEV'
        }, { status: 200 })
      })
    )

    const wrapper = mount(ApiServer)

    await flushPromises()

    const editButton = wrapper.findAll('button').find((b) => b.text() === 'Edit')
    expect(editButton).toBeTruthy()

    await editButton.trigger('click')
    await flushPromises()

    expect(getEndpointCalls).toBe(1)

    const description = wrapper.find('input[placeholder="Description"]')
    expect(description.exists()).toBe(true)
    expect(description.element.value).toBe('Loaded from backend')
    expect(wrapper.text()).toContain('URL: http://localhost:8000/api/carsByBrand')
  })

  it('falls back to list data when getEndpoint returns 404', async () => {
    server.use(
      http.get('http://localhost:8000/apiserver/listEndpoints', () => {
        return HttpResponse.json([{
          id_endpoint: 2,
          id_query: 11,
          endpoint: 'carsByBrand',
          description: 'From list',
          query: 'SELECT 1',
          parameters: '[]',
          queryStringTest: '?brand=FORD',
          status: 'DEV'
        }], { status: 200 })
      }),
      http.get('http://localhost:8000/apiserver/getEndpoint', () => {
        return HttpResponse.json({ message: 'not found' }, { status: 404 })
      })
    )

    const wrapper = mount(ApiServer)
    await flushPromises()

    const editButton = wrapper.findAll('button').find((b) => b.text() === 'Edit')
    await editButton.trigger('click')
    await flushPromises()

    const description = wrapper.find('input[placeholder="Description"]')
    expect(description.exists()).toBe(true)
    expect(description.element.value).toBe('From list')
  })

  it('deletes endpoint and reloads list', async () => {
    let deleteCalls = 0
    let listCalls = 0
    server.use(
      http.get('http://localhost:8000/apiserver/listEndpoints', () => {
        listCalls += 1
        return HttpResponse.json([{
          id_endpoint: 2,
          id_query: 11,
          endpoint: 'carsByBrand',
          description: 'From list',
          query: 'SELECT 1',
          parameters: '[]',
          queryStringTest: '?brand=FORD',
          status: 'DEV'
        }], { status: 200 })
      }),
      http.get('http://localhost:8000/apiserver/deleteEndpoint', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('id_endpoint') === '2') {
          deleteCalls += 1
        }
        return HttpResponse.json({ ok: true }, { status: 200 })
      })
    )

    const wrapper = mount(ApiServer)
    await flushPromises()

    const deleteButton = wrapper.findAll('button').find((b) => b.text() === 'Delete')
    expect(deleteButton).toBeTruthy()

    await deleteButton.trigger('click')
    await flushPromises()

    expect(deleteCalls).toBe(1)
    expect(listCalls).toBeGreaterThanOrEqual(2)
  })

  it('saves and tests endpoint from edit form', async () => {
    let updateCalls = 0
    let testCalls = 0
    server.use(
      http.get('http://localhost:8000/apiserver/listEndpoints', () => {
        return HttpResponse.json([{
          id_endpoint: 2,
          id_query: 11,
          endpoint: 'carsByBrand',
          description: 'From list',
          query: 'SELECT 1',
          parameters: '[]',
          queryStringTest: '?brand=FORD',
          status: 'DEV'
        }], { status: 200 })
      }),
      http.get('http://localhost:8000/apiserver/getEndpoint', () => {
        return HttpResponse.json({
          id_endpoint: 2,
          id_query: 11,
          endpoint: 'carsByBrand',
          description: 'Loaded from backend',
          query: 'SELECT * FROM cars WHERE brand = {brand}',
          parameters: '[{"name":"brand","exampleValue":"FORD"}]',
          queryStringTest: '?brand=FORD',
          status: 'DEV'
        }, { status: 200 })
      }),
      http.post('http://localhost:8000/apiserver/update', async ({ request }) => {
        const body = await request.json()
        if (body.id_query === 11 && body.id_endpoint === 2 && body.endpoint === 'carsByBrand') {
          updateCalls += 1
        }
        return HttpResponse.json({ ok: true }, { status: 200 })
      }),
      http.get('http://localhost:8000/api/carsByBrand', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('brand') === 'FORD') {
          testCalls += 1
        }
        return HttpResponse.json([{ brand: 'FORD' }], { status: 200 })
      })
    )

    const wrapper = mount(ApiServer)
    await flushPromises()

    const editButton = wrapper.findAll('button').find((b) => b.text() === 'Edit')
    await editButton.trigger('click')
    await flushPromises()

    const testButton = wrapper.findAll('button').find((b) => b.text().includes('Save and Test endpoint'))
    await testButton.trigger('click')
    await flushPromises()

    expect(updateCalls).toBe(1)
    expect(testCalls).toBe(1)
    expect(wrapper.find('textarea').element.value).toContain('"brand": "FORD"')
  })
})
