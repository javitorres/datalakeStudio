<template>
  <div class="compact-panel settings-view">
    <h2 class="compact-title">{{ t('SettingsPanel.language') }}</h2>
    <p class="compact-muted mb-2">{{ t('SettingsPanel.languageHelp') }}</p>
    <div class="settings-options" role="radiogroup" :aria-label="t('SettingsPanel.language')">
      <button
        v-for="lang in LANGUAGES"
        :key="lang.code"
        type="button"
        class="btn settings-option"
        :class="{ 'settings-option-active': locale === lang.code }"
        role="radio"
        :aria-checked="locale === lang.code"
        @click="setLocale(lang.code)"
      >
        {{ lang.label }}
      </button>
    </div>

    <h2 class="compact-title mt-4">{{ t('SettingsPanel.model') }}</h2>
    <p class="compact-muted mb-2">{{ t('SettingsPanel.modelHelp') }}</p>
    <select
      id="aiModelSelect"
      class="form-select settings-model"
      :value="aiModel || ''"
      :disabled="!models"
      :aria-label="t('SettingsPanel.model')"
      @change="aiModel = $event.target.value || null"
    >
      <option value="">{{ t('SettingsPanel.modelDefault', { model: models?.configured || '…' }) }}</option>
      <option v-for="model in modelChoices" :key="model" :value="model">{{ model }}</option>
    </select>
    <p v-if="models?.error" class="compact-muted mb-0">{{ t('SettingsPanel.modelsError', { detail: models.error }) }}</p>

    <h2 class="compact-title mt-4">{{ t('SettingsPanel.voice') }}</h2>
    <p class="compact-muted mb-2">{{ t('SettingsPanel.voiceHelp') }}</p>
    <div class="form-check form-switch">
      <input
        id="elevenLabsSwitch"
        class="form-check-input"
        type="checkbox"
        role="switch"
        :disabled="!elevenLabsConfigured"
        :checked="elevenLabsConfigured && voiceProvider === 'elevenlabs'"
        @change="voiceProvider = $event.target.checked ? 'elevenlabs' : 'openai'"
      >
      <label class="form-check-label" for="elevenLabsSwitch">{{ t('SettingsPanel.useElevenLabs') }}</label>
    </div>
    <p v-if="status && !elevenLabsConfigured" class="compact-muted mb-0">{{ t('SettingsPanel.elevenLabsMissing') }}</p>
    <p class="compact-muted mt-3 mb-0" :class="{ 'text-danger': preferencesError }">
      <i :class="preferencesError ? 'bi bi-cloud-slash' : 'bi bi-cloud-check'"></i>
      {{ preferencesError ? t('SettingsPanel.saveError') : t('SettingsPanel.savedOnServer') }}
    </p>

    <h2 class="compact-title mt-4">{{ t('SettingsPanel.integrations') }}</h2>
    <p class="compact-muted mb-2">{{ t('SettingsPanel.integrationsHelp') }}</p>
    <p v-if="error" class="text-danger">{{ t('SettingsPanel.statusError') }}</p>
    <div v-if="status" class="settings-files compact-muted mb-2">
      <span v-for="file in ['config', 'secrets']" :key="file">
        <i :class="status.files[file] ? 'bi bi-check-circle-fill text-success' : 'bi bi-x-circle-fill text-danger'"></i>
        {{ file }}.yml {{ status.files[file] ? t('SettingsPanel.read') : t('SettingsPanel.notFound') }}
      </span>
    </div>
    <ul v-if="status" class="settings-list">
      <li v-for="item in status.integrations" :key="item.id" class="settings-item">
        <i
          class="bi settings-item-icon"
          :class="item.configured ? 'bi-check-circle-fill text-success' : 'bi-dash-circle settings-missing'"
        ></i>
        <div class="settings-item-text">
          <span class="settings-item-name">{{ t(`SettingsPanel.services.${item.id}.name`) }}</span>
          <span class="compact-muted">{{ t(`SettingsPanel.services.${item.id}.use`) }}</span>
        </div>
        <span class="settings-item-state" :class="{ 'settings-missing': !item.configured }">
          {{ item.configured
            ? (item.source === 'aws' ? t('SettingsPanel.awsChain') : t('SettingsPanel.configured'))
            : t('SettingsPanel.notDefined') }}
        </span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '../services/api';
import { LANGUAGES, setLocale } from '../i18n';
import { aiModel, preferencesError, voiceProvider } from '../lib/preferences';

const { t, locale } = useI18n();
const status = ref(null);
const error = ref(false);
const models = ref(null);

// The chosen model stays in the list even if the key no longer lists it
const modelChoices = computed(() => {
  const list = models.value?.models || [];
  return aiModel.value && !list.includes(aiModel.value) ? [aiModel.value, ...list] : list;
});

const elevenLabsConfigured = computed(
  () => !!status.value?.integrations.find((i) => i.id === 'elevenlabs')?.configured
);

onMounted(async () => {
  api.get('/settings/models')
    .then((response) => { models.value = response.data; })
    .catch(() => { models.value = { configured: null, models: [], error: t('SettingsPanel.unknownError') }; });
  try {
    status.value = (await api.get('/settings/status')).data;
  } catch {
    error.value = true;
  }
});
</script>

<style scoped>
.settings-options { display:flex; gap:8px; }
.settings-option { min-width:120px; border:1px solid var(--ds-line); background:#fff; font-size:12px; font-weight:600; }
.settings-option-active { border-color:var(--ds-teal); color:var(--ds-teal-dark); background:#e4f4ef; }
.settings-model { max-width:360px; font-size:13px; }
.settings-files { display:flex; gap:18px; }
.settings-list { list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:8px; }
.settings-item { display:flex; align-items:center; gap:10px; padding:10px 12px; border:1px solid var(--ds-line); border-radius:10px; background:#fff; }
.settings-item-icon { font-size:18px; }
.settings-item-text { display:flex; flex-direction:column; flex:1; min-width:0; }
.settings-item-name { font-size:12.5px; font-weight:650; color:var(--ds-ink); }
.settings-item-state { font-size:11px; font-weight:600; color:var(--ds-teal-dark); white-space:nowrap; }
.settings-missing { color:var(--ds-muted); }
</style>
