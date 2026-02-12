<template>
  <div class="row compact-query-view" v-if="tables && tables.length > 0">
    <div class="row">
      <div class="col-md-12 compact-panel">
        <ul class="nav nav-tabs compact-tabs">
      <!-- Main query  -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeQueryTab === 'mainQuery' }" aria-current="page" href="#"
          @click.prevent="activeQueryTab = 'mainQuery'">Main query</a>
      </li>

      <!-- Aux query 1  -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeQueryTab === 'aux1' }" aria-current="page" href="#"
          @click.prevent="activeQueryTab = 'aux1'">Aux 1</a>
      </li>
      <!-- Aux query 2  -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeQueryTab === 'aux2' }" aria-current="page" href="#"
          @click.prevent="activeQueryTab = 'aux2'">Aux 2</a>
      </li>
      <!-- Aux query 3 -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeQueryTab === 'aux3' }" aria-current="page" href="#"
          @click.prevent="activeQueryTab = 'aux3'">Aux 3</a>
      </li>
      <!-- Aux query 4 -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeQueryTab === 'aux4' }" aria-current="page" href="#"
          @click.prevent="activeQueryTab = 'aux4'">Aux 4</a>
      </li>
      <!-- Aux query 5 -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeQueryTab === 'aux5' }" aria-current="page" href="#"
          @click.prevent="activeQueryTab = 'aux5'">Aux 5</a>
      </li>


      
    </ul>

        <div class="form-group mt-2">
            <!-- https://dev.to/medilies/codemirror-v6-on-vue3-hooked-to-pinia-store-g8j 
              https://github.com/surmon-china/vue-codemirror  -->

            
              <codemirror v-if="activeQueryTab === 'mainQuery'"
              v-model="query" 
              placeholder="SELECT * FROM ..."
              :style="{ height: '240px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"          />

              <codemirror v-if="activeQueryTab === 'aux1'"
              v-model="auxQuery1" 
              placeholder="SELECT * FROM ..."
              :style="{ height: '240px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"          />

              <codemirror v-if="activeQueryTab === 'aux2'"
              v-model="auxQuery2" 
              placeholder="SELECT * FROM ..."
              :style="{ height: '240px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"          />

              <codemirror v-if="activeQueryTab === 'aux3'"
              v-model="auxQuery3" 
              placeholder="SELECT * FROM ..."
              :style="{ height: '240px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"          />

              <codemirror v-if="activeQueryTab === 'aux4'"
              v-model="auxQuery4" 
              placeholder="SELECT * FROM ..."
              :style="{ height: '240px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"          />

              <codemirror v-if="activeQueryTab === 'aux5'"
              v-model="auxQuery5" 
              placeholder="SELECT * FROM ..."
              :style="{ height: '240px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"          />


        </div>
        
        <div v-if="queryError" class="query-error">
          <p>{{ queryError }}</p>
        </div>
        <div class="compact-actions">
          <button type="button" class="btn btn-sm btn-primary" @click="runQuery">Run Query</button>
        </div>

        <ul class="nav nav-tabs compact-tabs mt-2">
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
            
            
            <div class="input-group mb-3 compact-input-group">
              <span class="input-group-text" id="basic-addon1">Table name</span>
              <input type="text" class="form-control" id="tableNameInput" placeholder="New table name" v-model="tableFromQuery">
            </div>
           
            <div class="md-col-2" v-if="tableFromQuery">
              <button type="button" class="btn btn-sm btn-primary" @click="createTable">Create table</button>
            </div>
          </div>
        </div>

        <!-- Save query  -->
        <div class="col-md-12" v-if="activeTab === 'saveSql'">
          <div class="form-group">
            <br />
            <div class="input-group mb-3 compact-input-group">
              <span class="input-group-text" id="basic-addon1">Query name</span>
              <input type="text" class="form-control" placeholder="Query name" v-model="sqlQueryName">
            </div>

            <div class="input-group mb-3 compact-input-group">
              <span class="input-group-text" id="basic-addon1">Description</span>
              <input type="text" class="form-control" placeholder="Description" v-model="sqlQueryDescription">
            </div>

            <button type="button" class="btn btn-sm btn-primary" v-if="sqlQueryName && sqlQueryDescription"
            @click="saveSqlQuery">Save SQL query</button>
          </div>
        </div>

        <!-- Load query  -->
        <div class="col-md-12" v-if="activeTab === 'loadSql'">
          <div class="form-group">
            <br />
            <div class="input-group mb-3 compact-input-group">
              <span class="input-group-text" id="basic-addon1">Search query</span>
              <input type="text" class="form-control" placeholder="Query name" v-model="sqlSearchQuery" @input="searchQuery">
            </div>

            <div v-if="queries && queries.length > 0">
              <ul class="list-group d-flex flex-wrap compact-query-list">
                <li v-for="queryCandidate in queries" :key="queryCandidate.id_query" class="list-group-item compact-query-item" @click="selectQuery(queryCandidate)">
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
            <div class="input-group mb-3 compact-input-group">
              <span class="input-group-text" id="basic-addon1">Your question</span>
              <input type="text" class="form-control" id="chatGPTInput" placeholder="Ask ChatGPT" v-model="chatGPTInput">
              
            </div>
            <button type="button" class="btn btn-sm btn-primary" @click="askChatGPT">Ask ChatGPT</button>

            <div v-if="chatGPTOutput" class="mt-2">
              <input type="text" class="form-control" id="chatGPTOutput" v-model="chatGPTOutput">
              <button type="button" class="btn btn-sm btn-primary mt-2" @click="useChatGPTAnswer">Run this query</button>
            </div>
          </div>
        </div>
      </div>
    </div>
      <div class="row">

      <div class="col-md-12">
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

<script setup>
import { ref } from 'vue';
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

defineProps({
  tables: Object,
  secrets: Object,
});

const emit = defineEmits(['tableCreated']);

const extensions = [sql()];
const expanded = ref(true);
const query = ref('SELECT * FROM iris');
const mainQuery = ref('');
const auxQuery1 = ref('');
const auxQuery2 = ref('');
const auxQuery3 = ref('');
const auxQuery4 = ref('');
const auxQuery5 = ref('');
const sampleData = ref(null);
const activeTab = ref('');
const activeQueryTab = ref('mainQuery');
const table = ref(null);
const tableFromQuery = ref('');
const sqlQueryName = ref('');
const sqlQueryDescription = ref('');
const sqlSearchQuery = ref('');
const queries = ref([]);
const chatGPTInput = ref('dame askingprice medio');
const chatGPTOutput = ref('');
const tableName = ref('__lastQuery');
const querySuccesful = ref(false);
const showOptions = ref(true);
const queryError = ref(null);

async function runQuery() {
  queryError.value = null;
  querySuccesful.value = false;

  let queryToRun = query.value;
  if (activeQueryTab.value === 'aux1') {
    queryToRun = auxQuery1.value;
  } else if (activeQueryTab.value === 'aux2') {
    queryToRun = auxQuery2.value;
  } else if (activeQueryTab.value === 'aux3') {
    queryToRun = auxQuery3.value;
  } else if (activeQueryTab.value === 'aux4') {
    queryToRun = auxQuery4.value;
  } else if (activeQueryTab.value === 'aux5') {
    queryToRun = auxQuery5.value;
  }
  const fetchData = () => axios.post(`${apiUrl}/database/runQuery`, {
    query: queryToRun,
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
    sampleData.value = response.data;
    querySuccesful.value = true;
  }).catch((error) => {
    if (error.response.data.message) {
      queryError.value = error.response.data.message;
    } else {
      queryError.value = error.response.data;
    }
  });
}

async function createTable() {
  const fetchData = () => axios.get(`${apiUrl}/database/createTableFromQuery`, {
    params: {
      query: query.value,
      tableName: tableFromQuery.value,
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

async function askChatGPT() {
  const fetchData = () => axios.get(`${apiUrl}/gpt/askGPT`, {
    params: {
      question: chatGPTInput.value,
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
    chatGPTOutput.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function useChatGPTAnswer() {
  query.value = chatGPTOutput.value;
  runQuery();
}

async function saveSqlQuery() {
  const fetchData = () => axios.post(`${apiUrl}/queries/saveSqlQuery`, {
    query: query.value,
    sqlQueryName: sqlQueryName.value,
    description: sqlQueryDescription.value
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Saving SQL query, please wait...',
      success: 'SQL query saved',
      error: 'Error saving SQL query'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function searchQuery() {
  const fetchData = () => axios.get(`${apiUrl}/queries/searchQuery`, {
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
  query.value = queryCandidate.query;
  sqlSearchQuery.value = null;
  queries.value = [];
}

async function deleteQuery(queryCandidate) {
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
  ).then(() => {
    searchQuery();
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
.compact-query-view {
  font-size: 13px;
}

.query-error p {
  color: #cf2f36;
  font-size: 12px;
  margin: 8px 0 0;
}

.compact-query-list {
  gap: 6px;
}

.compact-query-item {
  cursor: pointer;
  font-size: 12px;
  line-height: 1.3;
  border-radius: 8px;
  border: 1px solid #dbe0ea;
  background: #f8f9fc;
}

.compact-query-item:hover {
  background: #edf1fa;
}
</style>
