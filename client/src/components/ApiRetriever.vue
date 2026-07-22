<template>
  <section class="api-retriever" v-if="tables && tables.length > 0">
    <header class="flow-header">
      <div>
        <span class="page-kicker">Data enrichment pipeline</span>
        <h2>Connect your data to an API</h2>
        <p>Map table columns to request parameters, inspect a real response and create an enriched dataset.</p>
      </div>
      <div class="flow-progress" aria-label="Configuration progress">
        <span class="progress-step complete"><i>1</i>Dataset</span>
        <b></b>
        <span class="progress-step" :class="{ complete: table }"><i>2</i>Endpoint</span>
        <b></b>
        <span class="progress-step" :class="{ complete: methodInfo || methodPathManualMode }"><i>3</i>Map</span>
        <b></b>
        <span class="progress-step" :class="{ complete: newTableName }"><i>4</i>Run</span>
      </div>
    </header>

    <div class="flow-layout">
      <main class="flow-main">
        <article class="step-card">
          <header class="step-header">
            <span class="step-number">01</span>
            <div><span class="step-label">Input</span><h3>Select a dataset</h3><p>Choose the local table whose rows will be enriched.</p></div>
            <span v-if="table" class="step-status"><i class="bi bi-check2"></i> Ready</span>
          </header>
          <div class="step-body dataset-step">
            <label class="field-label" for="tableSelector">Source table</label>
            <div class="select-control">
              <i class="bi bi-table"></i>
              <select id="tableSelector" v-model="table">
                <option :value="null" disabled>Select a table...</option>
                <option v-for="tableOption in tables" :key="tableOption" :value="tableOption">{{ tableOption }}</option>
              </select>
              <i class="bi bi-chevron-down"></i>
            </div>
            <div v-if="table && schema" class="schema-preview">
              <span v-for="(fieldType, field) in schema" :key="field"><b>{{ field }}</b><small>{{ fieldType }}</small></span>
            </div>
            <details v-if="table" class="dataset-preview">
              <summary><i class="bi bi-eye"></i> Preview source data</summary>
              <div><TableInspector :tableName="table" :showOptions="showOptions" /></div>
            </details>
          </div>
        </article>

        <article class="step-card" :class="{ locked: !table }">
          <header class="step-header">
            <span class="step-number">02</span>
            <div><span class="step-label">Connection</span><h3>Choose an API endpoint</h3><p>Discover a registered service or enter a URL manually.</p></div>
            <span v-if="methodInfo || methodPathManualMode" class="step-status"><i class="bi bi-check2"></i> Configured</span>
          </header>
          <div class="step-body" v-if="table">
            <div class="mode-selector">
              <label :class="{ active: mode === 'search' }">
                <input type="radio" name="apiMode" v-model="mode" value="search">
                <i class="bi bi-search"></i>
                <span><b>Discover service</b><small>Search the API catalogue</small></span>
                <em></em>
              </label>
              <label :class="{ active: mode === 'write' }">
                <input type="radio" name="apiMode" v-model="mode" value="write">
                <i class="bi bi-link-45deg"></i>
                <span><b>Direct URL</b><small>Use a known endpoint</small></span>
                <em></em>
              </label>
            </div>

            <div v-if="mode === 'search'" class="endpoint-config">
              <label class="field-label" for="apiServiceName">Find a service</label>
              <div class="text-control">
                <i class="bi bi-search"></i>
                <input id="apiServiceName" v-model="apiServiceName" type="search" placeholder="Search by service name..." @input="searchService(apiServiceName)">
              </div>

              <div v-if="services && services.length" class="result-list service-results">
                <button v-for="serviceOption in services" :key="serviceOption" :class="{ selected: service === serviceOption }" @click="searchMethod(serviceOption, '')">
                  <i class="bi bi-box"></i><span><b>{{ serviceOption }}</b><small>API service</small></span><i class="bi bi-chevron-right"></i>
                </button>
              </div>

              <div v-if="service" class="method-search">
                <div class="selected-service"><span>Selected service</span><b>{{ service }}</b></div>
                <label class="field-label" for="methodPath">Find an operation</label>
                <div class="text-control"><i class="bi bi-diagram-2"></i><input id="methodPath" v-model="methodPath" type="search" placeholder="Filter by method or path..." @input="searchMethod(service, methodPath)"></div>
                <div v-if="methods && methods.length" class="method-results">
                  <button v-for="methodOption in methods" :key="methodOption.path + methodOption.method" @click="clickMethod(service, methodOption)">
                    <span class="method-badge" :class="'method-' + methodOption.method.toLowerCase()">{{ methodOption.method }}</span>
                    <span><b>{{ methodOption.path }}</b><small>{{ methodOption.controller }}</small></span>
                    <i class="bi bi-arrow-right"></i>
                  </button>
                </div>
              </div>

              <div v-if="methodInfo" class="endpoint-summary">
                <div class="endpoint-title"><span class="method-badge" :class="'method-' + methodInfo.method.toLowerCase()">{{ methodInfo.method }}</span><code>{{ methodInfo.url }}</code></div>
                <div v-if="methodInfo.parameters && methodInfo.parameters.length" class="parameter-tags">
                  <span v-for="param in methodInfo.parameters" :key="param.name"><b>{{ param.name }}</b><small>{{ param.schema?.type || 'value' }} · {{ param.required ? 'required' : 'optional' }}</small></span>
                </div>
                <p v-else class="empty-note">This endpoint has no declared query parameters.</p>
              </div>
            </div>

            <div v-else class="endpoint-config">
              <label class="field-label" for="manualApiUrl">Endpoint URL</label>
              <div class="text-control"><i class="bi bi-link-45deg"></i><input id="manualApiUrl" v-model="methodPathManualMode" type="url" placeholder="https://service/api?param={column}"></div>
              <p class="field-help"><i class="bi bi-info-circle"></i> Use placeholders such as <code>{customer_id}</code> to represent values from your table.</p>
            </div>
          </div>
          <div class="locked-message" v-else><i class="bi bi-lock"></i><span>Select a source table to configure the endpoint.</span></div>
        </article>

        <article class="step-card" v-if="methodInfo || methodPathManualMode">
          <header class="step-header">
            <span class="step-number">03</span>
            <div><span class="step-label">Request mapping</span><h3>Connect fields and test</h3><p>Map request parameters and validate the API response with the first row.</p></div>
          </header>
          <div class="step-body mapping-layout">
            <section class="mapping-panel">
              <div class="subsection-title"><i class="bi bi-bezier2"></i><div><h4>Parameter mapping</h4><p>Choose the source column for each request value.</p></div></div>
              <div v-if="mode === 'search' && methodInfo">
                <div v-for="param in methodInfo.parameters" :key="param.name" class="mapping-row">
                  <div><b>{{ param.name }}</b><small>{{ param.required ? 'Required' : 'Optional' }}</small></div>
                  <i class="bi bi-arrow-right"></i>
                  <select :id="'fieldSelector-' + param.name" v-model="selectedFields[param.name]" @change="buildQueryString">
                    <option value="">Do not map</option>
                    <option v-for="(fieldType, field) in schema" :key="field" :value="field">{{ field }} · {{ fieldType }}</option>
                  </select>
                </div>
              </div>
              <div v-if="mode === 'write'" class="manual-mapping">
                <label class="field-label" for="fieldSelector">Placeholder field</label>
                <div class="text-control"><i class="bi bi-braces"></i><input id="fieldSelector" v-model="selectedFields.field" placeholder="Column name" @change="buildQueryString"></div>
              </div>
            </section>

            <section class="response-panel">
              <div class="subsection-title"><i class="bi bi-braces-asterisk"></i><div><h4>Response preview</h4><p>Sample generated from the first source row.</p></div></div>
              <div v-if="fullUrlExample" class="request-url"><span>GET</span><code>{{ fullUrlExample }}</code></div>
              <pre v-if="sampleResponse">{{ JSON.stringify(sampleResponse, null, 2) }}</pre>
              <div v-else class="response-empty"><i class="bi bi-send"></i><p>Map a parameter to send a sample request.</p></div>
            </section>
          </div>
        </article>

        <article class="step-card output-card" :class="{ locked: !table }">
          <header class="step-header">
            <span class="step-number">04</span>
            <div><span class="step-label">Output</span><h3>Build the enriched table</h3><p>Choose which response fields to keep and where to store them.</p></div>
          </header>
          <div class="step-body" v-if="table">
            <div class="extract-header"><div><h4>Response fields</h4><p>Leave the JSON path empty to store the complete response.</p></div><button class="add-mapping" @click="addMapping"><i class="bi bi-plus-lg"></i> Add field</button></div>
            <div class="extract-list">
              <div v-for="(mapping, index) in mappings" :key="index" class="extract-row">
                <span class="mapping-index">{{ String(index + 1).padStart(2, '0') }}</span>
                <div><label>JSON path</label><input v-model="mapping.jsonField" placeholder="data.customer.segment"></div>
                <i class="bi bi-arrow-right"></i>
                <div><label>New column</label><input v-model="mapping.newFieldName" placeholder="customer_segment"></div>
              </div>
            </div>
            <button v-if="mappings.length" class="clear-mappings" @click="deleteAllMappings"><i class="bi bi-trash3"></i> Clear mappings</button>

            <div class="run-config">
              <div><label for="recordsToProcess">Rows to process</label><input id="recordsToProcess" v-model="recordsToProcess" placeholder="10"><small>Leave empty to process every row</small></div>
              <div><label for="newTableName">Output table</label><input id="newTableName" v-model="newTableName" placeholder="enrichedTable"><small>A new local table will be created</small></div>
              <button v-if="newTableName" class="run-button" @click="runDataEnrichment()">Run</button>
            </div>
          </div>
        </article>
      </main>

      <aside class="flow-summary">
        <div class="summary-card">
          <span class="summary-kicker">Pipeline summary</span>
          <h3>Enrichment job</h3>
          <dl>
            <div><dt><i class="bi bi-table"></i> Dataset</dt><dd>{{ table || 'Not selected' }}</dd></div>
            <div><dt><i class="bi bi-box"></i> Service</dt><dd>{{ mode === 'write' ? 'Direct URL' : (service || 'Not selected') }}</dd></div>
            <div><dt><i class="bi bi-signpost-2"></i> Endpoint</dt><dd>{{ methodInfo?.method || (methodPathManualMode ? 'URL' : 'Not selected') }}</dd></div>
            <div><dt><i class="bi bi-bezier2"></i> Parameters</dt><dd>{{ Object.keys(selectedFields).filter(key => selectedFields[key]).length }} mapped</dd></div>
            <div><dt><i class="bi bi-layout-three-columns"></i> Output fields</dt><dd>{{ mappings.length }}</dd></div>
          </dl>
          <div class="summary-output" :class="{ ready: newTableName }"><span>Output</span><b>{{ newTableName || 'Name your result table' }}</b></div>
        </div>
        <div class="summary-tip"><i class="bi bi-lightbulb"></i><p><b>Start with a small sample.</b> Test 10 rows before processing the complete dataset.</p></div>
      </aside>
    </div>
  </section>

  <section v-else class="api-empty">
    <i class="bi bi-database-exclamation"></i>
    <h2>No data available</h2>
    <p>Load a table before creating an API enrichment pipeline.</p>
  </section>
</template>
<script setup>
import { ref, watch } from 'vue';
import TableInspector from './TableInspector.vue';

import api from '../services/api';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

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
  const fetchData = async () => await api.get(`/apiRetriever/getServices`, {
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
  const fetchData = async () => await api.get(`/apiRetriever/getRepositoryMethodList`, {
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
  const fetchData = async () => await api.get(`/apiRetriever/getMethodInfo`, {
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
  const fetchData = async () => await api.get(`/database/getTableSchema`, {
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

  await api.get(`/database/getSampleData`, {
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
  const fieldNames = rows[0].split(',');
  const firstDataRow = (rows[1] || '').split(',');
  const valueForField = (field) => {
    const index = fieldNames.indexOf(field);
    return index >= 0 ? firstDataRow[index] : field;
  };

  const queryParameters = [];
  for (const [parameter, sourceField] of Object.entries(selectedFields.value)) {
    if (!sourceField || parameter === 'field') continue;
    queryParameters.push(`${parameter}=${encodeURIComponent(valueForField(sourceField))}`);
  }

  if (mode.value === 'write') {
    fullUrl.value = methodPathManualMode.value;
    const sourceField = selectedFields.value.field;
    const sampleValue = sourceField ? encodeURIComponent(valueForField(sourceField)) : '';
    fullUrlExample.value = methodPathManualMode.value.replace(/\{[^}]+\}/g, sampleValue);
  } else {
    fullUrl.value = methodInfo.value?.url || '';
    const queryString = queryParameters.join('&');
    fullUrlExample.value = queryString ? `${fullUrl.value}?${queryString}` : fullUrl.value;
  }

  if (!fullUrlExample.value) return;

  const fetchData = async () => await axios.get(fullUrlExample.value, {});

  toast.promise(
    fetchData(),
    {
      pending: 'Loading example request...',
      success: 'Example loaded',
      error: 'Error loading sample data'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    sampleResponse.value = response.data;
  }).catch((error) => {
    toast.error(error.response?.data?.message || 'Error loading the API response', {
      position: toast.POSITION.BOTTOM_RIGHT
    });
  });
}

function addMapping() {
  mappings.value.push({ jsonField: '', newFieldName: '' });
}

function deleteAllMappings() {
  mappings.value = [];
}

async function runDataEnrichment() {
  const fetchData = async () => await api.post(`/apiRetriever/runApiEnrichment`, {
    tableName: table.value,
    parameters: selectedFields.value,
    mappings: mappings.value,
    recordsToProcess: recordsToProcess.value,
    service: service.value,
    method: method.value,
    url: fullUrl.value || methodPathManualMode.value,
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
.api-retriever{display:grid;gap:13px}.flow-header{display:flex;align-items:center;justify-content:space-between;gap:30px;padding:20px 22px;border:1px solid var(--ds-line);border-radius:13px;background:linear-gradient(115deg,#fff,#f0f8f5);box-shadow:0 8px 28px rgba(31,67,58,.045)}.page-kicker,.step-label,.summary-kicker{color:#7f8e89;font-size:8px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.flow-header h2{margin:2px 0 3px;color:var(--ds-ink);font-size:1.25rem;font-weight:760;letter-spacing:-.03em}.flow-header p{margin:0;color:var(--ds-muted);font-size:10px}.flow-progress{display:flex;align-items:center;min-width:430px}.flow-progress>b{flex:1;height:1px;background:#d8e4e0}.progress-step{display:grid;justify-items:center;gap:3px;color:#9aa5a2;font-size:8px;font-weight:700}.progress-step i{width:24px;height:24px;display:grid;place-items:center;border:1px solid #d6e1de;border-radius:50%;background:#fff;font-style:normal}.progress-step.complete{color:var(--ds-teal-dark)}.progress-step.complete i{border-color:var(--ds-teal);background:var(--ds-teal);color:#fff}.flow-layout{display:grid;grid-template-columns:minmax(0,1fr) 245px;gap:13px;align-items:start}.flow-main{display:grid;gap:11px}.step-card{overflow:hidden;border:1px solid var(--ds-line);border-radius:13px;background:#fff;box-shadow:0 7px 24px rgba(31,67,58,.04)}.step-header{display:grid;grid-template-columns:34px minmax(0,1fr) auto;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid var(--ds-line);background:#fbfcfc}.step-number{width:31px;height:31px;display:grid;place-items:center;border-radius:9px;background:var(--ds-mint);color:var(--ds-teal-dark);font-size:9px;font-weight:800}.step-header h3{margin:0;color:var(--ds-ink);font-size:.96rem;font-weight:750;letter-spacing:-.02em}.step-header p{margin:1px 0 0;color:#83908c;font-size:9px}.step-status{display:flex;align-items:center;gap:4px;padding:4px 7px;border-radius:20px;background:#e8f6f1;color:var(--ds-teal-dark);font-size:8px;font-weight:750}.step-body{padding:16px}.field-label{display:block;margin-bottom:6px;color:#53635f;font-size:9px;font-weight:750}.select-control,.text-control{height:39px;display:grid;grid-template-columns:30px minmax(0,1fr) 20px;align-items:center;max-width:520px;border:1px solid #d8e3df;border-radius:8px;background:#f9fbfa;color:#80908b}.select-control:focus-within,.text-control:focus-within{border-color:#73baa8;box-shadow:0 0 0 3px rgba(13,132,111,.08);background:#fff}.select-control select,.text-control input{width:100%;height:100%;border:0;outline:0;background:transparent;color:var(--ds-ink);font-size:10px}.text-control{grid-template-columns:30px minmax(0,1fr)}.schema-preview{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px}.schema-preview>span{display:flex;align-items:center;gap:5px;padding:4px 6px;border:1px solid #e0e8e5;border-radius:6px;background:#f8faf9}.schema-preview b{font-size:8px}.schema-preview small{color:#909c98;font-size:7px;text-transform:uppercase}.dataset-preview{margin-top:12px;border-top:1px solid var(--ds-line)}.dataset-preview summary{padding:10px 1px 0;cursor:pointer;color:var(--ds-teal-dark);font-size:9px;font-weight:700}.dataset-preview>div{margin-top:10px}.mode-selector{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:15px}.mode-selector label{position:relative;display:grid;grid-template-columns:34px 1fr 16px;align-items:center;gap:8px;padding:10px;border:1px solid #dfe7e4;border-radius:9px;background:#fafcfb;cursor:pointer}.mode-selector label.active{border-color:#83bfae;background:#edf8f4}.mode-selector input{position:absolute;opacity:0}.mode-selector label>i{width:32px;height:32px;display:grid;place-items:center;border-radius:8px;background:#e8efed;color:#6e7e79}.mode-selector label.active>i{background:#d9f0e9;color:var(--ds-teal)}.mode-selector label>span{display:grid}.mode-selector b{font-size:10px}.mode-selector small{color:#899691;font-size:8px}.mode-selector em{width:13px;height:13px;border:1px solid #bdcbc7;border-radius:50%}.mode-selector label.active em{border:4px solid var(--ds-teal)}.endpoint-config{display:grid;gap:9px}.result-list{display:flex;flex-wrap:wrap;gap:6px}.result-list button{display:grid;grid-template-columns:25px 1fr 15px;align-items:center;min-width:160px;padding:7px;border:1px solid #dce6e3;border-radius:8px;background:#fff;color:#61716c;text-align:left}.result-list button:hover,.result-list button.selected{border-color:#93c8ba;background:#f0f8f5}.result-list button>span{display:grid}.result-list b{font-size:9px}.result-list small{color:#929e9a;font-size:7px}.method-search{display:grid;gap:8px;margin-top:4px;padding-top:12px;border-top:1px solid var(--ds-line)}.selected-service{display:flex;align-items:center;gap:8px;color:#87938f;font-size:8px}.selected-service b{padding:3px 6px;border-radius:5px;background:var(--ds-mint);color:var(--ds-teal-dark)}.method-results{display:grid;gap:4px;max-height:210px;overflow:auto}.method-results button{display:grid;grid-template-columns:45px minmax(0,1fr) 18px;align-items:center;gap:8px;padding:7px;border:1px solid transparent;border-radius:7px;background:#f7faf9;color:#5d6d68;text-align:left}.method-results button:hover{border-color:#d4e3de;background:#fff}.method-results button>span:nth-child(2){display:grid}.method-results b{overflow:hidden;text-overflow:ellipsis;font:700 9px ui-monospace,monospace}.method-results small{color:#909c98;font-size:7px}.method-badge{display:inline-grid;place-items:center;width:max-content;min-width:38px;padding:3px 5px;border-radius:5px;background:#e6f3ef;color:#08735f;font-size:7px;font-weight:850}.method-post{background:#eaf0fb;color:#365f9e}.method-delete{background:#fbeaec;color:#b43d4c}.method-put,.method-patch{background:#fff2dd;color:#9b6817}.endpoint-summary{margin-top:5px;padding:11px;border:1px solid #cfe3dd;border-radius:9px;background:#f4faf8}.endpoint-title{display:flex;align-items:center;gap:8px}.endpoint-title code{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#40514c;font-size:9px}.parameter-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:9px}.parameter-tags span{display:grid;padding:4px 6px;border-radius:5px;background:#fff}.parameter-tags b{font-size:8px}.parameter-tags small{color:#8b9793;font-size:7px}.empty-note,.field-help{margin:4px 0 0;color:#83908c;font-size:8px}.field-help code{color:var(--ds-teal-dark)}.locked{background:#fafcfb}.locked-message{display:flex;align-items:center;justify-content:center;gap:8px;padding:22px;color:#98a39f;font-size:9px}.mapping-layout{display:grid;grid-template-columns:1fr 1fr;gap:12px}.mapping-panel,.response-panel{min-width:0;padding:12px;border:1px solid var(--ds-line);border-radius:10px;background:#f9fbfa}.subsection-title{display:flex;align-items:center;gap:9px;margin-bottom:11px}.subsection-title>i{width:30px;height:30px;display:grid;place-items:center;border-radius:8px;background:var(--ds-mint);color:var(--ds-teal)}.subsection-title h4,.extract-header h4{margin:0;font-size:.82rem;font-weight:750}.subsection-title p,.extract-header p{margin:1px 0 0;color:#87938f;font-size:8px}.mapping-row{display:grid;grid-template-columns:100px 18px minmax(0,1fr);align-items:center;gap:5px;padding:7px 0;border-top:1px solid #e5ece9}.mapping-row>div{display:grid}.mapping-row b{font-size:9px}.mapping-row small{color:#909b98;font-size:7px}.mapping-row>i{color:#9ba7a3}.mapping-row select{min-width:0;height:31px;border:1px solid #d8e3df;border-radius:7px;background:#fff;color:#4c5d58;font-size:8px}.request-url{display:flex;align-items:center;gap:7px;padding:6px;border-radius:6px;background:#e9f5f1}.request-url span{color:var(--ds-teal-dark);font-size:7px;font-weight:850}.request-url code{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#43534f;font-size:8px}.response-panel pre{max-height:250px;margin:8px 0 0;padding:10px;overflow:auto;border-radius:7px;background:#17211f;color:#bde9de;font-size:8px}.response-empty{min-height:135px;display:grid;place-items:center;align-content:center;color:#98a39f;text-align:center}.response-empty i{font-size:20px}.response-empty p{font-size:8px}.extract-header{display:flex;align-items:center;justify-content:space-between;gap:12px}.add-mapping{display:flex;align-items:center;gap:5px;padding:6px 9px;border:0;border-radius:7px;background:var(--ds-mint);color:var(--ds-teal-dark);font-size:9px;font-weight:750}.extract-list{display:grid;gap:5px;margin-top:10px}.extract-row{display:grid;grid-template-columns:25px minmax(0,1fr) 20px minmax(0,1fr);align-items:end;gap:7px;padding:8px;border:1px solid #e1e9e6;border-radius:8px;background:#f9fbfa}.mapping-index{align-self:center;color:#9aa5a2;font-size:8px;font-weight:800}.extract-row>div{display:grid}.extract-row label,.run-config label{margin-bottom:3px;color:#71807b;font-size:8px;font-weight:750}.extract-row input,.run-config input{height:32px;padding:0 8px;border:1px solid #d8e3df;border-radius:7px;background:#fff;color:var(--ds-ink);font-size:9px;outline:0}.extract-row input:focus,.run-config input:focus{border-color:#73baa8;box-shadow:0 0 0 3px rgba(13,132,111,.07)}.extract-row>i{align-self:center;color:#93a09c}.clear-mappings{margin-top:8px;padding:4px 0;border:0;background:transparent;color:#a85b64;font-size:8px}.run-config{display:grid;grid-template-columns:1fr 1fr auto;align-items:end;gap:9px;margin-top:14px;padding:12px;border-radius:10px;background:#17211f}.run-config>div{display:grid}.run-config label{color:#b5c4c0}.run-config small{margin-top:3px;color:#71847f;font-size:7px}.run-button{height:32px;padding:0 18px;border:0;border-radius:7px;background:#73cbb6;color:#10241f;font-size:9px;font-weight:850}.flow-summary{position:sticky;top:95px;display:grid;gap:10px}.summary-card,.summary-tip{padding:15px;border:1px solid var(--ds-line);border-radius:12px;background:#fff}.summary-card h3{margin:2px 0 13px;font-size:.93rem;font-weight:750}.summary-card dl{display:grid;gap:0;margin:0}.summary-card dl>div{display:grid;grid-template-columns:1fr 1fr;gap:5px;padding:8px 0;border-top:1px solid #edf1f0}.summary-card dt{color:#7b8985;font-size:8px;font-weight:650}.summary-card dt i{margin-right:4px;color:var(--ds-teal)}.summary-card dd{margin:0;overflow:hidden;text-overflow:ellipsis;color:#3f504b;font-size:8px;font-weight:750;text-align:right;white-space:nowrap}.summary-output{display:grid;margin-top:10px;padding:9px;border-radius:8px;background:#f2f5f4;color:#87938f}.summary-output.ready{background:#e6f5f0;color:var(--ds-teal-dark)}.summary-output span{font-size:7px;text-transform:uppercase}.summary-output b{overflow:hidden;text-overflow:ellipsis;font-size:9px;white-space:nowrap}.summary-tip{display:flex;gap:9px;background:#f8faf9;color:#71807b}.summary-tip>i{color:#bd842f}.summary-tip p{margin:0;font-size:8px}.api-empty{min-height:360px;display:grid;place-items:center;align-content:center;border:1px dashed #c7d7d2;border-radius:13px;background:#f8fbfa;text-align:center}.api-empty>i{font-size:28px;color:#8fb0a7}.api-empty h2{margin:10px 0 0;font-size:1rem}.api-empty p{color:var(--ds-muted);font-size:10px}
@media(max-width:1100px){.flow-layout{grid-template-columns:1fr}.flow-summary{position:static;grid-template-columns:1fr 1fr}.flow-progress{min-width:350px}}
@media(max-width:760px){.flow-header{align-items:flex-start;flex-direction:column}.flow-progress{width:100%;min-width:0}.progress-step{font-size:0}.flow-layout{display:block}.flow-main{gap:9px}.flow-summary{grid-template-columns:1fr;margin-top:9px}.step-header{grid-template-columns:31px 1fr}.step-status{display:none}.mode-selector,.mapping-layout{grid-template-columns:1fr}.extract-row{grid-template-columns:22px 1fr}.extract-row>i{display:none}.run-config{grid-template-columns:1fr}.schema-preview{max-height:90px;overflow:auto}}
</style>