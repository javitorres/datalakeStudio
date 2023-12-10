<template>
  <!-- Table list -->
  <hr>
  <h1 v-on:click="expanded = !expanded">{{ expanded ? "-" : "+" }} Tables loaded in DatalakeStudio</h1>
  <div v-if="expanded">
    <div class="row">
      <div class="col-md-12">
        <div v-if="tables && tables.length > 0">
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

    <div class="row" v-if="selectedTable">
      <h2>Table {{ selectedTable }}</h2>
      <!-- Delete button -->
      <div class="row-md-2" v-if="selectedTable">
        <button class="btn btn-primary m-1 opcion-style" @click="deleteTable">
          <img src="../assets/delete.svg" alt="delete table" width="30" height="30">
          Delete table
        </button>

        <button class="btn btn-primary m-1 opcion-style" @click="getSampleData(selectedTable)">
          <img src="../assets/table.svg" alt="show sample data" width="30" height="30">
          Show sample data
        </button>

        <button class="btn btn-primary m-1 opcion-style" @click="getTableProfile(selectedTable)">
          <img src="../assets/magnifying-glass.svg" alt="profile table" width="30" height="30">
          Show table profile
        </button>
      </div>
      <!-- Fields -->
      <div class="col-md-2" v-if="schema">
        <h4>Table Fields</h4>
        <div class="row" v-for="(type, field) in schema" :key="field">
          <button class="btn btn-primary m-1 opcion-style" @click="analyzeField">
            {{ field }} ({{ type }})
          </button>
        </div>

      </div>
      <!-- Sample data -->
      <div v-if="sampleData && showSampleData" class="col-md-10">
        <h4>Sample Data</h4>
        <div ref="table"></div>
      </div>

      <div v-if="tableProfile && showProfile" class="col-md-10">
        <h4>Table profile</h4>
        <!-- Global Stats -->
        <div class="card mb-3">
          <div class="card-header">Estadísticas Globales</div>
          <div class="card-body">
            <p v-for="(value, key) in tableProfile.global_stats" :key="key">
              <strong>{{ key }}:</strong> {{ value }}
            </p>
          </div>
        </div>

        <!-- Data Stats -->
        <div class="card mb-3" v-for="(columnStats, index) in tableProfile.data_stats" :key="index">
    <div class="card-header">Estadísticas de Datos - {{ columnStats.column_name }}</div>
    <div class="card-body">
        <!-- Mostrar todos los elementos excepto statistics -->
        <p v-for="(value, key) in columnStats" v-if="key !== 'statistics'" :key="key">
            <strong>{{ key }}:</strong> {{ value }}
        </p>

        <!-- Mostrar elemento Statistics -->
        <div v-if="columnStats.statistics">
            <h5>Statistics:</h5>
            <p v-for="(statValue, statKey) in columnStats.statistics" :key="statKey">
                <strong>{{ statKey }}:</strong> {{ statValue }}
            </p>

            <!-- Si hay quantiles dentro de statistics, mostrarlos también -->
            <div v-if="columnStats.statistics.quantiles">
                <h6>Quantiles:</h6>
                <p v-for="(quantileValue, quantileKey) in columnStats.statistics.quantiles" :key="quantileKey">
                    <strong>{{ quantileKey }}:</strong> {{ quantileValue }}
                </p>
            </div>

            <!-- Si hay data_type_representation dentro de statistics, mostrarlos también -->
            <div v-if="columnStats.statistics.data_type_representation">
                <h6>Data Type Representation:</h6>
                <p v-for="(dataTypeValue, dataTypeKey) in columnStats.statistics.data_type_representation" :key="dataTypeKey">
                    <strong>{{ dataTypeKey }}:</strong> {{ dataTypeValue }}
                </p>
            </div>
        </div>
    </div>
</div>

      </div>
    </div>
    </div>
</template>

<script>
import axios from 'axios';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

export default {
  name: 'TablesPanel',
  data() {
    return {
      expanded: true,
      serverHost: 'localhost',
      serverPort: '8000',
      schema: [],
      sampleData: [],

      showSampleData: true,
      showProfile: false,

      tableProfile: {},

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

      this.getSampleData(table);
    },

    ////////////////////////////////////////////////////
    async getSampleData(table) {
      this.showSampleData = true;
      this.showProfile = false;
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/getSampleData`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
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
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${error.message}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////

    async getTableProfile(table) {
      this.showSampleData = false;
      this.showProfile = true;
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/getTableProfile`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.tableProfile = response.data.profile;

        } else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${error.message}`);
      }).finally(() => {

      });
    },
    ////////////////////////////////////////////////////
    async deleteTable() {
      this.$emit('deleteTable', this.selectedTable);
      this.selectedTable = '';
    },
    ////////////////////////////////////////////////////

    async analyzeField(field) {
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/analyzeField`, {
        params: {
          tableName: this.selectedTable,
          fieldName: field,
        },
      }).then((response) => {
        if (response.status === 200) {
          toast.success('Field analyzed successfully');
        } else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${error.message}`);
      }).finally(() => {
        this.loading = false;
      });
    },

  }
}

</script>
<style scoped></style>