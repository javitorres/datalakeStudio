<template>

  <!-- Show endpoints list  -->
  <div class="form-group" v-if="activeTab === 'listEndpoints'">
    <h2>Published endpoints</h2>
    <br />
    <div  v-if="availableEndpoints && availableEndpoints.length == 0">
      <p >No endpoints published </p>
    </div>
    
    <div v-if="availableEndpoints && availableEndpoints.length > 0">

      <table class="table table-striped table-hover table-bordered">
        <thead>
          <tr class="table-primary">
            <th>ID</th>
            <th>Endpoint</th>
            <th>Description</th>
            <th>URL</th>
            <th>Parameters</th>
            <th>id_query</th>
            <th>status</th>
            <th>query</th>
            <th>Example</th>

            <th>Actions</th>
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
              <button type="button" class="btn btn-danger" @click="deleteEndpoint(endpointItem.id_endpoint)">Delete</button>
              <button type="button" class="btn btn-secondary" @click="editEndpoint(endpointItem)">Edit</button>
            </td>
          </tr>
        </tbody>
      </table>


    </div>
    
    <button type="button" class="btn btn-primary" @click="createEmptyEndpoint">Create new endpoint</button>
  </div>





  <!-- Endpoint editor  -->
  <div class="form-group" v-if="activeTab === 'newEndpoint' || activeTab === 'editEndpoint'">
    <h2>Edit endpoint</h2>
    <br />

    <p>Select the query your endpoint will be based on</p>
    <div class="input-group mb-3">
      <span class="input-group-text" id="basic-addon1">Search query</span>
      <input type="text" class="form-control" placeholder="Query name" v-model="sqlSearchQuery" @input="searchQuery">
    </div>

    <div v-if="queries && queries.length > 0">
      <ul class="list-group d-flex flex-wrap">
        <li v-for="queryCandidate in queries" :key="queryCandidate.id_query" class="list-group-item"
          @click="selectQuery(queryCandidate)">
          <b>id:</b>{{ queryCandidate.id_query }} <b>Name:</b> {{ queryCandidate.name }}<br /><b>Description:</b>{{
            queryCandidate.description }}<br /><b>SQL:</b>{{ queryCandidate.query }}
        </li>
      </ul>
    </div>
    

    <div v-if="activeTab === 'editEndpoint' && ! endpointForm.id_endpoint">
      <p>No endpoint selected, select one of published endpoints list</p>
    </div>

    

      <p>Add any {parameter} in your SQL query to add query params:</p>
      <div class="form-group">
        <codemirror v-model="endpointForm.query" placeholder="code goes here..." :style="{ height: '300px' }"
          :autofocus="true" :indent-with-tab="true" :tab-size="4" :extensions="extensions"
          @change="sqlChanged('change', $event)" />
      </div>
      <br />
      <div class="col-md-3">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Endpoint</span>
          <input type="text" class="form-control" placeholder="Query name" v-model="endpointForm.endpoint">
        </div>
      </div>
    
    <h3 v-if="endpointForm.endpoint">URL: {{ apiUrl }}/api/{{ endpointForm.endpoint }}{{ (endpointForm.parameters && endpointForm.parameters.length > 0) ?
      endpointForm.queryStringTest : "" }}</h3>

    <!-- For each parameter an imput -->
    <div v-if="endpointForm.query && endpointForm.parameters && endpointForm.parameters.length > 0">
      <br />
      <div class="col-md-4" v-for="parameter in endpointForm.parameters" :key="parameter">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">{{ parameter.name }}</span>
          <input type="text" class="form-control" placeholder="Write an example value for testing"
            v-model="parameter.exampleValue" @keyup="rebuildQueryStringTest">
        </div>
      </div>
    </div>



    <!-- Description -->
    <div v-if="endpointForm.endpoint">
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Description</span>
        <input type="text" class="form-control" placeholder="Description" v-model="endpointForm.description">
      </div>
    </div>

    <!-- status: combo with DEV, READY-->
    <div v-if="endpointForm.endpoint">
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Status</span>
        <select class="form-select" v-model="endpointForm.status">
          <option value="DEV">DEV</option>
          <option value="PROD">PROD</option>
        </select>
      </div>
    </div>

    <!-- Simulate endpoint -->
    <div v-if="endpointForm.query">
      <button type="button" class="btn btn-primary" @click="testEndpoint">Save and Test endpoint</button>
    </div>

    <br />
    <!-- Cancel button, go to list of endpoints -->
    <div v-if="endpointForm.query">
      <button type="button" class="btn btn-danger" @click="activeTab = 'listEndpoints'">Cancel and back to endpoint list</button>
    </div>

    <br />

    <!-- Show json response -->
    <div v-if="endpointForm.query && response">
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Response</span>
        <textarea class="form-control" aria-label="With textarea" v-model="response" rows="15"></textarea>
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
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { Codemirror } from "vue-codemirror";
import { sql } from "@codemirror/lang-sql";

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

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
  const fetchData = async () => await axios.get(`${apiUrl}/queries/searchQuery`, {
    params: {
      query: sqlSearchQuery.value,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Searching SQL queries, please wait...',
      success: 'SQL queries loaded',
      error: 'Error loading SQL queries'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    queries.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
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
  const fetchData = async () => await axios.get(`${apiUrl}/apiserver/create`, {
    params: {
      endpoint: endpointForm.value.endpoint,
    },

  });

  return toast.promise(
    fetchData(),
    {
      pending: 'Creating new endpoint, please wait...',
      success: 'New endpoint created',
      error: 'Error creating new endpoint'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    endpointForm.value.id_endpoint = response.data.id_endpoint;
    reloadAvailableEndpoints();

  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function testEndpoint() {
  if (endpointForm.value.id_endpoint == null) {
    await createEmptyEndpoint();
  }

  await update();

  const url = apiUrl + "/api/" + endpointForm.value.endpoint + ((endpointForm.value.parameters.length > 0) ? endpointForm.value.queryStringTest : "");

  toast.info('Info' + `Testing endpoint: ${url}`, { position: toast.POSITION.BOTTOM_RIGHT });
  const fetchData = async () => await axios.get(url, {});

  toast.promise(
    fetchData(),
    {
      pending: 'Testing endpoint, please wait...',
      success: 'Endpoint tested',
      error: 'Error testing endpoint'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((result) => {
    response.value = JSON.stringify(result.data, null, 2);
  }).catch((error) => {
    if (error.response && error.response.status === 400) {
      response.value = JSON.stringify(error.response.data, null, 2);
      toast.error('Info' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      response.value = JSON.stringify(error, null, 2);
      toast.error('Info' + `Error: ${error}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function update() {
  const fetchData = async () => await axios.post(`${apiUrl}/apiserver/update`, {
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
      pending: 'Publishing endpoint, please wait...',
      success: 'Endpoint published',
      error: 'Error publishing endpoint'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    published.value = true;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function reloadAvailableEndpoints() {
  const fetchData = async () => await axios.get(`${apiUrl}/apiserver/listEndpoints`, {});

  toast.promise(
    fetchData(),
    {
      error: 'Error loading endpoints'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((result) => {
    availableEndpoints.value = result.data;
    activeTab.value = 'listEndpoints';
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function deleteEndpoint(id_endpoint) {
  const fetchData = async () => await axios.get(`${apiUrl}/apiserver/deleteEndpoint`, {
    params: {
      id_endpoint: id_endpoint
    },

  });

  toast.promise(
    fetchData(),
    {
      pending: 'Deleting endpoint, please wait...',
      success: 'Endpoint deleted',
      error: 'Error deleting endpoint'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    reloadAvailableEndpoints();
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function editEndpoint(selectedEndpoint) {
  const fetchData = async () => await axios.get(`${apiUrl}/apiserver/getEndpoint`, {
    params: {
      id_endpoint: selectedEndpoint.id_endpoint,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Loading endpoint configuration...',
      success: 'Endpoint loaded',
      error: 'Error loading endpoint'
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
      toast.info('Loaded endpoint from local list (server detail endpoint not available).', { position: toast.POSITION.BOTTOM_RIGHT });
      return;
    }

    if (error.response?.data?.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response?.data || error.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}
</script>

<style scoped></style>
