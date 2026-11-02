<template>
  <div class="ai-key compact-card">
    <template v-if="!editing && settings.key">
      <span><i class="bi bi-key"></i> Using your OpenAI key <code>{{ maskedKey }}</code> · {{ settings.model }}</span>
      <button class="btn btn-sm btn-link" @click="editing = true">Change</button>
      <button class="btn btn-sm btn-link text-danger" @click="forget">Forget key</button>
    </template>
    <form v-else @submit.prevent="save">
      <p class="mb-2">
        <b><i class="bi bi-key"></i> Use your own OpenAI API key</b><br>
        It's kept only in this browser and sent only to OpenAI. To answer, the assistant sends OpenAI your question and
        the names and types of your tables' columns{{ sendsRows ? ', and the first rows of each query result to explain it' : '' }}.
        Your tables themselves never leave this browser.
      </p>
      <div class="input-group input-group-sm mb-2">
        <span class="input-group-text">API key</span>
        <input v-model="key" type="password" class="form-control" placeholder="sk-..." autocomplete="off" spellcheck="false">
      </div>
      <div class="input-group input-group-sm mb-2">
        <span class="input-group-text">Model</span>
        <input v-model="model" type="text" class="form-control" :placeholder="DEFAULT_MODEL">
      </div>
      <button class="btn btn-sm btn-primary" type="submit" :disabled="!key.trim()">Save in this browser</button>
      <button v-if="settings.key" class="btn btn-sm btn-link" type="button" @click="editing = false">Cancel</button>
      <a class="btn btn-sm btn-link" href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">Get a key <i class="bi bi-box-arrow-up-right"></i></a>
    </form>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { DEFAULT_MODEL, forgetAiKey, getAiSettings, saveAiSettings } from '../ai';

defineProps({
  // The chat also sends query results to OpenAI
  sendsRows: { type: Boolean, default: false },
});
const emit = defineEmits(['change']);

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
