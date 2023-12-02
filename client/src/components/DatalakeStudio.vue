<template>
  <div class="container-fluid">
    <div class="row" style="width: 800px">

      <div class="col-md-6">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">File</span>
          <input id="fileInput" type="text" class="form-control" placeholder="Path to the file " aria-label="File"
            aria-describedby="basic-addon1" v-model="fileInput" @input="findFileInS3">
        </div>
      </div>

      <div class="col-md-4">
        <!-- Table name input -->
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Table</span>
          <input id="tableNameInput" type="text" class="form-control" placeholder="Table name"
            aria-label="Table name" aria-describedby="basic-addon1" v-model="tableNameInput">
        </div>
        
      </div>

      <div class="col-md-2">
        <!-- Load file button -->
        <button class="btn btn-primary m-1 opcion-style" @click="loadFile">
          Load file
        </button>
        
      </div>

      <div class="row">
      <div class="col-md-6">
        <div class="spinner-border" role="status" v-if="loading">
          <span class="visually-hidden">Loading...</span>
        </div>
        <div class="alert alert-danger" role="alert" v-if="error">
          {{ error }}
        </div>
        <div class="alert primary alert" role="alert" v-if="info">
          {{ info }}
        </div>
        <div v-if="S3Files && S3Files.length > 0">
          <ul class="list-unstyled d-flex flex-wrap">
            <li v-for="S3File in S3Files" :key="S3File.id">
              <button class="btn btn-primary m-1 opcion-style" @click="clickS3File(S3File, true)">
                {{ S3File }}
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>


    </div>
  </div>
</template>

<script>
import axios from 'axios';

//import axios from 'axios';
//import L from 'leaflet';

export default {
  name: 'DatalakeStudio',
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
    };
  },
  methods: {
    getProperty(path, defaultValue = '') {
      try {
        return path.split('.').reduce((o, i) => o[i], this);
      } catch (e) {
        return defaultValue;
      }
    },
    initDatabase() {
      console.log('initDatabase');
      axios.get(`http://${this.serverHost}:${this.serverPort}/init`);
    },

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
  }
}


</script>
