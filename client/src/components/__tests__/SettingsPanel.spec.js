import { flushPromises, mount } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import SettingsPanel from '../SettingsPanel.vue'
import { server } from '../../test/msw/server'
import { i18n, setLocale } from '../../i18n'
import { aiModel, loadPreferences, voiceProvider } from '../../lib/preferences'
import { setEngine } from '../../engine'
import { capabilities } from '../../engine/engine'
import { fakeEngine } from '../../test/fakeEngine'

const STATUS = {
  files: { config: true, secrets: true },
  authEnabled: true,
  integrations: [
    { id: 'openai', configured: true, source: null },
    { id: 'elevenlabs', configured: false, source: null },
    { id: 'mapbox', configured: true, source: null },
    { id: 's3', configured: true, source: 'aws' },
  ],
}

const API = 'http://localhost:8000'
const MODELS = { current: 'gpt-5.4-mini', configured: 'gpt-5.4-mini', models: ['gpt-5.4-mini', 'gpt-5.4', 'o3'], error: null }
// What the server saved: the PATCHes, in order
let patches

function serveStatus(status, preferences = {}) {
  server.use(
    http.get(`${API}/settings/status`, () => HttpResponse.json(status)),
    http.get(`${API}/settings/models`, () => HttpResponse.json(MODELS)),
    http.get(`${API}/settings/preferences`, () => HttpResponse.json(preferences)),
    http.patch(`${API}/settings/preferences`, async ({ request }) => {
      patches.push(await request.json())
      return HttpResponse.json({})
    }),
  )
}

describe('SettingsPanel', () => {
  beforeEach(() => {
    patches = []
    setEngine(fakeEngine())
  })

  afterEach(() => {
    aiModel.value = null
    setLocale('en')
    voiceProvider.value = 'elevenlabs'
  })

  it('shows what the server read from its settings', async () => {
    serveStatus(STATUS)

    const wrapper = mount(SettingsPanel)
    await flushPromises()

    const items = wrapper.findAll('.settings-item').map((item) => item.text())
    expect(items[0]).toContain('OpenAI')
    expect(items[0]).toContain('Configured')
    expect(items[1]).toContain('ElevenLabs')
    expect(items[1]).toContain('Not defined')
    expect(items[3]).toContain('AWS credentials')
    expect(wrapper.text()).toContain('secrets.yml read')
  })

  it('disables the ElevenLabs switch when it has no key', async () => {
    serveStatus(STATUS)

    const wrapper = mount(SettingsPanel)
    await flushPromises()

    const toggle = wrapper.find('#elevenLabsSwitch')
    expect(toggle.element.disabled).toBe(true)
    expect(toggle.element.checked).toBe(false)
    expect(wrapper.text()).toContain('elevenlabs_api_key')
  })

  it('switches between ElevenLabs and OpenAI when it is configured', async () => {
    serveStatus({ ...STATUS, integrations: [{ id: 'elevenlabs', configured: true, source: null }] })

    const wrapper = mount(SettingsPanel)
    await flushPromises()
    const toggle = wrapper.find('#elevenLabsSwitch')
    expect(toggle.element.checked).toBe(true)

    await toggle.setValue(false)
    expect(voiceProvider.value).toBe('openai')
    expect(localStorage.getItem('voiceProvider')).toBe('openai')
  })

  it('changes the app language', async () => {
    serveStatus(STATUS)

    const wrapper = mount(SettingsPanel)
    await flushPromises()
    await wrapper.findAll('.settings-option').find((b) => b.text() === 'Español').trigger('click')

    expect(i18n.global.locale.value).toBe('es')
    expect(localStorage.getItem('locale')).toBe('es')
    expect(document.documentElement.lang).toBe('es')
    expect(wrapper.text()).toContain('Integraciones')
    expect(wrapper.text()).toContain('No definido')
  })

  it('chooses the AI model and saves it on the server', async () => {
    serveStatus(STATUS)

    const wrapper = mount(SettingsPanel)
    await flushPromises()
    const select = wrapper.find('#aiModelSelect')
    expect(select.findAll('option').map((o) => o.text())).toEqual(
      ['The one in the config (gpt-5.4-mini)', 'gpt-5.4-mini', 'gpt-5.4', 'o3'])

    await select.setValue('o3')
    await flushPromises()
    expect(aiModel.value).toBe('o3')
    expect(patches).toEqual([{ aiModel: 'o3' }])

    await select.setValue('')
    await flushPromises()
    expect(aiModel.value).toBe(null)
    expect(patches[1]).toEqual({ aiModel: null })
  })

  it('takes the preferences saved on the server, and saves the ones it lacks', async () => {
    serveStatus(STATUS, { locale: 'es', aiModel: 'gpt-5.4' })
    voiceProvider.value = 'openai'
    await flushPromises()
    patches = []

    await loadPreferences()
    await flushPromises()

    expect(i18n.global.locale.value).toBe('es')
    expect(aiModel.value).toBe('gpt-5.4')
    // Only what the server did not have: what it sent is not saved back
    expect(patches).toEqual([{ voiceProvider: 'openai' }])
  })

  it('keeps everything in the browser with DuckDB in the browser', async () => {
    const requests = []
    server.events.on('request:start', ({ request }) => requests.push(request.url))
    setEngine({ ...fakeEngine(), mode: 'local', capabilities: capabilities({ ownAi: true }) })

    const wrapper = mount(SettingsPanel)
    await flushPromises()
    await wrapper.findAll('.settings-option').find((b) => b.text() === 'Español').trigger('click')
    await loadPreferences()
    await flushPromises()
    server.events.removeAllListeners()

    expect(requests).toEqual([])
    expect(wrapper.find('.ai-key').exists()).toBe(true)
    expect(wrapper.find('#aiModelSelect').exists()).toBe(false)
    expect(wrapper.find('#elevenLabsSwitch').exists()).toBe(false)
    expect(wrapper.find('.settings-list').exists()).toBe(false)
    expect(wrapper.text()).toContain('solo en este navegador')
  })
})
