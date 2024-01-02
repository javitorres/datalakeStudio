<template>
  <div class="row">
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

    <div class="row">
      <div class="col-md-6">
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
</template>

<script>
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'LoadDataPanel',
  data() {
    return {
      expanded: true,
      fileInput: '',
      S3Files: [],
      tableNameInput: '',

    };
  },

  emits: ['tableCreated'],

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

      // Remove s3 from beginning of the string
      var fileInputCleaned = this.fileInput;
      if (this.fileInput.substring(0, 2) === 's3') {
        fileInputCleaned = this.fileInput.substring(3, this.fileInput.length);
      }

      const fetchData = () => axios.get(`${apiUrl}/s3Search`, {
        params: {
          bucket: 'madiva-datalake',
          fileName: fileInputCleaned,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Searching in S3, please wait...',
          success: 'S3 search finished',
          error: 'Error searching in S3'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.S3Files = response.data.results;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    
    },
    ////////////////////////////////////////////////////////////////
    clickS3File(S3File, isFile) {
      this.fileInput = S3File;
      this.S3Files = [];
    },
    ////////////////////////////////////////////////////////////////
    async loadFile() {
      const fetchData = () => axios.get(`${apiUrl}/loadFile`, {
        params: {
          tableName: this.tableNameInput,
          fileName: this.fileInput,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Creating table from file, please wait...',
          success: 'Table created',
          error: 'Error creting table from file'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.$emit('tableCreated');
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },

  },
}

</script>
<style scoped></style>