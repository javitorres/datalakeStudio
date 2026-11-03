// Preferences set on the Settings page. They are saved on the server for each user, so they follow them to any
// browser; the browser keeps a copy to start with them before the server answers.
import { ref, watch } from 'vue';
import api from '../services/api';
import { i18n, setLocale } from '../i18n';

const VOICE_KEY = 'voiceProvider';

function load(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback;
  } catch {
    return fallback;
  }
}

// "elevenlabs": ElevenLabs when the server has its key, else OpenAI. "openai": always OpenAI.
export const voiceProvider = ref(load(VOICE_KEY, 'elevenlabs'));
// The assistant model, null for the one in the server config
export const aiModel = ref(null);
// The last save failed
export const preferencesError = ref(false);

watch(voiceProvider, (value) => {
  try {
    localStorage.setItem(VOICE_KEY, value);
  } catch { /* storage blocked */ }
});

function current() {
  return { locale: i18n.global.locale.value, voiceProvider: voiceProvider.value, aiModel: aiModel.value };
}

let applying = false;

async function save(changes) {
  if (applying) {
    return;
  }
  try {
    await api.patch('/settings/preferences', changes);
    preferencesError.value = false;
  } catch {
    preferencesError.value = true;
  }
}

// Synchronous, so that loadPreferences can tell its own changes apart
watch(() => i18n.global.locale.value, (locale) => save({ locale }), { flush: 'sync' });
watch(voiceProvider, (value) => save({ voiceProvider: value }), { flush: 'sync' });
watch(aiModel, (value) => save({ aiModel: value }), { flush: 'sync' });

// After login: the user's saved preferences win; the ones they never saved are taken from this browser
export async function loadPreferences() {
  let saved;
  try {
    saved = (await api.get('/settings/preferences')).data;
  } catch {
    return;
  }
  applying = true;
  if (saved.locale) {
    setLocale(saved.locale);
  }
  if (saved.voiceProvider) {
    voiceProvider.value = saved.voiceProvider;
  }
  if ('aiModel' in saved) {
    aiModel.value = saved.aiModel;
  }
  applying = false;
  const missing = Object.fromEntries(Object.entries(current()).filter(([key]) => !(key in saved) && key !== 'aiModel'));
  if (Object.keys(missing).length) {
    await save(missing);
  }
}
