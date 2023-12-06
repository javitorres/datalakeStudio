<template>
  <hr>
  <h1 v-on:click="expanded = !expanded">{{ expanded ? "-" : "+" }} Remote databases</h1>
  <div v-if="expanded">
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
              @click="query = 'SELECT * FROM ' + schemaSelected + '.' + table + ' LIMIT 30'">
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
          <codemirror v-model="query" style="height: 300px;" />
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
  </div>
</template>

<script>
import axios from 'axios';
import { Codemirror } from 'vue-codemirror'
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

export default {
  name: 'RemoteDbPanel',
  data() {
    return {
      expanded: true,
      serverHost: 'localhost',
      serverPort: '8000',
      tabulator: null,
      connectedDatabase: '',
      loading: false,

      databaseInput: '',
      databases: [],
      schemas: [],
      schemaSelected: '',
      showSchemas: true,
      tables: [],

      query: '',
      sampleData: [],
      tabulator: null,
      tableFromQuery: '',
      filterTable: '',
    };
  },
  components: {
    Codemirror,
  },

  emits: ['tableCreated'],

  methods: {
    async searchDatabase() {
      if (this.databaseInput.length > 0) {
        axios.get(`http://${this.serverHost}:${this.serverPort}/getDatabaseList`, {
          params: {
            databaseName: this.databaseInput
          },
        }).then((response) => {
          if (response.status === 200) {
            //console.log('response.data: ' + response.data);
            this.databases = response.data;

            //toast.success('Table created successfully');
          }
          else {
            toast.error(`Error: HTTP ${response.message}`);
          }
        }).catch((error) => {
          toast.error(`Error: HTTP ${response.data}`);
        }).finally(() => {
          this.loading = false;
          //this.info = '';
          //this.getTables();
        });
      }
    },
    ////////////////////////////////////////////////////
    async clickDatabase(database) {
      console.log('clickDatabase()');
      console.log('database: ' + database);
      axios.get(`http://${this.serverHost}:${this.serverPort}/connectDatabase`, {
        params: {
          databaseName: database
        },
      }).then((response) => {
        if (response.status === 200) {
          //console.log('response.data: ' + response.data);
          if (response.data.status === 'ok') {
            this.connectedDatabase = database;
            this.databases = [];
            this.schemas = response.data.schemas;
            toast.success('Database ' + database + ' connected');
          }
          else {
            toast.error(`Error: HTTP ${response.message}`);
          }
        }
        else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${response.data}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    ///////////////////////////////////////////////////
    async clickSchema(schema) {
      this.showSchemas = false;
      this.loading = true;
      this.schemaSelected = schema;
      axios.get(`http://${this.serverHost}:${this.serverPort}/getTablesFromRemoteSchema`, {
        params: {
          schema: schema
        },
      }).then((response) => {
        if (response.status === 200) {
          //console.log('response.data: ' + response.data);
          if (response.data.status === 'ok') {
            this.tables = response.data.tables;
            //toast.success('Schema ' + schema + ' connected');
          }
          else {
            toast.error(`Error: HTTP ${response.data.message}`);
          }
        }
        else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${response.data}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    /////////////////////////////////////////////////////////////
    async runRemoteQuery(query) {
      this.loading = true;
      console.log('runRemoteQuery()');
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/runRemoteQuery`, {
        params: {
          database: this.database,
          query: this.query,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          this.sampleData = response.data;
          var columns = [];
          for (var key in this.sampleData[0]) {
            columns.push({ title: key, field: key });
          }
          var table = new Tabulator(this.$refs.table, {
            data: this.sampleData,
            reactiveData: true,
            importFormat: "csv",
            autoColumns: true,

          });

        } else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: ${error.message}`;
      }).finally(() => {
        this.loading = false;
      });
    },
    ///////////////////////////////////////////////////////
    async createTableFromRemoteQuery() {
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/createTableFromRemoteQuery`, {
        params: {
          query: this.query,
          tableName: this.tableFromQuery,
        },
      }).then((response) => {
        if (response.status === 200) {
          toast.success('Table created successfully');
          this.$emit('tableCreated');
        } else {
          toast.error('Table creation error::' + response.message);
        }
      }).catch((error) => {
        toast.error('Table creation error:' + error);
      }).finally(() => {
        this.loading = false;
      });
    },

  },

}




</script>
<style scoped></style>