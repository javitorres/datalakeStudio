<template>
  <!-- Fields -->
  <div class="col-md-1" v-if="schema && showOptions">

    <!-- Check all and check none buttons -->
    <button class="btn btn-primary m-1 opcion-style" @click="selectAllFields(false)">
      <i class="bi bi-x-square"></i>
      None
    </button>
    <button class="btn btn-primary m-1 opcion-style" @click="selectAllFields(true)">
      <i class="bi bi-check-square"></i>
      All
    </button>

    <div class="row" v-for="(type, field) in schema" :key="field">
      <button class="btn m-1 opcion-style" :class="selectedFields.includes(field) ? 'btn-primary' : 'btn-secondary'"
        @click="toggleField(field)">
        <span v-html="imageSrc(type)"></span>
        {{ field }}
      </button>
    </div>
  </div>

  <!-- Data and metadata -->
  <div class="col-md-10 custom-col">
    <div class="row-md-2" v-if="showOptions">
      <!--<p>Row: {{ rowSelected }}</p>-->

      <button class="btn btn-primary m-1 opcion-style" :class="{ active: showSampleData }"
        @click="getSampleData(tableName)">
        <i class="bi bi-table"></i>
        Show sample data
      </button>

      <button class="btn btn-primary m-1 opcion-style" :class="{ active: showProfile }"
        @click="getTableProfile(tableName)">
        <i class="bi bi-search"></i>
        Show table profile
      </button>

      <button class="btn btn-primary m-1 opcion-style" :class="{ active: showCrossfilters }"
        @click="crossFilters(tableName)">
        <i class="bi bi-graph-up-arrow"></i>
        Plot data
      </button>
    </div>

    <div class="row" v-if="sampleData && showSampleData">
      <!-- Sample data -->
      <div class="col-md-3" v-if="showOptions">
        <div class="btn-group">
          <button class="btn btn-secondary"><i class="bi bi-list-columns-reverse"></i> {{ rowcount }} rows</button>
          <button class="btn btn-secondary"><i class="bi bi-eyedropper"></i>{{ records != 0 ? records : rowcount }}
            showed</button>
        </div>
      </div>

      <div class="col-md-2" v-if="showOptions">
        <div class="btn-group">
          <button class="btn btn-primary"><i class="bi bi-arrows-vertical"></i></button>
          <button class="btn btn-primary" :class="{ active: type === 'First' }" @click="setType('First')">First</button>
          <button class="btn btn-primary" :class="{ active: type === 'Shuffle' }"
            @click="setType('Shuffle')">Shuffle</button>
          <button class="btn btn-primary" :class="{ active: type === 'Last' }" @click="setType('Last')">Last</button>
        </div>

      </div>
      <div class="col-md-2" v-if="showOptions">
        <div class="btn-group">
          <button class="btn btn-primary"><i class="bi bi-grid-3x3-gap-fill"></i></button>
          <button class="btn btn-primary" :class="{ active: records === 50 }" @click="setRecords(50)">50</button>
          <button class="btn btn-primary" :class="{ active: records === 100 }" @click="setRecords(100)">100</button>
          <button class="btn btn-primary" :class="{ active: records === 200 }" @click="setRecords(200)">200</button>
          <button v-if="records < 1000" class="btn btn-primary" :class="{ active: records === 0 }"
            @click="setRecords(0)">All</button>
        </div>
      </div>
      <!-- Data Table -->
      <div ref="table"></div>
    </div>

    <!-- Data profile -->
    <div v-if="tableProfile && showProfile">
      <h4>Table profile</h4>
      <div ref="tableProfile"></div>
    </div>

    <!-- Cross filters -->
    <GenericCross v-if="sampleData && chartConfig && showCrossfilters" :key="genericCrossKey" :dataStr="sampleData"
      :chartConfig="chartConfig">
    </GenericCross>

  </div>
</template>

<script>
import axios from 'axios';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import GenericCross from './GenericCross.vue';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'TableInspector',

  // This variable cant be reactive to avoid interactions with Tabulator state
  myTabulator: null,
  data() {
    return {
      selectedFields: null,
      showSampleData: true,
      showProfile: false,
      showCrossfilters: false,
      sampleData: Object,
      schema: Object,
      tableProfile: Object,
      rowcount: 0,
      type: 'First',
      records: 10,
      rowSelected: null,

      chartConfig: null,
      genericCrossKey: 0,
    };
  },

  components: {
    GenericCross
  },
  props: {
    tableName: String,
    showOptions: Boolean,
  },
  mounted() {
    this.load();
  },

  emits: [],

  watch: {
    tableName: function (newVal, oldVal) {
      this.load();
    }
  },

  methods: {
    selectAllFields(all) {
      this.selectedFields = [];
      if (all) {
        this.selectedFields = Object.keys(this.schema)
      }
      this.generateCharts();
    },
    ////////////////////////////////////////////////////
    toggleField(field) {
      if (this.selectedFields == null) {
        this.selectedFields = [];
      }
      if (this.selectedFields.includes(field)) {
        this.selectedFields = this.selectedFields.filter(item => item !== field);
      } else {
        this.selectedFields.push(field);
      }
      this.generateCharts();
      this.updateTable();
     
    },
    ////////////////////////////////////////////////////
    updateTable() {
      var columns = [];
      for (var key in this.schema) {
        if (this.selectedFields.includes(key)) {
          columns.push({ title: key, field: key });
        }
      }
    
      this.myTabulator.setColumns(columns);
      //this.$refs.table.setColumns(columns);
    },
    /////////////////////////////////////////////////
    setType(newType) {
      this.type = newType;
      this.getSampleData(this.tableName);
    },
    ////////////////////////////////////////////////////
    setRecords(newRecords) {
      this.records = newRecords;
      this.getSampleData(this.tableName);
    },
    ////////////////////////////////////////////////////
    async load() {
      await this.getSampleData(this.tableName);
      await this.getRowcount();
      await this.getTableSchema(this.tableName);
    },
    ////////////////////////////////////////////////////
    imageSrc(type) {
      if (type === 'object') return '<i class="bi bi-alphabet-uppercase"></i>';
      else if (type === 'float32') return '<i class="bi bi-123"></i>';
      else if (type === 'float64') return '<i class="bi bi-123"></i>';
      else if (type === 'int64') return '<i class="bi bi-123"></i>';
      else if (type === 'boolean') return "MNO";
      else if (type === 'null') return "PQR";
      else return type;
    },
    /////////////////////////////////////////////////
    async getRowcount() {
      await axios.get(`${apiUrl}/database/getRowCount`, {
        params: {
          tableName: this.tableName,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.rowcount = response.data.rows;
        } else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${response.message}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////
    async getTableSchema(table) {
      await axios.get(`${apiUrl}/database/getTableSchema`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.schema = response.data;
          if (this.selectedFields  == null) {
            this.selectedFields = [];
            // All fields selected by default. Fill selectedFields with fields from schema
            for (var key in this.schema) {
              this.selectedFields.push(key).field;
            }
          }
          
        } else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${response.message}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////
    async getSampleData(tableName) {
      this.showSampleData = true;
      this.showProfile = false;
      this.showCrossfilters = false;
      
      await axios.get(`${apiUrl}/database/getSampleData`, {
        params: {
          tableName: tableName,
          type: this.type,
          records: this.records,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.sampleData = response.data;
          
          this.myTabulator = new Tabulator(this.$refs.table, {
            data: this.sampleData,
            importFormat: "csv",
            autoColumns: true,
            layout: "fitColumns",
            //layout: "fitDataStretch",
            persistence: true, // TODO: Review this, not working
            /*rowClick: function (e, row) {
              console.log("ROW1" + JSON.stringify(row));
            },*/
          });
          
          /*this.myTabulator.on("rowClick", function (row) {
            // TODO get tow data and emit row info
            console.log("ROW2" + JSON.stringify(row));
            this.rowSelected = row;
          });
          */

          // Update selected columns state
          this.myTabulator.on("tableBuilt", (data) => {
            console.log("tableBuilt");
            // TODO It doens't work
            this.updateTable();
          });

          
        } else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error:: HTTP ${error.message}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////
    async getTableProfile(table) {
      this.showSampleData = false;
      this.showProfile = true;
      this.showCrossfilters = false;
      
      const fetchData = () => axios.get(`${apiUrl}/database/getTableProfile`, {
        params: {
          tableName: table,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Loading table profile, please wait...',
          success: 'Profile loaded',
          error: 'Error loading profile'
        },
        {
          position: toast.POSITION.BOTTOM_RIGHT,
        }
      ).then((response) => {
        if (response.status === 200) {
          this.tableProfile = response.data;
          
          new Tabulator(this.$refs.tableProfile, {
            data: this.tableProfile,
            reactiveData: true,
            layout: "fitColumns",
            importFormat: "csv",
            autoColumns: true,
          });
        }
      }).catch((error) => {
        console.error('Error: ', error.message);
      });
    },
    ////////////////////////////////////////////////////
    async crossFilters(table) {
      this.showSampleData = false;
      this.showProfile = false;
      this.showCrossfilters = true;

      //await this.getTableSchema(table);
      this.generateCharts();
    },
    ////////////////////////////////////////////////////
    generateCharts() {
      var charts = [];
      for (var key in this.schema) {
        // if key in selectedFields
        if (this.selectedFields.includes(key)) {
          var chart = {
            title: key,
            type: this.schema[key],
            fields: key
          };
          if (chart.type === 'object' || chart.type === 'bool') {
            chart.type = 'categorical';
          } else if (chart.type === 'int64' || chart.type === 'float64') {
            chart.type = 'numerical';
          } else if (chart.type === 'datetime64[ns]') {
            chart.type = 'date';
          } else {
            chart.type = 'categorical';
          }
          charts.push(chart);
        }
      }
      this.chartConfig = {
        charts: charts
      };

      // Invalidate GenericCross to force re-render
      this.genericCrossKey++;
    }
  },
}

</script>
<style scoped>
.tabulator {
  background-color: #ffffff;
  padding-left: 20px;
  padding-right: 20px;
  padding-top: 20px;
  padding-bottom: 20px;
  border: #ffffff;
}

.custom-col {
  padding-left: 20px;

}
</style>