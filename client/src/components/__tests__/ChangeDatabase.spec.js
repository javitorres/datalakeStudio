import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import { toast } from 'vue3-toastify'
import ChangeDatabase from '../ChangeDatabase.vue'
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

describe('ChangeDatabase', () => {
  beforeEach(() => {
    toast.error.mockReset()
    toast.success.mockReset()
  })

  it('loads database list on mount and renders options', async () => {
    server.use(
      http.get('http://localhost:8000/database/getDatabaseList', () => {
        return HttpResponse.json(['main.db', 'analytics.db'])
      })
    )

    const wrapper = mount(ChangeDatabase)
    await flushPromises()

    expect(wrapper.text()).toContain('MAIN.DB')
    expect(wrapper.text()).toContain('ANALYTICS.DB')
  })

  it('changes database and emits changedDatabase event', async () => {
    let changeCalls = 0
    server.use(
      http.get('http://localhost:8000/database/getDatabaseList', () => {
        return HttpResponse.json(['main.db'])
      }),
      http.get('http://localhost:8000/database/changeDatabase', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('databaseName') === 'main.db') {
          changeCalls += 1
        }
        return HttpResponse.json({ ok: true })
      })
    )

    const wrapper = mount(ChangeDatabase)
    await flushPromises()

    const button = wrapper.findAll('button').find((b) => b.text().includes('MAIN.DB'))
    await button.trigger('click')
    await flushPromises()

    expect(changeCalls).toBe(1)
    expect(wrapper.emitted('changedDatabase')).toBeTruthy()
    expect(wrapper.emitted('changedDatabase')[0]).toEqual(['main.db'])
  })

  it('shows validation error and avoids request when creating database without .db suffix', async () => {
    let createCalls = 0
    server.use(
      http.get('http://localhost:8000/database/getDatabaseList', () => {
        return HttpResponse.json(['main.db'])
      }),
      http.get('http://localhost:8000/database/createDatabase', () => {
        createCalls += 1
        return HttpResponse.json({ ok: true })
      })
    )

    const wrapper = mount(ChangeDatabase)
    await flushPromises()

    const input = wrapper.find('input[placeholder="Database name"]')
    await input.setValue('invalidName')
    await flushPromises()

    const createButton = wrapper.findAll('button').find((b) => b.text().includes('Create new database'))
    await createButton.trigger('click')
    await flushPromises()

    expect(toast.error).toHaveBeenCalledWith('Database name must end with .db')
    expect(createCalls).toBe(0)
  })
})
