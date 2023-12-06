<template>
  
    <!-- Table list -->
    <div class="row">
      <div class="col-md-12">
        <div v-if="tables && tables.length > 0">
          <hr>
          <h1>Tables loaded in DatalakeStudio</h1>
          <ul class="list-unstyled d-flex flex-wrap">
            <!-- None Button -->
            <li>
              <button class="btn btn-secondary m-1 opcion-style" @click="selectedTable = None">
                Close table view
              </button>
            </li>
            <li v-for="table in tables" :key="table.id">
              <button class="btn btn-primary m-1 opcion-style" @click="clickTable(table)">
                {{ table }}
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="row"  v-if="selectedTable">
      <h2>Table {{ selectedTable }}</h2>
      <!-- Delete button -->
      <div class="row-md-2" v-if="selectedTable">
        <button class="btn btn-primary m-1 opcion-style" @click="deleteTable">
          Delete table
        </button>
      </div>
      <!-- Fields -->
      <div class="col-md-2" v-if="schema">
        <h4>Table Fields</h4>
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
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

export default {
  name: 'TablesPanel',
  data() {
    return {
      serverHost: 'localhost',
      serverPort: '8080',
      schema: [],
      sampleData: [],

      tabulator: null,
      table: [],

      selectedTable: '',
    };
  },
  props: {
    tables: Object,
  },

  emits: ['deleteTable'],

  methods: {
    async clickTable(table) {
      this.selectedTable = table;
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/getTableSchema`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.schema = response.data;
        } else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${response.message}`);
      }).finally(() => {
        this.loading = false;
      });

      response = await axios.get(`http://${this.serverHost}:${this.serverPort}/getSampleData`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
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
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${error.message}`);
        
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////
    async deleteTable() {
      this.$emit('deleteTable', this.selectedTable);
      this.selectedTable = '';
    },
    
}
}

</script>
<style scoped>
</style>