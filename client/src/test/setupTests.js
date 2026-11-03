import { afterAll, afterEach, beforeAll } from 'vitest'
import { config } from '@vue/test-utils'
import { server } from './msw/server'
import { i18n, setLocale } from '../i18n'

// Components use $t / useI18n: tests run in English
setLocale('en')
config.global.plugins = [i18n]

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'bypass' })
})

afterEach(() => {
  server.resetHandlers()
})

afterAll(() => {
  server.close()
})
