<template>
  <ul class="nav nav-tabs">
    <!-- Published endpoints  -->
    <li class="nav-item">
      <a :class="{ 'nav-link': true, active: activeTab === 'listEndpoints' }" aria-current="page" href="#"
        @click.prevent="reloadAvailableEndpoints()">Published endpoints</a>
    </li>

    <!-- New endpoint -->
    <li class="nav-item">
      <a :class="{ 'nav-link': true, active: activeTab === 'newEndpoint' }" aria-current="page" href="#"
        @click.prevent="activeTab = 'newEndpoint'">New endpoint</a>
    </li>
  </ul>

  <!-- Show endpoints list  -->
  <div class="form-group" v-if="activeTab === 'listEndpoints'">
    <br />
    <p v-if="availableEndpoints && availableEndpoints.length == 0">No endpoints published </p>
    <div v-if="availableEndpoints && availableEndpoints.length > 0">

      <table class="table table-striped table-hover table-bordered">
        <thead>
          <tr class="table-primary">
            <th>ID</th>
            <th>Endpoint</th>
            <th>Description</th>
            <th>URL</th>
            <th>Parameters</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="endpoint in availableEndpoints" :key="endpoint.id_endpoint">
            <td>{{ endpoint.id_endpoint }}</td>
            <td>{{ endpoint.endpoint }}</td>
            <td>{{ endpoint.description }}</td>
            <td>
              <a :href="`${apiUrl}/api/${endpoint.endpoint}`" target="_blank">{{ apiUrl }}/api/{{ endpoint.endpoint }}</a>
            </td>
            <td>{{ endpoint.parameters }}</td>
            <td>
              <button type="button" class="btn btn-danger" @click="deleteEndpoint(endpoint.id_endpoint)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>


    </div>
  </div>

  <!-- New endpoint  -->
  <div class="form-group" v-if="activeTab === 'newEndpoint'">
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

    <div v-if="query">
      <h4>SQL Query</h4><p>Add any {parameter} in your SQL query to add parameters:</p>
        <div class="form-group">
          <codemirror v-model="query.query" :options="cmOption" style="height: 300px;" />
        </div>
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Endpoint</span>
        <input type="text" class="form-control" placeholder="Query name" v-model="endpoint">
      </div>
    </div>

    <!-- Simulate endpoint -->
    <div v-if="query">
      <button type="button" class="btn btn-primary" @click="runQuery">Simulate endpoint</button>
    </div>
    <br />

    <!-- Show json response -->
    <div v-if="query && response">
      <p>URL: {{ apiUrl }}/api/{{ endpoint }}</p>
      <p>Parameters: {{ parameters }}</p>
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Response</span>
        <textarea class="form-control" aria-label="With textarea" v-model="response" rows="15"></textarea>
      </div>
    </div>

    <!-- Parameters -->
    <div v-if="query">
      <br />
      <p>Add parameters to filter output. All parameters will be used with '==' operator and will be mandatory</p>
      <div>
        <ul class="list-group d-flex flex-wrap">
          <li v-for="field in getFields" :key="field" class="list-group-item">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckChecked" :checked="false"
                @click="toggleField(field)">
              <label class="form-check-label" for="flexSwitchCheckChecked">{{ field }}</label>
            </div>
          </li>
        </ul>
      </div>

      <!-- Description -->
      <div>
        <br />
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Description</span>
          <input type="text" class="form-control" placeholder="Description" v-model="description">
        </div>
      </div>

      <!-- Publish button -->
      <div v-if="query && query.id_query && endpoint && description">
        <br />
        <button type="button" class="btn btn-primary" @click="publish">Publish</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';
import { Codemirror } from 'vue-codemirror'

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'ApiServer',

  data() {
    return {
      sqlSearchQuery: null,
      queries: [],

      query: null,
      parameters: [],
      description: null,

      response: null,
      apiUrl: apiUrl,
      published: false,
      activeTab: 'listEndpoints',

      availableEndpoints: null,

      cmOption: {
        tabSize: 4,
        styleActiveLine: true,
        lineNumbers: true,
        line: true,
        foldGutter: true,
        styleSelectedText: true,
        mode: 'text/python',
        keyMap: "sublime",
        matchBrackets: true,
        showCursorWhenSelecting: true,
        theme: "monokai",
        extraKeys: { "Ctrl": "autocomplete" },
        hintOptions: {
          completeSingle: false
        }
      }
    };
  },
  props: {},

  components: {
    Codemirror,
  },

  mounted() {
    this.reloadAvailableEndpoints();
  },
  computed: {
    // Get possible keys in the json response
    getFields() {
      if (this.response) {
        return Object.keys(JSON.parse(this.response)[0]);
      }
    },

  },

  methods: {
    /////////////////////////////////////////////////
    async searchQuery(query) {
      const fetchData = () => axios.get(`${apiUrl}/queries/searchQuery`, {
        params: {
          query: this.sqlSearchQuery,
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
        this.queries = response.data;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    /////////////////////////////////////////////////
    async selectQuery(queryCandidate) {
      this.query = queryCandidate;
      this.sqlSearchQuery = queryCandidate.name;
      this.queries = [];
      this.endpoint = queryCandidate.name;

    },
    /////////////////////////////////////////////////
    async runQuery() {
      const fetchData = () => axios.get(`${apiUrl}/apiserver/runQuery`, {
        params: {
          id_query: this.query.id_query,
        },

      });

      toast.promise(
        fetchData(),
        {
          pending: 'Testing query, please wait...',
          success: 'Query tested',
          error: 'Error testing query'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        //toast.success('Info:' + `Query result: ${response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        this.response = JSON.stringify(response.data, null, 2);
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    /////////////////////////////////////////////////
    toggleField(field) {
      if (this.parameters.includes(field)) {
        this.parameters = this.parameters.filter(item => item !== field);
      } else {
        this.parameters.push(field);
      }
    },
    /////////////////////////////////////////////////
    async publish() {
      const fetchData = () => axios.post(`${apiUrl}/apiserver/publish`, {
        id_query: this.query.id_query,
        endpoint: this.endpoint,
        parameters: this.parameters,
        description: this.description,
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Publishing endpoint, please wait...',
          success: 'Endpoint published',
          error: 'Error publishing endpoint'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {

        this.published = true;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },

    /////////////////////////////////////////////////
    async reloadAvailableEndpoints() {
      const fetchData = () => axios.get(`${apiUrl}/apiserver/listEndpoints`, {

      });

      toast.promise(
        fetchData(),
        {
          pending: 'Loading endpoints, please wait...',
          success: 'Endpoints loaded',
          error: 'Error loading endpoints'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.availableEndpoints = response.data;
        this.activeTab = 'listEndpoints'
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    /////////////////////////////////////////////////
    async deleteEndpoint(id_endpoint) {
      const fetchData = () => axios.get(`${apiUrl}/apiserver/deleteEndpoint`, {
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
      ).then((response) => {
        this.reloadAvailableEndpoints();
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
  }
}

</script>

<style scoped></style>