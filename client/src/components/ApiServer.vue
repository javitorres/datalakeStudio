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

    <div v-if="endpoint.query">

      <p>Add any {parameter} in your SQL query to add query params:</p>
      <div class="form-group">
        <codemirror v-model="endpoint.query" placeholder="code goes here..." :style="{ height: '300px' }" :autofocus="true"
          :indent-with-tab="true" :tab-size="4" :extensions="extensions" @change="sqlChanged('change', $event)" />
      </div>
      <br />
      <div class="col-md-3">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Endpoint</span>
          <input type="text" class="form-control" placeholder="Query name" v-model="endpoint.endpoint">
        </div>
      </div>
    </div>
    <h3>URL: {{ apiUrl }}/api/{{ endpoint.endpoint }}{{ (endpoint.parameters.length > 0) ? endpoint.queryStringTest : "" }}</h3>

    <!-- For each parameter an imput -->
    <div v-if="endpoint.query && endpoint.parameters.length > 0">
      <br />
      <div class="col-md-4" v-for="parameter in parameters" :key="parameter">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">{{ parameter }}</span>
          <input type="text" class="form-control" placeholder="Write an example value for testing"
            v-model="parameter.exampleValue" @keyup="rebuildQueryStringTest">
        </div>
      </div>
    </div>

    VOY PORQUE ME FALLA EL UPDATE

    <!-- Description -->
    <div>
        <br />
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Description</span>
          <input type="text" class="form-control" placeholder="Description" v-model="description">
        </div>
      </div>

    <!-- Simulate endpoint -->
    <div v-if="endpoint.query">
      <button type="button" class="btn btn-primary" @click="testEndpoint">Test endpoint</button>
    </div>
    <br />

    <!-- Show json response -->
    <div v-if="query && response">

      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Response</span>
        <textarea class="form-control" aria-label="With textarea" v-model="response" rows="15"></textarea>
      </div>
    </div>

    <!-- Parameters -->
    <div v-if="endpoint.query">

      

      <!-- Publish button -->
      <div v-if="endpoint.query && endpoint.endpoint && endpoint.description">
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

import { Codemirror } from "vue-codemirror";
import { sql } from "@codemirror/lang-sql";

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'ApiServer',

  setup() {
    const extensions = [sql()]
    return { extensions }
  },

  data() {
    return {
      sqlSearchQuery: null,
      queries: [],

      query: null,
      endpoint: 
        {
          id_query: null,
          endpointId: null,
          endpoint: null,
          parameters: [],
          description: null,
          queryStringTest: null,
          status: 'DEV'
       },
      
      response: null,
      apiUrl: apiUrl,
      activeTab: 'listEndpoints',
      availableEndpoints: null,
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
    sqlChanged(event, editor) {
      // TODO There is a delay of one keypressed 
      // console.log('sqlChanged: ' + this.query.query);

      // Find all {parameters} in the query and add them to the parameters array
      this.parameters = [];
      const regex = /{([^}]+)}/g;
      let m;
      while ((m = regex.exec(this.query.query)) !== null) {
        // This is necessary to avoid infinite loops with zero-width matches
        if (m.index === regex.lastIndex) {
          regex.lastIndex++;
        }

        m.forEach((match, groupIndex) => {
          if (groupIndex == 1) {
            this.parameters.push({ "name": match, "exampleValue": null });
          }
        });
      }
      this.rebuildQueryStringTest();
    },
    /////////////////////////////////////////////////
    rebuildQueryStringTest() {
      this.queryStringTest = "?";
      for (let i = 0; i < this.parameters.length; i++) {
        this.queryStringTest += this.parameters[i].name + "=" + this.parameters[i].exampleValue + "&";
      }
      this.queryStringTest = this.queryStringTest.slice(0, -1);
    },
    /////////////////////////////////////////////////
    async searchQuery(query) {
      const fetchData = async () => await axios.get(`${apiUrl}/queries/searchQuery`, {
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
      
      this.sqlSearchQuery = queryCandidate.name;
      this.queries = [];

      this.endpoint.endpoint = queryCandidate.name;
      this.endpoint.id_query = queryCandidate.id_query;
      this.endpoint.query = queryCandidate.query;


    },
    /////////////////////////////////////////////////
    async createEmptyEndpoint() {
      // Create new endpoint and get the id
      const fetchData = async () => await axios.get(`${apiUrl}/apiserver/create`, {

      });

      toast.promise(
        fetchData(),
        {
          pending: 'Creating new endpoint, please wait...',
          success: 'New endpoint created',
          error: 'Error creating new endpoint'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        console.log('createEmptyEndpoint: ' + response.data.id_endpoint);
        this.endpoint.endpointId = response.data.id_endpoint;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },

    /////////////////////////////////////////////////
    async testEndpoint() {
      if (this.endpoint.endpointId == null) {
        await this.createEmptyEndpoint();
      }
      this.update(this.endpoint)
      

    },
    /////////////////////////////////////////////////
    async update() {
      const fetchData = async () => await axios.post(`${apiUrl}/apiserver/update`, {
        id_query: this.endpoint.id_query,
        endpointId: this.endpoint.endpointId,
        endpoint: this.endpoint.endpoint,
        parameters: this.parameters,
        description: this.description,
        queryStringTest: this.queryStringTest,
        status: this.endpoint.status,

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
        // get id_endpoint
        this.newEndpointId = response.data;

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
      const fetchData = async () => await axios.get(`${apiUrl}/apiserver/listEndpoints`, {

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