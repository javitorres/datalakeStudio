<template>
  <div class="row">
    <div class="col-md-6">
      <div class="col-md-6">
        <div class="input-group mb-3">
          <span class="input-group-text" id="basic-addon1">S3 Bucket</span>
          <input id="bucket" type="text" class="form-control" placeholder="s3 bucket" aria-label="File"
            aria-describedby="basic-addon1" v-model="bucket">
        </div>
      </div>

      <!-- Show list of folders -->
      <div class="col-md-8">
        <!--Debug: path: {{ path }}
        <br />
        selectedElement: {{ selectedElement }}
        <br />
        selectionType: {{ selectionType }}
        <br />
        -->
        

        <div v-if=" path == null">
          <button class="btn btn-primary m-1 opcion-style" @click="getContent">
            List S3 content
          </button>
        </div>
        <div v-else>
          <h3>Folder: {{ path ? path : "/" }}</h3>
          <br />
          <h3 v-if="path != ''" @click="back()"><i class="bi bi-arrow-left"> Back</i></h3>
          <br />
          <!-- For every content in content -->
          <p v-if=" content.length == 1">No content in this folder</p>
          <div v-for="item in content" :key="item.id">
            <h4 @click="clickS3Element(item)" v-if="item != path">
              <i v-if="isFolder(item)" class="bi bi-folder" style="color:blue;"> {{ itemWithoutPath(item) }}</i>
              <i v-if="!isFolder(item)" class="bi bi-file-earmark-text-fill" style="color:green;"> {{ itemWithoutPath(item) }}</i>
            </h4>
          </div>
        </div>
      </div>

    </div>
    <div class="col-md-6">
      <div v-if="selectedElement != null">
        <h3>Details of {{ selectionType }} {{ selectedElement }}</h3>
        
        <div v-if="selectionType === 'file'">
          <h3>File preview:</h3>
          <textarea class="form-control" id="exampleFormControlTextarea1" v-model="fileContent"></textarea>
          <br />
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Load data as table</span>
            <input id="bucket" type="text" class="form-control" placeholder="s3 bucket" aria-label="File" aria-describedby="basic-addon1" v-model="newTableName">
            <button class="btn btn-primary m-1 opcion-style" @click="loadFile(newTableName, selectedElement)">
              Load file {{ newTableName }}
            </button>
          </div>

        </div>

        <div v-if="selectionType === 'folder'">
          <br />
          <h3>Folder info:</h3>
          <br />
          <div v-if=" ! folderMetadata ">
            <h2>No metadata found</h2>
            <p>Metadata is relevant convenient to maintain your datalake well documented. Also, if documentation is clear, SQL AI assistant will give you more accurate results</p>
            <!-- Button create metadata -->
            <button class="btn btn-primary m-1 opcion-style" @click="createEmptyMetadata">
              Create metadata
            </button>
          </div>
          <div v-else>
            
            <div class="form-floating mb-3">
              <textarea v-model="folderMetadata.description" style="height: 200px" class="form-control" placeholder="Leave a comment here" id="floatingTextarea"></textarea>
              <label for="floatingInput">Description</label>
            </div>
            
            <button class="btn btn-primary m-1 opcion-style" @click="updateMetadata">
              Update metadata
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'S3Explorer',

  data() {
    return {
      bucket: '',
      path: null,
      content: [],
      selectedElement: null,
      selectionType: null,
      fileContent: null,
      folderMetadata: null,
      loading: false,
      newTableName: null,

    };
  },
  props: {},

  methods: {
    itemWithoutPath(item) {
      if (item == null) {
        return '';
      }
      const regex = new RegExp(this.path, 'g');
      return item.replace(regex, '');
    },
    //////////////////////////////////////////////////////////////////
    async getContent() {
      
      if (this.path == null) {
        this.path = '';
      }

      const fetchData = () => axios.get(`${apiUrl}/s3/getContent`, {
        params: {
          bucket: this.bucket,
          path: this.path,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Listing S3 content, please wait...',
          success: '',
          error: 'Error searching in S3'
        },
        { position: toast.POSITION.BOTTOM_RIGHT, timeout: 1000 }
      ).then((response) => {
        this.content = response.data.content;
        this.folderMetadata = response.data.metadata;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
      
    },

    //////////////////////////////////////////////////////////////////
    isFolder(item) {
      return item.endsWith('/');
    },
    ////////////////////////////////////////////////////////////////
    getOnlyFileNameWithOutExtension(fileName) {
      //  In: clientes/bbva/marcas.csv
      // Out: marcas
      return fileName.split('/').pop().split('.').slice(0, -1).join('.');

      
    },

    ////////////////////////////////////////////////////////////////
    async clickS3Element(item) {
      this.loading = true;
      this.selectedElement = item;
      if (this.isFolder(item)) {
        this.content = [];
        this.path = item;
        this.selectionType = "folder";
        this.getContent();
      } else {
        this.newTableName = this.getOnlyFileNameWithOutExtension(item);
        
        this.selectedElement = item;
        this.selectionType = "file";
        await this.getFilePreview(item);
      }
      this.loading = false;
    },
    ////////////////////////////////////////////////////////////////
    async getFilePreview(item) {
      const fileExtension = item.toLowerCase().split('.').pop();
      //console.log("fileExtension:" + fileExtension);
      if (!['csv', 'txt', 'json'].includes(fileExtension)) {
        this.fileContent = 'File preview not available for this file type (' + fileExtension + '). Only .csv, .txt and .json files are supported.';
        return;
      }
      var response = '';
      const fetchData = () => axios.get(`${apiUrl}/s3/getFilePreview`, {
        params: {
          bucket: this.bucket,
          path: item,
        },
      });

      return toast.promise(
        fetchData(),
        {
          pending: 'Getting file content, please wait...',
          success: 'File content retrieved',
          error: 'Error getting file content'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        //return response.data.results;
        this.fileContent = response.data;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },

    ////////////////////////////////////////////////////////////////
    async back() {
      //console.log("PRE back:" + "path:" + this.path + " selectedElement:" + this.selectedElement + " selectionType:" + this.selectionType);
      this.content = [];
      if (this.isFolder(this.selectedElement)) {
        var folders = this.path.split('/').filter(Boolean);
        folders.pop();

        this.selectionType = "folder";
        this.selectedElement = this.path;
        this.path = folders.join('/');
        this.path = this.path + '/';
        if (this.path == '/') {
          this.path = '';
        }
      }
      else {
        this.selectionType = 'folder';
        this.selectedElement = this.path;
      }
      //console.log("POST back:" + "path:" + this.path + " selectedElement:" + this.selectedElement + " selectionType:" + this.selectionType);
      this.metadata = null;
      this.getContent();
    },
    //////////////////////////////////////////////////////////////////////
    createEmptyMetadata(){
      this.folderMetadata = {
        description: '',
      }
    },

    ////////////////////////////////////////////////////////////////
    async updateMetadata() {
      this.folderMetadata.path = this.path;
      this.folderMetadata.bucket = this.bucket;

      const fetchData = () => axios.post(`${apiUrl}/s3/updateMetadata`, 
         this.folderMetadata,
      );

      toast.promise(
        fetchData(),
        {
          pending: 'Updating metadata, please wait...',
          success: 'Metadata updated',
          error: 'Error updating metadata'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.getContent();
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    //////////////////////////////////////////////////////////////////////
    async loadFile(tableNameInput, fileInput) {
      const fetchData = () => axios.get(`${apiUrl}/database/loadFile`, {
        params: {
          tableName: tableNameInput,
          fileName: "s3://" + this.bucket + "/" + fileInput,
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
  }
}

</script>

<style scoped></style>