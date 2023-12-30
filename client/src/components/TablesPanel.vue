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
              <button v-if="selectedTable !== table" class="btn btn-primary m-1 opcion-style" @click="selectedTable=table">
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
      <div class="col-md-1">
        <button class="btn btn-danger m-1 opcion-style" @click="confirmDelete">
          <i class="bi bi-x-octagon"></i>
          Delete table
        </button>
      </div>
      <div class="col-md-2">
        <button class="btn btn-success m-1 opcion-style" @click="confirmDownload">
          <i class="bi bi-x-octagon"></i>
          Download data
        </button>
      </div>

      <div class="row" v-if="selectedTable">
        <TableInspector :tableName="selectedTable" :showOptions="showOptions"/>
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

  <div v-if="showDownloadDialog" class="modal fade show" style="display: block;" aria-modal="true" role="dialog">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Download data</h5>
          <button type="button" class="btn-close" @click="showDownloadDialog = false" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p>Downloading {{ selectedTable }}, select format:</p>
          <button class="btn btn-success m-1 opcion-style" @click="download('csv')"><i class="bi bi-filetype-csv"></i> CSV</button>
          <button class="btn btn-success m-1 opcion-style" @click="download('parquet')"><i class="bi bi-table"></i> Parquet</button>
          <button class="btn btn-success m-1 opcion-style" @click="download('excel')"><i class="bi bi-filetype-xlsx"></i> Excel</button>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showDownloadDialog = false">Cancel</button>
          <!--<button type="button" class="btn btn-danger" @click="deleteTable">Yes, delete it</button>-->
        </div>
      </div>
    </div>
  </div>
  <div v-if="showDialog" class="modal-backdrop fade show"></div>


</template>

<script>
import TableInspector from './TableInspector.vue';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'TablesPanel',
  components: {
    TableInspector
  },
  data() {
    return {
      showDialog: false,
      showDownloadDialog: false,
      expanded: true,
      showOptions: true,

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
    ////////////////////////////////////////////////////
    confirmDelete() {
      this.showDialog = true;
    },
    ////////////////////////////////////////////////////
    confirmDownload() {
      this.showDownloadDialog = true;

    },
    ////////////////////////////////////////////////////
    download(format) {
      console.log('downloading ' + format);

      const fetchData = async () => await axios.get(`${apiUrl}/exportData`, {
        params: {
          format: format,
          tableName: this.selectedTable,
        },
        responseType: 'blob'
        
      });
        
      toast.promise(
        fetchData(),
        {
          pending: 'Exporting data, please wait...',
          success: 'Data exported successfully',
          error: 'Error creating export'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.showDownloadDialog = false;  

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'exported_data.' + format); 
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
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
      var response = await axios.get(`${apiUrl}/analyzeField`, {
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
    ////////////////////////////////////////////////////
    

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
  z-index: 1040;
  /* Backdrop debe estar detrás del modal */
}

.modal-content {
  background-color: #fefefe;
  margin: 15% auto;
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
}
</style>