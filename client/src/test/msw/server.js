import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

// Requests every mounted app makes (tests override them with server.use)
const defaults = [
  http.get('http://localhost:8000/settings/preferences', () => HttpResponse.json({})),
  http.patch('http://localhost:8000/settings/preferences', () => HttpResponse.json({})),
]

export const server = setupServer(...defaults)
