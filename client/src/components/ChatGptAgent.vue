<template>
  <section class="assistant">
    <!-- Recent conversations, saved on the server -->
    <aside v-if="showHistory" class="assistant-history" :aria-label="t('ChatGptAgent.history.title')">
      <button type="button" class="assistant-new" :disabled="busy" @click="newChat">
        <i class="bi bi-pencil-square"></i>{{ t('ChatGptAgent.newChat') }}
      </button>
      <label class="assistant-history-search">
        <i class="bi bi-search"></i>
        <input v-model="historyFilter" type="search" :placeholder="t('ChatGptAgent.history.search')" :aria-label="t('ChatGptAgent.history.search')">
      </label>

      <nav class="assistant-history-list">
        <p v-if="historyError" class="assistant-history-note text-danger">{{ t('ChatGptAgent.history.loadError') }}</p>
        <p v-else-if="!conversations.length" class="assistant-history-note">{{ t('ChatGptAgent.history.empty') }}</p>
        <p v-else-if="!historyGroups.length" class="assistant-history-note">{{ t('ChatGptAgent.history.noMatch') }}</p>
        <template v-for="group in historyGroups" :key="group.key">
          <h4 class="assistant-history-group">{{ t(`ChatGptAgent.history.groups.${group.key}`) }}</h4>
          <div
            v-for="conversation in group.items"
            :key="conversation.id"
            class="assistant-history-item"
            :class="{ 'is-active': conversation.id === currentId }"
          >
            <input
              v-if="renamingId === conversation.id"
              ref="renameInput"
              v-model="renameDraft"
              class="assistant-history-rename"
              maxlength="200"
              :aria-label="t('ChatGptAgent.history.rename')"
              @keydown.enter.prevent="finishRename(conversation)"
              @keydown.esc.prevent="renamingId = null"
              @blur="finishRename(conversation)"
            >
            <template v-else-if="deletingId === conversation.id">
              <span class="assistant-history-confirm">{{ t('ChatGptAgent.history.confirmDelete') }}</span>
              <button type="button" class="assistant-history-action is-danger" :title="t('ChatGptAgent.history.delete')" @click="removeConversation(conversation)">
                <i class="bi bi-check-lg"></i>
              </button>
              <button type="button" class="assistant-history-action" :title="t('ChatGptAgent.history.cancel')" @click="deletingId = null">
                <i class="bi bi-x-lg"></i>
              </button>
            </template>
            <template v-else>
              <button
                type="button"
                class="assistant-history-open"
                :title="conversation.title"
                :disabled="busy && conversation.id !== currentId"
                @click="openConversation(conversation)"
              >
                {{ conversation.title }}
              </button>
              <span class="assistant-history-actions">
                <button type="button" class="assistant-history-action" :title="t('ChatGptAgent.history.rename')" @click="startRename(conversation)">
                  <i class="bi bi-pencil"></i>
                </button>
                <button
                  type="button"
                  class="assistant-history-action"
                  :title="t('ChatGptAgent.history.delete')"
                  :disabled="busy && conversation.id === currentId"
                  @click="deletingId = conversation.id"
                >
                  <i class="bi bi-trash3"></i>
                </button>
              </span>
            </template>
          </div>
        </template>
      </nav>
      <p v-if="saveError" class="assistant-history-note text-danger"><i class="bi bi-cloud-slash"></i> {{ t('ChatGptAgent.history.saveError') }}</p>
    </aside>

    <div class="assistant-main">
    <header class="assistant-bar">
      <div class="assistant-bar-start">
        <button
          type="button"
          class="assistant-icon-btn assistant-history-toggle"
          :aria-pressed="showHistory"
          :title="t(showHistory ? 'ChatGptAgent.history.hide' : 'ChatGptAgent.history.show')"
          @click="showHistory = !showHistory"
        >
          <i class="bi bi-layout-sidebar"></i>
        </button>
        <p v-if="currentConversation" class="assistant-bar-name">{{ currentConversation.title }}</p>
        <p v-else class="assistant-bar-title">{{ t('ChatGptAgent.subtitle') }}</p>
      </div>
      <div class="assistant-bar-actions">
        <button
          type="button"
          class="assistant-chip"
          :class="{ 'is-on': tts }"
          :aria-pressed="tts"
          :title="t('ChatGptAgent.ttsHelp')"
          @click="tts = !tts"
        >
          <i :class="tts ? 'bi bi-volume-up-fill' : 'bi bi-volume-mute'"></i>
          {{ t('ChatGptAgent.tts') }}
        </button>
        <button
          type="button"
          class="assistant-chip"
          :class="{ 'is-on': blindMode }"
          :aria-pressed="blindMode"
          :title="t('ChatGptAgent.blindModeHelp')"
          @click="blindMode = !blindMode"
        >
          <i :class="blindMode ? 'bi bi-eye-slash-fill' : 'bi bi-eye'"></i>
          {{ t('ChatGptAgent.blindMode') }}
        </button>
        <button
          v-if="!showHistory"
          type="button"
          class="assistant-chip"
          :disabled="!messages.length || busy"
          :title="t('ChatGptAgent.newChat')"
          @click="newChat"
        >
          <i class="bi bi-plus-lg"></i>
          {{ t('ChatGptAgent.newChat') }}
        </button>
      </div>
    </header>

    <!-- DuckDB in the browser: the user's own OpenAI key, and what is sent to OpenAI -->
    <div v-if="ownKey" class="assistant-key">
      <AiKeySettings sends-rows @change="ready = aiReady()" />
    </div>

    <div ref="feed" class="assistant-feed">
      <div class="assistant-column">
        <!-- Blind mode: the conversation is hidden, only what the assistant is doing shows -->
        <div v-if="blindMode" class="assistant-empty">
          <span class="assistant-empty-icon"><i class="bi bi-eye-slash"></i></span>
          <h3>{{ t('ChatGptAgent.blindModeOn') }}</h3>
          <p>{{ t('ChatGptAgent.blindModeHint') }}</p>
        </div>

        <!-- Empty conversation: welcome and suggestions from the user's tables -->
        <div v-else-if="!messages.length" class="assistant-empty">
          <span class="assistant-empty-icon"><i class="bi bi-stars"></i></span>
          <h3>{{ t('ChatGptAgent.emptyTitle') }}</h3>
          <p>{{ t('ChatGptAgent.emptyHint') }}</p>
          <div v-if="suggestions.length" class="assistant-suggestions">
            <button
              v-for="suggestion in suggestions"
              :key="suggestion"
              type="button"
              class="assistant-suggestion"
              :disabled="!ready"
              @click="ask(suggestion)"
            >
              <i class="bi bi-arrow-return-right"></i>{{ suggestion }}
            </button>
          </div>
          <p v-else class="assistant-empty-note">{{ t('ChatGptAgent.noTables') }}</p>
        </div>

        <template v-else>
          <article
            v-for="message in messages"
            :key="message.id"
            class="assistant-message"
            :class="message.role === 'user' ? 'from-user' : 'from-assistant'"
          >
            <div v-if="message.role === 'user'" class="user-bubble">{{ message.text }}</div>

            <template v-else>
              <span class="assistant-avatar small"><i class="bi bi-stars"></i></span>
              <div class="assistant-body">
                <div v-if="message.sql" class="assistant-sql">
                  <div class="assistant-sql-head">
                    <span><i class="bi bi-code-slash"></i> SQL</span>
                    <button type="button" class="assistant-icon-btn" :title="t('ChatGptAgent.copySql')" @click="copySql(message)">
                      <i :class="message.copied ? 'bi bi-check2' : 'bi bi-clipboard'"></i>
                      {{ message.copied ? t('ChatGptAgent.copied') : t('ChatGptAgent.copy') }}
                    </button>
                  </div>
                  <pre><code>{{ message.sql }}</code></pre>
                </div>

                <div v-if="message.chart && message.result" class="assistant-chart">
                  <div class="assistant-chart-head">
                    <span class="assistant-chart-title">{{ message.chart.title }}</span>
                    <div class="assistant-chart-types" role="radiogroup" :aria-label="t('ChatGptAgent.chart.type')">
                      <button
                        v-for="type in CHART_TYPES"
                        :key="type.id"
                        type="button"
                        class="assistant-icon-btn"
                        :class="{ 'is-on': message.chart.type === type.id }"
                        role="radio"
                        :aria-checked="message.chart.type === type.id"
                        :title="t(`ChatGptAgent.chart.types.${type.id}`)"
                        @click="changeChartType(message, type.id)"
                      >
                        <i :class="type.icon"></i>
                      </button>
                    </div>
                  </div>
                  <v-chart class="assistant-chart-canvas" :option="chartOption(message.chart, message.result)" autoresize />
                </div>

                <div v-if="message.result" class="assistant-result">
                  <div class="assistant-result-scroll">
                    <table>
                      <thead>
                        <tr><th v-for="(column, i) in message.result.columns" :key="i">{{ column }}</th></tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, r) in message.result.rows.slice(0, RESULT_ROWS)" :key="r">
                          <td v-for="(cell, c) in row" :key="c">{{ cell }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <p class="assistant-result-foot">
                    {{ resultTotal(message.result) > RESULT_ROWS
                      ? t('ChatGptAgent.rowsShown', { shown: RESULT_ROWS, total: resultTotal(message.result) })
                      : t('ChatGptAgent.rows', resultTotal(message.result)) }}
                  </p>
                </div>

                <!-- eslint-disable-next-line vue/no-v-html -- renderMarkdown escapes the text first -->
                <div v-if="message.text" class="assistant-text" v-html="renderMarkdown(message.text)"></div>

                <p v-if="message.error" class="assistant-error"><i class="bi bi-exclamation-triangle"></i> {{ message.error }}</p>

                <div v-if="message.status" class="assistant-status">
                  <span class="assistant-dots"><i></i><i></i><i></i></span>{{ t(`ChatGptAgent.status.${message.status}`) }}
                </div>

                <div v-if="message.text && !message.status" class="assistant-actions">
                  <button type="button" class="assistant-icon-btn" :title="t('ChatGptAgent.readAloud')" :disabled="message.speaking" @click="speak(message)">
                    <i :class="message.speaking ? 'bi bi-soundwave' : 'bi bi-volume-up'"></i> {{ t('ChatGptAgent.readAloud') }}
                  </button>
                </div>
              </div>
            </template>
          </article>
        </template>

        <div v-if="pendingStatus" class="assistant-message from-assistant">
          <span class="assistant-avatar small"><i class="bi bi-stars"></i></span>
          <div class="assistant-status">
            <span class="assistant-dots"><i></i><i></i><i></i></span>{{ t(`ChatGptAgent.status.${pendingStatus}`) }}
          </div>
        </div>
      </div>
    </div>

    <footer class="assistant-composer-wrap">
      <form class="assistant-composer" @submit.prevent="ask(draft)">
        <textarea
          ref="input"
          v-model="draft"
          rows="1"
          :placeholder="ready ? t('ChatGptAgent.placeholder') : t('ChatGptAgent.needsKey')"
          :disabled="!ready"
          :aria-label="t('ChatGptAgent.textQuestion')"
          @input="autoGrow"
          @keydown.enter.exact.prevent="ask(draft)"
        ></textarea>
        <div class="assistant-composer-actions">
          <recorder-widget compact :time="2" :disabled="busy || !ready" @newRecording="processRecording" />
          <button
            type="submit"
            class="assistant-send"
            :disabled="!draft.trim() || busy || !ready"
            :title="t('ChatGptAgent.ask')"
            :aria-label="t('ChatGptAgent.ask')"
          >
            <i class="bi bi-arrow-up"></i>
          </button>
        </div>
      </form>
      <p class="assistant-disclaimer">{{ t('ChatGptAgent.disclaimer') }}</p>
    </footer>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { currentLanguage } from '../i18n';
import { useEngine } from '../engine';
import { getTableSchema, rowCount, runUserQuery, sample } from '../data/tables';
import { aiReady, askSql, conversationTitle, explainResult, speak as speakText, transcribe, usesOwnKey } from '../ai';
import {
  deleteConversation, getConversation, listConversations, renameConversation, saveConversation as storeConversation,
} from '../lib/conversations';
import AiKeySettings from './AiKeySettings.vue';
import RecorderWidget from './RecorderWidget.vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { BarChart, LineChart, PieChart, ScatterChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

use([BarChart, LineChart, PieChart, ScatterChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

const engine = useEngine();
// With DuckDB in the browser the assistant uses the user's own OpenAI key
const ownKey = usesOwnKey();
const ready = ref(aiReady());

const props = defineProps({
  tables: { type: Array, default: () => [] }
});

const { t } = useI18n();
// Rows shown per answer, and sent to the AI to explain the result (fewer rows, fewer tokens)
const RESULT_ROWS = 20;
const QUERY_ROWS = 100;

const blindMode = ref(false);
// Off by default: spoken answers cost tokens
const tts = ref(false);
const messages = ref([]);
const draft = ref('');
const pendingStatus = ref(null);
const busy = ref(false);
const feed = ref(null);
const input = ref(null);
let nextId = 1;

// Conversation history: the list holds { id, title, updated, saved }, the messages of the open one are in `messages`
const HISTORY_KEY = 'assistantHistory';
const TITLE_LENGTH = 60;
const conversations = ref([]);
const currentId = ref(null);
const historyFilter = ref('');
const historyError = ref(false);
const saveError = ref(false);
const renamingId = ref(null);
const renameDraft = ref('');
const renameInput = ref(null);
const deletingId = ref(null);
const showHistory = ref(loadShowHistory());

function loadShowHistory() {
  try {
    return localStorage.getItem(HISTORY_KEY) !== 'hidden';
  } catch {
    return true;
  }
}

watch(showHistory, (value) => {
  try {
    localStorage.setItem(HISTORY_KEY, value ? 'shown' : 'hidden');
  } catch { /* storage blocked */ }
});

const currentConversation = computed(() => conversations.value.find((c) => c.id === currentId.value));

// Today, yesterday, the last 7 days and older, most recent first
const historyGroups = computed(() => {
  const filter = historyFilter.value.trim().toLowerCase();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const startOfToday = today.getTime() / 1000;
  const day = 24 * 3600;
  const groups = { today: [], yesterday: [], week: [], older: [] };
  for (const conversation of conversations.value) {
    if (filter && !conversation.title.toLowerCase().includes(filter)) {
      continue;
    }
    const updated = conversation.updated || 0;
    const key = updated >= startOfToday ? 'today'
      : updated >= startOfToday - day ? 'yesterday'
        : updated >= startOfToday - 7 * day ? 'week' : 'older';
    groups[key].push(conversation);
  }
  return Object.entries(groups).filter(([, items]) => items.length).map(([key, items]) => ({ key, items }));
});

onMounted(loadConversations);

async function loadConversations() {
  try {
    const list = await listConversations();
    conversations.value = list.map((c) => ({ ...c, saved: true }));
    historyError.value = false;
  } catch {
    historyError.value = true;
  }
}

// crypto.randomUUID needs a secure context: the app may be served over plain HTTP
function newConversationId() {
  return `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
}

function shortTitle(question) {
  return question.length > TITLE_LENGTH ? `${question.slice(0, TITLE_LENGTH - 1).trimEnd()}…` : question;
}

function startConversation(question) {
  conversations.value.unshift({ id: newConversationId(), title: shortTitle(question), updated: Date.now() / 1000, saved: false });
  // The reactive copy, so that the title updates re-render
  const conversation = conversations.value[0];
  currentId.value = conversation.id;
  nameConversation(conversation, question);
  return conversation;
}

// The AI names the conversation after its first question, unless the user renamed it meanwhile
async function nameConversation(conversation, question) {
  try {
    const title = await conversationTitle(question, currentLanguage());
    if (!title || conversation.renamed) {
      return;
    }
    conversation.title = title;
    if (conversation.saved) {
      await renameConversation(conversation.id, title);
    }
  } catch { /* keeps the question as its title */ }
}

// What is stored of each message: no ids or transient state (status, speaking, copied)
function storedMessage({ role, text, sql, result, chart, error }) {
  return Object.fromEntries(Object.entries({ role, text, sql, result, chart, error }).filter(([, v]) => v != null));
}

async function saveConversation(conversation) {
  const title = conversation.title;
  try {
    const saved = await storeConversation(conversation.id, { title, messages: messages.value.map(storedMessage) });
    Object.assign(conversation, { updated: saved.updated, database: saved.database, saved: true });
    // Renamed (by the AI or the user) while it was being saved
    if (conversation.title !== title) {
      await renameConversation(conversation.id, conversation.title);
    }
    // The most recent goes first
    conversations.value = [conversation, ...conversations.value.filter((c) => c.id !== conversation.id)];
    saveError.value = false;
  } catch {
    saveError.value = true;
  }
}

async function openConversation(conversation) {
  if (busy.value || conversation.id === currentId.value) {
    return;
  }
  try {
    const { messages: stored } = await getConversation(conversation.id);
    messages.value = stored.map((message) => ({ ...message, id: nextId++ }));
    currentId.value = conversation.id;
    draft.value = '';
    historyError.value = false;
    await scrollToEnd();
  } catch {
    historyError.value = true;
  }
}

async function startRename(conversation) {
  renamingId.value = conversation.id;
  renameDraft.value = conversation.title;
  await nextTick();
  renameInput.value?.[0]?.select();
}

async function finishRename(conversation) {
  if (renamingId.value !== conversation.id) {
    return;
  }
  renamingId.value = null;
  const title = renameDraft.value.trim();
  if (!title || title === conversation.title) {
    return;
  }
  conversation.title = title;
  conversation.renamed = true;
  if (conversation.saved) {
    try {
      await renameConversation(conversation.id, title);
    } catch {
      saveError.value = true;
    }
  }
}

async function removeConversation(conversation) {
  deletingId.value = null;
  try {
    if (conversation.saved) {
      await deleteConversation(conversation.id);
    }
    conversations.value = conversations.value.filter((c) => c.id !== conversation.id);
    if (conversation.id === currentId.value) {
      newChat();
    }
  } catch {
    saveError.value = true;
  }
}

const suggestions = computed(() => {
  const table = props.tables.find((name) => !name.startsWith('__'));
  if (!table) {
    return [];
  }
  return ['rowCount', 'describe', 'sample'].map((key) => t(`ChatGptAgent.suggestions.${key}`, { table }));
});

// The AI layer and the engines throw plain Errors with a message for the user
function errorDetail(error) {
  return error?.message || t('ChatGptAgent.unknownError');
}

// Rows of the result, also beyond the ones it keeps
function resultTotal(result) {
  return result.total ?? result.rows.length;
}

// The last query result (__lastQuery) as { columns, rows of strings, total }: its first QUERY_ROWS rows
async function readResult() {
  const [schema, rows, total] = await Promise.all([
    getTableSchema(engine, '__lastQuery'),
    sample(engine, '__lastQuery', { records: QUERY_ROWS }),
    rowCount(engine, '__lastQuery'),
  ]);
  const columns = Object.keys(schema);
  const text = (value) => (value == null ? '' : typeof value === 'object' ? JSON.stringify(value) : String(value));
  return { columns, rows: rows.map((row) => columns.map((column) => text(row[column]))), total };
}

async function scrollToEnd() {
  await nextTick();
  feed.value?.scrollTo({ top: feed.value.scrollHeight, behavior: 'smooth' });
}

function autoGrow() {
  const el = input.value;
  if (el) {
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }
}

function newChat() {
  messages.value = [];
  draft.value = '';
  currentId.value = null;
  input.value?.focus();
}

async function processRecording(recordedBlob) {
  busy.value = true;
  pendingStatus.value = 'transcribing';
  await scrollToEnd();
  try {
    const transcription = await transcribe(recordedBlob, currentLanguage());
    pendingStatus.value = null;
    busy.value = false;
    if (!transcription) {
      messages.value.push({ id: nextId++, role: 'assistant', error: t('ChatGptAgent.emptyAudio') });
      return;
    }
    await ask(transcription);
  } catch (error) {
    pendingStatus.value = null;
    busy.value = false;
    messages.value.push({ id: nextId++, role: 'assistant', error: t('ChatGptAgent.error', { detail: errorDetail(error) }) });
  }
}

// One turn: the question becomes SQL, the SQL runs, and the result is explained
async function ask(text) {
  const question = String(text || '').trim();
  if (!question || busy.value || !ready.value) {
    return;
  }
  draft.value = '';
  await nextTick();
  autoGrow();
  busy.value = true;
  const conversation = currentConversation.value || startConversation(question);
  messages.value.push({ id: nextId++, role: 'user', text: question });
  messages.value.push({ id: nextId++, role: 'assistant', status: 'writing' });
  // The reactive copy, so that the updates below re-render
  const answer = messages.value[messages.value.length - 1];
  await scrollToEnd();

  try {
    const sql = await askSql(question);
    answer.sql = sql;
    answer.status = 'running';
    await scrollToEnd();

    let result;
    try {
      // On the active engine: the backend, or DuckDB in the browser
      await runUserQuery(engine, sql);
      result = await readResult();
    } catch (error) {
      answer.error = t('ChatGptAgent.queryFailed', { detail: errorDetail(error) });
      return;
    }
    answer.result = result;
    answer.status = 'explaining';
    await scrollToEnd();

    // The explanation, and the chart the AI chose for the result (if any)
    const explained = await explainResult({ question, sql, result, language: currentLanguage() });
    answer.chart = explained.chart || undefined;
    answer.text = explained.answer;
    answer.status = null;
    if (tts.value) {
      speak(answer);
    }
  } catch (error) {
    answer.error = t('ChatGptAgent.error', { detail: errorDetail(error) });
  } finally {
    answer.status = null;
    busy.value = false;
    await scrollToEnd();
    await saveConversation(conversation);
  }
}

async function speak(message) {
  message.speaking = true;
  try {
    const audio = new Audio(window.URL.createObjectURL(await speakText(message.text, currentLanguage())));
    audio.addEventListener('ended', () => { message.speaking = false; });
    await audio.play();
  } catch (error) {
    message.speaking = false;
    message.error = t('ChatGptAgent.speechError', { detail: errorDetail(error) });
  }
}

async function copySql(message) {
  try {
    await navigator.clipboard.writeText(message.sql);
    message.copied = true;
    setTimeout(() => { message.copied = false; }, 1500);
  } catch { /* clipboard blocked */ }
}

// Charts of the results: the AI picks the type and the columns, the user can switch the type
const CHART_TYPES = [
  { id: 'bar', icon: 'bi bi-bar-chart' },
  { id: 'horizontalBar', icon: 'bi bi-bar-chart-steps' },
  { id: 'line', icon: 'bi bi-graph-up' },
  { id: 'area', icon: 'bi bi-graph-up-arrow' },
  { id: 'pie', icon: 'bi bi-pie-chart' },
  { id: 'scatter', icon: 'bi bi-dot' },
];
const CHART_COLORS = ['#0d846f', '#f2a541', '#5c7cfa', '#e76f51', '#2fb594', '#c77dff', '#8d99ae', '#ffd166', '#4cc9f0', '#b5838d'];
// Slices of a pie chart: the rest are added up in one
const PIE_SLICES = 10;

async function changeChartType(message, type) {
  message.chart.type = type;
  if (currentConversation.value?.saved) {
    await saveConversation(currentConversation.value);
  }
}

function chartOption(chart, result) {
  const column = (name) => result.columns.indexOf(name);
  const x = column(chart.x);
  const ys = chart.y.map(column).filter((i) => i >= 0);
  const number = (value) => (value === '' ? null : Number(value));
  const base = { color: CHART_COLORS, animationDuration: 400, tooltip: { trigger: chart.type === 'pie' || chart.type === 'scatter' ? 'item' : 'axis' } };

  if (chart.type === 'pie') {
    const slices = result.rows.map((row) => ({ name: row[x], value: number(row[ys[0]]) || 0 }))
      .sort((a, b) => b.value - a.value);
    if (slices.length > PIE_SLICES) {
      const rest = slices.splice(PIE_SLICES - 1);
      slices.push({ name: t('ChatGptAgent.chart.others'), value: rest.reduce((sum, s) => sum + s.value, 0) });
    }
    return {
      ...base,
      legend: { type: 'scroll', bottom: 0 },
      series: [{
        type: 'pie', radius: ['38%', '68%'], center: ['50%', '45%'], data: slices,
        itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 4 },
        label: { formatter: '{b}: {d}%' },
      }],
    };
  }

  const horizontal = chart.type === 'horizontalBar';
  const scatter = chart.type === 'scatter';
  const categories = result.rows.map((row) => row[x]);
  const categoryAxis = { type: 'category', data: categories, axisLabel: { hideOverlap: true } };
  const valueAxis = { type: 'value', scale: scatter };
  return {
    ...base,
    legend: ys.length > 1 ? { top: 0 } : undefined,
    grid: { left: 12, right: 16, top: ys.length > 1 ? 32 : 16, bottom: 8, containLabel: true },
    xAxis: scatter ? { type: 'value', scale: true, name: chart.x } : horizontal ? valueAxis : categoryAxis,
    yAxis: horizontal ? { ...categoryAxis, inverse: true } : valueAxis,
    series: ys.map((i) => ({
      name: result.columns[i],
      type: scatter ? 'scatter' : horizontal ? 'bar' : chart.type === 'area' ? 'line' : chart.type,
      data: scatter ? result.rows.map((row) => [number(row[x]), number(row[i])]) : result.rows.map((row) => number(row[i])),
      smooth: chart.type === 'area',
      areaStyle: chart.type === 'area' ? { opacity: 0.18 } : undefined,
      itemStyle: chart.type === 'bar' || horizontal ? { borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] } : undefined,
    })),
  };
}

const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

// The answers come in Markdown: paragraphs, lists, bold and code. The text is escaped before any tag is added.
function renderMarkdown(text) {
  const inline = (s) => escapeHtml(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  const html = [];
  let list = null;
  const closeList = () => { if (list) { html.push(`</${list}>`); list = null; } };
  for (const block of text.replace(/\r/g, '').split(/\n{2,}/)) {
    const lines = block.split('\n');
    if (lines.every((l) => /^\s*([-*]|\d+[.)])\s+/.test(l))) {
      const kind = /^\s*\d/.test(lines[0]) ? 'ol' : 'ul';
      if (list !== kind) { closeList(); html.push(`<${kind}>`); list = kind; }
      lines.forEach((l) => html.push(`<li>${inline(l.replace(/^\s*([-*]|\d+[.)])\s+/, ''))}</li>`));
    } else {
      closeList();
      const heading = block.match(/^#{1,6}\s+(.*)$/);
      html.push(heading ? `<p><strong>${inline(heading[1])}</strong></p>` : `<p>${lines.map(inline).join('<br>')}</p>`);
    }
  }
  closeList();
  return html.join('');
}
</script>

<style scoped>
.assistant {
  display: flex;
  height: calc(100vh - 130px);
  min-height: 520px;
  background: var(--ds-surface);
  border: 1px solid var(--ds-line);
  border-radius: 16px;
  box-shadow: var(--ds-shadow);
  overflow: hidden;
}
.assistant-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }

/* Recent conversations */
.assistant-history {
  flex: none; width: 260px; display: flex; flex-direction: column; gap: 10px; padding: 12px 10px;
  border-right: 1px solid var(--ds-line); background: var(--ds-surface-muted);
}
.assistant-new {
  display: flex; align-items: center; gap: 8px; padding: 9px 12px; border: 1px solid var(--ds-line); border-radius: 10px;
  background: #fff; font-size: 13px; font-weight: 650; color: var(--ds-ink); transition: border-color .15s, box-shadow .15s;
}
.assistant-new i { color: var(--ds-teal); }
.assistant-new:hover:not(:disabled) { border-color: #9fd3c3; box-shadow: 0 4px 12px rgba(28, 58, 51, .07); }
.assistant-new:disabled { opacity: .5; cursor: not-allowed; }
.assistant-history-search {
  display: flex; align-items: center; gap: 7px; margin: 0; padding: 6px 10px; border-radius: 9px;
  background: #fff; border: 1px solid transparent; color: var(--ds-muted); font-size: 12px;
}
.assistant-history-search:focus-within { border-color: #9fd3c3; }
.assistant-history-search input { flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; font-size: 12.5px; color: var(--ds-ink); }
.assistant-history-list { flex: 1; overflow-y: auto; margin: 0 -4px; padding: 0 4px; }
.assistant-history-group {
  margin: 12px 8px 4px; font-size: 10.5px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--ds-muted);
}
.assistant-history-group:first-child { margin-top: 2px; }
.assistant-history-note { margin: 8px; font-size: 12px; color: var(--ds-muted); }
.assistant-history-item {
  position: relative; display: flex; align-items: center; gap: 2px; min-height: 34px; padding: 0 4px 0 0; border-radius: 8px;
}
.assistant-history-item:hover, .assistant-history-item:focus-within { background: #e6efec; }
.assistant-history-item.is-active { background: var(--ds-mint); }
.assistant-history-item.is-active .assistant-history-open { color: var(--ds-teal-dark); font-weight: 650; }
.assistant-history-open {
  flex: 1; min-width: 0; padding: 7px 4px 7px 10px; border: 0; background: transparent; text-align: left;
  font-size: 12.5px; color: var(--ds-ink-soft); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.assistant-history-open:disabled { cursor: not-allowed; opacity: .6; }
.assistant-history-actions { display: none; }
.assistant-history-item:hover .assistant-history-actions,
.assistant-history-item:focus-within .assistant-history-actions,
.assistant-history-item.is-active .assistant-history-actions { display: flex; }
.assistant-history-action {
  width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; border: 0; border-radius: 6px;
  background: transparent; color: var(--ds-muted); font-size: 12px;
}
.assistant-history-action:hover:not(:disabled) { background: #fff; color: var(--ds-ink); }
.assistant-history-action.is-danger:hover { color: #b3263a; }
.assistant-history-action:disabled { opacity: .4; }
.assistant-history-confirm { flex: 1; padding-left: 10px; font-size: 12px; font-weight: 600; color: #a9404d; }
.assistant-history-rename {
  flex: 1; min-width: 0; margin: 3px 0 3px 4px; padding: 4px 6px; border: 1px solid var(--ds-teal); border-radius: 6px;
  outline: 0; font-size: 12.5px; background: #fff; color: var(--ds-ink);
}

/* Top bar */
.assistant-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--ds-line);
  background: linear-gradient(180deg, #fff, var(--ds-surface-muted));
}
.assistant-bar-start { display: flex; align-items: center; gap: 8px; min-width: 0; }
.assistant-history-toggle { font-size: 15px; padding: 4px 7px; }
.assistant-history-toggle[aria-pressed="true"] { color: var(--ds-teal-dark); }
.assistant-bar-title { margin: 0; min-width: 0; font-size: 12.5px; color: var(--ds-muted); }
.assistant-bar-name { margin: 0; min-width: 0; font-size: 13.5px; font-weight: 700; color: var(--ds-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.assistant-bar-actions { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.assistant-chip {
  display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px;
  border: 1px solid var(--ds-line); border-radius: 999px; background: #fff;
  font-size: 12px; font-weight: 600; color: var(--ds-ink-soft);
  transition: background .15s, border-color .15s, color .15s;
}
.assistant-chip:hover:not(:disabled) { border-color: #b9ded2; background: var(--ds-surface-muted); }
.assistant-chip.is-on { background: var(--ds-mint); border-color: #9fd3c3; color: var(--ds-teal-dark); }
.assistant-chip:disabled { opacity: .45; cursor: not-allowed; }

.assistant-avatar {
  flex: none; width: 36px; height: 36px; border-radius: 11px;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--ds-teal), #2fb594); color: #fff; font-size: 1rem;
  box-shadow: 0 4px 12px rgba(13, 132, 111, .25);
}
.assistant-avatar.small { width: 28px; height: 28px; border-radius: 9px; font-size: .8rem; }

.assistant-key { padding: 12px 20px 0; background: var(--ds-canvas); }
.assistant-key :deep(.ai-key) { max-width: 860px; margin: 0 auto; }

/* Conversation */
.assistant-feed { flex: 1; overflow-y: auto; padding: 24px 20px 12px; background: var(--ds-canvas); }
.assistant-column { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px; }

.assistant-empty { text-align: center; padding: 56px 12px 24px; }
.assistant-empty-icon {
  display: inline-flex; width: 56px; height: 56px; border-radius: 18px; align-items: center; justify-content: center;
  background: var(--ds-mint); color: var(--ds-teal); font-size: 1.5rem; margin-bottom: 14px;
}
.assistant-empty h3 { font-size: 20px; font-weight: 750; color: var(--ds-ink); margin: 0 0 6px; }
.assistant-empty p { font-size: 13px; color: var(--ds-muted); margin: 0 auto; max-width: 460px; }
.assistant-empty-note { margin-top: 18px !important; }
.assistant-suggestions { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-top: 26px; text-align: left; }
.assistant-suggestion {
  display: flex; align-items: flex-start; gap: 8px; padding: 12px 14px;
  border: 1px solid var(--ds-line); border-radius: 12px; background: #fff;
  font-size: 12.5px; color: var(--ds-ink-soft); text-align: left;
  transition: border-color .15s, box-shadow .15s, transform .15s;
}
.assistant-suggestion i { color: var(--ds-teal); margin-top: 1px; }
.assistant-suggestion:hover:not(:disabled) { border-color: #9fd3c3; box-shadow: 0 6px 18px rgba(28, 58, 51, .08); transform: translateY(-1px); }
.assistant-suggestion:disabled { opacity: .5; cursor: not-allowed; }

.assistant-message { display: flex; gap: 12px; }
.assistant-message.from-user { justify-content: flex-end; }
.user-bubble {
  max-width: 75%; padding: 10px 14px; border-radius: 16px 16px 4px 16px;
  background: var(--ds-teal); color: #fff; font-size: 13.5px; line-height: 1.5;
  white-space: pre-wrap; word-break: break-word; box-shadow: 0 4px 14px rgba(13, 132, 111, .18);
}
.assistant-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 10px; padding-top: 3px; }

.assistant-sql { border-radius: 12px; overflow: hidden; background: var(--ds-ink); border: 1px solid #0f1715; }
.assistant-sql-head {
  display: flex; align-items: center; justify-content: space-between; padding: 6px 10px 6px 14px;
  font-size: 11px; font-weight: 700; letter-spacing: .06em; color: #9fdcc9; background: #1f2b28;
}
.assistant-sql-head .assistant-icon-btn { color: #c9d6d2; }
.assistant-sql-head .assistant-icon-btn:hover { background: rgba(255, 255, 255, .08); color: #fff; }
.assistant-sql pre { margin: 0; padding: 12px 14px; color: #e8f1ee; font-size: 12.5px; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }

.assistant-chart { border: 1px solid var(--ds-line); border-radius: 12px; background: #fff; padding: 10px 12px 8px; }
.assistant-chart-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.assistant-chart-title { font-size: 13px; font-weight: 700; color: var(--ds-ink); }
.assistant-chart-types { display: flex; gap: 2px; padding: 2px; border-radius: 9px; background: var(--ds-surface-muted); }
.assistant-chart-types .assistant-icon-btn { padding: 4px 7px; font-size: 13px; }
.assistant-chart-types .assistant-icon-btn.is-on { background: #fff; color: var(--ds-teal-dark); box-shadow: 0 1px 3px rgba(28, 58, 51, .12); }
.assistant-chart-canvas { height: 320px; width: 100%; }

.assistant-result { border: 1px solid var(--ds-line); border-radius: 12px; background: #fff; overflow: hidden; }
.assistant-result-scroll { max-height: 280px; overflow: auto; }
.assistant-result table { width: 100%; border-collapse: collapse; font-size: 12px; }
.assistant-result th {
  position: sticky; top: 0; background: var(--ds-surface-muted); color: var(--ds-muted);
  font-weight: 700; text-align: left; padding: 7px 12px; border-bottom: 1px solid var(--ds-line); white-space: nowrap;
}
.assistant-result td { padding: 6px 12px; border-bottom: 1px solid #eef3f1; color: var(--ds-ink); white-space: nowrap; }
.assistant-result tbody tr:hover td { background: #f6faf8; }
.assistant-result-foot { margin: 0; padding: 6px 12px; font-size: 11px; color: var(--ds-muted); border-top: 1px solid var(--ds-line); background: var(--ds-surface-muted); }

.assistant-text { font-size: 14px; line-height: 1.65; color: var(--ds-ink); }
.assistant-text :deep(p) { margin: 0 0 8px; }
.assistant-text :deep(p:last-child) { margin-bottom: 0; }
.assistant-text :deep(ul), .assistant-text :deep(ol) { margin: 0 0 8px; padding-left: 22px; }
.assistant-text :deep(li) { margin: 2px 0; }
.assistant-text :deep(code) { padding: 1px 5px; border-radius: 5px; background: var(--ds-mint); color: var(--ds-teal-dark); font-size: 12.5px; }

.assistant-error {
  margin: 0; padding: 9px 12px; border-radius: 10px; font-size: 12.5px;
  background: #fff4f5; border: 1px solid #efc9cd; color: #a9404d;
}

.assistant-status { display: flex; align-items: center; gap: 10px; font-size: 12.5px; color: var(--ds-muted); padding: 6px 0; }
.assistant-dots { display: inline-flex; gap: 4px; }
.assistant-dots i { width: 6px; height: 6px; border-radius: 50%; background: var(--ds-teal); animation: dot-bounce 1.2s infinite ease-in-out; }
.assistant-dots i:nth-child(2) { animation-delay: .15s; }
.assistant-dots i:nth-child(3) { animation-delay: .3s; }
@keyframes dot-bounce { 0%, 80%, 100% { transform: translateY(0); opacity: .35; } 40% { transform: translateY(-4px); opacity: 1; } }

.assistant-actions { display: flex; gap: 4px; }
.assistant-icon-btn {
  display: inline-flex; align-items: center; gap: 5px; padding: 4px 8px; border: 0; border-radius: 7px;
  background: transparent; font-size: 11.5px; color: var(--ds-muted);
}
.assistant-icon-btn:hover:not(:disabled) { background: var(--ds-mint); color: var(--ds-teal-dark); }
.assistant-icon-btn:disabled { opacity: .6; }

/* Composer */
.assistant-composer-wrap { padding: 12px 20px 14px; background: var(--ds-canvas); border-top: 1px solid var(--ds-line); }
.assistant-composer {
  max-width: 860px; margin: 0 auto; display: flex; align-items: flex-end; gap: 10px;
  padding: 8px 8px 8px 16px; background: #fff; border: 1px solid #cfe0da; border-radius: 18px;
  box-shadow: 0 8px 24px rgba(28, 58, 51, .08); transition: border-color .15s, box-shadow .15s;
}
.assistant-composer:focus-within { border-color: var(--ds-teal); box-shadow: 0 0 0 3px rgba(13, 132, 111, .12), 0 8px 24px rgba(28, 58, 51, .08); }
.assistant-composer textarea {
  flex: 1; border: 0; outline: 0; resize: none; background: transparent; padding: 8px 0;
  font-size: 14px; line-height: 1.5; color: var(--ds-ink); max-height: 180px;
}
.assistant-composer-actions { display: flex; align-items: center; gap: 6px; }
.assistant-send {
  width: 36px; height: 36px; border-radius: 50%; border: 0; background: var(--ds-teal); color: #fff;
  display: inline-flex; align-items: center; justify-content: center; font-size: 1.05rem;
  transition: background .15s, opacity .15s;
}
.assistant-send:hover:not(:disabled) { background: var(--ds-teal-dark); }
.assistant-send:disabled { opacity: .35; cursor: not-allowed; }
.assistant-disclaimer { max-width: 860px; margin: 6px auto 0; text-align: center; font-size: 10.5px; color: var(--ds-muted); }

@media (max-width: 900px) {
  .assistant-history { width: 210px; }
  .assistant-bar { flex-direction: column; align-items: flex-start; }
  .assistant-bar-actions { justify-content: flex-start; }
  .user-bubble { max-width: 90%; }
}
</style>
