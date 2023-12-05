<template>
  <div class="container-fluid">
    <div class="row">

      <div class="col-md-6">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">File</span>
          <input id="fileInput" type="text" class="form-control" placeholder="Path to the file " aria-label="File"
            aria-describedby="basic-addon1" v-model="fileInput" @input="findFileInS3">
        </div>
      </div> <!-- col-md-6 -->

      <div class="col-md-4">
        <!-- Table name input -->
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Table</span>
          <input id="tableNameInput" type="text" class="form-control" placeholder="Table name" aria-label="Table name"
            aria-describedby="basic-addon1" v-model="tableNameInput">
        </div> 
      </div> <!-- col-md-4 -->

      <div class="col-md-2">
        <!-- Load file button -->
        <button class="btn btn-primary m-1 opcion-style" @click="loadFile">
          Load file
        </button>
      </div> <!-- col-md-2 -->
    </div> <!-- row -->

    <div class="row">
      <div class="col-md-6">

        <div class="row">
          <div class="col-md-2">
            <div class="spinner-border" role="status" v-if="loading">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>

          <div class="col-md-10">
            <div class="alert alert-danger" role="alert" v-if="error">
              {{ error }}
            </div>
            <div class="alert primary alert" role="alert" v-if="info">
              {{ info }}
            </div>
          </div>
        </div>

        <div class="row">
          <div v-if="S3Files && S3Files.length > 0">
            <ul class="list-unstyled d-flex flex-wrap">
              <li v-for="S3File in S3Files" :key="S3File.id">
                <button class="btn btn-primary m-1 opcion-style" @click="clickS3File(S3File, true)">
                  {{ S3File }}
                </button>
              </li>
            </ul>
          </div> <!-- v-if -->
        </div> <!-- row -->
      </div> <!-- col-md-6 -->
    </div> <!-- row -->

    <TablesPanel 
      :tables="tables"

      @deleteTable="this.deleteTable"
      >
    </TablesPanel>
    <br/>
    <QueryPanel
      @tableCreated="this.tableCreated"
      
    ></QueryPanel>

  </div> <!-- container-fluid -->
</template>

<script>
import axios from 'axios';
import TablesPanel from './TablesPanel.vue';
import QueryPanel from './QueryPanel.vue';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';
//import { get } from 'express/lib/response';

export default {
  name: 'DatalakeStudio',

  /*
  // Toast setup
  setup() {
    const notify = () => {
      toast("Wow so easy !", {
        autoClose: 1000,
      }); // ToastOptions
    }
    return { notify };
   },
  */
  components: { 
    TablesPanel,
    QueryPanel,
  },

  data() {
    return {
      fileInput: '',
      serverHost: 'localhost',
      serverPort: '8080',
      loading: false,
      error: '',
      info: '',
      S3Files: [],
      tableNameInput: '',
      tables: [],
    };
  },

  mounted() {
    this.getTables();
    
  },

  methods: {
    getProperty(path, defaultValue = '') {
      try {
        return path.split('.').reduce((o, i) => o[i], this);
      }
      catch (e) {
        return defaultValue;
      }
    },
    ////////////////////////////////////////////////////////////////
    findFileInS3() {
      this.S3Files = [];
      var response = '';
      this.loading = true;
      axios.get(`http://${this.serverHost}:${this.serverPort}/s3Search`, {
        params: {
          bucket: 'madiva-datalake',
          fileName: this.fileInput,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          this.S3Files = response.data.results;
        }
        else {
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
    ////////////////////////////////////////////////////////////////
    loadFile() {
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
          toast.success('Table created successfully');
        }
        else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: HTTP ${response.data}`;
      }).finally(() => {
        this.loading = false;
        this.info = '';
        this.getTables();
      });
    },
    ////////////////////////////////////////////////////////////////
    getTables() {
      axios.get(`http://${this.serverHost}:${this.serverPort}/getTables`, {
        params: {
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          this.tables = response.data;
        }
        else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: HTTP ${response.data}`;
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////////////////
    async deleteTable(table){
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/deleteTable`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          
          toast.success('Table deleted successfully');
          this.getTables();
          //this.emit("tableDeleted");
        } else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: ${error.message}`;
      }).finally(() => {
        this.loading = false;
      });
    },

    async tableCreated(){
      this.getTables();
    },
  },
  
}


</script>
