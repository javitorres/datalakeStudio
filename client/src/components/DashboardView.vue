<template>
  <div class="dash">
    <!-- Filters: the controls of the dashboard, and the categories picked by clicking its charts -->
    <div v-if="spec.filters.length" class="dash-filters">
      <template v-for="filter in controls" :key="filter.id">
        <details v-if="filter.type === 'select'" class="dash-filter dash-select" :data-filter="filter.id">
          <summary :class="{ 'is-set': isSet(filter) }">
            <i class="bi bi-funnel"></i>{{ filter.label }}
            <span v-if="isSet(filter)" class="dash-count">{{ state[filter.id].length }}</span>
            <i class="bi bi-chevron-down dash-caret"></i>
          </summary>
          <div class="dash-options">
            <p v-if="!(info[filter.id] || []).length" class="dash-note">{{ t('DashboardView.noValues') }}</p>
            <label v-for="option in info[filter.id] || []" :key="option.value" class="dash-option">
              <input type="checkbox" :checked="(state[filter.id] || []).includes(option.value)" @change="toggle(filter, option.value)">
              <span class="dash-option-name" :title="option.value">{{ option.value }}</span>
              <span class="dash-option-count">{{ format(option.n) }}</span>
            </label>
          </div>
        </details>

        <div v-else class="dash-filter dash-range" :class="{ 'is-set': isSet(filter) }" :data-filter="filter.id">
          <span class="dash-range-label"><i class="bi bi-funnel"></i>{{ filter.label }}</span>
          <input
            v-for="(side, index) in ['min', 'max']"
            :key="side"
            :type="filter.type === 'range' ? 'number' : 'date'"
            :value="(state[filter.id] || [])[index] ?? ''"
            :placeholder="placeholder(filter, side)"
            :min="filter.type === 'dateRange' ? info[filter.id]?.min : undefined"
            :max="filter.type === 'dateRange' ? info[filter.id]?.max : undefined"
            :aria-label="`${filter.label}: ${t(`DashboardView.${side}`)}`"
            step="any"
            @change="setBound(filter, index, $event.target.value)"
          >
        </div>
      </template>

      <button
        v-for="filter in clicked"
        :key="filter.id"
        type="button"
        class="dash-chip"
        :title="t('DashboardView.removeFilter')"
        @click="clear(filter)"
      >
        {{ filter.label }}: {{ state[filter.id].join(', ') }} <i class="bi bi-x-lg"></i>
      </button>
      <button v-if="anySet" type="button" class="dash-clear" @click="clearAll">
        <i class="bi bi-x-circle"></i> {{ t('DashboardView.clearFilters') }}
      </button>
    </div>

    <div class="dash-grid">
      <section
        v-for="widget in spec.widgets"
        :key="widget.id"
        class="dash-widget"
        :class="[`is-${widget.type}`, `span-${widget.width}`]"
        :data-widget="widget.id"
      >
        <header v-if="widget.title || editable" class="dash-widget-head">
          <h3>{{ widget.title }}</h3>
          <div v-if="editable" class="dash-tools">
            <template v-if="CHART_WIDGETS.includes(widget.type)">
              <button
                v-for="type in chartTypes"
                :key="type.id"
                type="button"
                class="dash-tool"
                :class="{ 'is-on': widget.type === type.id }"
                :title="t(`ChatGptAgent.chart.types.${type.id}`)"
                @click="emit('change', widget, { type: type.id })"
              >
                <i :class="type.icon"></i>
              </button>
            </template>
            <select
              class="dash-width"
              :value="widget.width"
              :title="t('DashboardView.width')"
              :aria-label="t('DashboardView.width')"
              @change="emit('change', widget, { width: Number($event.target.value) })"
            >
              <option v-for="width in WIDTHS" :key="width" :value="width">{{ width }}/12</option>
            </select>
            <button type="button" class="dash-tool is-danger" :title="t('DashboardView.removeWidget')" @click="emit('remove', widget)">
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </header>

        <!-- eslint-disable-next-line vue/no-v-html -- renderMarkdown escapes the text first -->
        <div v-if="widget.type === 'text'" class="dash-text" v-html="renderMarkdown(widget.text || '')"></div>

        <p v-else-if="data[widget.id]?.error" class="dash-error">
          <i class="bi bi-exclamation-triangle"></i> {{ data[widget.id].error }}
        </p>
        <p v-else-if="!data[widget.id]?.rows" class="dash-note dash-loading">{{ t('DashboardView.loading') }}</p>

        <div v-else-if="widget.type === 'kpi'" class="dash-kpis">
          <div v-for="(measure, index) in widget.measures" :key="index" class="dash-kpi">
            <span class="dash-kpi-value">{{ format(data[widget.id].rows[0]?.[`m${index}`], true) }}</span>
            <span class="dash-kpi-label">{{ measureLabel(measure) }}</span>
          </div>
        </div>

        <div v-else-if="widget.type === 'table'" class="dash-table">
          <table>
            <thead><tr><th v-for="column in tableColumns(widget)" :key="column">{{ column }}</th></tr></thead>
            <tbody>
              <tr v-for="(row, r) in data[widget.id].rows" :key="r">
                <td v-for="column in tableColumns(widget)" :key="column">{{ cell(row[column]) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-else-if="!data[widget.id].rows.length" class="dash-note">{{ t('DashboardView.noData') }}</p>
        <v-chart
          v-else
          class="dash-chart"
          :class="{ 'is-clickable': clickFilter(widget) }"
          :option="option(widget)"
          autoresize
          @click="chartClick(widget, $event)"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, reactive, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { BarChart, LineChart, PieChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { CHART_TYPES, chartOption } from '../lib/charts';
import { renderMarkdown } from '../lib/markdown';
import { CHART_WIDGETS, CLICKABLE_WIDGETS, measureLabel, WIDTHS } from '../dashboards/spec';

use([BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

// Draws a dashboard specification. Its rows come from `source` (see dashboards/source.js): the user's
// engine, or the server for a published dashboard. With `editable`, each widget has its tools.
const props = defineProps({
  spec: { type: Object, required: true },
  source: { type: Object, required: true },
  editable: { type: Boolean, default: false },
});
const emit = defineEmits(['change', 'remove']);
const { t, locale } = useI18n();

const chartTypes = CHART_TYPES.filter((type) => CHART_WIDGETS.includes(type.id));
// The values of the filters ({ filter id: value }), what each control offers and the rows of each widget
const state = reactive({});
const info = reactive({});
const data = reactive({});
// Only the answers to the latest request of each widget are kept
const requests = {};
const loadedFilters = ref('');
let reloadTimer = null;

const controls = computed(() => props.spec.filters.filter((filter) => !filter.implicit));
const clicked = computed(() => props.spec.filters.filter((filter) => filter.implicit && isSet(filter)));
const anySet = computed(() => props.spec.filters.some(isSet));

function isSet(filter) {
  const value = state[filter.id];
  return Array.isArray(value) && value.some((v) => v !== null && v !== '');
}

// What makes a widget's rows: a change to anything else (its title, its width) redraws it without
// asking for them again
function queryKey(widget) {
  const { title, width, text, ...query } = widget; // eslint-disable-line no-unused-vars
  return JSON.stringify(query);
}
const dataKey = computed(() => JSON.stringify([props.spec.datasets, props.spec.filters, props.spec.widgets.map(queryKey)]));
const loadedWidgets = {};

watch([dataKey, () => props.source], () => {
  for (const id of Object.keys(state)) {
    if (!props.spec.filters.some((filter) => filter.id === id)) delete state[id];
  }
  // Rows of another widget, or of this one before it changed, are not shown meanwhile
  for (const widget of props.spec.widgets) {
    const key = JSON.stringify(props.spec.datasets) + queryKey(widget);
    if (loadedWidgets[widget.id] !== key) delete data[widget.id];
    loadedWidgets[widget.id] = key;
  }
  loadFilters();
  loadWidgets();
}, { immediate: true });

onUnmounted(() => clearTimeout(reloadTimer));

function message(error) {
  return error?.message || String(error);
}

async function loadFilters() {
  const key = JSON.stringify([props.spec.datasets, controls.value]);
  if (key === loadedFilters.value) return;
  loadedFilters.value = key;
  await Promise.all(controls.value.map(async (filter) => {
    try {
      const rows = await props.source.filter(filter);
      info[filter.id] = filter.type === 'select' ? rows.map((row) => ({ value: String(row.value), n: row.n })) : rows[0] || {};
    } catch {
      // The control still works without its values
      info[filter.id] = filter.type === 'select' ? [] : {};
    }
  }));
}

function loadWidgets() {
  const filters = JSON.parse(JSON.stringify(state));
  return Promise.all(props.spec.widgets.filter((widget) => widget.type !== 'text').map(async (widget) => {
    const request = requests[widget.id] = (requests[widget.id] || 0) + 1;
    try {
      const rows = await props.source.widget(widget, filters);
      if (requests[widget.id] === request) data[widget.id] = { rows };
    } catch (error) {
      if (requests[widget.id] === request) data[widget.id] = { error: message(error) };
    }
  }));
}

// Typing a range sends one request, not one per key
function filtersChanged() {
  clearTimeout(reloadTimer);
  reloadTimer = setTimeout(loadWidgets, 200);
}

function toggle(filter, value) {
  const chosen = state[filter.id] || [];
  state[filter.id] = chosen.includes(value) ? chosen.filter((v) => v !== value) : [...chosen, value];
  filtersChanged();
}

function setBound(filter, index, value) {
  const bounds = [...(state[filter.id] || [null, null])];
  bounds[index] = value === '' ? null : filter.type === 'range' ? Number(value) : value;
  state[filter.id] = bounds;
  filtersChanged();
}

function clear(filter) {
  delete state[filter.id];
  filtersChanged();
}

function clearAll() {
  for (const id of Object.keys(state)) delete state[id];
  filtersChanged();
}

function placeholder(filter, side) {
  const value = info[filter.id]?.[side];
  return value == null ? t(`DashboardView.${side}`) : filter.type === 'range' ? format(value) : value;
}

// The filter a click on this chart sets: the one on its dimension
function clickFilter(widget) {
  if (!CLICKABLE_WIDGETS.includes(widget.type)) return null;
  return props.spec.filters.find((filter) => filter.type === 'select' && filter.column === widget.dimension) || null;
}

function chartClick(widget, event) {
  const filter = clickFilter(widget);
  const value = event?.name;
  // The slice that adds up the smallest ones is not a category
  if (!filter || value == null || value === t('ChatGptAgent.chart.others')) return;
  toggle(filter, String(value));
}

function format(value, compact = false) {
  if (value === null || value === undefined || value === '') return '–';
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  return new Intl.NumberFormat(locale.value, compact && Math.abs(number) >= 100000
    ? { notation: 'compact', maximumFractionDigits: 1 } : { maximumFractionDigits: 2 }).format(number);
}

function cell(value) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'number') return format(value);
  return typeof value === 'object' ? JSON.stringify(value) : String(value);
}

function tableColumns(widget) {
  const rows = data[widget.id].rows;
  return rows.length ? Object.keys(rows[0]) : widget.columns || [];
}

function option(widget) {
  const rows = data[widget.id].rows;
  if (widget.type === 'histogram') {
    const result = { columns: ['x', widget.dimension], rows: rows.map((row) => [format(row.x0), row.m0]) };
    const histogram = chartOption({ type: 'bar', x: 'x', y: [widget.dimension] }, result);
    histogram.series[0].barCategoryGap = '4%';
    histogram.tooltip.formatter = (items) => {
      const row = rows[items[0].dataIndex];
      return `${format(row.x0)} – ${format(row.x1)}<br>${format(row.m0)}`;
    };
    return histogram;
  }
  const labels = widget.measures.map(measureLabel);
  const result = { columns: ['x', ...labels], rows: rows.map((row) => [row.x ?? '', ...labels.map((_, i) => row[`m${i}`])]) };
  const chart = chartOption({ type: widget.type, x: 'x', y: labels }, result, { others: t('ChatGptAgent.chart.others') });
  // The categories picked on this chart stand out from the rest
  const filter = clickFilter(widget);
  if (filter && isSet(filter)) {
    const chosen = state[filter.id];
    const dim = (name) => (chosen.includes(String(name)) ? 1 : 0.3);
    for (const series of chart.series) {
      series.data = series.type === 'pie'
        ? series.data.map((slice) => ({ ...slice, itemStyle: { opacity: dim(slice.name) } }))
        : series.data.map((value, index) => ({ value, itemStyle: { opacity: dim(result.rows[index][0]) } }));
    }
  }
  return chart;
}
</script>

<style scoped>
.dash { display: flex; flex-direction: column; gap: 14px; }

.dash-filters { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.dash-filter { position: relative; font-size: 12.5px; }
.dash-select summary, .dash-range {
  display: inline-flex; align-items: center; gap: 7px; min-height: 34px; padding: 5px 11px;
  border: 1px solid var(--ds-line); border-radius: 10px; background: #fff; color: var(--ds-ink-soft);
}
.dash-select summary { cursor: pointer; list-style: none; font-weight: 600; }
.dash-select summary::-webkit-details-marker { display: none; }
.dash-select summary i:first-child, .dash-range-label i { color: var(--ds-teal); }
.dash-select summary.is-set, .dash-range.is-set { border-color: #9fd3c3; background: var(--ds-mint); color: var(--ds-teal-dark); }
.dash-caret { font-size: 10px; opacity: .6; }
.dash-count { padding: 0 6px; border-radius: 999px; background: var(--ds-teal); color: #fff; font-size: 11px; font-weight: 700; }
.dash-options {
  position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; width: 240px; max-height: 280px; overflow-y: auto;
  padding: 6px; border: 1px solid var(--ds-line); border-radius: 10px; background: #fff; box-shadow: var(--ds-shadow);
}
.dash-option { display: flex; align-items: center; gap: 8px; margin: 0; padding: 5px 7px; border-radius: 7px; cursor: pointer; }
.dash-option:hover { background: var(--ds-surface-muted); }
.dash-option-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--ds-ink); }
.dash-option-count { color: var(--ds-muted); font-size: 11px; font-variant-numeric: tabular-nums; }
.dash-range-label { display: inline-flex; align-items: center; gap: 7px; font-weight: 600; }
.dash-range input {
  width: 96px; padding: 2px 6px; border: 1px solid var(--ds-line); border-radius: 6px; background: #fff;
  font-size: 12px; color: var(--ds-ink);
}
.dash-range input[type="date"] { width: 128px; }
.dash-range input:focus { outline: 0; border-color: var(--ds-teal); }
.dash-chip, .dash-clear {
  display: inline-flex; align-items: center; gap: 6px; min-height: 30px; padding: 4px 11px; border-radius: 999px;
  font-size: 12px; font-weight: 600;
}
.dash-chip { border: 1px solid #9fd3c3; background: var(--ds-mint); color: var(--ds-teal-dark); }
.dash-chip i { font-size: 9px; }
.dash-clear { border: 0; background: transparent; color: var(--ds-muted); }
.dash-clear:hover { color: var(--ds-ink); }

.dash-grid { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 12px; }
.dash-widget {
  grid-column: span 6; min-width: 0; display: flex; flex-direction: column; gap: 8px; padding: 12px 14px;
  border: 1px solid var(--ds-line); border-radius: 12px; background: #fff;
}
.dash-widget.span-3 { grid-column: span 3; }
.dash-widget.span-4 { grid-column: span 4; }
.dash-widget.span-8 { grid-column: span 8; }
.dash-widget.span-12 { grid-column: span 12; }
.dash-widget-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 24px; }
.dash-widget-head h3 { margin: 0; min-width: 0; font-size: 13px; font-weight: 700; color: var(--ds-ink); }
.dash-tools { display: flex; align-items: center; gap: 2px; opacity: 0; transition: opacity .15s; }
.dash-widget:hover .dash-tools, .dash-widget:focus-within .dash-tools { opacity: 1; }
.dash-tool {
  width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; border: 0; border-radius: 6px;
  background: transparent; color: var(--ds-muted); font-size: 12.5px;
}
.dash-tool:hover { background: var(--ds-mint); color: var(--ds-teal-dark); }
.dash-tool.is-on { background: var(--ds-surface-muted); color: var(--ds-teal-dark); }
.dash-tool.is-danger:hover { background: #fff4f5; color: #b3263a; }
.dash-width { height: 26px; margin: 0 2px; padding: 0 4px; border: 1px solid var(--ds-line); border-radius: 6px; background: #fff; font-size: 11px; color: var(--ds-ink-soft); }

.dash-kpis { display: flex; flex-wrap: wrap; gap: 6px 22px; }
.dash-kpi { display: flex; flex-direction: column; min-width: 0; }
.dash-kpi-value { font-size: 26px; font-weight: 750; line-height: 1.15; letter-spacing: -.02em; color: var(--ds-ink); font-variant-numeric: tabular-nums; }
.dash-kpi-label { font-size: 12px; color: var(--ds-muted); }
.dash-chart { width: 100%; height: 280px; }
.dash-chart.is-clickable { cursor: pointer; }
.dash-table { max-height: 320px; overflow: auto; border: 1px solid var(--ds-line); border-radius: 8px; }
.dash-table table { width: 100%; border-collapse: collapse; font-size: 12px; }
.dash-table th {
  position: sticky; top: 0; padding: 6px 10px; border-bottom: 1px solid var(--ds-line); background: var(--ds-surface-muted);
  color: var(--ds-muted); font-weight: 700; text-align: left; white-space: nowrap;
}
.dash-table td { padding: 5px 10px; border-bottom: 1px solid #eef3f1; color: var(--ds-ink); white-space: nowrap; }
.dash-text { font-size: 13.5px; line-height: 1.6; color: var(--ds-ink); }
.dash-text :deep(p) { margin: 0 0 6px; }
.dash-text :deep(p:last-child) { margin-bottom: 0; }
.dash-text :deep(ul), .dash-text :deep(ol) { margin: 0 0 6px; padding-left: 20px; }
.dash-note { margin: 0; font-size: 12px; color: var(--ds-muted); }
.dash-loading { padding: 18px 0; }
.dash-error { margin: 0; padding: 8px 10px; border: 1px solid #efc9cd; border-radius: 8px; background: #fff4f5; color: #a9404d; font-size: 12px; }

@media (max-width: 900px) {
  .dash-widget, .dash-widget.span-3, .dash-widget.span-4, .dash-widget.span-8 { grid-column: span 12; }
  .dash-widget.span-3 { grid-column: span 6; }
}
</style>
