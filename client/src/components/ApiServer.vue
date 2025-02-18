<template>
  
  <ul class="nav nav-tabs">
    <!-- Published endpoints  -->
    <li class="nav-item">
      <a :class="{ 'nav-link': true, active: activeTab === 'listEndpoints' }" aria-current="page" href="#"
        @click.prevent="reloadAvailableEndpoints()">Published endpoints</a>
    </li>

    <!-- New endpoint 
    <li class="nav-item">
      <a :class="{ 'nav-link': true, active: activeTab === 'newEndpoint' }" aria-current="page" href="#"
        @click.prevent="createEmptyEndpoint()">New endpoint</a>
    </li>
    -->

    <!-- Edit endpoint -->
    <li class="nav-item">
      <a :class="{ 'nav-link': true, active: activeTab === 'editEndpoint' }" aria-current="page" href="#"
        @click.prevent="activeTab = 'editEndpoint'">Edit endpoint</a>
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
            <th>id_query</th>
            <th>status</th>
            <th>query</th>
            <th>Example</th>

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
            <td>{{ endpoint.id_query }}</td>
            <td>{{ endpoint.status }}</td>
            <td>{{ endpoint.query }}</td>
            <td>
              <a :href="`${apiUrl}/api/${endpoint.endpoint}${endpoint.queryStringTest}`" target="_blank">{{ apiUrl
              }}/api/{{ endpoint.endpoint }}{{ endpoint.queryStringTest }}</a>
            </td>
            <td>
              <button type="button" class="btn btn-danger" @click="deleteEndpoint(endpoint.id_endpoint)">Delete</button>
              <button type="button" class="btn btn-secondary" @click="editEndpoint(endpoint)">Edit</button>
            </td>
          </tr>
        </tbody>
      </table>


    </div>
    <!-- Create endpoint button -->
    <div v-if="availableEndpoints && availableEndpoints.length > 0">
      <button type="button" class="btn btn-primary" @click="createEmptyEndpoint">Create new endpoint</button>
    </div>
  </div>





  <!-- Endpoint editor  -->
  <div class="form-group" v-if="activeTab === 'newEndpoint' || activeTab === 'editEndpoint'">
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
    

    <div v-if="activeTab === 'editEndpoint' && ! endpoint.id_endpoint">
      <p>No endpoint selected, select one of published endpoints list</p>
    </div>

    

      <p>Add any {parameter} in your SQL query to add query params:</p>
      <div class="form-group">
        <codemirror v-model="endpoint.query" placeholder="code goes here..." :style="{ height: '300px' }"
          :autofocus="true" :indent-with-tab="true" :tab-size="4" :extensions="extensions"
          @change="sqlChanged('change', $event)" />
      </div>
      <br />
      <div class="col-md-3">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Endpoint</span>
          <input type="text" class="form-control" placeholder="Query name" v-model="endpoint.endpoint">
        </div>
      </div>
    
    <h3 v-if="endpoint.endpoint">URL: {{ apiUrl }}/api/{{ endpoint.endpoint }}{{ (endpoint.parameters && endpoint.parameters.length > 0) ?
      endpoint.queryStringTest : "" }}</h3>

    <!-- For each parameter an imput -->
    <div v-if="endpoint.query && endpoint.parameters && endpoint.parameters.length > 0">
      <br />
      <div class="col-md-4" v-for="parameter in endpoint.parameters" :key="parameter">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">{{ parameter.name }}</span>
          <input type="text" class="form-control" placeholder="Write an example value for testing"
            v-model="parameter.exampleValue" @keyup="rebuildQueryStringTest">
        </div>
      </div>
    </div>



    <!-- Description -->
    <div v-if="endpoint.endpoint">
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Description</span>
        <input type="text" class="form-control" placeholder="Description" v-model="endpoint.description">
      </div>
    </div>

    <!-- status: combo with DEV, READY-->
    <div v-if="endpoint.endpoint">
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Status</span>
        <select class="form-select" v-model="endpoint.status">
          <option value="DEV">DEV</option>
          <option value="PROD">PROD</option>
        </select>
      </div>
    </div>

    <!-- Simulate endpoint -->
    <div v-if="endpoint.query">
      <button type="button" class="btn btn-primary" @click="testEndpoint">Save and Test endpoint</button>
    </div>
    <br />

    <!-- Show json response -->
    <div v-if="endpoint.query && response">
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
        id_endpoint: null,
        endpoint: null,
        query: null,
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
      //console.log('sqlChanged: ' + this.endpoint.query);

      // Find all {parameters} in the query and add them to the parameters array
      var oldParameters = this.endpoint.parameters;
      this.endpoint.parameters = [];
      const regex = /{([^}]+)}/g;
      let m;
      while ((m = regex.exec(this.endpoint.query)) !== null) {
        // This is necessary to avoid infinite loops with zero-width matches
        if (m.index === regex.lastIndex) {
          regex.lastIndex++;
        }

        m.forEach((match, groupIndex) => {
          if (groupIndex == 1) {
            this.endpoint.parameters.push({ "name": match, "exampleValue": null });
          }
        });
      }
      // Set parameters example values if they existed before
      for (let i = 0; i < this.endpoint.parameters.length; i++) {
        for (let j = 0; j < oldParameters.length; j++) {
          if (this.endpoint.parameters[i].name == oldParameters[j].name) {
            this.endpoint.parameters[i].exampleValue = oldParameters[j].exampleValue;
          }
        }
      }

      this.rebuildQueryStringTest();
    },
    /////////////////////////////////////////////////
    rebuildQueryStringTest() {
      this.endpoint.queryStringTest = "?";
      for (let i = 0; i < this.endpoint.parameters.length; i++) {
        this.endpoint.queryStringTest += this.endpoint.parameters[i].name + "=" + this.endpoint.parameters[i].exampleValue + "&";
      }
      this.endpoint.queryStringTest = this.endpoint.queryStringTest.slice(0, -1);
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
        params: {
          endpoint: this.endpoint.endpoint,
        },

      });

      // This return is needed because this method is called from a wait method
      return toast.promise(
        fetchData(),
        {
          pending: 'Creating new endpoint, please wait...',
          success: 'New endpoint created',
          error: 'Error creating new endpoint'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.endpoint.id_endpoint = response.data.id_endpoint;
        // Refresh the list of available endpoints
      this.reloadAvailableEndpoints();

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
      if (this.endpoint.id_endpoint == null) {
        await this.createEmptyEndpoint();
      }

      await this.update(this.endpoint)

      var url = this.apiUrl + "/api/" + this.endpoint.endpoint + ((this.endpoint.parameters.length > 0) ? this.endpoint.queryStringTest : "");

      toast.info('Info' + `Testing endpoint: ${url}`, { position: toast.POSITION.BOTTOM_RIGHT });
      const fetchData = async () => await axios.get(url, {

      });

      toast.promise(
        fetchData(),
        {
          pending: 'Testing endpoint, please wait...',
          success: 'Endpoint tested',
          error: 'Error testing endpoint'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.response = JSON.stringify(response.data, null, 2);
      }).catch((error) => {
        if (error.response && error.response.status === 400) {
          this.response = JSON.stringify(error.response.data, null, 2);
          console.log(JSON.stringify(error.response.data, null, 2));
          toast.error('Info' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          this.response = JSON.stringify(error, null, 2);
          console.log(JSON.stringify(error, null, 2));
          toast.error('Info' + `Error: ${error}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    /////////////////////////////////////////////////
    async update() {
      const fetchData = async () => await axios.post(`${apiUrl}/apiserver/update`, {
        id_query: this.endpoint.id_query,
        id_endpoint: this.endpoint.id_endpoint,
        endpoint: this.endpoint.endpoint,
        parameters: this.endpoint.parameters,
        description: this.endpoint.description,
        queryStringTest: this.endpoint.queryStringTest,
        status: this.endpoint.status,
        query: btoa(this.endpoint.query)

      });

      return toast.promise(
        fetchData(),
        {
          pending: 'Publishing endpoint, please wait...',
          success: 'Endpoint published',
          error: 'Error publishing endpoint'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        // get id_endpoint
        //this.newEndpointId = response.data;

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
    /////////////////////////////////////////////////
    async editEndpoint(endpoint) {
      this.endpoint = endpoint;
      console.log("params:" + this.endpoint.parameters);
      this.endpoint.parameters = JSON.parse(this.endpoint.parameters);
      this.activeTab = 'editEndpoint';
    },
  }
}

</script>

<style scoped></style>