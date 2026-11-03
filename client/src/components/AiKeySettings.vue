<template>
  <div class="ai-key compact-card">
    <template v-if="!editing && settings.key">
      <span><i class="bi bi-key"></i> {{ t('AiKeySettings.using') }} <code>{{ maskedKey }}</code> · {{ settings.model }}</span>
      <button class="btn btn-sm btn-link" @click="editing = true">{{ t('AiKeySettings.change') }}</button>
      <button class="btn btn-sm btn-link text-danger" @click="forget">{{ t('AiKeySettings.forget') }}</button>
    </template>
    <form v-else @submit.prevent="save">
      <p class="mb-2">
        <b><i class="bi bi-key"></i> {{ t('AiKeySettings.title') }}</b><br>
        {{ sendsRows ? t('AiKeySettings.privacyWithRows') : t('AiKeySettings.privacy') }}
      </p>
      <div class="input-group input-group-sm mb-2">
        <span class="input-group-text">{{ t('AiKeySettings.key') }}</span>
        <input v-model="key" type="password" class="form-control" placeholder="sk-..." autocomplete="off" spellcheck="false">
      </div>
      <div class="input-group input-group-sm mb-2">
        <span class="input-group-text">{{ t('AiKeySettings.model') }}</span>
        <input v-model="model" type="text" class="form-control" :placeholder="DEFAULT_MODEL">
      </div>
      <button class="btn btn-sm btn-primary" type="submit" :disabled="!key.trim()">{{ t('AiKeySettings.save') }}</button>
      <button v-if="settings.key" class="btn btn-sm btn-link" type="button" @click="editing = false">{{ t('AiKeySettings.cancel') }}</button>
      <a class="btn btn-sm btn-link" href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">{{ t('AiKeySettings.getKey') }} <i class="bi bi-box-arrow-up-right"></i></a>
    </form>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { DEFAULT_MODEL, forgetAiKey, getAiSettings, saveAiSettings } from '../ai';

defineProps({
  // The chat also sends query results to OpenAI
  sendsRows: { type: Boolean, default: false },
});
const emit = defineEmits(['change']);
const { t } = useI18n();

const settings = ref(getAiSettings());
const editing = ref(!settings.value.key);
const key = ref('');
const model = ref(settings.value.model);
const maskedKey = computed(() => settings.value.key.slice(0, 3) + '…' + settings.value.key.slice(-4));

function save() {
  saveAiSettings({ key: key.value, model: model.value });
  settings.value = getAiSettings();
  key.value = '';
  editing.value = false;
  emit('change');
}

function forget() {
  forgetAiKey();
  settings.value = getAiSettings();
  editing.value = true;
  emit('change');
}
</script>

<style scoped>
.ai-key { margin-bottom: 10px; padding: 10px 12px; font-size: 12px; }
.ai-key > span { margin-right: 6px; }
.ai-key p { color: #5f6b68; font-size: 11.5px; line-height: 1.5; }
.ai-key code { font-size: 11px; }
</style>
