<template>
  
    <!-- Table list -->
    <div class="row">
      <div class="col-md-12">
        <div v-if="tables && tables.length > 0">
          <ul class="list-unstyled d-flex flex-wrap">
            <li v-for="table in tables" :key="table.id">
              <button class="btn btn-primary m-1 opcion-style" @click="clickTable(table)">
                {{ table }}
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="row">
      <!-- Fields -->
      <div class="col-md-2" v-if="schema">
        <h4>Schema Fields</h4>
        <ul>
          <li v-for="(type, field) in schema" :key="field">
            {{ field }} ({{ type }})
          </li>
        </ul>
      </div>
      <!-- Sample data -->
      <div class="col-md-10" v-if="sampleData">
        <h4>Sample Data</h4>
        <div ref="table"></div>
      </div>
    </div>
</template>

<script>
import axios from 'axios';
import {TabulatorFull as Tabulator} from 'tabulator-tables';

export default {
  name: 'TablesPanel',
  data() {
    return {
      error: '',
      info: '',
      serverHost: 'localhost',
      serverPort: '8080',
      schema: [],
      sampleData: [],

      tabulator: null,
      table: [],
      
    };
  },
  props: {
    tables: {
      type: Array,
      required: true,
    },
  },
  methods: {

    getTables() {

      axios.get(`http://${this.serverHost}:${this.serverPort}/getTables`, {
        params: {
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          this.tables = response.data.results;
        } else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: HTTP ${response.data}`;
      }).finally(() => {
        this.loading = false;
      });
    },

    clickS3File(S3File, isFile) {
      this.fileInput = S3File;
    },

    loadFile() {
      console.log('loadFile');
      this.loading = true;
      this.info = 'Loading file please wait...';
      axios.get(`http://${this.serverHost}:${this.serverPort}/loadFile`, {
        params: {
          tableName: this.tableNameInput,
          fileName: this.fileInput,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
        } else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: HTTP ${response.data}`;
      }).finally(() => {
        this.loading = false;
      });
    },

    async clickTable(table) {
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/getTableSchema`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          this.schema = response.data;
        } else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: ${error.message}`;
      }).finally(() => {
        this.loading = false;
      });

      response = await axios.get(`http://${this.serverHost}:${this.serverPort}/getSampleData`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          this.sampleData = response.data;
          var columns = [];
          for (var key in this.sampleData[0]) {
            columns.push({title: key, field: key});
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
    
}
}

</script>
<style scoped>
</style>