<template>
  <!-- Fields -->
  <div class="col-md-2" v-if="schema && showOptions">
    
    <div class="row" v-for="(type, field) in schema" :key="field">
      <button class="btn btn-secondary m-1 opcion-style" @click="analyzeField">
        <span v-html="imageSrc(type)"></span>
        {{ field }}
      </button>
    </div>
  </div>

  <!-- Data and metadata -->
  <div class="col-md-10">
    <div class="row-md-2" v-if="showOptions">

      <button class="btn btn-primary m-1 opcion-style" @click="getSampleData(tableName)">
        <i class="bi bi-table"></i>
        Show sample data
      </button>

      <button class="btn btn-primary m-1 opcion-style" @click="getTableProfile(tableName)">
        <i class="bi bi-search"></i>
        Show table profile
      </button>

      <button class="btn btn-primary m-1 opcion-style" @click="crossFilters(tableName)">
        <i class="bi bi-graph-up-arrow"></i>
        Plot data
      </button>
    </div>

    <div class="row" v-if="sampleData && showSampleData">
      <!-- Sample data -->
      <h4 v-if="showOptions">Total rows: {{ rowcount }}.   Showing {{ records<rowcount?records:rowcount }}</h4>
      
    
      <div class="col-md-6" v-if="showOptions">
        <i class="bi bi-arrows-vertical"></i>
        <div class="btn-group">
          <button class="btn btn-primary" :class="{ active: type === 'First' }" @click="setType('First')">First</button>
          <button class="btn btn-primary" :class="{ active: type === 'Shuffle' }"
            @click="setType('Shuffle')">Shuffle</button>
          <button class="btn btn-primary" :class="{ active: type === 'Last' }" @click="setType('Last')">Last</button>
        </div>
        <i class="bi bi-grid-3x3-gap-fill"></i>
        <div class="btn-group">
          <button class="btn btn-primary" :class="{ active: records === 50 }" @click="setRecords(50)">50</button>
          <button class="btn btn-primary" :class="{ active: records === 100 }" @click="setRecords(100)">100</button>
          <button class="btn btn-primary" :class="{ active: records === 200 }" @click="setRecords(200)">200</button>
          <button v-if="records<1000" class="btn btn-primary" :class="{ active: records === 0 }" @click="setRecords(0)">All</button>
        </div>
      </div>
      <div class="col-md-6">

      </div>
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
  data() {
    return {
      showSampleData: true,
      showProfile: false,
      showCrossfilters: false,
      sampleData: Object,
      schema: Object,
      tableProfile: Object,
      rowcount: 0,
      type: 'First',
      records: 10,

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
    /*if (this.showOptionsProp === false) {
      this.showOptions = false;
    }else{
      this.showOptions = true;
    }*/
    
  },

  emits: [],

  watch: {
    tableName: function (newVal, oldVal) {
      this.load();
    }
  },

  methods: {
    setType(newType) {
      this.type = newType;
      this.getSampleData(this.tableName);
    },
    setRecords(newRecords) {
      this.records = newRecords;
      this.getSampleData(this.tableName);
    },

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
    async getRowcount(){
      await axios.get(`${apiUrl}/getRowCount`, {
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
      await axios.get(`${apiUrl}/getTableSchema`, {
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

    },
    ////////////////////////////////////////////////////
    async getSampleData(table) {
      this.showSampleData = true;
      this.showProfile = false;
      this.showCrossfilters = false;


      await axios.get(`${apiUrl}/getSampleData`, {
        params: {
          tableName: table,
          type: this.type,
          records: this.records,
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
      this.showCrossfilters = false;

      const fetchData = () => axios.get(`${apiUrl}/getTableProfile`, {
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
          this.tableProfile = response.data.profile;
          var columns = [];
          for (var key in this.tableProfile[0]) {
            columns.push({ title: key, field: key });
          }
          new Tabulator(this.$refs.tableProfile, {
            data: this.tableProfile,
            reactiveData: true,
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

      await this.getTableSchema(table);

      var charts = [];
      for (var key in this.schema) {
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
      this.chartConfig = {
        charts: charts
      };

      // Invalidate GenericCross to force re-render
      this.genericCrossKey++;

    }

  }

}

</script>
<style scoped></style>