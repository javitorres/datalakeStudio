import api from '../services/api';
import { useEngine } from '../engine';
import { getDatabaseSchema } from '../data/tables';
import { cleanSql, DATA_SYSTEM_PROMPT, SQL_SYSTEM_PROMPT, sqlQuestion } from './prompts';

// The AI assistant. With the backend it uses the server's OpenAI key (/gpt/*). In the browser it calls
// OpenAI directly with the user's own key, which is kept only in this browser.

const KEY_STORAGE = 'datalakeStudio.openaiKey';
const MODEL_STORAGE = 'datalakeStudio.openaiModel';
export const DEFAULT_MODEL = 'gpt-5-mini';
const OPENAI = 'https://api.openai.com/v1';

export function usesOwnKey() {
  return !useEngine().capabilities.serverAi;
}

export function getAiSettings() {
  try {
    return { key: localStorage.getItem(KEY_STORAGE) || '', model: localStorage.getItem(MODEL_STORAGE) || DEFAULT_MODEL };
  } catch (_) {
    return { key: '', model: DEFAULT_MODEL };
  }
}

export function saveAiSettings({ key, model }) {
  localStorage.setItem(KEY_STORAGE, key.trim());
  localStorage.setItem(MODEL_STORAGE, (model || DEFAULT_MODEL).trim());
}

export function forgetAiKey() {
  localStorage.removeItem(KEY_STORAGE);
}

// Whether the assistant can answer now (in the browser it needs the user's key)
export function aiReady() {
  return !usesOwnKey() || Boolean(getAiSettings().key);
}

// SQL for a question about the tables of the active database
export async function askSql(question) {
  if (!usesOwnKey()) {
    const response = await serverCall(() => api.get('/gpt/askGPT', { params: { question } }));
    return response.data;
  }
  const schema = await getDatabaseSchema(useEngine());
  return cleanSql(await chat(SQL_SYSTEM_PROMPT, sqlQuestion(schema, question)));
}

// A plain answer to a question that carries its own data (the chat's explanation of a result)
export async function answer(question) {
  if (!usesOwnKey()) {
    const response = await serverCall(() => api.get('/gpt/genericQuestion', { params: { question } }));
    return response.data.answer;
  }
  return chat(DATA_SYSTEM_PROMPT, question);
}

// The text spoken in a WAV recording ('' when the recording is silent)
export async function transcribe(wav) {
  let text;
  if (!usesOwnKey()) {
    const form = new FormData();
    form.append('file', wav, 'audio.wav');
    const response = await serverCall(() => api.post('/gpt/askGPTWhisper', form, { headers: { 'Content-Type': 'multipart/form-data' } }));
    text = response.data.transcription;
  } else {
    const form = new FormData();
    form.append('file', wav, 'audio.wav');
    form.append('model', 'whisper-1');
    form.append('response_format', 'text');
    text = (await (await openai('/audio/transcriptions', { body: form })).text()).replace(/\n/g, '').trim();
  }
  // Whisper hears "you" in an empty recording
  return text === 'EMPTY_AUDIO' || text === 'you' ? '' : text;
}

// The text read aloud, as an audio Blob
export async function speak(text) {
  if (!usesOwnKey()) {
    const response = await serverCall(() => api.get('/gpt/text2speech', { params: { text }, responseType: 'blob' }));
    return response.data;
  }
  const input = text.length > 200 ? text.slice(0, 200) + '...' : text;
  const response = await openai('/audio/speech', {
    json: { model: 'tts-1', voice: 'alloy', input },
  });
  return response.blob();
}

async function chat(system, user) {
  const { model } = getAiSettings();
  const response = await openai('/chat/completions', {
    json: { model, messages: [{ role: 'system', content: system }, { role: 'user', content: user, name: 'DatalakeStudio' }] },
  });
  return (await response.json()).choices[0].message.content;
}

async function openai(path, { json, body }) {
  const { key } = getAiSettings();
  if (!key) throw new Error('Add your OpenAI API key to use the assistant');
  let response;
  try {
    response = await fetch(OPENAI + path, {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, ...(json ? { 'Content-Type': 'application/json' } : {}) },
      body: json ? JSON.stringify(json) : body,
    });
  } catch (_) {
    // OpenAI's error responses (a wrong key, for one) have no CORS headers: the browser only sees a failed request
    throw new Error("OpenAI couldn't be reached or rejected the request: check your API key and the model name");
  }
  if (!response.ok) {
    let message = `OpenAI answered ${response.status}`;
    try {
      message = (await response.json()).error?.message || message;
    } catch (_) { /* not JSON */ }
    throw new Error(message);
  }
  return response;
}

async function serverCall(request) {
  try {
    return await request();
  } catch (error) {
    const data = error.response?.data;
    throw new Error(data?.message || data?.detail || (typeof data === 'string' && data) || error.message);
  }
}
