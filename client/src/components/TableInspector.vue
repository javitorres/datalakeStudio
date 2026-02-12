<template>
  <!-- Fields -->
  <div class="col-md-1" v-if="tableSchema && showOptions">

    <!-- Check all and check none buttons -->
    <button class="btn btn-primary m-1 opcion-style" @click="selectAllFields(false)">
      <i class="bi bi-x-square"></i>
      Select None
    </button>
    <button class="btn btn-primary m-1 opcion-style" @click="selectAllFields(true)">
      <i class="bi bi-check-square"></i>
      Select All
    </button>
    <button class="btn btn-primary m-1 opcion-style" @click="copyToClipboard(true)">
      <i class="bi bi-clipboard"></i>
      Copy field names to clipboard
    </button>

    <div class="row" v-if="selectedFields" v-for="(type, field) in tableSchema" :key="field">
      <button class="btn m-1 opcion-style" :class="selectedFields.includes(field) ? 'btn-primary' : 'btn-secondary'"
        @click="toggleField(field)">
        <span v-html="imageSrc(type)"></span>
        {{ field }}
      </button>
    </div>
  </div>

  <!-- Data and metadata -->
  <div class="col-md-10 custom-col">
    <div class="row-md-2" v-if="showOptions">
      <!--<p>Row: {{ rowSelected }}</p>-->

      <button class="btn btn-primary m-1 opcion-style" :class="{ active: showSampleData }"
        @click="getSampleData(tableName)">
        <i class="bi bi-table"></i>
        Show sample data
      </button>

      <button class="btn btn-primary m-1 opcion-style" :class="{ active: showProfile }"
        @click="getTableProfile(tableName)">
        <i class="bi bi-search"></i>
        Show table profile
      </button>

      <!--<button class="btn btn-primary m-1 opcion-style" :class="{ active: showPlot }" @click="plotData(tableName)">
        <i class="bi bi-graph-up-arrow"></i>
        Plot data
      </button>
      -->

      <button class="btn btn-primary m-1 opcion-style" :class="{ active: showMosaic }" @click="toggleMosaic()">
        <i class="bi bi-graph-up-arrow"></i>
        Plot data
      </button>

      <button class="btn btn-primary m-1 opcion-style" :class="{ active: showMap }" @click="mapData(tableName)">
        <i class="bi bi-graph-up-arrow"></i>
        Show map
      </button>

      
    </div>


    <!-- Sample data -->
    <div class="row" v-show="sampleData && showSampleData">
      <div class="col-md-3" v-if="showOptions">
        <div class="btn-group">
          <button class="btn btn-secondary"><i class="bi bi-list-columns-reverse"></i> {{ rowcount }} rows</button>
          <button class="btn btn-secondary"><i class="bi bi-eyedropper"></i>{{ records != 0 ? records : rowcount }}
            showed</button>
        </div>
      </div>

      <div class="col-md-2" v-show="showOptions">
        <div class="btn-group">
          <button class="btn btn-primary"><i class="bi bi-arrows-vertical"></i></button>
          <button class="btn btn-primary" :class="{ active: type === 'First' }" @click="setType('First')">First</button>
          <button class="btn btn-primary" :class="{ active: type === 'Shuffle' }"
            @click="setType('Shuffle')">Shuffle</button>
          <button class="btn btn-primary" :class="{ active: type === 'Last' }" @click="setType('Last')">Last</button>
        </div>

      </div>
      <div class="col-md-2" v-show="showOptions">
        <div class="btn-group">
          <button class="btn btn-primary"><i class="bi bi-grid-3x3-gap-fill"></i></button>
          <button class="btn btn-primary" :class="{ active: records === 50 }" @click="setRecords(50)">50</button>
          <button class="btn btn-primary" :class="{ active: records === 100 }" @click="setRecords(100)">100</button>
          <button class="btn btn-primary" :class="{ active: records === 200 }" @click="setRecords(200)">200</button>
          <button v-if="records < 1000" class="btn btn-primary" :class="{ active: records === 0 }"
            @click="setRecords(0)">All</button>
        </div>
      </div>
      <!-- Data Table -->
      <div ref="table"></div>
    </div>

    <!-- Data profile -->
    <div v-if="tableProfile && showProfile">
      <h4>Table profile</h4>
      <div ref="tableProfileEl"></div>
    </div>

    <!-- Cross filters -->
    <div v-if="sampleData && chartConfig && showPlot">
      <!-- Map -->
      <div v-if="showMap">
        <br />
        <p>Found coordinates in (<b>{{ latField }}</b> , <b>{{ lonField }}</b>) fields</p>
        <!-- Hide map button -->
        <button class="btn btn-primary m-1 opcion-style" @click="hideMap = !hideMap">
          <i class="bi bi-graph-up-arrow"></i>
          {{ (hideMap) ? "Show Map" : "Hide map" }}
        </button>

        <Map v-if="!hideMap" :data="sampleData" :latField="latField" :lonField="lonField"></Map>
        <br />
      </div>

      <!-- Charts 
      <GenericCross :key="genericCrossKey" :dataStr="sampleData" :chartConfig="chartConfig">
      </GenericCross>
      -->
    </div>

    <div v-if="showMosaic">
      <Mosaic :table="tableName" :selectedFields="selectedFields" :schema="tableSchema">
      </Mosaic>
    </div>

    <!-- H3 Maps-->
    <div v-if="showMap">
      <MapH3 :table="tableName" :selectedFields="selectedFields" :schema="tableSchema">
      </MapH3>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import axios from 'axios';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import GenericCross from './GenericCross.vue';
import Map from './Map.vue';
import MapH3 from './MapH3.vue';
import Mosaic from './Mosaic.vue';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

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
  await axios.get(`${apiUrl}/database/getRowCount`, {
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
  await axios.get(`${apiUrl}/database/getTableSchema`, {
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

  await axios.get(`${apiUrl}/database/getSampleData`, {
    params: {
      tableName: tableName,
      type: type.value,
      records: records.value,
    },
  }).then((response) => {
    if (response.status === 200) {
      sampleData.value = response.data;

      myTabulator = new Tabulator(table.value, {
        data: sampleData.value,
        importFormat: 'csv',
        autoColumns: true,
        layout: 'fitColumns',
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

  const fetchData = () => axios.get(`${apiUrl}/database/getTableProfile`, {
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
        layout: 'fitColumns',
        importFormat: 'csv',
        autoColumns: true,
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
.tabulator {
  background-color: #ffffff;
  padding-left: 20px;
  padding-right: 20px;
  padding-top: 20px;
  padding-bottom: 20px;
  border: #ffffff;
}

.custom-col {
  padding-left: 20px;

}
</style>
