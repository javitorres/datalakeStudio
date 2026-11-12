<template>
  <section class="boards">
    <!-- The user's dashboards, and the ones other users published on this server -->
    <aside class="boards-list" :aria-label="t('Dashboards.mine')">
      <button type="button" class="boards-new" :disabled="busy" @click="newDashboard">
        <i class="bi bi-plus-lg"></i>{{ t('Dashboards.new') }}
      </button>
      <nav class="boards-nav">
        <h4>{{ t('Dashboards.mine') }}</h4>
        <p v-if="listError" class="boards-note text-danger">{{ t('Dashboards.loadError') }}</p>
        <p v-else-if="!dashboards.length" class="boards-note">{{ t('Dashboards.empty') }}</p>
        <div v-for="dashboard in dashboards" :key="dashboard.id" class="boards-item" :class="{ 'is-active': dashboard.id === current?.id }">
          <template v-if="deletingId === dashboard.id">
            <span class="boards-confirm">{{ t('Dashboards.confirmDelete') }}</span>
            <button type="button" class="boards-action is-danger" :title="t('Dashboards.delete')" @click="removeDashboard(dashboard)">
              <i class="bi bi-check-lg"></i>
            </button>
            <button type="button" class="boards-action" :title="t('Dashboards.cancel')" @click="deletingId = null">
              <i class="bi bi-x-lg"></i>
            </button>
          </template>
          <template v-else>
            <button type="button" class="boards-open" :title="dashboard.title" :disabled="busy" @click="openDashboard(dashboard)">
              <i v-if="dashboard.published" class="bi bi-broadcast" :title="t('Dashboards.published')"></i>
              {{ dashboard.title || t('Dashboards.untitled') }}
            </button>
            <button type="button" class="boards-action" :title="t('Dashboards.delete')" :disabled="busy" @click="deletingId = dashboard.id">
              <i class="bi bi-trash3"></i>
            </button>
          </template>
        </div>

        <template v-if="shared.length">
          <h4>{{ t('Dashboards.shared') }}</h4>
          <a v-for="dashboard in shared" :key="dashboard.path" class="boards-shared" :href="publishedUrl(dashboard.path)" target="_blank" rel="noopener">
            <span>{{ dashboard.title || dashboard.path }}</span>
            <small>{{ dashboard.path }} · {{ dashboard.owner }}</small>
          </a>
        </template>
      </nav>
    </aside>

    <div class="boards-main">
      <header v-if="current" class="boards-bar">
        <input
          v-model="current.title"
          class="boards-title"
          maxlength="200"
          :placeholder="t('Dashboards.untitled')"
          :aria-label="t('Dashboards.titleLabel')"
          @change="save"
        >
        <span class="boards-state" :class="{ 'text-danger': saveError }">
          <template v-if="saveError"><i class="bi bi-cloud-slash"></i> {{ t('Dashboards.saveError', { detail: saveError }) }}</template>
          <template v-else-if="saving">{{ t('Dashboards.saving') }}</template>
          <template v-else-if="current.saved"><i class="bi bi-check2"></i> {{ t('Dashboards.saved') }}</template>
        </span>
        <span v-if="!publishable" class="boards-local" :title="t('Dashboards.localOnly')">
          <i class="bi bi-shield-lock"></i> {{ t('Dashboards.localOnly') }}
        </span>
        <button
          v-else
          type="button"
          class="boards-chip"
          :class="{ 'is-on': current.published }"
          :aria-expanded="showPublish"
          :disabled="!current.spec"
          :title="current.spec ? t('Dashboards.publish.title') : t('Dashboards.publish.needsSpec')"
          @click="showPublish = !showPublish"
        >
          <i class="bi bi-broadcast"></i> {{ current.published ? t('Dashboards.published') : t('Dashboards.publish.button') }}
        </button>
      </header>

      <!-- Publishing: the path other users open it at -->
      <form v-if="current && showPublish && publishable" class="boards-publish" @submit.prevent="publish">
        <p>{{ t('Dashboards.publish.help') }}</p>
        <div class="boards-publish-row">
          <label class="boards-path" :title="t('Dashboards.publish.pathHelp')">
            <span>{{ publishedUrl('') }}</span>
            <input v-model="path" :placeholder="'iris/flower_analysis'" :aria-label="t('Dashboards.publish.path')" spellcheck="false">
          </label>
          <button type="submit" class="btn btn-sm btn-primary" :disabled="!path.trim() || publishing || !current.spec || Boolean(broken)">
            {{ current.published ? t('Dashboards.publish.update') : t('Dashboards.publish.publish') }}
          </button>
          <template v-if="current.published">
            <a class="btn btn-sm btn-outline-primary" :href="publishedUrl(current.published.path)" target="_blank" rel="noopener">
              <i class="bi bi-box-arrow-up-right"></i> {{ t('Dashboards.publish.open') }}
            </a>
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="copyLink">
              <i :class="copied ? 'bi bi-check2' : 'bi bi-link-45deg'"></i> {{ copied ? t('Dashboards.publish.copied') : t('Dashboards.publish.copy') }}
            </button>
            <button type="button" class="btn btn-sm btn-danger" :disabled="publishing" @click="unpublish">{{ t('Dashboards.publish.unpublish') }}</button>
          </template>
        </div>
        <p v-if="publishError" class="boards-publish-note text-danger">{{ t('Dashboards.publish.error', { detail: publishError }) }}</p>
        <p v-else-if="current.published" class="boards-publish-note">
          {{ pendingChanges ? t('Dashboards.publish.pending') : t('Dashboards.publish.upToDate') }}
        </p>
        <p v-else class="boards-publish-note">{{ t('Dashboards.publish.pathHelp') }}</p>
      </form>

      <!-- DuckDB in the browser: the user's own OpenAI key -->
      <div v-if="ownKey" class="boards-key">
        <AiKeySettings @change="ready = aiReady()" />
      </div>

      <div class="boards-body">
        <div v-if="broken" class="boards-broken">
          <p><i class="bi bi-exclamation-triangle"></i> {{ t('Dashboards.broken', { detail: broken }) }}</p>
          <p>{{ t('Dashboards.brokenHint', { database: current.database || '–' }) }}</p>
        </div>
        <DashboardView v-else-if="current?.spec" :spec="current.spec" :source="source" editable @change="changeWidget" @remove="removeWidget" />
        <div v-else class="boards-empty">
          <span class="boards-empty-icon"><i class="bi bi-columns-gap"></i></span>
          <h3>{{ t('Dashboards.emptyTitle') }}</h3>
          <p>{{ t('Dashboards.emptyHint') }}</p>
          <div v-if="suggestions.length" class="boards-suggestions">
            <button v-for="suggestion in suggestions" :key="suggestion" type="button" class="boards-suggestion" :disabled="!ready || busy" @click="build(suggestion)">
              <i class="bi bi-arrow-return-right"></i>{{ suggestion }}
            </button>
          </div>
          <p v-else class="boards-empty-note">{{ t('Dashboards.noTables') }}</p>
        </div>
      </div>

      <footer class="boards-composer-wrap">
        <!-- The last instruction and what the assistant did with it -->
        <div v-if="status || lastExchange.length" class="boards-log">
          <p v-for="(entry, index) in lastExchange" :key="index" :class="`from-${entry.role}`">
            <i :class="entry.role === 'user' ? 'bi bi-person' : entry.error ? 'bi bi-exclamation-triangle' : 'bi bi-stars'"></i>
            <span :class="{ 'text-danger': entry.error }">{{ entry.text }}</span>
          </p>
          <p v-if="status" class="boards-status"><span class="boards-dots"><i></i><i></i><i></i></span>{{ t(`Dashboards.${status}`) }}</p>
        </div>
        <form class="boards-composer" @submit.prevent="build(draft)">
          <textarea
            ref="input"
            v-model="draft"
            rows="1"
            :placeholder="!ready ? t('Dashboards.needsKey') : current?.spec ? t('Dashboards.placeholderChange') : t('Dashboards.placeholderNew')"
            :disabled="!ready"
            :aria-label="t('Dashboards.send')"
            @keydown.enter.exact.prevent="build(draft)"
          ></textarea>
          <button type="submit" class="boards-send" :disabled="!draft.trim() || busy || !ready" :title="t('Dashboards.send')" :aria-label="t('Dashboards.send')">
            <i class="bi bi-arrow-up"></i>
          </button>
        </form>
        <p class="boards-disclaimer">{{ t('Dashboards.privacy') }}</p>
      </footer>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { toast } from 'vue3-toastify';
import { currentLanguage } from '../i18n';
import { useEngine } from '../engine';
import { aiReady, buildDashboard, usesOwnKey } from '../ai';
import { publishedQueries } from '../dashboards/compile';
import { engineSource } from '../dashboards/source';
import { aiSpec, validateDashboard } from '../dashboards/spec';
import {
  canPublish, deleteDashboard, getDashboard, listDashboards, listPublished, publishDashboard, publishedUrl,
  saveDashboard, unpublishDashboard,
} from '../lib/dashboards';
import AiKeySettings from './AiKeySettings.vue';
import DashboardView from './DashboardView.vue';

const props = defineProps({
  tables: { type: Array, default: () => [] },
  username: { type: String, default: '' },
});

const { t } = useI18n();
const engine = useEngine();
// With DuckDB in the browser the assistant uses the user's own OpenAI key, and nothing can be published
const ownKey = usesOwnKey();
const publishable = canPublish();
const ready = ref(aiReady());
// Instructions and answers kept with each dashboard
const HISTORY_LIMIT = 60;

const dashboards = ref([]);
const shared = ref([]);
const listError = ref(false);
// The open dashboard: { id, title, database, updated, published, spec, history, saved }. spec is null until it is built.
const current = ref(null);
// Why the open dashboard can't be drawn on this database
const broken = ref('');
const draft = ref('');
const busy = ref(false);
const status = ref(null);
const saving = ref(false);
const saveError = ref('');
const deletingId = ref(null);
const showPublish = ref(false);
const path = ref('');
const publishing = ref(false);
const publishError = ref('');
const copied = ref(false);
const input = ref(null);

const source = computed(() => engineSource(engine, current.value.spec));
const lastExchange = computed(() => {
  const history = current.value?.history || [];
  const start = history.map((entry) => entry.role).lastIndexOf('user');
  return start < 0 ? [] : history.slice(start);
});
const pendingChanges = computed(() => {
  const dashboard = current.value;
  return Boolean(dashboard?.published) && dashboard.updated > dashboard.published.updated + 1;
});
const suggestions = computed(() => {
  const table = props.tables.find((name) => !name.startsWith('__'));
  if (!table) return [];
  return ['overview', 'breakdown', 'trends'].map((key) => t(`Dashboards.suggestions.${key}`, { table }));
});

onMounted(loadLists);

async function loadLists() {
  try {
    dashboards.value = await listDashboards();
    listError.value = false;
  } catch {
    listError.value = true;
  }
  if (!publishable) return;
  try {
    shared.value = (await listPublished()).filter((dashboard) => dashboard.owner !== (props.username || 'default'));
  } catch { /* the user's own dashboards still work */ }
}

// crypto.randomUUID needs a secure context: the app may be served over plain HTTP
function newId() {
  return `d${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
}

function newDashboard() {
  current.value = null;
  broken.value = '';
  draft.value = '';
  showPublish.value = false;
  input.value?.focus();
}

async function openDashboard(summary) {
  if (busy.value || summary.id === current.value?.id) return;
  try {
    const dashboard = await getDashboard(summary.id);
    // Against the database as it is now: its tables may have changed since
    const { spec, errors } = await validateDashboard(engine, dashboard.spec);
    current.value = { ...dashboard, spec, history: dashboard.history || [], saved: true };
    broken.value = errors.join('; ');
    path.value = dashboard.published?.path || '';
    showPublish.value = false;
    publishError.value = '';
    saveError.value = '';
    listError.value = false;
  } catch {
    listError.value = true;
  }
}

// One instruction: the AI writes the specification (a new dashboard, or the open one changed), the app
// checks it against the data and, if it is valid, shows and saves it
async function build(text) {
  const instruction = String(text || '').trim();
  if (!instruction || busy.value || !ready.value) return;
  draft.value = '';
  busy.value = true;
  status.value = 'building';
  if (!current.value) {
    current.value = { id: newId(), title: '', database: null, published: null, spec: null, history: [], saved: false };
  }
  const dashboard = current.value;
  const history = dashboard.history;
  history.push({ role: 'user', text: instruction });
  try {
    const { spec, summary } = await buildDashboard({
      instruction,
      current: dashboard.spec ? aiSpec(dashboard.spec) : null,
      language: currentLanguage(),
      validate: async (raw) => {
        status.value = 'checking';
        const checked = await validateDashboard(engine, raw);
        status.value = 'building';
        return checked;
      },
    });
    // The AI names it, unless the user already did
    if (!dashboard.title || dashboard.title === dashboard.spec?.title) dashboard.title = spec.title;
    dashboard.spec = spec;
    broken.value = '';
    history.push({ role: 'assistant', text: summary || spec.title });
  } catch (error) {
    history.push({ role: 'assistant', text: t('Dashboards.buildFailed', { detail: error?.message || String(error) }), error: true });
  } finally {
    history.splice(0, Math.max(0, history.length - HISTORY_LIMIT));
    status.value = null;
    busy.value = false;
  }
  if (dashboard.spec) await save();
}

async function save() {
  const dashboard = current.value;
  if (!dashboard?.spec) return;
  saving.value = true;
  try {
    const title = dashboard.title.trim() || dashboard.spec.title || t('Dashboards.untitled');
    const saved = await saveDashboard(dashboard.id, { title, spec: dashboard.spec, history: dashboard.history });
    Object.assign(dashboard, saved, { saved: true });
    // The most recent goes first
    dashboards.value = [saved, ...dashboards.value.filter((d) => d.id !== saved.id)];
    saveError.value = '';
  } catch (error) {
    saveError.value = error.message;
  } finally {
    saving.value = false;
  }
}

function changeWidget(widget, changes) {
  Object.assign(widget, changes);
  save();
}

function removeWidget(widget) {
  const widgets = current.value.spec.widgets;
  widgets.splice(widgets.indexOf(widget), 1);
  save();
}

async function removeDashboard(dashboard) {
  deletingId.value = null;
  try {
    await deleteDashboard(dashboard.id);
    dashboards.value = dashboards.value.filter((d) => d.id !== dashboard.id);
    if (dashboard.id === current.value?.id) newDashboard();
  } catch (error) {
    toast.error(t('Dashboards.deleteError', { detail: error.message }));
  }
}

async function publish() {
  const dashboard = current.value;
  publishing.value = true;
  publishError.value = '';
  try {
    // What is published is the saved dashboard
    await save();
    if (saveError.value) throw new Error(saveError.value);
    const saved = await publishDashboard(dashboard.id, path.value, publishedQueries(dashboard.spec));
    Object.assign(dashboard, saved);
    path.value = saved.published.path;
    dashboards.value = dashboards.value.map((d) => (d.id === saved.id ? saved : d));
    toast.success(t('Dashboards.publish.done', { path: saved.published.path }));
  } catch (error) {
    publishError.value = error.message;
  } finally {
    publishing.value = false;
  }
}

async function unpublish() {
  const dashboard = current.value;
  publishing.value = true;
  publishError.value = '';
  try {
    const saved = await unpublishDashboard(dashboard.id);
    Object.assign(dashboard, saved);
    dashboards.value = dashboards.value.map((d) => (d.id === saved.id ? saved : d));
    toast.success(t('Dashboards.publish.undone'));
  } catch (error) {
    publishError.value = error.message;
  } finally {
    publishing.value = false;
  }
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(publishedUrl(current.value.published.path));
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 1500);
  } catch { /* clipboard blocked */ }
}
</script>

<style scoped>
.boards {
  display: flex; height: calc(100vh - 130px); min-height: 520px; overflow: hidden;
  background: var(--ds-surface); border: 1px solid var(--ds-line); border-radius: 16px; box-shadow: var(--ds-shadow);
}
.boards-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }

.boards-list {
  flex: none; width: 240px; display: flex; flex-direction: column; gap: 10px; padding: 12px 10px;
  border-right: 1px solid var(--ds-line); background: var(--ds-surface-muted);
}
.boards-new {
  display: flex; align-items: center; gap: 8px; padding: 9px 12px; border: 1px solid var(--ds-line); border-radius: 10px;
  background: #fff; font-size: 13px; font-weight: 650; color: var(--ds-ink); transition: border-color .15s, box-shadow .15s;
}
.boards-new i { color: var(--ds-teal); }
.boards-new:hover:not(:disabled) { border-color: #9fd3c3; box-shadow: 0 4px 12px rgba(28, 58, 51, .07); }
.boards-new:disabled { opacity: .5; cursor: not-allowed; }
.boards-nav { flex: 1; overflow-y: auto; margin: 0 -4px; padding: 0 4px; }
.boards-nav h4 { margin: 12px 8px 4px; font-size: 10.5px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--ds-muted); }
.boards-nav h4:first-child { margin-top: 2px; }
.boards-note { margin: 8px; font-size: 12px; color: var(--ds-muted); }
.boards-item { display: flex; align-items: center; gap: 2px; min-height: 34px; padding-right: 4px; border-radius: 8px; }
.boards-item:hover, .boards-item:focus-within { background: #e6efec; }
.boards-item.is-active { background: var(--ds-mint); }
.boards-item.is-active .boards-open { color: var(--ds-teal-dark); font-weight: 650; }
.boards-open {
  flex: 1; min-width: 0; padding: 7px 4px 7px 10px; border: 0; background: transparent; text-align: left;
  font-size: 12.5px; color: var(--ds-ink-soft); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.boards-open i { margin-right: 4px; color: var(--ds-teal); }
.boards-open:disabled { cursor: not-allowed; opacity: .6; }
.boards-action {
  display: none; width: 26px; height: 26px; align-items: center; justify-content: center; border: 0; border-radius: 6px;
  background: transparent; color: var(--ds-muted); font-size: 12px;
}
.boards-item:hover .boards-action, .boards-item:focus-within .boards-action, .boards-confirm ~ .boards-action { display: inline-flex; }
.boards-action:hover:not(:disabled) { background: #fff; color: var(--ds-ink); }
.boards-action.is-danger:hover { color: #b3263a; }
.boards-confirm { flex: 1; padding-left: 10px; font-size: 12px; font-weight: 600; color: #a9404d; }
.boards-shared { display: flex; flex-direction: column; padding: 6px 10px; border-radius: 8px; font-size: 12.5px; color: var(--ds-ink-soft); }
.boards-shared:hover { background: #e6efec; }
.boards-shared span, .boards-shared small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.boards-shared small { color: var(--ds-muted); font-size: 11px; }

.boards-bar {
  display: flex; align-items: center; gap: 12px; padding: 10px 20px; border-bottom: 1px solid var(--ds-line);
  background: linear-gradient(180deg, #fff, var(--ds-surface-muted));
}
.boards-title {
  flex: 1; min-width: 0; padding: 4px 8px; border: 1px solid transparent; border-radius: 8px; background: transparent;
  font-size: 15px; font-weight: 700; color: var(--ds-ink);
}
.boards-title:hover { border-color: var(--ds-line); }
.boards-title:focus { outline: 0; border-color: var(--ds-teal); background: #fff; }
.boards-state, .boards-local { flex: none; font-size: 11.5px; color: var(--ds-muted); }
.boards-local { padding: 4px 10px; border-radius: 999px; background: var(--ds-mint); color: var(--ds-teal-dark); font-weight: 600; }
.boards-chip {
  flex: none; display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border: 1px solid var(--ds-line);
  border-radius: 999px; background: #fff; font-size: 12px; font-weight: 600; color: var(--ds-ink-soft);
}
.boards-chip:hover:not(:disabled) { border-color: #b9ded2; background: var(--ds-surface-muted); }
.boards-chip.is-on { background: var(--ds-mint); border-color: #9fd3c3; color: var(--ds-teal-dark); }
.boards-chip:disabled { opacity: .45; cursor: not-allowed; }

.boards-publish { padding: 12px 20px; border-bottom: 1px solid var(--ds-line); background: var(--ds-surface-muted); font-size: 12.5px; }
.boards-publish p { margin: 0 0 8px; color: var(--ds-ink-soft); }
.boards-publish-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.boards-path {
  flex: 1; min-width: 280px; display: flex; align-items: center; margin: 0; border: 1px solid var(--ds-line); border-radius: 8px;
  background: #fff; overflow: hidden;
}
.boards-path:focus-within { border-color: var(--ds-teal); }
.boards-path span { padding: 5px 0 5px 10px; color: var(--ds-muted); white-space: nowrap; }
.boards-path input { flex: 1; min-width: 120px; padding: 5px 10px 5px 0; border: 0; outline: 0; font-size: 12.5px; font-weight: 600; color: var(--ds-ink); }
.boards-publish-note { margin: 8px 0 0 !important; font-size: 11.5px; color: var(--ds-muted) !important; }
.boards-publish-note.text-danger { color: #a9404d !important; }

.boards-key { padding: 12px 20px 0; background: var(--ds-canvas); }
.boards-body { flex: 1; overflow-y: auto; padding: 16px 20px; background: var(--ds-canvas); }
.boards-broken { padding: 12px 14px; border: 1px solid #efc9cd; border-radius: 12px; background: #fff4f5; color: #a9404d; font-size: 13px; }
.boards-broken p { margin: 0 0 4px; }
.boards-empty { text-align: center; padding: 48px 12px 24px; }
.boards-empty-icon {
  display: inline-flex; width: 56px; height: 56px; border-radius: 18px; align-items: center; justify-content: center;
  background: var(--ds-mint); color: var(--ds-teal); font-size: 1.5rem; margin-bottom: 14px;
}
.boards-empty h3 { font-size: 20px; font-weight: 750; color: var(--ds-ink); margin: 0 0 6px; }
.boards-empty p { font-size: 13px; color: var(--ds-muted); margin: 0 auto; max-width: 520px; }
.boards-empty-note { margin-top: 18px !important; }
.boards-suggestions { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; max-width: 860px; margin: 26px auto 0; text-align: left; }
.boards-suggestion {
  display: flex; align-items: flex-start; gap: 8px; padding: 12px 14px; border: 1px solid var(--ds-line); border-radius: 12px;
  background: #fff; font-size: 12.5px; color: var(--ds-ink-soft); text-align: left; transition: border-color .15s, box-shadow .15s;
}
.boards-suggestion i { color: var(--ds-teal); margin-top: 1px; }
.boards-suggestion:hover:not(:disabled) { border-color: #9fd3c3; box-shadow: 0 6px 18px rgba(28, 58, 51, .08); }
.boards-suggestion:disabled { opacity: .5; cursor: not-allowed; }

.boards-composer-wrap { padding: 10px 20px 12px; background: var(--ds-canvas); border-top: 1px solid var(--ds-line); }
.boards-log { max-width: 860px; margin: 0 auto 8px; font-size: 12.5px; color: var(--ds-ink-soft); }
.boards-log p { display: flex; gap: 8px; margin: 0 0 3px; }
.boards-log p i { flex: none; color: var(--ds-teal); }
.boards-log .from-user { color: var(--ds-muted); }
.boards-log .from-user span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.boards-status { align-items: center; color: var(--ds-muted); }
.boards-dots { display: inline-flex; gap: 4px; }
.boards-dots i { width: 6px; height: 6px; border-radius: 50%; background: var(--ds-teal); animation: boards-bounce 1.2s infinite ease-in-out; }
.boards-dots i:nth-child(2) { animation-delay: .15s; }
.boards-dots i:nth-child(3) { animation-delay: .3s; }
@keyframes boards-bounce { 0%, 80%, 100% { transform: translateY(0); opacity: .35; } 40% { transform: translateY(-4px); opacity: 1; } }
.boards-composer {
  max-width: 860px; margin: 0 auto; display: flex; align-items: flex-end; gap: 10px; padding: 8px 8px 8px 16px;
  background: #fff; border: 1px solid #cfe0da; border-radius: 18px; box-shadow: 0 8px 24px rgba(28, 58, 51, .08);
}
.boards-composer:focus-within { border-color: var(--ds-teal); box-shadow: 0 0 0 3px rgba(13, 132, 111, .12), 0 8px 24px rgba(28, 58, 51, .08); }
.boards-composer textarea {
  flex: 1; border: 0; outline: 0; resize: none; background: transparent; padding: 8px 0; font-size: 14px; line-height: 1.5;
  color: var(--ds-ink); max-height: 120px; field-sizing: content;
}
.boards-send {
  width: 36px; height: 36px; border-radius: 50%; border: 0; background: var(--ds-teal); color: #fff;
  display: inline-flex; align-items: center; justify-content: center; font-size: 1.05rem;
}
.boards-send:hover:not(:disabled) { background: var(--ds-teal-dark); }
.boards-send:disabled { opacity: .35; cursor: not-allowed; }
.boards-disclaimer { max-width: 860px; margin: 6px auto 0; text-align: center; font-size: 10.5px; color: var(--ds-muted); }

@media (max-width: 900px) {
  .boards-list { width: 190px; }
  .boards-bar { flex-wrap: wrap; }
}
</style>
