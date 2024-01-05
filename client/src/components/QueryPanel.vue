<template>
  <div class="row" v-if="tables && tables.length > 0">
    <div class="row">
      <div class="col-md-4">

        <h4>SQL Query</h4>
        <div class="form-group">
            <!-- https://dev.to/medilies/codemirror-v6-on-vue3-hooked-to-pinia-store-g8j 
              https://github.com/surmon-china/vue-codemirror  -->

            <codemirror
              v-model="query" 
              placeholder="SELECT * FROM ..."
              :style="{ height: '200px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"
              
          />
        </div>
        
        <div v-if="queryError">
          <p style="color: red;">{{ queryError }}</p>
        </div>
        <br />
        <button type="button" class="btn btn-primary" @click="runQuery">Run Query</button>
        <br /><br />

        <ul class="nav nav-tabs">
          <!-- Create table from query  -->
          <li class="nav-item">
            <a :class="{ 'nav-link': true, active: activeTab === 'newTable' }" aria-current="page" href="#"
              @click.prevent="activeTab = 'newTable'">New table</a>
          </li>

          <!-- Save query  -->
          <li class="nav-item">
            <a :class="{ 'nav-link': true, active: activeTab === 'saveSql' }" aria-current="page" href="#"
              @click.prevent="activeTab = 'saveSql'">Save SQL</a>
          </li>

          <!-- Load query  -->
          <li class="nav-item">
            <a :class="{ 'nav-link': true, active: activeTab === 'loadSql' }" aria-current="page" href="#"
              @click.prevent="activeTab = 'loadSql'">Load SQL</a>
          </li>

          <!-- Ask GPT -->
          <li class="nav-item">
            <a :class="{ 'nav-link': true, active: activeTab === 'askGpt' }" aria-current="page" href="#"
              @click.prevent="activeTab = 'askGpt'">Ask GPT</a>
          </li>
        </ul>

        <!-- Create table from query  -->
        <div class="col-md-6" v-if="activeTab === 'newTable'">
          <br />
          <p v-if="!sampleData">No data, run a query to create a new table with the result</p>
          <div class="form-group" v-if="sampleData">
            
            
            <div class="input-group mb-3">
              <span class="input-group-text" id="basic-addon1">Table name</span>
              <input type="text" class="form-control" id="tableNameInput" placeholder="New table name" v-model="tableFromQuery">
            </div>
           
            <div class="md-col-2">
              <button type="button" class="btn btn-primary" @click="createTable">Create table</button>
            </div>
          </div>
        </div>

        <!-- Save query  -->
        <div class="col-md-12" v-if="activeTab === 'saveSql'">
          <div class="form-group">
            <br />
            <div class="input-group mb-3">
              <span class="input-group-text" id="basic-addon1">Query name</span>
              <input type="text" class="form-control" placeholder="Query name" v-model="sqlQueryName">
            </div>

            <div class="input-group mb-3">
              <span class="input-group-text" id="basic-addon1">Description</span>
              <input type="text" class="form-control" placeholder="Description" v-model="sqlQueryDescription">
            </div>
            <button type="button" class="btn btn-primary" @click="saveSqlQuery">Save SQL query</button>
          </div>
        </div>

        <!-- Load query  -->
        <div class="col-md-12" v-if="activeTab === 'loadSql'">
          <div class="form-group">
            <br />
            <div class="input-group mb-3">
              <span class="input-group-text" id="basic-addon1">Search query</span>
              <input type="text" class="form-control" placeholder="Query name" v-model="sqlSearchQuery" @input="searchQuery">
            </div>

            <div v-if="queries && queries.length > 0">
              <ul class="list-group d-flex flex-wrap">
                <li v-for="queryCandidate in queries" :key="queryCandidate.id_query" class="list-group-item" @click="selectQuery(queryCandidate)">
                  <i class="bi bi-trash" @click.stop="deleteQuery(queryCandidate)"> Delete</i> <br/>
                  <b>Name:</b> {{ queryCandidate.name }}<br/><b>Description:</b>{{ queryCandidate.description }}<br/><b>SQL:</b>{{ queryCandidate.query }}
                </li>
              </ul>
            </div> 
          </div>
        </div>

        <!-- Ask GPT -->
        <div class="row" v-if="activeTab === 'askGpt'">
          <div class="col-md-12">
            <br />
            <div class="input-group mb-8">
              <span class="input-group-text" id="basic-addon1">Your question</span>
              <input type="text" class="form-control" id="chatGPTInput" placeholder="Ask ChatGPT" v-model="chatGPTInput">
              
            </div>
            <br />
            <button type="button" class="btn btn-primary" @click="askChatGPT">Ask ChatGPT</button>

            <br />
            <div v-if="chatGPTOutput">
              <input type="text" class="form-control" id="chatGPTOutput" v-model="chatGPTOutput">
              <button type="button" class="btn btn-primary" @click="useChatGPTAnswer">Run this query</button>
            </div>
          </div>
        </div>
        <br />
      </div>

      <div class="col-md-8">
        <div class="row" v-if="querySuccesful">
          <TableInspector :tableName="tableName" :showOptions="showOptions" />
        </div>
      </div>
    </div>

  </div>
  <div v-else>
    <h2>No tables to query on. Load some data before</h2>
  </div>

  <!-- <CodeEditor  /> -->
</template>

<script>
import { Codemirror } from "vue-codemirror";
import { sql } from "@codemirror/lang-sql";

import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import GenericCross from './GenericCross.vue';
import TableInspector from './TableInspector.vue';
import CodeEditor from './CodeEditor.vue';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'QueryPanel',

  components: {
    Codemirror,
    GenericCross,
    TableInspector,
    CodeEditor
  },

  setup() {
      const extensions = [sql()]
      return { extensions }
  },

  data() {
    return {
      expanded: true,
      query: 'SELECT * FROM homecenter',
      sampleData: null,

      activeTab: 'newTable',

      table: null,
      tableFromQuery: '',
      sqlQueryName: '',
      sqlQueryDescription: '',
      sqlSearchQuery: '',
      queries: [],

      chatGPTInput: 'dame askingprice medio',
      chatGPTOutput: '',

      tableName: "__lastQuery",
      querySuccesful: false,
      showOptions: true,

      queryError: null,
    };
  },
  props: {
    tables: Object,
    secrets: Object,
  },
  emits: ['tableCreated'],

  methods: {
    ///////////////////////////////////////////////////////
    async runQuery() {
      this.queryError = null;
      this.querySuccesful = false;
      const fetchData = () => axios.post(`${apiUrl}/database/runQuery`, {
        query: this.query,
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Running query, please wait...',
          success: 'Query executed',
          error: 'Error running query'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.sampleData = response.data;
        this.querySuccesful = true;
      }).catch((error) => {
        if (error.response.data.message) {
          this.queryError = error.response.data.message;
        } else {
          this.queryError = error.response.data;
        }
        
      });
    },
    ///////////////////////////////////////////////////////
    async createTable() {
      const fetchData = () => axios.get(`${apiUrl}/database/createTableFromQuery`, {
        params: {
          query: this.query,
          tableName: this.tableFromQuery,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Creating table from query, please wait...',
          success: 'Table created',
          error: 'Error creting table from query'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.$emit('tableCreated');
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });

    },
    ///////////////////////////////////////////////////////
    async askChatGPT() {
      const fetchData = () => axios.get(`${apiUrl}/gpt/askGPT`, {
        params: {
          question: this.chatGPTInput,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Asking ChatGPT, please wait...',
          success: 'ChatGPT answered',
          error: 'Error asking ChatGPT'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.chatGPTOutput = response.data;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    ///////////////////////////////////////////////////////
    async useChatGPTAnswer() {
      this.query = this.chatGPTOutput;
      this.runQuery();
    },
    ///////////////////////////////////////////////////////
    async saveSqlQuery() {
      const fetchData = () => axios.post(`${apiUrl}/queries/saveSqlQuery`, {

        query: this.query,
        sqlQueryName: this.sqlQueryName,
        description: this.sqlQueryDescription

      });

      toast.promise(
        fetchData(),
        {
          pending: 'Saving SQL query, please wait...',
          success: 'SQL query saved',
          error: 'Error saving SQL query'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {

      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    ///////////////////////////////////////////////////////
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
      this.query = queryCandidate.query;
      this.sqlSearchQuery = null;
      this.queries = [];

    },
    /////////////////////////////////////////////////
    async deleteQuery(queryCandidate) {
      const fetchData = () => axios.get(`${apiUrl}/queries/deleteQuery`, {
        params: {
          id_query: queryCandidate.id_query,
        },
        
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Deleting SQL query, please wait...',
          success: 'SQL query deleted',
          error: 'Error deleting SQL query'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.searchQuery();
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

<style scoped>
.nav-tabs {
  display: flex;
  flex-wrap: wrap;
}

.nav-item {
  flex: 1;
  /* Esto hará que cada pestaña tenga el mismo ancho */
}
</style>