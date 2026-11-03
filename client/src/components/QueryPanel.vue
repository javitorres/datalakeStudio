<template>
  <section class="query-workspace" v-if="tables && tables.length > 0" @keydown.ctrl.enter.prevent="runQuery" @keydown.meta.enter.prevent="runQuery">
    <header class="query-header">
      <div>
        <span class="page-kicker">{{ t('QueryPanel.kicker') }}</span>
        <h2>{{ t('QueryPanel.title') }}</h2>
        <p>{{ t('QueryPanel.intro') }}</p>
      </div>
      <div class="workspace-summary">
        <span><i class="bi bi-database"></i><b>{{ tables.length }}</b> {{ t('QueryPanel.tablesWord', tables.length) }}</span>
        <span :class="{ success: querySuccesful, error: queryError }">
          <i class="bi" :class="queryError ? 'bi-exclamation-triangle' : (querySuccesful ? 'bi-check-circle' : 'bi-circle')"></i>
          {{ queryError ? t('QueryPanel.status.failed') : (querySuccesful ? t('QueryPanel.status.succeeded') : t('QueryPanel.status.ready')) }}
        </span>
      </div>
    </header>

    <div class="query-layout">
      <main class="editor-panel">
        <nav class="query-tabs" :aria-label="t('QueryPanel.buffersLabel')">
          <button
            v-for="tab in queryTabs"
            :key="tab.id"
            :class="{ active: activeQueryTab === tab.id }"
            @click="activeQueryTab = tab.id"
          >
            <i class="bi" :class="tab.id === 'mainQuery' ? 'bi-filetype-sql' : 'bi-file-earmark-code'"></i>
            <span>{{ tab.label }}</span>
            <small>{{ tab.shortcut }}</small>
          </button>
          <span class="tab-spacer"></span>
          <span class="sql-dialect">DUCKDB SQL</span>
        </nav>

        <div class="editor-toolbar">
          <div class="editor-context">
            <span class="context-dot"></span>
            <span>{{ activeQueryLabel }}</span>
            <small>{{ t('QueryPanel.tokens', currentQuery.trim() ? currentQuery.trim().split(/\s+/).length : 0) }}</small>
            <small class="schema-status" :class="`schema-${schemaStatus}`">{{ schemaStatusText }}</small>
          </div>
          <div class="editor-actions">
            <button :title="t('QueryPanel.clearTitle')" @click="currentQuery = ''"><i class="bi bi-eraser"></i> {{ t('QueryPanel.clear') }}</button>
            <button class="run-query" :disabled="queryRunning || !currentQuery.trim()" @click="runQuery">
              <span v-if="queryRunning" class="spinner-border spinner-border-sm"></span>
              <i v-else class="bi bi-play-fill"></i>
              {{ t('QueryPanel.run') }}
              <kbd>⌘ ↵</kbd>
            </button>
          </div>
        </div>

        <div class="editor-body">
          <codemirror
            v-model="currentQuery"
            placeholder="SELECT * FROM ..."
            :style="{ height: '330px' }"
            :autofocus="true"
            :indent-with-tab="true"
            :tab-size="4"
            :extensions="extensions"
          />
        </div>

        <div v-if="queryError" class="query-error">
          <i class="bi bi-exclamation-octagon"></i>
          <div><b>{{ t('QueryPanel.executionFailed') }}</b><pre>{{ queryError }}</pre></div>
          <button @click="queryError = null" :aria-label="t('QueryPanel.dismissError')"><i class="bi bi-x-lg"></i></button>
        </div>

        <footer class="editor-footer">
          <span><i class="bi bi-lightning-charge"></i> {{ t('QueryPanel.poweredBy') }}</span>
          <span>{{ t('QueryPanel.tabSize', { n: 4 }) }}</span>
          <span>SQL</span>
        </footer>
      </main>

      <aside class="tools-panel">
        <header class="tools-header">
          <div><span class="page-kicker">{{ t('QueryPanel.toolsKicker') }}</span><h3>{{ t('QueryPanel.actions') }}</h3></div>
        </header>
        <nav class="tool-tabs">
          <a href="#" :class="{ active: activeTab === 'newTable' }" @click.prevent="activeTab = 'newTable'"><i class="bi bi-table"></i><span>{{ t('QueryPanel.toolTabs.newTable') }}</span></a>
          <a href="#" :class="{ active: activeTab === 'saveSql' }" @click.prevent="activeTab = 'saveSql'"><i class="bi bi-bookmark"></i><span>{{ t('QueryPanel.toolTabs.saveSql') }}</span></a>
          <a href="#" :class="{ active: activeTab === 'loadSql' }" @click.prevent="activeTab = 'loadSql'"><i class="bi bi-folder2-open"></i><span>{{ t('QueryPanel.toolTabs.library') }}</span></a>
          <a v-if="engine.capabilities.serverAi || engine.capabilities.ownAi" href="#" :class="{ active: activeTab === 'askGpt' }" @click.prevent="activeTab = 'askGpt'"><i class="bi bi-stars"></i><span>{{ t('QueryPanel.toolTabs.askAi') }}</span></a>
        </nav>

        <div class="tool-content">
          <section v-if="activeTab === 'newTable'" class="tool-section">
            <div class="tool-title"><i class="bi bi-table"></i><div><h4>{{ t('QueryPanel.newTable.title') }}</h4><p>{{ t('QueryPanel.newTable.help') }}</p></div></div>
            <div v-if="sampleData" class="tool-form">
              <label for="tableNameInput">{{ t('QueryPanel.newTable.nameLabel') }}</label>
              <input id="tableNameInput" v-model="tableFromQuery" type="text" :placeholder="t('QueryPanel.newTable.namePlaceholder')">
              <button v-if="tableFromQuery" @click="createTable"><i class="bi bi-plus-lg"></i> {{ t('QueryPanel.newTable.create') }}</button>
            </div>
            <div v-else class="tool-empty"><i class="bi bi-play-circle"></i><p>{{ t('QueryPanel.newTable.runFirst') }}</p></div>
          </section>

          <section v-if="activeTab === 'saveSql'" class="tool-section">
            <div class="tool-title"><i class="bi bi-bookmark"></i><div><h4>{{ t('QueryPanel.save.title') }}</h4><p>{{ t('QueryPanel.save.help') }}</p></div></div>
            <div class="tool-form">
              <label for="sqlQueryName">{{ t('QueryPanel.save.nameLabel') }}</label>
              <input id="sqlQueryName" v-model="sqlQueryName" :placeholder="t('QueryPanel.save.namePlaceholder')">
              <label for="sqlQueryDescription">{{ t('QueryPanel.save.descriptionLabel') }}</label>
              <textarea id="sqlQueryDescription" v-model="sqlQueryDescription" rows="3" :placeholder="t('QueryPanel.save.descriptionPlaceholder')"></textarea>
              <button v-if="sqlQueryName && sqlQueryDescription" @click="saveSqlQuery"><i class="bi bi-check2"></i> {{ t('QueryPanel.save.button') }}</button>
            </div>
          </section>

          <section v-if="activeTab === 'loadSql'" class="tool-section library-section">
            <div class="tool-title"><i class="bi bi-folder2-open"></i><div><h4>{{ t('QueryPanel.library.title') }}</h4><p>{{ t('QueryPanel.library.help') }}</p></div></div>
            <div class="library-search"><i class="bi bi-search"></i><input v-model="sqlSearchQuery" :placeholder="t('QueryPanel.library.searchPlaceholder')" @input="searchQuery"></div>
            <div v-if="queries && queries.length" class="query-library">
              <article v-for="queryCandidate in queries" :key="queryCandidate.id_query" @click="selectQuery(queryCandidate)">
                <header><b>{{ queryCandidate.name }}</b><button :title="t('QueryPanel.library.deleteTitle')" @click.stop="deleteQuery(queryCandidate)"><i class="bi bi-trash3"></i></button></header>
                <p>{{ queryCandidate.description }}</p>
                <code>{{ queryCandidate.query }}</code>
              </article>
            </div>
            <div v-else-if="sqlSearchQuery" class="tool-empty"><i class="bi bi-search"></i><p>{{ t('QueryPanel.library.noResults') }}</p></div>
          </section>

          <section v-if="activeTab === 'askGpt'" class="tool-section ai-section">
            <div class="tool-title"><i class="bi bi-stars"></i><div><h4>{{ t('QueryPanel.ai.title') }}</h4><p>{{ t('QueryPanel.ai.help') }}</p></div></div>
            <AiKeySettings v-if="usesOwnKey()" />
            <div class="ai-prompt">
              <textarea id="chatGPTInput" v-model="chatGPTInput" rows="5" :placeholder="t('QueryPanel.ai.placeholder')"></textarea>
              <button :disabled="!chatGPTInput.trim()" @click="askChatGPT"><i class="bi bi-send"></i> {{ t('QueryPanel.ai.generate') }}</button>
            </div>
            <div v-if="chatGPTOutput" class="ai-response">
              <span>{{ t('QueryPanel.ai.generated') }}</span>
              <code>{{ chatGPTOutput }}</code>
              <button @click="useChatGPTAnswer"><i class="bi bi-play-fill"></i> {{ t('QueryPanel.ai.runIt') }}</button>
            </div>
          </section>
        </div>
      </aside>
    </div>

    <section class="results-panel">
      <header class="results-header">
        <div>
          <span class="page-kicker">{{ t('QueryPanel.results.kicker') }}</span>
          <h3>{{ t('QueryPanel.results.title') }}</h3>
        </div>
        <div v-if="querySuccesful" class="result-status"><i class="bi bi-check2-circle"></i><span><b>{{ t('QueryPanel.results.success') }}</b><small>{{ t('QueryPanel.results.storedIn', { name: tableName }) }}</small></span></div>
      </header>
      <div v-if="querySuccesful" class="results-body">
        <TableInspector :tableName="tableName" :showOptions="showOptions" />
      </div>
      <div v-else class="results-empty">
        <div><i class="bi bi-terminal"></i></div>
        <h4>{{ t('QueryPanel.results.emptyTitle') }}</h4>
        <p>{{ t('QueryPanel.results.emptyHelp') }}</p>
      </div>
    </section>
  </section>

  <section v-else class="query-empty">
    <i class="bi bi-database-exclamation"></i>
    <h2>{{ t('QueryPanel.noTables') }}</h2>
    <p>{{ t('QueryPanel.noTablesHelp') }}</p>
  </section>
</template>
<script setup>
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Codemirror } from "vue-codemirror";
import { sql } from "@codemirror/lang-sql";

import { useEngine } from '../engine';
import { createTableFromQuery, getDatabaseSchema, runUserQuery } from '../data/tables';
import { deleteQuery as removeSavedQuery, saveQuery, searchQueries } from '../data/queries';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import TableInspector from './TableInspector.vue';
import AiKeySettings from './AiKeySettings.vue';
import { askSql, usesOwnKey } from '../ai';

const props = defineProps({
  tables: Object,
  secrets: Object,
});

const emit = defineEmits(['tableCreated']);
const { t } = useI18n();
const engine = useEngine();

const completionSchema = ref({});
const schemaStatus = ref('loading');
let schemaRequestId = 0;
const extensions = computed(() => [sql({
  schema: completionSchema.value,
  upperCaseKeywords: true
})]);
const schemaStatusText = computed(() => {
  if (schemaStatus.value === 'loading') return t('QueryPanel.schema.loading');
  if (schemaStatus.value === 'unavailable') return t('QueryPanel.schema.unavailable');
  const tableCount = Object.keys(completionSchema.value).length;
  return t('QueryPanel.schema.indexed', tableCount);
});
const query = ref('SELECT * FROM iris');
const auxQuery1 = ref('');
const auxQuery2 = ref('');
const auxQuery3 = ref('');
const auxQuery4 = ref('');
const auxQuery5 = ref('');
const sampleData = ref(null);
const activeTab = ref('newTable');
const activeQueryTab = ref('mainQuery');
const tableFromQuery = ref('');
const sqlQueryName = ref('');
const sqlQueryDescription = ref('');
const sqlSearchQuery = ref('');
const queries = ref([]);
const chatGPTInput = ref('dame askingprice medio');
const chatGPTOutput = ref('');
const tableName = ref('__lastQuery');
const querySuccesful = ref(false);
const showOptions = ref(true);
const queryError = ref(null);
const queryRunning = ref(false);
const queryTabs = computed(() => [
  { id: 'mainQuery', label: t('QueryPanel.tabs.main'), shortcut: '01' },
  ...[1, 2, 3, 4, 5].map((n) => ({ id: `aux${n}`, label: t('QueryPanel.tabs.aux', { n }), shortcut: `0${n + 1}` }))
]);
const queryBuffers = {
  mainQuery: query,
  aux1: auxQuery1,
  aux2: auxQuery2,
  aux3: auxQuery3,
  aux4: auxQuery4,
  aux5: auxQuery5
};
const currentQuery = computed({
  get: () => queryBuffers[activeQueryTab.value].value,
  set: (value) => { queryBuffers[activeQueryTab.value].value = value; }
});
const activeQueryLabel = computed(() => queryTabs.value.find((tab) => tab.id === activeQueryTab.value)?.label || t('QueryPanel.tabs.fallback'));

function toCompletionSchema(databaseSchema) {
  return Object.fromEntries(
    Object.entries(databaseSchema || {}).map(([tableName, columns]) => [
      tableName,
      Object.entries(columns || {}).map(([label, detail]) => ({
        label,
        type: 'property',
        detail,
        ...(!/^[A-Za-z_][A-Za-z0-9_$]*$/.test(label)
          ? { apply: `"${label.replaceAll('"', '""')}"` }
          : {})
      }))
    ])
  );
}

async function loadDatabaseSchema() {
  const requestId = ++schemaRequestId;
  schemaStatus.value = 'loading';

  try {
    const databaseSchema = await getDatabaseSchema(engine);
    if (requestId !== schemaRequestId) return;
    completionSchema.value = toCompletionSchema(databaseSchema);
    schemaStatus.value = 'ready';
  } catch (_) {
    if (requestId !== schemaRequestId) return;
    completionSchema.value = {};
    schemaStatus.value = 'unavailable';
  }
}

watch(() => props.tables, loadDatabaseSchema, { immediate: true, deep: true });


async function runQuery() {
  queryError.value = null;
  querySuccesful.value = false;

  queryRunning.value = true;
  const queryToRun = currentQuery.value;
  toast.promise(
    runUserQuery(engine, queryToRun),
    {
      pending: t('QueryPanel.toast.running'),
      success: t('QueryPanel.toast.executed'),
      error: t('QueryPanel.toast.runError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    // Only the flag matters: TableInspector reads the result from __lastQuery
    sampleData.value = true;
    querySuccesful.value = true;
  }).catch((error) => {
    queryError.value = error.message;
  }).finally(() => {
    queryRunning.value = false;
  });
}

async function createTable() {
  toast.promise(
    createTableFromQuery(engine, tableFromQuery.value, currentQuery.value),
    {
      pending: t('QueryPanel.toast.creatingTable'),
      success: t('QueryPanel.toast.tableCreated'),
      error: t('QueryPanel.toast.createTableError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    emit('tableCreated');
  }).catch((error) => {
    toast.error(t('QueryPanel.toast.errorDetail', { detail: error.message }), { position: toast.POSITION.BOTTOM_RIGHT });
  });
}

async function askChatGPT() {
  toast.promise(
    askSql(chatGPTInput.value),
    {
      pending: t('QueryPanel.toast.asking'),
      success: t('QueryPanel.toast.answered'),
      error: t('QueryPanel.toast.askError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((sql) => {
    chatGPTOutput.value = sql;
  }).catch((error) => {
    toast.error(t('QueryPanel.toast.errorDetail', { detail: error.message }), { position: toast.POSITION.BOTTOM_RIGHT });
  });
}

async function useChatGPTAnswer() {
  currentQuery.value = chatGPTOutput.value;
  runQuery();
}

async function saveSqlQuery() {
  toast.promise(
    saveQuery(engine, {
      name: sqlQueryName.value,
      query: currentQuery.value,
      description: sqlQueryDescription.value,
    }),
    {
      pending: t('QueryPanel.toast.saving'),
      success: t('QueryPanel.toast.saved'),
      error: t('QueryPanel.toast.saveError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).catch((error) => {
    toast.error(t('QueryPanel.toast.errorDetail', { detail: error.message }), { position: toast.POSITION.BOTTOM_RIGHT });
  });
}

async function searchQuery() {
  toast.promise(
    searchQueries(engine, sqlSearchQuery.value),
    {
      pending: t('QueryPanel.toast.searching'),
      success: t('QueryPanel.toast.loaded'),
      error: t('QueryPanel.toast.loadError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((rows) => {
    queries.value = rows;
  }).catch((error) => {
    toast.error(t('QueryPanel.toast.errorDetail', { detail: error.message }), { position: toast.POSITION.BOTTOM_RIGHT });
  });
}

async function selectQuery(queryCandidate) {
  currentQuery.value = queryCandidate.query;
  sqlSearchQuery.value = null;
  queries.value = [];
}

async function deleteQuery(queryCandidate) {
  toast.promise(
    removeSavedQuery(engine, queryCandidate.id_query),
    {
      pending: t('QueryPanel.toast.deleting'),
      success: t('QueryPanel.toast.deleted'),
      error: t('QueryPanel.toast.deleteError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    searchQuery();
  }).catch((error) => {
    toast.error(t('QueryPanel.toast.errorDetail', { detail: error.message }), { position: toast.POSITION.BOTTOM_RIGHT });
  });
}
</script>

<style scoped>
.query-workspace{display:grid;gap:13px}.query-header{display:flex;align-items:center;justify-content:space-between;gap:25px;padding:18px 20px;border:1px solid var(--ds-line);border-radius:13px;background:linear-gradient(115deg,#fff,#f0f8f5);box-shadow:0 8px 28px rgba(31,67,58,.045)}.page-kicker{color:#84918d;font-size:8px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.query-header h2{margin:1px 0 2px;color:var(--ds-ink);font-size:1.18rem;font-weight:760;letter-spacing:-.03em}.query-header p{margin:0;color:var(--ds-muted);font-size:9px}.workspace-summary{display:flex;gap:7px}.workspace-summary>span{display:flex;align-items:center;gap:5px;padding:6px 8px;border:1px solid #dce6e3;border-radius:7px;background:#fff;color:#74827e;font-size:8px}.workspace-summary i{color:#86938f}.workspace-summary .success{border-color:#b8ddcf;background:#edf8f4;color:var(--ds-teal-dark)}.workspace-summary .success i{color:var(--ds-teal)}.workspace-summary .error{border-color:#edc9cd;background:#fff4f5;color:#b33e4d}.query-layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:12px;align-items:start}.editor-panel,.tools-panel,.results-panel{overflow:hidden;border:1px solid var(--ds-line);border-radius:13px;background:#fff;box-shadow:0 7px 24px rgba(31,67,58,.04)}.query-tabs{display:flex;align-items:end;gap:2px;min-height:45px;padding:7px 8px 0;border-bottom:1px solid #2d3d39;background:#17211f}.query-tabs button{height:37px;min-width:78px;display:flex;align-items:center;gap:6px;padding:0 10px;border:0;border-radius:7px 7px 0 0;background:transparent;color:#788b86;font-size:9px;font-weight:700}.query-tabs button:hover{color:#c0d1cc;background:#20302d}.query-tabs button.active{color:#d7eee8;background:#263a35}.query-tabs button i{font-size:11px}.query-tabs button small{display:none}.tab-spacer{flex:1}.sql-dialect{align-self:center;margin:0 6px 6px;color:#60736e;font:700 7px ui-monospace,monospace;letter-spacing:.12em}.editor-toolbar{min-height:47px;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:6px 10px;border-bottom:1px solid #33443f;background:#263a35}.editor-context{display:flex;align-items:center;gap:7px;color:#b5c6c1;font-size:9px}.editor-context small{color:#6f847e}.context-dot{width:6px;height:6px;border-radius:50%;background:#65c7af;box-shadow:0 0 0 3px rgba(101,199,175,.12)}.editor-actions{display:flex;gap:5px}.editor-actions button{height:31px;display:flex;align-items:center;gap:6px;padding:0 9px;border:1px solid #40544e;border-radius:6px;background:#2d423d;color:#aebfba;font-size:8px;font-weight:700}.editor-actions button:hover{background:#364d47;color:#fff}.editor-actions .run-query{border-color:#74cbb6;background:#69c2ac;color:#11251f}.editor-actions .run-query:hover{background:#7dd2bd}.editor-actions button:disabled{opacity:.45}.editor-actions kbd{padding:1px 4px;border-radius:3px;background:#4ca992;color:#dff8f2;font-size:6px}.editor-body{background:#17211f}.editor-body :deep(.cm-editor){background:#17211f!important;color:#d6e6e2}.editor-body :deep(.cm-gutters){border-right:1px solid #2a3c37;background:#17211f!important;color:#536862}.editor-body :deep(.cm-activeLine),.editor-body :deep(.cm-activeLineGutter){background:#1d2d29!important}.editor-body :deep(.cm-content){padding:12px 0;font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace;font-size:11px;line-height:1.65}.editor-body :deep(.cm-cursor){border-left-color:#73cfb8}.editor-body :deep(.cm-selectionBackground){background:#315a50!important}.editor-body :deep(.ͼb){color:#89d7c4}.editor-body :deep(.ͼd){color:#deb77c}.query-error{display:grid;grid-template-columns:24px 1fr 24px;gap:8px;padding:10px 12px;border-top:1px solid #e7bfc4;background:#fff1f2;color:#ac3545}.query-error>b{font-size:9px}.query-error pre{max-height:100px;margin:2px 0 0;overflow:auto;white-space:pre-wrap;color:#8e3642;font-size:8px}.query-error button{border:0;background:transparent;color:#b55d69}.editor-footer{height:29px;display:flex;align-items:center;justify-content:flex-end;gap:14px;padding:0 10px;border-top:1px solid #2a3b36;background:#1c2a27;color:#61746e;font-size:7px}.editor-footer span:first-child{margin-right:auto}.editor-footer i{color:#67bda8}.tools-panel{min-height:454px}.tools-header{height:54px;display:flex;align-items:center;padding:9px 13px;border-bottom:1px solid var(--ds-line);background:#fbfcfc}.tools-header h3{margin:0;font-size:.9rem;font-weight:750}.tool-tabs{display:grid;grid-template-columns:repeat(4,1fr);padding:5px;border-bottom:1px solid var(--ds-line);background:#f0f5f3}.tool-tabs a{display:grid;justify-items:center;gap:2px;padding:7px 2px;border-radius:6px;color:#7b8985;font-size:7px;font-weight:700}.tool-tabs a i{font-size:11px}.tool-tabs a:hover{color:var(--ds-ink)}.tool-tabs a.active{background:#fff;color:var(--ds-teal-dark);box-shadow:0 2px 7px rgba(31,67,58,.08)}.tool-content{padding:13px}.tool-title{display:flex;align-items:center;gap:9px;margin-bottom:12px}.tool-title>i{width:31px;height:31px;display:grid;place-items:center;border-radius:8px;background:var(--ds-mint);color:var(--ds-teal)}.tool-title h4{margin:0;font-size:.8rem;font-weight:750}.tool-title p{margin:1px 0 0;color:#8a9692;font-size:7px}.tool-form{display:grid;gap:6px}.tool-form label{color:#687773;font-size:8px;font-weight:750}.tool-form input,.tool-form textarea,.library-search,.ai-prompt textarea{width:100%;padding:7px 8px;border:1px solid #d8e3df;border-radius:7px;background:#f9fbfa;color:var(--ds-ink);font-size:9px;outline:0}.tool-form input:focus,.tool-form textarea:focus,.library-search:focus-within,.ai-prompt textarea:focus{border-color:#70b9a7;box-shadow:0 0 0 3px rgba(13,132,111,.07);background:#fff}.tool-form button,.ai-prompt button,.ai-response button{display:flex;align-items:center;justify-content:center;gap:5px;margin-top:3px;padding:7px;border:0;border-radius:7px;background:var(--ds-teal);color:#fff;font-size:8px;font-weight:750}.tool-empty{min-height:145px;display:grid;place-items:center;align-content:center;color:#9aa5a2;text-align:center}.tool-empty i{font-size:20px}.tool-empty p{font-size:8px}.library-search{display:flex;align-items:center;gap:6px;padding:0 7px}.library-search input{width:100%;height:32px;border:0;outline:0;background:transparent;font-size:9px}.query-library{display:grid;gap:6px;max-height:300px;margin-top:8px;overflow:auto}.query-library article{padding:8px;border:1px solid #e0e8e5;border-radius:8px;background:#f9fbfa;cursor:pointer}.query-library article:hover{border-color:#a8cec4;background:#fff}.query-library header{display:flex;justify-content:space-between}.query-library b{font-size:9px}.query-library header button{border:0;background:transparent;color:#a35a63;font-size:8px}.query-library p{margin:2px 0;color:#84918d;font-size:7px}.query-library code{display:block;overflow:hidden;text-overflow:ellipsis;color:#52635e;font-size:7px;white-space:nowrap}.ai-prompt{display:grid;gap:6px}.ai-prompt textarea{resize:vertical}.ai-prompt button:disabled{opacity:.45}.ai-section .tool-title>i{background:#eeeafa;color:#775aa5}.ai-response{display:grid;gap:6px;margin-top:10px;padding:8px;border:1px solid #d9e5e1;border-radius:8px;background:#f5f9f7}.ai-response>span{color:#81908b;font-size:7px;text-transform:uppercase}.ai-response code{max-height:100px;overflow:auto;color:#31443e;font-size:8px;white-space:pre-wrap}.results-header{height:61px;display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-bottom:1px solid var(--ds-line);background:#fbfcfc}.results-header h3{margin:0;font-size:.93rem;font-weight:750}.result-status{display:flex;align-items:center;gap:7px;color:var(--ds-teal)}.result-status>span{display:grid}.result-status b{font-size:8px}.result-status small{color:#8a9692;font-size:7px}.results-body{padding:12px}.results-empty{min-height:230px;display:grid;place-items:center;align-content:center;color:#8c9995;text-align:center}.results-empty>div{width:47px;height:47px;display:grid;place-items:center;border-radius:12px;background:#edf4f1;color:#71958b;font-size:19px}.results-empty h4{margin:10px 0 1px;font-size:.9rem}.results-empty p{margin:0;font-size:8px}.query-empty{min-height:360px;display:grid;place-items:center;align-content:center;border:1px dashed #c7d7d2;border-radius:13px;background:#f8fbfa;text-align:center}.query-empty>i{font-size:28px;color:#8fb0a7}.query-empty h2{margin:10px 0 0;font-size:1rem}.query-empty p{color:var(--ds-muted);font-size:10px}
@media(max-width:1100px){.query-layout{grid-template-columns:1fr}.tools-panel{min-height:0}.tool-content{min-height:220px}.query-tabs button{min-width:65px}}
@media(max-width:700px){.query-header{align-items:flex-start;flex-direction:column}.workspace-summary{flex-wrap:wrap}.query-tabs{overflow-x:auto}.query-tabs button{min-width:70px}.sql-dialect{display:none}.editor-toolbar{align-items:flex-start;flex-direction:column}.editor-actions{width:100%;justify-content:space-between}.query-layout{display:block}.tools-panel{margin-top:10px}.results-panel{margin-top:10px}.results-body{padding:7px}}
</style>