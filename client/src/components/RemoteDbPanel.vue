<template>
  <div class="spinner-border" role="status" v-if="loading">
    <span class="visually-hidden">Loading...</span>
  </div>
  <div class="col-md-6">
    <div class="input-group mb-3">
      <span class="input-group-text" id="basic-addon1">Database name</span>
      <input id="databaseInput" type="text" class="form-control" placeholder="Write the database name" aria-label="File"
        aria-describedby="basic-addon1" v-model="databaseInput" @input="searchDatabase">
    </div>
  </div> <!-- col-md-6 -->

  <!-- Green button with connectedDatabase -->
  <div class="row">
    <div class="col-md-2" v-if="connectedDatabase">
      <button class="btn btn-success m-1 opcion-style" @click="disconnectDatabase(connectedDatabase)">
        Database: {{ connectedDatabase }}.<br /> Click to disconnect
      </button>
    </div> <!-- col-md-2 -->

    <div class="col-md-2" v-if="schemaSelected">
      <button class="btn btn-success m-1 opcion-style" @click="showSchemas = !showSchemas">
        Schema active: {{ schemaSelected }}.<br /> {{ showSchemas ? 'Click to hide schemas' : 'Click to show schemas' }}
      </button>
    </div> <!-- col-md-2 -->
  </div>

  <!-- Databases -->
  <div class="row">
    <div v-if="databases && databases.length > 0">
      <ul class="list-unstyled d-flex flex-wrap">
        <li v-for="database in databases" :key="database.id">
          <button class="btn btn-primary m-1 opcion-style" @click="clickDatabase(database, true)">
            {{ database }}
          </button>
        </li>
      </ul>
    </div> <!-- v-if -->
  </div> <!-- row -->

  <!-- Schemas -->
  <div class="row" v-if="connectedDatabase && showSchemas">
    <div v-if="schemas && schemas.length > 0">
      <p>Remote Schemas:</p>
      <ul class="list-unstyled d-flex flex-wrap">
        <li v-for="schema in schemas" :key="schema.id">
          <button class="btn btn-primary m-1 opcion-style" @click="clickSchema(schema, true)">
            {{ schema }}
          </button>
        </li>
      </ul>
    </div> <!-- v-if -->
  </div> <!-- row -->

  <!-- Tables -->
  <div class="row" v-if="connectedDatabase">
    <div v-if="tables && tables.length > 0">
      <p>Remote Tables:</p>
      <input type="text" class="form-control" id="tableNameInput" placeholder="Filter by name" v-model="filterTable">
      <ul class="list-unstyled d-flex flex-wrap">
        <li v-for="table in tables" :key="table.id">

          <button class="btn btn-primary m-1 opcion-style" v-if="table.indexOf(filterTable) > -1"
            @click="clickTable(table)">
            {{ table }}
          </button>
        </li>
      </ul>
    </div> <!-- v-if -->
  </div> <!-- row -->

  <div class="row" v-if="connectedDatabase">
    <div class="col-md-6">
      <h4>Query on remote database</h4>
      <div class="form-group">

        <codemirror
              v-model="query" 
              placeholder="code goes here..."
              :style="{ height: '300px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"
          />

      </div>
      <button type="button" class="btn btn-primary" @click="runRemoteQuery(query)">Run remote Query</button>

      <!-- Create table from query -->
      <div class="form-group" v-if="sampleData">
        <br />
        <label for="tableNameInput">Create table from query</label>
        <div class="row">
          <div class="md-col-4">
            <input type="text" class="form-control" id="tableNameInput" placeholder="New table name"
              v-model="tableFromQuery">
          </div>

          <div class="md-col-2">
            <button type="button" class="btn btn-primary" @click="createTableFromRemoteQuery">Create table</button>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div ref="table"></div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

import { Codemirror } from "vue-codemirror";
import { sql } from "@codemirror/lang-sql";

import { TabulatorFull as Tabulator } from 'tabulator-tables';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

const emit = defineEmits(['tableCreated']);

const extensions = [sql()];
const expanded = ref(true);
const tabulator = ref(null);
const connectedDatabase = ref('');
const loading = ref(false);
const databaseInput = ref('');
const databases = ref([]);
const schemas = ref([]);
const schemaSelected = ref('');
const showSchemas = ref(true);
const tables = ref([]);
const query = ref('');
const sampleData = ref([]);
const tableFromQuery = ref('');
const filterTable = ref('');
const table = ref(null);
const error = ref('');

function clickTable(nextTable) {
  query.value = 'SELECT * FROM ' + schemaSelected.value + '.' + nextTable + ' LIMIT 30';
  runRemoteQuery(query.value);
}

async function searchDatabase() {
  if (databaseInput.value.length > 0) {
    axios.get(`${apiUrl}/remotedb/getDatabaseList`, {
      params: {
        databaseName: databaseInput.value
      },
    }).then((response) => {
      if (response.status === 200) {
        databases.value = response.data;
      }
      else {
        toast.error(`Error: HTTP ${response.message}`);
      }
    }).catch(() => {
      toast.error('Error searching databases');
    }).finally(() => {
      loading.value = false;
    });
  }
}

async function clickDatabase(database) {
  axios.get(`${apiUrl}/remotedb/connectDatabase`, {
    params: {
      databaseName: database
    },
  }).then((response) => {
    if (response.status === 200) {
      if (response.data.status === 'ok') {
        connectedDatabase.value = database;
        databases.value = [];
        schemas.value = response.data.schemas;
        toast.success('Database ' + database + ' connected');
      }
      else {
        toast.error(`Error: HTTP ${response.message}`);
      }
    }
    else {
      toast.error(`Error: HTTP ${response.message}`);
    }
  }).catch(() => {
    toast.error('Error connecting to remote database');
  }).finally(() => {
    loading.value = false;
  });
}

async function clickSchema(schema) {
  showSchemas.value = false;
  loading.value = true;
  schemaSelected.value = schema;
  axios.get(`${apiUrl}/remotedb/getTablesFromRemoteSchema`, {
    params: {
      schema: schema
    },
  }).then((response) => {
    if (response.status === 200) {
      if (response.data.status === 'ok') {
        tables.value = response.data.tables;
      }
      else {
        toast.error(`Error: HTTP ${response.data.message}`);
      }
    }
    else {
      toast.error(`Error: HTTP ${response.message}`);
    }
  }).catch(() => {
    toast.error('Error loading schemas');
  }).finally(() => {
    loading.value = false;
  });
}

async function runRemoteQuery(nextQuery) {
  loading.value = true;
  await axios.get(`${apiUrl}/remotedb/runRemoteQuery`, {
    params: {
      database: connectedDatabase.value,
      query: nextQuery,
    },
  }).then((response) => {
    if (response.status === 200) {
      error.value = '';
      sampleData.value = response.data;
      tabulator.value = new Tabulator(table.value, {
        data: sampleData.value,
        reactiveData: true,
        importFormat: 'csv',
        autoColumns: true,
        layout: 'fitColumns',
      });
    } else {
      error.value = `Error: HTTP ${response.message}`;
    }
  }).catch((err) => {
    error.value = `Error: ${err.message}`;
  }).finally(() => {
    loading.value = false;
  });
}

async function createTableFromRemoteQuery() {
  await axios.get(`${apiUrl}/remotedb/createTableFromRemoteQuery`, {
    params: {
      query: query.value,
      tableName: tableFromQuery.value,
    },
  }).then((response) => {
    if (response.status === 200) {
      toast.success('Table created successfully');
      emit('tableCreated');
    } else {
      toast.error('Table creation error::' + response.message);
    }
  }).catch((error) => {
    toast.error('Table creation error:' + error);
  }).finally(() => {
    loading.value = false;
  });
}

async function disconnectDatabase(database) {
  await axios.get(`${apiUrl}/remotedb/disconnectDatabase`, {
    params: {
      databaseName: database,
    },
  }).then(() => {
    connectedDatabase.value = '';
    schemas.value = [];
    tables.value = [];
    schemaSelected.value = '';
  }).catch(() => {
    toast.error('Error disconnecting remote database');
  });
}
</script>
<style scoped></style>
