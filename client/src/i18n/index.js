// App translations. Each component has its own file per language in ./locales/<lang>/<Component>.json,
// and its texts are under that name: t('LoadDataPanel.title'). common.json holds the shared ones.
import { createI18n } from 'vue-i18n';

export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Español' },
];
const STORAGE_KEY = 'locale';

const files = import.meta.glob('./locales/*/*.json', { eager: true });
const messages = {};
for (const [file, module] of Object.entries(files)) {
  const [, lang, name] = file.match(/\.\/locales\/(\w+)\/(\w+)\.json$/);
  messages[lang] = messages[lang] || {};
  messages[lang][name] = module.default;
}

function initialLocale() {
  let saved = null;
  try {
    saved = localStorage.getItem(STORAGE_KEY);
  } catch { /* storage blocked */ }
  if (LANGUAGES.some((l) => l.code === saved)) {
    return saved;
  }
  return (navigator.language || 'en').toLowerCase().startsWith('es') ? 'es' : 'en';
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: initialLocale(),
  fallbackLocale: 'en',
  messages,
});
// The data tests run in Node, without a document
if (typeof document !== 'undefined') {
  document.documentElement.lang = i18n.global.locale.value;
}

export function setLocale(code) {
  i18n.global.locale.value = code;
  if (typeof document !== 'undefined') {
    document.documentElement.lang = code;
  }
  try {
    localStorage.setItem(STORAGE_KEY, code);
  } catch { /* storage blocked */ }
}

// The language the assistant answers, speaks and listens in
export function currentLanguage() {
  return i18n.global.locale.value;
}
