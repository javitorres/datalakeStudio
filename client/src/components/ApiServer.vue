<template>
  <p>Api server</p>

  <div class="form-group">
    <br />
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
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Endpoint</span>
        <input type="text" class="form-control" placeholder="Query name" v-model="endpoint" @input="searchQuery">
      </div>
    </div>

    <!-- Test button -->
    <div v-if="query">
      <button type="button" class="btn btn-primary" @click="runQuery">Run query</button>
    </div>

    <!-- Show json response -->
    <div v-if="query && response">
      <br />
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon1">Response</span>
        <textarea class="form-control" aria-label="With textarea" v-model="response" rows="15"></textarea>
      </div>
    </div>

    <!-- Form to build parameters array: paramName, operand(==,!=,>=,<=,>,<) and value-->
    <div v-if="query">
      <br />
      <div>
        <div v-for="(parameter, index) in parameters" :key="index" class="row">
          <div class="col-md-2">
            <div class="input-group mb-3">
              <span class="input-group-text" id="basic-addon1">Field</span>
              <input v-model="parameter.field" placeholder="Field" class="form-control">
            </div>
          </div>

          <div class="col-md-2">
            <div class="input-group mb-3">
              <span class="input-group-text" id="basic-addon1">Operand</span>
              <select v-model="parameter.operand" class="form-select">
                <option value="==">==</option>
                <option value="!=">!=</option>
                <option value=">=">>=</option>
                <option value="<=">&lt=</option>
                <option value=">">></option>
                <option value="<">&lt</option>
              </select>
            </div>
          </div>
        

        <div class="col-md-2">
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Value</span>
            <input v-model="parameter.value" placeholder="Value" class="form-control">
          </div>
        </div>
      </div>

      <button class="btn btn-primary m-1 opcion-style" @click="addParameter">Add new</button>
      <button class="btn btn-primary m-1 opcion-style" @click="deleteAllParameters">Delete all parameters</button>
    </div>
  </div>
</div></template>

<script>
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'ApiServer',

  data() {
    return {
      sqlSearchQuery: null,
      queries: [],
      query: null,
      parameters: [{ "field": null, "operand": null, "value": null }],
      response: null,
    };
  },
  props: {


  },

  methods: {
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
      //this.sqlSearchQuery = null;
      //this.queries = [];
      this.endpoint = queryCandidate.name;

    },
    /////////////////////////////////////////////////
    async runQuery() {
      const fetchData = () => axios.get(`${apiUrl}/queries/runQuery`, {
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


  }
}

</script>

<style scoped></style>