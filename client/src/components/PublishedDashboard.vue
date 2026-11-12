<template>
  <main class="published">
    <header class="published-bar">
      <img src="../assets/logo.svg" alt="" width="30" height="30">
      <div class="published-heading">
        <h1>{{ dashboard?.title || path }}</h1>
        <p v-if="dashboard">{{ t('PublishedDashboard.by', { owner: dashboard.owner }) }} · {{ path }}</p>
      </div>
      <a class="published-app" href="#/"><i class="bi bi-grid-1x2"></i> {{ t('PublishedDashboard.openApp') }}</a>
    </header>

    <div v-if="notFound" class="published-message">
      <h2>{{ t('PublishedDashboard.notFound', { path }) }}</h2>
      <p>{{ t('PublishedDashboard.notFoundHint') }}</p>
    </div>
    <p v-else-if="error" class="published-message text-danger">{{ t('PublishedDashboard.error', { detail: error }) }}</p>
    <p v-else-if="!dashboard" class="published-message">{{ t('PublishedDashboard.loading') }}</p>
    <DashboardView v-else :spec="dashboard.spec" :source="source" />
  </main>
</template>

<script setup>
import { onUnmounted, ref, shallowRef, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { publishedSource } from '../dashboards/source';
import { getPublished } from '../lib/dashboards';
import DashboardView from './DashboardView.vue';

// A dashboard another user published, opened by its path (#/d/iris/flower_analysis). Its rows come from
// the server, which runs the author's queries: this page only sends the values of the filters.
const props = defineProps({
  path: { type: String, required: true },
});
const { t } = useI18n();

const dashboard = ref(null);
const source = shallowRef(null);
const notFound = ref(false);
const error = ref('');
const appTitle = document.title;

onUnmounted(() => { document.title = appTitle; });
watch(() => props.path, load, { immediate: true });

async function load(path) {
  dashboard.value = null;
  notFound.value = false;
  error.value = '';
  try {
    const found = await getPublished(path);
    if (path !== props.path) return;
    source.value = publishedSource(found.path);
    dashboard.value = found;
    document.title = `${found.title} · Datalake Studio`;
  } catch (failure) {
    if (/not found|invalid path/i.test(failure.message)) notFound.value = true;
    else error.value = failure.message;
  }
}
</script>

<style scoped>
.published { max-width: 1400px; margin: 0 auto; display: flex; flex-direction: column; gap: 14px; }
.published-bar {
  display: flex; align-items: center; gap: 12px; padding: 10px 17px; border: 1px solid var(--ds-line); border-radius: 13px;
  background: rgba(255, 255, 255, .88); box-shadow: 0 8px 28px rgba(31, 67, 58, .045);
}
.published-heading { flex: 1; min-width: 0; }
.published-heading h1 { margin: 0; font-size: 1.05rem; font-weight: 750; letter-spacing: -.02em; color: var(--ds-ink); }
.published-heading p { margin: 0; font-size: 11.5px; color: var(--ds-muted); }
.published-app {
  flex: none; display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border: 1px solid var(--ds-line);
  border-radius: 999px; background: #fff; font-size: 12px; font-weight: 600; color: var(--ds-ink-soft);
}
.published-app:hover { border-color: #b9ded2; background: var(--ds-surface-muted); }
.published-message { padding: 56px 12px; text-align: center; color: var(--ds-muted); font-size: 13px; }
.published-message h2 { margin: 0 0 6px; font-size: 18px; font-weight: 750; color: var(--ds-ink); }
</style>
