<template>
  <!-- Table list -->
  <hr>
  <h1 v-on:click="expanded = !expanded">{{ expanded ? "-" : "+" }} Table explorer</h1>
  <div v-if="expanded">
    <div class="row">
      <div class="col-md-12">
        <div v-if="tables && tables.length > 0">
          <ul class="list-unstyled d-flex flex-wrap">
            <li v-for="table in tables" :key="table.id">
              <button v-if="selectedTable !== table" class="btn btn-primary m-1 opcion-style" @click="clickTable(table)">
                <i class="bi bi-table"></i>
                {{ table }}
              </button>
              <!-- if table selected then  button green -->
              <button v-if="selectedTable === table" class="btn btn-success m-1 opcion-style" @click="clickTable(table)">
                <i class="bi bi-table"></i>
                {{ table }}
              </button>
            </li>
            <li>
              <button v-if="selectedTable" class="btn btn-secondary m-1 opcion-style" @click="selectedTable = None">
                <i class="bi bi-x-square"></i>
                Close table view
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="row" v-if="selectedTable">
      <!-- Delete button -->
      <div class="row-md-2" v-if="selectedTable">
        <button class="btn btn-danger m-1 opcion-style" @click="confirmDelete">
          <i class="bi bi-x-octagon"></i>
          Delete table
        </button>

        <button class="btn btn-primary m-1 opcion-style" @click="getSampleData(selectedTable)">
          <i class="bi bi-table"></i>
          Show sample data
        </button>

        <button class="btn btn-primary m-1 opcion-style" @click="getTableProfile(selectedTable)">
          <i class="bi bi-search"></i>
          Show table profile
        </button>
      </div>
      <!-- Fields -->
      <div class="col-md-2" v-if="schema">
        <h4>Table Fields</h4>
        <div class="row" v-for="(type, field) in schema" :key="field">
          <button class="btn btn-secondary m-1 opcion-style" @click="analyzeField">
            <!--<img :src="imageSrc(type)" alt="profile table" width="30" height="30">-->
            <span v-html="imageSrc(type)"></span>
            {{ field }} 
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
        <div ref="tableProfile"></div>
      </div>
    </div>
  </div>

  <!-- Diálogo de confirmación -->
  <div v-if="showDialog" class="modal fade show" style="display: block;" aria-modal="true" role="dialog">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Attention</h5>
          <button type="button" class="btn-close" @click="showDialog = false" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p>Are you sure you want to drop table {{ selectedTable }}?</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showDialog = false">Cancel</button>
          <button type="button" class="btn btn-danger" @click="deleteTable">Yes, delete it</button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="showDialog" class="modal-backdrop fade show"></div>

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
      showDialog: false,
      expanded: true,
      serverHost: 'localhost',
      serverPort: '8000',
      schema: [],
      sampleData: [],

      showSampleData: true,
      showProfile: false,

      tabulator: null,
      table: [],
      tableProfile: [],

      selectedTable: '',
    };
  },
  props: {
    tables: Object,
  },

  emits: ['deleteTable'],


  methods: {
    imageSrc(type) {
      
      if (type === 'object') return '<i class="bi bi-alphabet-uppercase"></i>';
      else if (type === 'float32') return '<i class="bi bi-123"></i>';
      else if (type === 'float64') return '<i class="bi bi-123"></i>';
      else if (type === 'int64') return '<i class="bi bi-123"></i>';
      else if (type === 'boolean') return "MNO";
      else if (type === 'null') return "PQR";
      else return type;
      
    },
    confirmDelete() {
      this.showDialog = true;
    },
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

      const fetchData = () => axios.get(`http://${this.serverHost}:${this.serverPort}/getTableProfile`, {
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
    async deleteTable() {
      this.$emit('deleteTable', this.selectedTable);
      this.selectedTable = '';
      this.showDialog = false;
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
<style scoped>
.modal {
  display: block;
  position: fixed;
  z-index: 1050;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-backdrop {
  z-index: 1040; /* Backdrop debe estar detrás del modal */
}

.modal-content {
  background-color: #fefefe;
  margin: 15% auto;
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
}


</style>