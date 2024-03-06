<template>
  <div class="row">

    <ul class="nav nav-tabs">
      <!-- Upload file  -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeTab === 'uploadFile' }" aria-current="page" href="#"
          @click.prevent="activeTab = 'uploadFile'">Upload file</a>
      </li>

      <!-- Load from S3  -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeTab === 'loadS3' }" aria-current="page" href="#"
          @click.prevent="activeTab = 'loadS3'">Load from S3</a>
      </li>

      <!-- Load from URL -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeTab === 'loadSql' }" aria-current="page" href="#"
          @click.prevent="activeTab = 'loadUrl'">Load from URL</a>
      </li>

      <!-- Load from Path -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeTab === 'loadPath' }" aria-current="page" href="#"
          @click.prevent="activeTab = 'loadPath'">Load from Path</a>
      </li>
    </ul>

    <!-- Upload file ########################################################### -->
    <div v-if="activeTab == 'uploadFile'">
      <div class="col-md-6">
        <div class="mb-3">
          <br />
          <input class="form-control" type="file" id="formFile" ref="fileInputUpload">
        </div>

        <!-- Table name input -->
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Table</span>
          <input id="tableNameInputUpload" type="text" class="form-control" placeholder="Table name"
            aria-label="Table name" aria-describedby="basic-addon1" v-model="tableNameInputUpload">
        </div>

        <div class="col-md-2" v-if="tableNameInputUpload">
          <!-- Load file button -->
          <button class="btn btn-primary m-1 opcion-style" @click="uploadFile(tableNameInputUpload, fileInputUpload)">
            Load file
          </button>
        </div> <!-- col-md-2 -->
      </div>
    </div>

    <!-- Load from S3 ########################################################### -->
    <div v-if="activeTab == 'loadS3'">

      <div class="col-md-6">
        <br />
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">S3 Bucket</span>
          <input id="bucket" type="text" class="form-control" placeholder="s3 bucket" aria-label="File"
            aria-describedby="basic-addon1" v-model="bucket">
        </div>
      </div>

      <div class="col-md-6">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Data file to load</span>
          <input id="fileInput" type="text" class="form-control" placeholder="Search S3 file" aria-label="File"
            aria-describedby="basic-addon1" v-model="fileInputS3" @input="findFileInS3">
        </div>
      </div> <!-- col-md-6 -->

      <div class="col-md-4" v-if="fileInputS3">
        <!-- Table name input -->
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Table</span>
          <input id="tableNameInput" type="text" class="form-control" placeholder="Table name" aria-label="Table name"
            aria-describedby="basic-addon1" v-model="tableNameInputS3">
        </div>
      </div> <!-- col-md-4 -->

      <div class="col-md-2" v-if="fileInputS3 && tableNameInputS3">
        <!-- Load file button -->
        <button class="btn btn-primary m-1 opcion-style" @click="loadFile(tableNameInputS3, fileInputS3)">
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

    </div>

    <!-- Load from URL ###########################################################  -->
    <div v-if="activeTab == 'loadUrl'">
      <div class="col-md-6">
        <br />
        <p>Example:</p>
        <ul>
          <li>https://raw.githubusercontent.com/javitorres/GenericCross/main/public/data/iris.csv</li>
        </ul>

        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">URL to load</span>
          <input id="fileInputUrl" type="text" class="form-control"
            placeholder="Path to the file. Start with 's3 ' for search in your bucket while you type" aria-label="File"
            aria-describedby="basic-addon1" v-model="fileInputUrl">

        </div>

        <div class="col-md-4" v-if="fileInputUrl">
          <!-- Table name input -->
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Table</span>
            <input id="tableNameInputUrl" type="text" class="form-control" placeholder="Table name"
              aria-label="Table name" aria-describedby="basic-addon1" v-model="tableNameInputUrl">
          </div>
        </div> <!-- col-md-4 -->

        <div class="col-md-2" v-if="fileInputUrl && tableNameInputUrl">
          <!-- Load file button -->
          <button class="btn btn-primary m-1 opcion-style" @click="loadFile(tableNameInputUrl, fileInputUrl)">
            Load file
          </button>
        </div> <!-- col-md-2 -->
      </div>
    </div>

    <!-- Load from PATH ###########################################################  -->
    <div v-if="activeTab == 'loadPath'">
      <div class="col-md-6">
        <br />
        <p>Examples:</p>
        <ul>
          <li>/home/mydata/myfile.csv</li>
          <li>/home/mydata/*.csv</li>
        </ul>

        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">Path or file to load</span>
          <input id="fileInputUrl" type="text" class="form-control"
            placeholder="Path to the file. Start with 's3 ' for search in your bucket while you type" aria-label="File"
            aria-describedby="basic-addon1" v-model="fileInputPath">

        </div>

        <div class="col-md-4" v-if="fileInputPath">
          <!-- Table name input -->
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Table</span>
            <input id="tableNameInputUrl" type="text" class="form-control" placeholder="Table name"
              aria-label="Table name" aria-describedby="basic-addon1" v-model="tableNameInputPath">
          </div>
        </div> <!-- col-md-4 -->

        <div class="col-md-2" v-if="fileInputPath && tableNameInputPath">
          <!-- Load file button -->
          <button class="btn btn-primary m-1 opcion-style" @click="loadFile(tableNameInputPath, fileInputPath)">
            Load file
          </button>
        </div> <!-- col-md-2 -->
      </div>
    </div>

  </div> <!-- row -->
</template>

<script>
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { ref } from 'vue'
const fileInput = ref < HTMLInputElement | null > (null)
const files = ref()

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'LoadDataPanel',
  data() {
    return {
      activeTab: 'uploadFile',

      bucket: '',
      fileInputS3: '',
      fileInputUrl: '',
      fileInputPath: '',

      tableNameInputUpload: '',
      tableNameInputS3: '',
      tableNameInputUrl: '',
      tableNameInputPath: '',

      S3Files: [],

    };
  },

  emits: ['tableCreated'],

  methods: {
    ////////////////////////////////////////////////////////////////
    uploadFile(tableNameInputUpload, fileInputUpload) {
      const file = this.$refs.fileInputUpload.files[0];
      console.log(file)
      // post file
      const formData = new FormData()
      formData.append('file', file)
      formData.append('tableName', this.tableNameInputUpload)

      const fetchData = () => axios.post(`${apiUrl}/database/uploadFile`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      toast.promise(
        fetchData(),
        {
          pending: 'Uploading file, please wait...',
          success: 'Upload finished',
          error: 'Error uploading file'
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
    ////////////////////////////////////////////////////////////////
    handleFileChange() {
      files.value = fileInput.value?.files
    },
    ////////////////////////////////////////////////////////////////
    doSomething() {
      const file = files.value[0]
      console.log(file)
      // and do other things...
    },
    ////////////////////////////////////////////////////////////////

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
      // If fileName length is less than 3
      if (this.fileInputS3.length < 3) {
        this.S3Files = [];
        return;
      }

      this.S3Files = [];

      const fetchData = () => axios.get(`${apiUrl}/s3/s3Search`, {
        params: {
          bucket: this.bucket,
          fileName: this.fileInputS3,
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
      this.fileInputS3 = S3File;
      this.S3Files = [];
    },
    ////////////////////////////////////////////////////////////////
    async loadFile(tableNameInput, fileInput) {
      const fetchData = () => axios.get(`${apiUrl}/database/loadFile`, {
        params: {
          tableName: tableNameInput,
          fileName: fileInput,
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