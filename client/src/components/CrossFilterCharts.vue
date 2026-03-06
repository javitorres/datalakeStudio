<template>
  <div class="crossfilter-container">
    <div class="charts-grid">
      <div v-for="field in numericFields" :key="field" class="chart-wrapper">
        <button class="close-btn" title="Remove field" @click="removeField(field)">✕</button>
        <v-chart
          :ref="el => setChartRef(field, el)"
          :option="chartOptions[field]"
          :autoresize="true"
          class="chart"
          @brush="e => onBrush(field, e)"
          @brushEnd="e => onBrushEnd(field, e)"
          @datazoom="e => onDataZoom(field, e)"
        />
      </div>
      <div v-for="field in categoricalFields" :key="field" class="chart-wrapper">
        <button class="close-btn" title="Remove field" @click="removeField(field)">✕</button>
        <v-chart
          :ref="el => setChartRef(field, el)"
          :option="chartOptions[field]"
          :autoresize="true"
          class="chart"
          @click="e => onCategoryClick(field, e)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { BarChart, PieChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  BrushComponent,
  ToolboxComponent,
  LegendComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import axios from 'axios';
import { API_HOST, API_PORT } from '../../config';

use([
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  BrushComponent,
  ToolboxComponent,
  LegendComponent,
  CanvasRenderer,
]);

const apiUrl = `${API_HOST}:${API_PORT}`;

const props = defineProps({
  table: String,
  selectedFields: Array,
  schema: Object,
});

const emit = defineEmits(['removeField']);

const chartOptions = ref({});
const chartRefs = {};
const fullData = ref({});
const brushFilters = ref({});
const numericFields = ref([]);
const categoricalFields = ref([]);
const zoomRanges = ref({});
const fieldRanges = ref({});
const HISTOGRAM_BINS = 30;

function removeField(field) {
  emit('removeField', field);
}

function setChartRef(field, el) {
  if (el) chartRefs[field] = el;
}

function classifyFields() {
  if (!props.selectedFields || !props.schema) return;
  const numeric = [];
  const categorical = [];
  for (const field of props.selectedFields) {
    const type = props.schema[field];
    if (!type) continue;
    if (type.startsWith('int') || type.startsWith('float') || type === 'double' || type === 'bigint') {
      numeric.push(field);
    } else if (type === 'varchar' || type === 'string' || type === 'object') {
      categorical.push(field);
    }
  }
  numericFields.value = numeric;
  categoricalFields.value = categorical;
}

async function fetchInitialRange(field) {
  const sql = `
    SELECT
      approx_quantile("${field}", 0.02) AS mn,
      approx_quantile("${field}", 0.98) AS mx
    FROM "${props.table}"
  `;
  const res = await axios.post(`${apiUrl}/database/restConnector`, { type: 'json', sql });
  const row = res.data[0];
  const mn = Number(row.mn);
  const mx = Number(row.mx);
  fieldRanges.value[field] = { mn, mx };
  return { mn, mx };
}

async function fetchHistogram(field, excludeField) {
  let range = fieldRanges.value[field];
  if (!range) range = await fetchInitialRange(field);
  const { mn, mx } = range;
  if (mn >= mx) return [];

  const whereClause = buildWhereClause(excludeField);
  const sql = `
    WITH bins AS (
      SELECT
        ${mn} + (${mx} - ${mn}) * i / ${HISTOGRAM_BINS} AS bin_start,
        ${mn} + (${mx} - ${mn}) * (i + 1) / ${HISTOGRAM_BINS} AS bin_end
      FROM generate_series(0, ${HISTOGRAM_BINS - 1}) AS t(i)
    )
    SELECT
      b.bin_start,
      b.bin_end,
      COUNT(t."${field}") AS cnt
    FROM bins b
    LEFT JOIN "${props.table}" t ON t."${field}" >= b.bin_start AND t."${field}" < b.bin_end ${whereClause ? whereClause.replace('WHERE', 'AND') : ''}
    GROUP BY b.bin_start, b.bin_end
    ORDER BY b.bin_start
  `;
  const res = await axios.post(`${apiUrl}/database/restConnector`, { type: 'json', sql });
  return res.data;
}

async function fetchCategoryCounts(field, excludeField) {
  const whereClause = buildWhereClause(excludeField);
  const sql = `
    SELECT "${field}" AS category, COUNT(*) AS cnt
    FROM "${props.table}" ${whereClause}
    GROUP BY "${field}"
    ORDER BY cnt DESC
    LIMIT 50
  `;
  const res = await axios.post(`${apiUrl}/database/restConnector`, { type: 'json', sql });
  return res.data;
}

function buildWhereClause(excludeField) {
  const conditions = [];
  for (const [field, filter] of Object.entries(brushFilters.value)) {
    if (field === excludeField) continue;
    if (filter.type === 'range') {
      conditions.push(`"${field}" >= ${filter.min} AND "${field}" <= ${filter.max}`);
    } else if (filter.type === 'category') {
      const escaped = filter.values.map(v => `'${String(v).replace(/'/g, "''")}'`).join(',');
      conditions.push(`"${field}" IN (${escaped})`);
    }
  }
  return conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
}

function buildHistogramOption(field, data) {
  const labels = data.map(d => {
    const start = Number(d.bin_start);
    return start.toFixed(1);
  });
  const values = data.map(d => Number(d.cnt));

  return {
    title: { text: field, left: 'center', textStyle: { fontSize: 13 } },
    tooltip: {
      trigger: 'axis',
      formatter(params) {
        const idx = params[0].dataIndex;
        const d = data[idx];
        return `${Number(d.bin_start).toFixed(2)} - ${Number(d.bin_end).toFixed(2)}<br/>Count: ${d.cnt}`;
      },
    },
    grid: { left: 50, right: 20, top: 35, bottom: 60 },
    dataZoom: [
      { type: 'slider', xAxisIndex: 0, bottom: 5, height: 20, start: zoomRanges.value[field]?.start ?? 0, end: zoomRanges.value[field]?.end ?? 100 },
      { type: 'inside', xAxisIndex: 0, start: zoomRanges.value[field]?.start ?? 0, end: zoomRanges.value[field]?.end ?? 100 },
    ],
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 0,
        fontSize: 10,
        interval: Math.max(0, Math.floor(labels.length / 6) - 1),
      },
    },
    yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
    brush: {
      toolbox: ['lineX', 'clear'],
      xAxisIndex: 0,
      brushStyle: { borderWidth: 1, color: 'rgba(70,130,180,0.2)', borderColor: 'rgba(70,130,180,0.8)' },
    },
    toolbox: {
      feature: {
        brush: { title: { lineX: 'Brush', clear: 'Clear' } },
      },
      right: 20,
      top: 0,
    },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: { color: 'steelblue' },
      barCategoryGap: '0%',
      barGap: '0%',
    }],
  };
}

function buildCategoryOption(field, data) {
  const isSelected = brushFilters.value[field]?.type === 'category';
  const selectedValues = isSelected ? brushFilters.value[field].values.map(String) : [];

  const pieData = data.map(d => {
    const name = String(d.category);
    const selected = isSelected && selectedValues.includes(name);
    return {
      name,
      value: Number(d.cnt),
      selected,
      itemStyle: isSelected && !selectedValues.includes(name)
        ? { opacity: 0.3 }
        : {},
    };
  });

  return {
    title: { text: field, left: 'center', textStyle: { fontSize: 13 } },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'horizontal',
      bottom: 0,
      type: 'scroll',
      textStyle: { fontSize: 10 },
    },
    series: [{
      type: 'pie',
      radius: ['25%', '60%'],
      center: ['50%', '45%'],
      data: pieData,
      label: { show: false },
      emphasis: {
        label: { show: true, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' },
      },
      selectedMode: 'multiple',
    }],
  };
}

let updateTimer = null;

async function updateAllCharts(triggerField) {
  const promises = [];

  for (const field of numericFields.value) {
    promises.push(
      fetchHistogram(field, field).then(data => {
        fullData.value[field] = data;
        chartOptions.value[field] = buildHistogramOption(field, data);
      }).catch(err => console.error(`Error fetching ${field}:`, err))
    );
  }

  for (const field of categoricalFields.value) {
    promises.push(
      fetchCategoryCounts(field, field).then(data => {
        fullData.value[field] = data;
        chartOptions.value[field] = buildCategoryOption(field, data);
      }).catch(err => console.error(`Error fetching ${field}:`, err))
    );
  }

  await Promise.all(promises);
}

function onBrush(field, params) {
  if (!params.areas || params.areas.length === 0) {
    if (brushFilters.value[field]) {
      delete brushFilters.value[field];
      debouncedUpdate(field);
    }
  }
}

function onBrushEnd(field, params) {
  if (!params.areas || params.areas.length === 0) {
    delete brushFilters.value[field];
    debouncedUpdate(field);
    return;
  }
  const area = params.areas[0];
  if (area.coordRange) {
    const [startIdx, endIdx] = area.coordRange;
    const data = fullData.value[field];
    if (data && data.length > 0) {
      const minVal = Number(data[Math.max(0, Math.floor(startIdx))]?.bin_start ?? 0);
      const maxIdx = Math.min(data.length - 1, Math.ceil(endIdx));
      const maxVal = Number(data[maxIdx]?.bin_end ?? 0);
      brushFilters.value[field] = { type: 'range', min: minVal, max: maxVal };
      debouncedUpdate(field);
    }
  }
}

function onDataZoom(field, params) {
  const data = fullData.value[field];
  if (!data || data.length === 0) return;

  let start, end;
  if (params.batch && params.batch.length > 0) {
    start = params.batch[0].start;
    end = params.batch[0].end;
  } else {
    start = params.start;
    end = params.end;
  }
  if (start == null || end == null) return;

  zoomRanges.value[field] = { start, end };

  if (start <= 0 && end >= 100) {
    if (brushFilters.value[field]) {
      delete brushFilters.value[field];
      debouncedUpdate(field);
    }
    return;
  }

  const startIdx = Math.round(start / 100 * (data.length - 1));
  const endIdx = Math.round(end / 100 * (data.length - 1));
  const minVal = Number(data[Math.max(0, startIdx)]?.bin_start ?? 0);
  const maxVal = Number(data[Math.min(data.length - 1, endIdx)]?.bin_end ?? 0);

  brushFilters.value[field] = { type: 'range', min: minVal, max: maxVal };
  debouncedUpdate(field);
}

function onCategoryClick(field, params) {
  const category = params.name;
  if (!category) return;

  const current = brushFilters.value[field];
  if (current?.type === 'category') {
    const idx = current.values.indexOf(category);
    if (idx >= 0) {
      current.values.splice(idx, 1);
      if (current.values.length === 0) {
        delete brushFilters.value[field];
      }
    } else {
      current.values.push(category);
    }
  } else {
    brushFilters.value[field] = { type: 'category', values: [category] };
  }
  debouncedUpdate(field);
}

function debouncedUpdate(triggerField) {
  if (updateTimer) clearTimeout(updateTimer);
  updateTimer = setTimeout(() => updateAllCharts(triggerField), 150);
}

async function init() {
  if (!props.table || !props.selectedFields || !props.schema) return;
  classifyFields();
  brushFilters.value = {};
  zoomRanges.value = {};
  fieldRanges.value = {};
  await nextTick();
  await updateAllCharts();
}

watch(() => [props.table, props.selectedFields, props.schema], init, { deep: true, immediate: true });
</script>

<style scoped>
.crossfilter-container {
  padding: 10px;
}
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.chart-wrapper {
  position: relative;
  min-height: 350px;
}
.chart {
  width: 100%;
  height: 350px;
}
.close-btn {
  position: absolute;
  top: 4px;
  left: 4px;
  z-index: 10;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.15);
  color: #333;
  font-size: 13px;
  line-height: 22px;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.close-btn:hover {
  background: rgba(220, 53, 69, 0.8);
  color: #fff;
}
</style>
