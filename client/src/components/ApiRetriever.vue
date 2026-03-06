<template>
  <div class="row compact-api-view" v-if="tables && tables.length > 0">
    <div class="col-md-6 compact-panel">
      <h3 class="compact-title">Select Dataset</h3>
      <div class="row">
        <!-- Table selector -->
        <div class="row">
          <div class="col-md-6">
            <div class="form-group">
              <div class="input-group mb-3 compact-input-group">
                <span class="input-group-text" id="basic-addon1">Select table</span>
                
              <select class="form-control" id="tableSelector" v-model="table">
                <option v-for="table in tables" :key="table.id" :value="table">{{ table }}</option>
              </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Sample data-->
        <div class="row" v-if="table">
          <TableInspector :tableName="table" :showOptions="showOptions" />
        </div>
      </div>
    </div>

    <div class="col-md-6 compact-panel" v-if="table">
      <h3 class="compact-title">API configuration</h3>
      <!-- Search API or use a known endpoint -->
      <div class="form-check">
        <input class="form-check-input" type="radio" name="flexRadioDefault" id="flexRadioDefault1" v-model="mode"
          value="search">
        <label class="form-check-label" for="flexRadioDefault1">Search the API</label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="radio" name="flexRadioDefault" id="flexRadioDefault2" v-model="mode"
          value="write">
        <label class="form-check-label" for="flexRadioDefault2">Write directly the API URL</label>
      </div>


      <div v-if="mode === 'search'">
        <div class="input-group mb-3 compact-input-group">
            <span class="input-group-text" id="basic-addon1">Service name</span>
        <input id="apiServiceName" type="text" class="form-control" placeholder="Service name" aria-label="File"
          aria-describedby="basic-addon1" v-model="apiServiceName" @input="searchService(apiServiceName)">
        </div>
      </div>

      <div v-if="services && services.length > 0">
        <ul class="list-unstyled compact-chip-list">
          <li v-for="service in services" :key="service.id">
            <button class="btn btn-outline-primary compact-chip-btn" @click="searchMethod(service, '')">
              {{ service }}
            </button>
          </li>
        </ul>
      </div>

      
      <div v-if="service && mode === 'search'">
        <p class="compact-muted">Service: {{ service }}</p>

        <div class="input-group mb-3 compact-input-group">
            <span class="input-group-text" id="basic-addon1">Method name</span>
        <input id="methodPath" type="text" class="form-control" placeholder="Method name" aria-label="File"
          aria-describedby="basic-addon1" v-model="methodPath" @input="searchMethod(service, methodPath)">
        </div>

        <!-- Methods found -->
        <ul class="list-unstyled compact-chip-list" v-if="methods">
          <li v-for="method in methods" :key="method.id">
            <button class="btn btn-outline-primary compact-chip-btn" @click="clickMethod(service, method)">
              {{ method.controller }} - {{ method.method }} - {{ method.path }}
            </button>
          </li>
        </ul>

        <!-- Method selected info -->
        <div v-if="methodInfo" class="compact-card">

          <!--<p>Summary: {{ methodInfo.summary }}</p>-->
          <p class="compact-muted"><b>Method:</b> {{ methodInfo.method }}</p>
          <p class="compact-muted"><b>URL:</b> {{ methodInfo.url }}</p>

          <p class="compact-muted"><b>Query parameters:</b></p>
          <div v-if="methodInfo.method === 'GET'">

            <ul>
              <div v-for="param in methodInfo.parameters">
                <li>
                  <p><b>Param:</b> {{ param.name }} ({{ param.schema.type }}). {{ param.required ? "Required" : "Optional"
                  }}
                  </p>
                </li>
              </div>
            </ul>
          </div>
        </div>

        
      </div>

      <div v-if="mode === 'write'">
          <p class="compact-muted">Write the URL with this format http://service/endpoint?param1={param1Value}&param2={param2Value}</p>
          <div class="input-group mb-3 compact-input-group">
            <span class="input-group-text" id="basic-addon1">URL</span>
            <input id="methodPath" type="text" class="form-control" placeholder="URL" aria-label="File"
              aria-describedby="basic-addon1" v-model="methodPathManualMode">
        </div>

      </div>
    </div>

    <div class="row mt-2" v-if="methodInfo || methodPathManualMode">
      <div class="col-md-4 compact-panel">
        <p class="compact-title"><i class="bi bi-puzzle"></i> Field mapping </p>

        <div v-if="mode === 'search'">
          <p class="compact-muted">Select the field to map with the API parameter</p>

          <div v-for="param in methodInfo.parameters" :key="param.name">
            <label :for="'fieldSelector-' + param.name">{{ param.name }}</label>
            <select class="form-control" :id="'fieldSelector-' + param.name" v-model="selectedFields[param.name]" @change="buildQueryString">
              <option value="">None</option>
              <option v-for="(type, field) in schema" :key="field" :value="field">{{ field }}</option>
            </select>
          <br />
        </div>


        <div v-if="mode === write">
          <p>Write the field to map with the API parameter</p>
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Field name</span>
            <input id="fieldSelector" type="text" class="form-control" placeholder="Field name" aria-label="File"
              aria-describedby="basic-addon1" v-model="selectedFields['field']" @change="buildQueryString">
          </div>
          <br />
          </div>



      </div>


      </div>

      <div class="col-md-4 compact-panel">
        <p class="compact-title"><i class="bi bi-check-circle"></i> API response sample</p>
        <p class="compact-muted">Sample for first record:</p>
        <!-- Show queryString -->
        <div v-if="fullUrlExample">
          <p class="compact-muted"><b>Query string:</b> {{ fullUrlExample }}</p>
        </div>
        
        <div v-if="sampleData">
          <!-- text area -->
          <div class="form-group">
            <label for="exampleFormControlTextarea1">Sample response</label>
            <textarea class="form-control" id="exampleFormControlTextarea1" rows="10">{{ sampleResponse }}</textarea>
          </div>
        </div>
      </div>

      <div class="col-md-4 compact-panel">
        <p class="compact-title"><i class="bi bi-check2-square"></i> Extract fields</p>
        <p class="compact-muted">Write field to load, example: data.car.model. If empty, full response is stored in RESPONSE_JSON.</p>
      
        <div>
          <div v-for="(mapping, index) in mappings" :key="index" class="row">
            <div class="col-md-6">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">Json field</span>
                <input v-model="mapping.jsonField" placeholder="Json Field" class="form-control">
              </div>
            </div>
            <div class="col-md-6">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">New field name</span>
                <input v-model="mapping.newFieldName" placeholder="New Field Name" class="form-control">
              </div>
            </div>
          </div>
        
          <div class="compact-actions">
            <button class="btn btn-sm btn-primary" @click="addMapping">Add new</button>
            <button class="btn btn-sm btn-outline-secondary" @click="deleteAllMappings">Delete all mappings</button>
          </div>
        </div>
      </div>
    </div> <!-- process config -->
    <div class="row mt-2" v-if="table && mappings.length > 0">
      <div class="col-md-4 compact-panel">
        <div class="input-group mb-3 compact-input-group">
            <span class="input-group-text" id="basic-addon1">Records to process (empty for all)</span>
            <input v-model="recordsToProcess" placeholder="10" class="form-control">
        </div>
            <div class="input-group mb-3 compact-input-group">
            <span class="input-group-text" id="basic-addon1">New table name</span>
            <input v-model="newTableName" placeholder="enrichedTable" class="form-control">
        </div>
        <button v-if="newTableName" class="btn btn-sm btn-primary" @click="runDataEnrichment()">Run</button>
      </div>
      
    </div>
  </div>
  <div v-else>
    <h2>No tables to enrich with extrnal APIs. Load some data before</h2>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import TableInspector from './TableInspector.vue';

import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

const props = defineProps({
  tables: Object,
});

const emit = defineEmits(['tableCreated']);

const expanded = ref(true);
const showOptions = ref(false);
const apiServiceName = ref('');
const services = ref([]);
const service = ref('');
const methodPath = ref('');
const methods = ref([]);
const method = ref('');
const methodInfo = ref(null);
const selectedFields = ref({});
const fullUrl = ref('');
const fullUrlExample = ref('');
const sampleData = ref(null);
const sampleResponse = ref(null);
const methodPathManualMode = ref('');
const mappings = ref([{ jsonField: '', newFieldName: '' }]);
const recordsToProcess = ref(10);
const newTableName = ref(null);
const schema = ref(null);
const table = ref(null);
const mode = ref('search');
const showSampleData = ref(false);
const showProfile = ref(false);
const showCrossfilters = ref(false);
const loading = ref(false);
const type = ref(null);

watch(table, (newVal) => {
  if (newVal) {
    getTableSchema(newVal);
  }
});

async function searchService(apiServiceNameInput) {
  methods.value = [];
  const fetchData = async () => await axios.get(`${apiUrl}/apiRetriever/getServices`, {
    params: {
      serviceName: apiServiceNameInput,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Searching service, please wait...',
      error: 'Error Searching  service'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    services.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function searchMethod(nextService, nextMethodPath) {
  service.value = nextService;
  selectedFields.value = {};
  const fetchData = async () => await axios.get(`${apiUrl}/apiRetriever/getRepositoryMethodList`, {
    params: {
      serviceName: nextService,
      methodPath: nextMethodPath
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Loading service, please wait...',
      error: 'Error loading  service'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    methods.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function clickMethod(nextService, selectedMethod) {
  method.value = selectedMethod;
  selectedFields.value = {};
  const fetchData = async () => await axios.get(`${apiUrl}/apiRetriever/getMethodInfo`, {
    params: {
      serviceName: nextService,
      methodPath: selectedMethod.path,
      methodMethod: selectedMethod.method,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Loading method info, please wait...',
      error: 'Error loading  method'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    methodInfo.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function getTableSchema(nextTable) {
  const fetchData = async () => await axios.get(`${apiUrl}/database/getTableSchema`, {
    params: {
      tableName: nextTable,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Loading table schema, please wait...',
      success: 'Schema loaded',
      error: 'Error loading  schema'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    schema.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function getSampleData(nextTable) {
  showSampleData.value = true;
  showProfile.value = false;
  showCrossfilters.value = false;

  await axios.get(`${apiUrl}/database/getSampleData`, {
    params: {
      tableName: nextTable,
      type: type.value,
      records: 5,
    },
  }).then((response) => {
    sampleData.value = response.data;
  }).catch((error) => {
    toast.error(`Error: HTTP ${error.message}`);
  }).finally(() => {
    loading.value = false;
  });
}

async function buildQueryString() {
  await getSampleData(table.value);

  const rows = sampleData.value.split('\n');
  const firstRow = rows[0].split(',');
  const secondRow = rows[1].split(',');

  let queryString = '';
  for (const key in selectedFields.value) {
    const fieldIndex = Object.keys(selectedFields.value).indexOf(key);
    if (fieldIndex !== -1 && firstRow[fieldIndex]) {
      queryString += `${key}=${encodeURIComponent(secondRow[fieldIndex])}&`;
    } else {
      queryString += `${key}=${encodeURIComponent(selectedFields.value[key])}&`;
    }
  }

  fullUrl.value = `${methodInfo.value.url}`;
  fullUrlExample.value = `${methodInfo.value.url}?${queryString}`;
  const fetchData = async () => await axios.get(`${fullUrlExample.value}`, {});

  toast.promise(
    fetchData(),
    {
      pending: 'Example requet, please wait...',
      success: 'Example loaded',
      error: 'Error loading  sample data'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    sampleResponse.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

function addMapping() {
  mappings.value.push({ jsonField: '', newFieldName: '' });
}

function deleteAllMappings() {
  mappings.value = [];
}

async function runDataEnrichment() {
  const fetchData = async () => await axios.post(`${apiUrl}/apiRetriever/runApiEnrichment`, {
    tableName: table.value,
    parameters: selectedFields.value,
    mappings: mappings.value,
    recordsToProcess: recordsToProcess.value,
    service: service.value,
    method: method.value,
    url: fullUrl.value,
    newTableName: newTableName.value,
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Generating new table using API, please wait...',
      success: 'New table created',
      error: 'Error creating table'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    emit('tableCreated');
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}
</script>
<style scoped>
.compact-api-view {
  font-size: 13px;
  row-gap: 10px;
}

.compact-api-view .compact-panel {
  margin-bottom: 10px;
}

.compact-api-view textarea.form-control {
  font-size: 12px;
}
</style>
