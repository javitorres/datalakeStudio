<template>

  <!-- Show endpoints list  -->
  <div class="form-group compact-panel compact-api-server" v-if="activeTab === 'listEndpoints'">
    <h2 class="compact-title">{{ t('ApiServer.title') }}</h2>
    <div  v-if="availableEndpoints && availableEndpoints.length == 0">
      <p class="compact-muted">{{ t('ApiServer.empty') }}</p>
    </div>
    
    <div v-if="availableEndpoints && availableEndpoints.length > 0">

      <div class="table-responsive">
      <table class="table table-striped table-hover table-bordered table-sm">
        <thead>
          <tr class="table-primary">
            <th>{{ t('ApiServer.columns.id') }}</th>
            <th>{{ t('ApiServer.columns.endpoint') }}</th>
            <th>{{ t('ApiServer.columns.description') }}</th>
            <th>{{ t('ApiServer.columns.url') }}</th>
            <th>{{ t('ApiServer.columns.parameters') }}</th>
            <th>id_query</th>
            <th>{{ t('ApiServer.columns.status') }}</th>
            <th>{{ t('ApiServer.columns.query') }}</th>
            <th>{{ t('ApiServer.columns.example') }}</th>

            <th>{{ t('ApiServer.columns.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="endpointItem in availableEndpoints" :key="endpointItem.id_endpoint">
            <td>{{ endpointItem.id_endpoint }}</td>
            <td>{{ endpointItem.endpoint }}</td>
            <td>{{ endpointItem.description }}</td>
            <td>
              <a :href="`${apiUrl}/api/${endpointItem.endpoint}`" target="_blank">{{ apiUrl }}/api/{{ endpointItem.endpoint }}</a>
            </td>
            <td>{{ endpointItem.parameters }}</td>
            <td>{{ endpointItem.id_query }}</td>
            <td>{{ endpointItem.status }}</td>
            <td>{{ endpointItem.query }}</td>
            <td>
              <a :href="`${apiUrl}/api/${endpointItem.endpoint}${endpointItem.queryStringTest}`" target="_blank">{{ apiUrl
              }}/api/{{ endpointItem.endpoint }}{{ endpointItem.queryStringTest }}</a>
            </td>
            <td>
              <button type="button" class="btn btn-danger" @click="deleteEndpoint(endpointItem.id_endpoint)">{{ t('ApiServer.delete') }}</button>
              <button type="button" class="btn btn-secondary" @click="editEndpoint(endpointItem)">{{ t('ApiServer.edit') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>

    </div>
    
    <button type="button" class="btn btn-sm btn-primary" @click="createEmptyEndpoint">{{ t('ApiServer.createNew') }}</button>
  </div>





  <!-- Endpoint editor  -->
  <div class="form-group compact-panel compact-api-server" v-if="activeTab === 'newEndpoint' || activeTab === 'editEndpoint'">
    <h2 class="compact-title">{{ t('ApiServer.editTitle') }}</h2>

    <p class="compact-muted">{{ t('ApiServer.selectQueryHelp') }}</p>
    <div class="input-group mb-3 compact-input-group">
      <span class="input-group-text" id="basic-addon1">{{ t('ApiServer.searchQuery') }}</span>
      <input type="text" class="form-control" :placeholder="t('ApiServer.queryName')" v-model="sqlSearchQuery" @input="searchQuery">
    </div>

    <div v-if="queries && queries.length > 0">
      <ul class="list-group d-flex flex-wrap compact-query-list">
        <li v-for="queryCandidate in queries" :key="queryCandidate.id_query" class="list-group-item"
          @click="selectQuery(queryCandidate)">
          <b>{{ t('ApiServer.queryItem.id') }}</b>{{ queryCandidate.id_query }} <b>{{ t('ApiServer.queryItem.name') }}</b> {{ queryCandidate.name }}<br /><b>{{ t('ApiServer.queryItem.description') }}</b>{{
            queryCandidate.description }}<br /><b>{{ t('ApiServer.queryItem.sql') }}</b>{{ queryCandidate.query }}
        </li>
      </ul>
    </div>
    

    <div v-if="activeTab === 'editEndpoint' && ! endpointForm.id_endpoint">
      <p class="compact-muted">{{ t('ApiServer.noEndpointSelected') }}</p>
    </div>

    

      <p class="compact-muted">{{ t('ApiServer.parametersHelp') }}</p>
      <div class="form-group">
        <codemirror v-model="endpointForm.query" :placeholder="t('ApiServer.codePlaceholder')" :style="{ height: '240px' }"
          :autofocus="true" :indent-with-tab="true" :tab-size="4" :extensions="extensions"
          @change="sqlChanged('change', $event)" />
      </div>
      <div class="col-md-3">
        <div class="input-group mb-3 compact-input-group mt-2">
          <span class="input-group-text" id="basic-addon1">{{ t('ApiServer.endpoint') }}</span>
          <input type="text" class="form-control" :placeholder="t('ApiServer.endpointName')" v-model="endpointForm.endpoint">
        </div>
      </div>
    
    <h3 v-if="endpointForm.endpoint">{{ t('ApiServer.url', { url: `${apiUrl}/api/${endpointForm.endpoint}${(endpointForm.parameters && endpointForm.parameters.length > 0) ?
      endpointForm.queryStringTest : ''}` }) }}</h3>

    <!-- For each parameter an imput -->
    <div v-if="endpointForm.query && endpointForm.parameters && endpointForm.parameters.length > 0">
      <div class="col-md-4" v-for="parameter in endpointForm.parameters" :key="parameter">
        <div class="input-group mb-3 compact-input-group">
          <span class="input-group-text" id="basic-addon1">{{ parameter.name }}</span>
          <input type="text" class="form-control" :placeholder="t('ApiServer.exampleValuePlaceholder')"
            v-model="parameter.exampleValue" @keyup="rebuildQueryStringTest">
        </div>
      </div>
    </div>



    <!-- Description -->
    <div v-if="endpointForm.endpoint">
      <div class="input-group mb-3 compact-input-group">
        <span class="input-group-text" id="basic-addon1">{{ t('ApiServer.description') }}</span>
        <input type="text" class="form-control" :placeholder="t('ApiServer.description')" v-model="endpointForm.description">
      </div>
    </div>

    <!-- status: combo with DEV, READY-->
    <div v-if="endpointForm.endpoint">
      <div class="input-group mb-3 compact-input-group">
        <span class="input-group-text" id="basic-addon1">{{ t('ApiServer.status') }}</span>
        <select class="form-select" v-model="endpointForm.status">
          <option value="DEV">DEV</option>
          <option value="PROD">PROD</option>
        </select>
      </div>
    </div>

    <!-- Simulate endpoint -->
    <div v-if="endpointForm.query">
      <button type="button" class="btn btn-sm btn-primary" @click="testEndpoint">{{ t('ApiServer.saveAndTest') }}</button>
    </div>

    <!-- Cancel button, go to list of endpoints -->
    <div v-if="endpointForm.query" class="mt-2">
      <button type="button" class="btn btn-sm btn-danger" @click="activeTab = 'listEndpoints'">{{ t('ApiServer.cancelAndBack') }}</button>
    </div>

    <!-- Show json response -->
    <div v-if="endpointForm.query && response" class="mt-2">
      <div class="input-group mb-3 compact-input-group">
        <span class="input-group-text" id="basic-addon1">{{ t('ApiServer.response') }}</span>
        <textarea class="form-control" :aria-label="t('ApiServer.responseAria')" v-model="response" rows="15"></textarea>
      </div>
    </div>

    <!-- Publish button 
      TODO: Change property status to DEV or PROD
      <div v-if="endpoint.query && endpoint.endpoint && endpoint.description">
        <br />
        <button type="button" class="btn btn-primary" @click="publish">Publish</button>
      </div>
      -->
    
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '../services/api';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { Codemirror } from "vue-codemirror";
import { sql } from "@codemirror/lang-sql";

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

const { t } = useI18n();

const extensions = [sql()];

const sqlSearchQuery = ref(null);
const queries = ref([]);
const endpointForm = ref({
  id_query: null,
  id_endpoint: null,
  endpoint: null,
  query: null,
  parameters: [],
  description: null,
  queryStringTest: null,
  status: 'DEV'
});
const response = ref(null);
const activeTab = ref('listEndpoints');
const availableEndpoints = ref(null);
const published = ref(false);

onMounted(() => {
  reloadAvailableEndpoints();
});

function sqlChanged(event, editor) {
  const oldParameters = endpointForm.value.parameters || [];
  endpointForm.value.parameters = [];
  const regex = /{([^}]+)}/g;
  let m;
  while ((m = regex.exec(endpointForm.value.query || '')) !== null) {
    if (m.index === regex.lastIndex) {
      regex.lastIndex++;
    }

    m.forEach((match, groupIndex) => {
      if (groupIndex == 1) {
        endpointForm.value.parameters.push({ "name": match, "exampleValue": null });
      }
    });
  }
  for (let i = 0; i < endpointForm.value.parameters.length; i++) {
    for (let j = 0; j < oldParameters.length; j++) {
      if (endpointForm.value.parameters[i].name == oldParameters[j].name) {
        endpointForm.value.parameters[i].exampleValue = oldParameters[j].exampleValue;
      }
    }
  }

  rebuildQueryStringTest();
}

function rebuildQueryStringTest() {
  endpointForm.value.queryStringTest = "?";
  for (let i = 0; i < endpointForm.value.parameters.length; i++) {
    endpointForm.value.queryStringTest += endpointForm.value.parameters[i].name + "=" + endpointForm.value.parameters[i].exampleValue + "&";
  }
  endpointForm.value.queryStringTest = endpointForm.value.queryStringTest.slice(0, -1);
}

async function searchQuery() {
  const fetchData = async () => await api.get(`/queries/searchQuery`, {
    params: {
      query: sqlSearchQuery.value,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: t('ApiServer.toast.searchingQueries'),
      success: t('ApiServer.toast.queriesLoaded'),
      error: t('ApiServer.toast.queriesError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    queries.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function selectQuery(queryCandidate) {
  sqlSearchQuery.value = queryCandidate.name;
  queries.value = [];

  endpointForm.value.endpoint = queryCandidate.name;
  endpointForm.value.id_query = queryCandidate.id_query;
  endpointForm.value.query = queryCandidate.query;
}

async function createEmptyEndpoint() {
  const fetchData = async () => await api.get(`/apiserver/create`, {
    params: {
      endpoint: endpointForm.value.endpoint,
    },

  });

  return toast.promise(
    fetchData(),
    {
      pending: t('ApiServer.toast.creating'),
      success: t('ApiServer.toast.created'),
      error: t('ApiServer.toast.createError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    endpointForm.value.id_endpoint = response.data.id_endpoint;
    reloadAvailableEndpoints();

  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function testEndpoint() {
  if (endpointForm.value.id_endpoint == null) {
    await createEmptyEndpoint();
  }

  await update();

  const path = "/api/" + endpointForm.value.endpoint + ((endpointForm.value.parameters.length > 0) ? endpointForm.value.queryStringTest : "");
  const url = apiUrl + path;

  toast.info(t('ApiServer.testingUrl', { url }), { position: toast.POSITION.BOTTOM_RIGHT });
  const fetchData = async () => await api.get(path, {});

  toast.promise(
    fetchData(),
    {
      pending: t('ApiServer.toast.testing'),
      success: t('ApiServer.toast.tested'),
      error: t('ApiServer.toast.testError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((result) => {
    response.value = JSON.stringify(result.data, null, 2);
  }).catch((error) => {
    if (error.response && error.response.status === 400) {
      response.value = JSON.stringify(error.response.data, null, 2);
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      response.value = JSON.stringify(error, null, 2);
      toast.error(t('ApiServer.errorDetail', { detail: error }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function update() {
  const fetchData = async () => await api.post(`/apiserver/update`, {
    id_query: endpointForm.value.id_query,
    id_endpoint: endpointForm.value.id_endpoint,
    endpoint: endpointForm.value.endpoint,
    parameters: endpointForm.value.parameters,
    description: endpointForm.value.description,
    queryStringTest: endpointForm.value.queryStringTest,
    status: endpointForm.value.status,
    query: btoa(endpointForm.value.query || '')

  });

  return toast.promise(
    fetchData(),
    {
      pending: t('ApiServer.toast.publishing'),
      success: t('ApiServer.toast.published'),
      error: t('ApiServer.toast.publishError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    published.value = true;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function reloadAvailableEndpoints() {
  const fetchData = async () => await api.get(`/apiserver/listEndpoints`, {});

  toast.promise(
    fetchData(),
    {
      error: t('ApiServer.toast.listError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((result) => {
    availableEndpoints.value = result.data;
    activeTab.value = 'listEndpoints';
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function deleteEndpoint(id_endpoint) {
  const fetchData = async () => await api.get(`/apiserver/deleteEndpoint`, {
    params: {
      id_endpoint: id_endpoint
    },

  });

  toast.promise(
    fetchData(),
    {
      pending: t('ApiServer.toast.deleting'),
      success: t('ApiServer.toast.deleted'),
      error: t('ApiServer.toast.deleteError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    reloadAvailableEndpoints();
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function editEndpoint(selectedEndpoint) {
  const fetchData = async () => await api.get(`/apiserver/getEndpoint`, {
    params: {
      id_endpoint: selectedEndpoint.id_endpoint,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: t('ApiServer.toast.loading'),
      success: t('ApiServer.toast.loaded'),
      error: t('ApiServer.toast.loadError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((result) => {
    endpointForm.value = JSON.parse(JSON.stringify(result.data));
    if (typeof endpointForm.value.parameters === 'string') {
      try {
        endpointForm.value.parameters = JSON.parse(endpointForm.value.parameters);
      } catch {
        endpointForm.value.parameters = [];
      }
    }
    activeTab.value = 'editEndpoint';
  }).catch((error) => {
    // Fallback for older backends (without /getEndpoint) or missing ids.
    if (error.response?.status === 404) {
      endpointForm.value = JSON.parse(JSON.stringify(selectedEndpoint));
      if (typeof endpointForm.value.parameters === 'string') {
        try {
          endpointForm.value.parameters = JSON.parse(endpointForm.value.parameters);
        } catch {
          endpointForm.value.parameters = [];
        }
      }
      activeTab.value = 'editEndpoint';
      toast.info(t('ApiServer.loadedFromList'), { position: toast.POSITION.BOTTOM_RIGHT });
      return;
    }

    if (error.response?.data?.message) {
      toast.error(t('ApiServer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('ApiServer.errorDetail', { detail: error.response?.data || error.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}
</script>

<style scoped>
.compact-api-server {
  font-size: 13px;
}

.compact-api-server table td,
.compact-api-server table th {
  font-size: 12px;
  vertical-align: middle;
}

.compact-api-server .btn {
  font-size: 12px;
}

.compact-query-list {
  gap: 6px;
}

.compact-query-list .list-group-item {
  cursor: pointer;
  font-size: 12px;
  line-height: 1.3;
  border-radius: 8px;
  border: 1px solid #dbe0ea;
  background: #f8f9fc;
}

.compact-query-list .list-group-item:hover {
  background: #edf1fa;
}
</style>
