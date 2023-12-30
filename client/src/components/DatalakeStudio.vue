<template>
  <div class="container-fluid">

    <div class="row">
      <h1 v-on:click="expanded = !expanded">{{ expanded ? "-" : "+" }} Load data from files</h1>
      <div v-if="expanded">
        <div class="col-md-6">
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Data file to load</span>
            <input id="fileInput" type="text" class="form-control"
              placeholder="Path to the file. Start with 's3 ' for search in your bucket while you type" aria-label="File"
              aria-describedby="basic-addon1" v-model="fileInput" @input="findFileInS3">
          </div>
        </div> <!-- col-md-6 -->

        <div class="col-md-4" v-if="fileInput">
          <!-- Table name input -->
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Table</span>
            <input id="tableNameInput" type="text" class="form-control" placeholder="Table name" aria-label="Table name"
              aria-describedby="basic-addon1" v-model="tableNameInput">
          </div>
        </div> <!-- col-md-4 -->

        <div class="col-md-2" v-if="fileInput && tableNameInput">
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
      </div> <!-- if expanded -->
    </div> <!-- row -->

    <RemoteDbPanel @tableCreated="this.tableCreated"></RemoteDbPanel>

    <TablesPanel v-if="tables && tables.length > 0" :tables="tables" @deleteTable="this.deleteTable">
    </TablesPanel>
    

    <QueryPanel v-if="tables && tables.length > 0" @tableCreated="this.tableCreated"></QueryPanel>

    <ApiRetriever v-if="tables && tables.length > 0" :tables="tables" @tableCreated="this.tableCreated"></ApiRetriever>

  </div> <!-- container-fluid -->
</template>

<script>
import axios from 'axios';
import TablesPanel from './TablesPanel.vue';
import QueryPanel from './QueryPanel.vue';
import RemoteDbPanel from './RemoteDbPanel.vue';
import ApiRetriever from './ApiRetriever.vue';

import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

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
    RemoteDbPanel,
    ApiRetriever
  },

  data() {
    return {
      expanded: true,
      fileInput: '',

      loading: false,
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
    async findFileInS3() {
      // If fileName length is less than 3 or fileName doesn start with 's3' don't search
      if (this.fileInput.length < 5 || this.fileInput.substring(0, 2) !== 's3') {
        this.S3Files = [];
        //console.log('No search:"' + this.fileInput.substring(0, 3) + '"');
        return;
      }

      this.S3Files = [];
      var response = '';
      this.loading = true;

      // Remove s3 from beginning of the string
      var fileInputCleaned = this.fileInput;
      if (this.fileInput.substring(0, 2) === 's3') {
        fileInputCleaned = this.fileInput.substring(3, this.fileInput.length);
      }


      await axios.get(`${apiUrl}/s3Search`, {
        params: {
          bucket: 'madiva-datalake',
          fileName: fileInputCleaned,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.S3Files = response.data.results;
        }
        else {
          //toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        //toast.error(`Error: HTTP ${response.data}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////////////////
    clickS3File(S3File, isFile) {
      this.fileInput = S3File;
      this.S3Files = [];
    },
    ////////////////////////////////////////////////////////////////
    async loadFile() {
      this.loading = true;
      this.info = 'Loading file please wait...';
      axios.get(`${apiUrl}/loadFile`, {
        params: {
          tableName: this.tableNameInput,
          fileName: this.fileInput,
        },
      }).then((response) => {
        if (response.status === 200) {
          toast.success('Table created successfully');
        }
        else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${response.data}`);
      }).finally(() => {
        this.loading = false;
        this.info = '';
        this.getTables();
      });
    },
    ////////////////////////////////////////////////////////////////
    async getTables() {
      await axios.get(`${apiUrl}/getTables`, {
        params: {
        },
      }).then((response) => {
        this.tables = response.data;
        
      }).catch((error) => {
        toast.error(`Error: HTTP ${response.data}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////////////////
    async deleteTable(table) {
      var response = await axios.get(`${apiUrl}/deleteTable`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
          toast.success('Table deleted successfully');
          this.getTables();
        } else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${error.message}`);
      }).finally(() => {
        this.loading = false;
      });
    },
    ////////////////////////////////////////////////////////////////
    async tableCreated() {
      this.getTables();
    },
  },

}


</script>
