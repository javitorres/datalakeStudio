<template>
  <div class="inspector-layout">
    <aside class="field-column" v-if="tableSchema && showOptions">
      <div class="schema-heading">
        <div>
          <span class="section-kicker">Schema</span>
          <h3>Columns</h3>
        </div>
        <span class="field-count">{{ selectedFields?.length || 0 }}/{{ Object.keys(tableSchema).length }}</span>
      </div>

      <div class="field-toolbar">
        <button class="schema-action" title="Deselect all fields" @click="selectAllFields(false)">
          <i class="bi bi-square"></i><span>None</span>
        </button>
        <button class="schema-action primary" title="Select all fields" @click="selectAllFields(true)">
          <i class="bi bi-check2-square"></i><span>All</span>
        </button>
        <button class="schema-action" title="Copy selected field names" @click="copyToClipboard(true)">
          <i class="bi bi-copy"></i><span>Copy</span>
        </button>
      </div>

      <div class="field-list" v-if="selectedFields">
        <button
          v-for="(fieldType, field) in tableSchema"
          :key="field"
          class="field-chip"
          :class="{ selected: selectedFields.includes(field) }"
          @click="toggleField(field)"
        >
          <span class="field-check"><i class="bi" :class="selectedFields.includes(field) ? 'bi-check' : ''"></i></span>
          <span class="field-name" :title="field">{{ field }}</span>
          <span class="field-type">{{ fieldType }}</span>
        </button>
      </div>
    </aside>

    <section class="data-column">
      <nav class="explorer-nav" v-if="showOptions" aria-label="Table views">
        <button :class="{ active: showSampleData }" @click="getSampleData(tableName)">
          <i class="bi bi-table"></i><span>Data</span><small>Browse rows</small>
        </button>
        <button :class="{ active: showProfile }" @click="getTableProfile(tableName)">
          <i class="bi bi-activity"></i><span>Profile</span><small>Statistics</small>
        </button>
        <button :class="{ active: showMosaic }" @click="toggleMosaic()">
          <i class="bi bi-bar-chart"></i><span>Charts</span><small>Cross-filter</small>
        </button>
        <button :class="{ active: showMap }" @click="mapData(tableName)">
          <i class="bi bi-map"></i><span>Map</span><small>Geospatial</small>
        </button>
      </nav>

      <div class="view-canvas">
        <div class="table-view" v-show="sampleData && showSampleData">
          <header class="view-header">
            <div>
              <span class="section-kicker">Data preview</span>
              <h3>Sample rows</h3>
            </div>
            <div class="view-metrics">
              <span><i class="bi bi-list-ul"></i><b>{{ rowcount }}</b> total rows</span>
              <span><i class="bi bi-eye"></i><b>{{ records || rowcount }}</b> displayed</span>
              <span><i class="bi bi-layout-three-columns"></i><b>{{ selectedFields?.length || 0 }}</b> columns</span>
            </div>
          </header>

          <div class="sample-toolbar" v-if="showOptions">
            <div class="toolbar-group">
              <span class="toolbar-label">Sample</span>
              <button :class="{ active: type === 'First' }" @click="setType('First')">First</button>
              <button :class="{ active: type === 'Shuffle' }" @click="setType('Shuffle')">Random</button>
              <button :class="{ active: type === 'Last' }" @click="setType('Last')">Last</button>
            </div>
            <div class="toolbar-group">
              <span class="toolbar-label">Rows</span>
              <button :class="{ active: records === 50 }" @click="setRecords(50)">50</button>
              <button :class="{ active: records === 100 }" @click="setRecords(100)">100</button>
              <button :class="{ active: records === 200 }" @click="setRecords(200)">200</button>
              <button v-if="records < 1000" :class="{ active: records === 0 }" @click="setRecords(0)">All</button>
            </div>
            <div class="toolbar-group" v-if="activeFilter">
              <span class="toolbar-label">Cross-filter</span>
              <button :class="{ active: dataShowFiltered }" @click="setDataFiltered(true)">Show filtered</button>
              <button :class="{ active: !dataShowFiltered }" @click="setDataFiltered(false)">Show all</button>
            </div>
          </div>

          <div class="active-filters" v-if="activeFilter && dataShowFiltered && activeFilterList.length">
            <span class="filters-label">Filters</span>
            <span class="filter-chip" v-for="f in activeFilterList" :key="f.field"><b>{{ f.field }}</b> {{ f.text }}</span>
          </div>

          <div class="table-shell"><div ref="table"></div></div>
        </div>

        <div class="profile-view" v-if="tableProfile && showProfile">
          <header class="view-header">
            <div><span class="section-kicker">Column analysis</span><h3>Table profile</h3></div>
            <p>Distribution and descriptive statistics for the selected dataset.</p>
          </header>
          <div class="profile-table" ref="tableProfileEl"></div>
        </div>

        <div v-if="sampleData && chartConfig && showPlot">
          <div v-if="showMap">
            <p>Found coordinates in <b>{{ latField }}</b> and <b>{{ lonField }}</b></p>
            <button class="btn btn-primary" @click="hideMap = !hideMap">{{ hideMap ? 'Show map' : 'Hide map' }}</button>
            <Map v-if="!hideMap" :data="sampleData" :latField="latField" :lonField="lonField" />
          </div>
        </div>

        <!-- v-show + keep-alive keep the charts mounted so cross-filters survive tab switches -->
        <div class="visualization-view" v-show="showMosaic">
          <header class="view-header">
            <div><span class="section-kicker">Interactive analysis</span><h3>Cross-filter charts</h3></div>
            <p>Select ranges in any chart to filter every visualization.</p>
          </header>
          <keep-alive>
            <CrossFilterCharts v-if="showMosaic" :table="tableName" :selectedFields="selectedFields" :schema="tableSchema" @removeField="toggleField" @filterChange="onFilterChange" />
          </keep-alive>
        </div>

        <!-- v-show + keep-alive keep the map alive so it (and its layers) survive tab switches -->
        <div class="map-view" v-show="showMap">
          <header class="view-header">
            <div><span class="section-kicker">Spatial analysis</span><h3>Geospatial explorer</h3></div>
            <p>Configure coordinates, H3 aggregation and point layers.</p>
            <div class="filter-toggle" v-if="activeFilter">
              <span class="toolbar-label">Cross-filter</span>
              <button :class="{ active: mapShowFiltered }" @click="mapShowFiltered = true">Show filtered</button>
              <button :class="{ active: !mapShowFiltered }" @click="mapShowFiltered = false">Show all</button>
            </div>
          </header>
          <div class="active-filters" v-if="activeFilter && mapShowFiltered && activeFilterList.length">
            <span class="filters-label">Filters</span>
            <span class="filter-chip" v-for="f in activeFilterList" :key="f.field"><b>{{ f.field }}</b> {{ f.text }}</span>
          </div>
          <keep-alive>
            <MapH3 v-if="showMap" :table="tableName" :selectedFields="selectedFields" :schema="tableSchema" :filter="mapShowFiltered ? activeFilter : ''" />
          </keep-alive>
        </div>
      </div>
    </section>
  </div>
</template>
<script setup>
import { onMounted, ref, watch } from 'vue';
import api from '../services/api';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import GenericCross from './GenericCross.vue';
import Map from './Map.vue';
import MapH3 from './MapH3.vue';
import CrossFilterCharts from './CrossFilterCharts.vue';

const props = defineProps({
  tableName: String,
  showOptions: Boolean,
});

let myTabulator = null;

const selectedFields = ref(null);
const showSampleData = ref(true);
const showProfile = ref(false);
const showPlot = ref(false);
const showMap = ref(false);
const showMosaic = ref(false);
const hideMap = ref(false);

// Cross-filter shared from the Charts tab (SQL predicate + readable list).
const activeFilter = ref('');
const activeFilterList = ref([]);
const dataShowFiltered = ref(true);
const mapShowFiltered = ref(true);

function onFilterChange(payload) {
  activeFilter.value = payload?.sql || '';
  activeFilterList.value = payload?.list || [];
}

function setDataFiltered(value) {
  dataShowFiltered.value = value;
  getSampleData(props.tableName);
}
const latField = ref(null);
const lonField = ref(null);
const sampleData = ref(Object);
const tableSchema = ref(Object);
const tableProfile = ref(Object);
const rowcount = ref(0);
const type = ref('First');
const records = ref(10);
const rowSelected = ref(null);
const chartConfig = ref(null);
const genericCrossKey = ref(0);
const loading = ref(false);
const table = ref(null);
const tableProfileEl = ref(null);

onMounted(() => {
  load();
});

watch(() => props.tableName, async () => {
  await load();
  setRecords(50);
});

function selectAllFields(all) {
  selectedFields.value = [];
  if (all) {
    selectedFields.value = Object.keys(tableSchema.value);
  }
  generateCharts();
  updateTable();
}

function toggleField(field) {
  if (selectedFields.value == null) {
    selectedFields.value = [];
  }
  if (selectedFields.value.includes(field)) {
    selectedFields.value = selectedFields.value.filter(item => item !== field);
  } else {
    selectedFields.value.push(field);
  }
  generateCharts();
  updateTable();
}

function copyToClipboard() {
  var text = selectedFields.value.join(', ');
  navigator.clipboard.writeText(text).then(function () {
    toast.success('Fields names copied to clipboard');
  }, function () {
    toast.error('Error copying fields names to clipboard');
  });
}

function updateTable() {
  var columns = [];
  for (var key in tableSchema.value) {
    if (selectedFields.value && selectedFields.value.includes(key)) {
      columns.push({ title: key, field: key });
    }
  }

  myTabulator.setColumns(columns);
}

function setType(newType) {
  type.value = newType;
  getSampleData(props.tableName);
}

function setRecords(newRecords) {
  records.value = newRecords;
  getSampleData(props.tableName);
}

async function load() {
  await getSampleData(props.tableName);
  await getRowcount();
  await getTableSchema(props.tableName);
}

function imageSrc(typeInput) {
  if (typeInput === 'object') return '<i class="bi bi-alphabet-uppercase"></i>';
  else if (typeInput === 'float32') return '<i class="bi bi-123"></i>';
  else if (typeInput === 'float64') return '<i class="bi bi-123"></i>';
  else if (typeInput === 'int64') return '<i class="bi bi-123"></i>';
  else if (typeInput === 'boolean') return 'MNO';
  else if (typeInput === 'null') return 'PQR';
  else return typeInput;
}

async function getRowcount() {
  await api.get(`/database/getRowCount`, {
    params: {
      tableName: props.tableName,
    },
  }).then((response) => {
    if (response.status === 200) {
      rowcount.value = response.data.rows;
    } else {
      toast.error(`Error: HTTP ${response.message}`);
    }
  }).catch(() => {
    toast.error('Error loading rowcount');
  }).finally(() => {
    loading.value = false;
  });
}

async function getTableSchema(tableName) {
  await api.get(`/database/getTableSchema`, {
    params: {
      tableName: tableName,
    },
  }).then((response) => {
    if (response.status === 200) {
      tableSchema.value = response.data;

      selectedFields.value = [];
      for (var key in tableSchema.value) {
        selectedFields.value.push(key).field;
      }
    } else {
      toast.error(`Error: HTTP ${response.message}`);
    }
  }).catch(() => {
    toast.error('Error loading schema');
  }).finally(() => {
    loading.value = false;
  });
}

async function getSampleData(tableName) {
  showSampleData.value = true;
  showProfile.value = false;
  showPlot.value = false;
  showMap.value = false;
  showMosaic.value = false;

  await api.get(`/database/getSampleData`, {
    params: {
      tableName: tableName,
      type: type.value,
      records: records.value,
      filter: dataShowFiltered.value ? activeFilter.value : '',
    },
  }).then((response) => {
    if (response.status === 200) {
      sampleData.value = response.data;

      myTabulator = new Tabulator(table.value, {
        data: sampleData.value,
        importFormat: 'csv',
        autoColumns: true,
        layout: 'fitDataTable',
        columnDefaults: {
          headerTooltip: true,
          tooltip: true,
        },
        persistence: true,
      });
    } else {
      toast.error(`Error: HTTP ${response.message}`);
    }
  }).catch((error) => {
    toast.error(`Error:: HTTP ${error.message}`);
  }).finally(() => {
    loading.value = false;
  });

  myTabulator.on('tableBuilt', () => {
    updateTable();
  });
}

async function getTableProfile(tableName) {
  showSampleData.value = false;
  showProfile.value = true;
  showPlot.value = false;
  showMap.value = false;
  showMosaic.value = false;

  const fetchData = () => api.get(`/database/getTableProfile`, {
    params: {
      tableName: tableName,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Loading table profile, please wait...',
      success: 'Profile loaded',
      error: 'Error loading profile'
    },
    {
      position: toast.POSITION.BOTTOM_RIGHT,
    }
  ).then((response) => {
    if (response.status === 200) {
      tableProfile.value = response.data;

      new Tabulator(tableProfileEl.value, {
        data: tableProfile.value,
        reactiveData: true,
        layout: 'fitDataTable',
        importFormat: 'csv',
        autoColumns: true,
        columnDefaults: {
          headerTooltip: true,
          tooltip: true,
        },
      });
    }
  }).catch((error) => {
    console.error('Error: ', error.message);
  });
}

async function plotData(tableName) {
  showSampleData.value = false;
  showProfile.value = false;
  showPlot.value = true;
  showMap.value = false;
  showMosaic.value = false;

  for (var key in tableSchema.value) {
    if (key.toLowerCase() === 'lat' || key.toLowerCase() === 'latitude' || key.toLowerCase() === 'latitud') {
      latField.value = key;
    }
    if (key.toLowerCase() === 'lon' || key.toLowerCase() === 'longitude' || key.toLowerCase() === 'longitud') {
      lonField.value = key;
    }
  }

  generateCharts();
}

async function mapData(tableName) {
  showSampleData.value = false;
  showProfile.value = false;
  showPlot.value = false;
  showMap.value = true;
  showMosaic.value = false;

  for (var key in tableSchema.value) {
    if (key.toLowerCase() === 'lat' || key.toLowerCase() === 'latitude' || key.toLowerCase() === 'latitud') {
      latField.value = key;
    }
    if (key.toLowerCase() === 'lon' || key.toLowerCase() === 'longitude' || key.toLowerCase() === 'longitud') {
      lonField.value = key;
    }
  }

  generateCharts();
}

function generateCharts() {
  var charts = [];
  for (var key in tableSchema.value) {
    if (selectedFields.value.includes(key)) {
      var chart = {
        title: key,
        type: tableSchema.value[key],
        fields: key
      };
      if (chart.type === 'object' || chart.type === 'bool') {
        chart.type = 'categorical';
      } else if (chart.type === 'int64' || chart.type === 'float64') {
        chart.type = 'numerical';
      } else if (chart.type === 'datetime64[ns]') {
        chart.type = 'date';
      } else {
        chart.type = 'categorical';
      }
      charts.push(chart);
    }
  }
  chartConfig.value = {
    charts: charts
  };

  genericCrossKey.value++;
}

function toggleMosaic() {
  showSampleData.value = false;
  showProfile.value = false;
  showPlot.value = false;
  showMap.value = false;
  showMosaic.value = !showMosaic.value;
}
</script>
<style scoped>
.inspector-layout{display:grid;grid-template-columns:250px minmax(0,1fr);gap:13px;font-size:13px}
.field-column{position:sticky;top:95px;align-self:start;max-height:calc(100vh - 120px);display:flex;flex-direction:column;overflow:hidden;border:1px solid var(--ds-line);border-radius:12px;background:#f7faf9}
.schema-heading{display:flex;align-items:center;justify-content:space-between;padding:15px 14px 11px}
.section-kicker{display:block;color:#84928e;font-size:8px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}
.schema-heading h3,.view-header h3{margin:1px 0 0;color:var(--ds-ink);font-size:.95rem;font-weight:750;letter-spacing:-.02em}
.field-count{padding:4px 7px;border-radius:20px;background:var(--ds-mint);color:var(--ds-teal-dark);font-size:9px;font-weight:800}
.field-toolbar{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;padding:0 10px 10px;border-bottom:1px solid var(--ds-line)}
.schema-action{display:flex;align-items:center;justify-content:center;gap:5px;padding:6px 4px;border:1px solid #d9e4e0;border-radius:7px;background:#fff;color:#64736f;font-size:9px;font-weight:700}
.schema-action:hover{border-color:#9bcbbc;color:var(--ds-teal-dark)}.schema-action.primary{border-color:#a5d2c6;background:#e9f6f2;color:var(--ds-teal-dark)}
.field-list{display:grid;gap:3px;padding:8px;overflow-y:auto}
.field-chip{width:100%;min-width:0;display:grid;grid-template-columns:18px minmax(0,1fr) auto;align-items:center;gap:7px;padding:7px;border:1px solid transparent;border-radius:7px;background:transparent;color:#62706d;text-align:left;transition:.12s}
.field-chip:hover{background:#eef4f2;color:var(--ds-ink)}.field-chip.selected{background:#fff;color:var(--ds-ink);border-color:#dce6e3;box-shadow:0 2px 7px rgba(31,67,58,.05)}
.field-check{width:16px;height:16px;display:grid;place-items:center;border:1px solid #c7d3cf;border-radius:4px;color:#fff;font-size:10px}.selected .field-check{border-color:var(--ds-teal);background:var(--ds-teal)}
.field-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:10px;font-weight:650}.field-type{max-width:75px;overflow:hidden;text-overflow:ellipsis;padding:2px 5px;border-radius:4px;background:#edf2f0;color:#85918e;font-size:7px;font-weight:750;text-transform:uppercase;white-space:nowrap}
.data-column{min-width:0}.explorer-nav{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-bottom:10px;padding:5px;border:1px solid var(--ds-line);border-radius:11px;background:#edf3f1}
.explorer-nav button{position:relative;display:grid;grid-template-columns:28px 1fr;grid-template-rows:auto auto;column-gap:8px;padding:8px 10px;border:0;border-radius:8px;background:transparent;color:#687773;text-align:left}
.explorer-nav button>i{grid-row:1/3;width:28px;height:28px;display:grid;place-items:center;align-self:center;border-radius:7px;background:#e3ebe8;color:#72817d}.explorer-nav button>span{font-size:10px;font-weight:750}.explorer-nav button>small{color:#96a19e;font-size:8px}
.explorer-nav button:hover{background:rgba(255,255,255,.55)}.explorer-nav button.active{background:#fff;color:var(--ds-teal-dark);box-shadow:0 2px 9px rgba(30,65,57,.09)}.explorer-nav button.active>i{background:var(--ds-mint);color:var(--ds-teal)}
.view-canvas{min-height:410px}.table-view,.profile-view,.visualization-view,.map-view{border:1px solid var(--ds-line);border-radius:12px;background:#fff;overflow:hidden}
.view-header{min-height:62px;display:flex;align-items:center;justify-content:space-between;gap:25px;padding:12px 15px;border-bottom:1px solid var(--ds-line);background:#fbfcfc}.view-header p{max-width:430px;margin:0;color:#7a8783;font-size:10px}
.view-metrics{display:flex;align-items:center;gap:7px}.view-metrics>span{display:flex;align-items:center;gap:5px;padding:5px 8px;border:1px solid #e0e8e5;border-radius:7px;background:#fff;color:#788581;font-size:8px}.view-metrics i{color:var(--ds-teal)}.view-metrics b{color:#384944;font-size:9px}
.sample-toolbar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 12px;border-bottom:1px solid var(--ds-line);background:#f7faf9}.toolbar-group{display:flex;align-items:center;gap:3px}.toolbar-label{margin-right:5px;color:#84918d;font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}.toolbar-group button{min-width:35px;padding:4px 7px;border:1px solid transparent;border-radius:6px;background:transparent;color:#6b7975;font-size:9px;font-weight:700}.toolbar-group button:hover{background:#e7efec}.toolbar-group button.active{border-color:#b6d8cf;background:#fff;color:var(--ds-teal-dark);box-shadow:0 2px 6px rgba(32,65,57,.06)}
.table-shell,.profile-table{width:100%;max-height:60vh;overflow:auto;background:#fff}.profile-table{padding:12px}
.table-shell :deep(.tabulator),.profile-table :deep(.tabulator){min-width:100%;border:0;background:#fff;font-size:11px}.table-shell :deep(.tabulator-header),.profile-table :deep(.tabulator-header){position:sticky;top:0;z-index:3;border-bottom:1px solid #d8e3df;background:#eef4f2;color:#42534e}.table-shell :deep(.tabulator-col),.profile-table :deep(.tabulator-col){background:transparent!important;border-right:1px solid #dfe7e4!important}.table-shell :deep(.tabulator-col-title),.profile-table :deep(.tabulator-col-title){padding:2px;font-size:9px;font-weight:800;letter-spacing:.02em}.table-shell :deep(.tabulator-row),.profile-table :deep(.tabulator-row){min-height:31px;border-bottom:1px solid #edf1f0;background:#fff}.table-shell :deep(.tabulator-row:nth-child(even)),.profile-table :deep(.tabulator-row:nth-child(even)){background:#fafcfb}.table-shell :deep(.tabulator-row:hover),.profile-table :deep(.tabulator-row:hover){background:#edf7f3}.table-shell :deep(.tabulator-cell),.profile-table :deep(.tabulator-cell){padding:7px 9px;border-right:1px solid #edf1f0}
.visualization-view,.map-view{padding-bottom:14px}.visualization-view>:not(.view-header),.map-view>:not(.view-header){margin:14px}
@media(max-width:1100px){.inspector-layout{grid-template-columns:210px minmax(0,1fr)}.view-metrics span{font-size:0}.view-metrics b{font-size:9px}}
.active-filters{display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:8px 12px;border-bottom:1px solid var(--ds-line);background:#f2f8f6}
.active-filters .filters-label{color:#84918d;font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}
.filter-chip{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border:1px solid #b6d8cf;border-radius:20px;background:#fff;color:#3f5b55;font-size:10px}
.filter-chip b{color:var(--ds-teal-dark);font-weight:700}
.filter-toggle{display:flex;align-items:center;gap:3px}
.filter-toggle button{min-width:35px;padding:4px 7px;border:1px solid transparent;border-radius:6px;background:transparent;color:#6b7975;font-size:9px;font-weight:700;cursor:pointer}
.filter-toggle button:hover{background:#e7efec}
.filter-toggle button.active{border-color:#b6d8cf;background:#fff;color:var(--ds-teal-dark);box-shadow:0 2px 6px rgba(32,65,57,.06)}
@media(max-width:850px){.inspector-layout{grid-template-columns:1fr}.field-column{position:static;max-height:none}.field-list{max-height:190px;grid-template-columns:repeat(2,minmax(0,1fr))}.explorer-nav button>small{display:none}.explorer-nav button{grid-template-columns:24px 1fr;padding:7px}.view-header{align-items:flex-start;flex-direction:column;gap:8px}.view-metrics{flex-wrap:wrap}.sample-toolbar{align-items:flex-start;flex-direction:column}}
</style>