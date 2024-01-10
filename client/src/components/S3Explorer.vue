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
        <!--path: {{ path }}
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
          <textarea class="form-control" id="exampleFormControlTextarea1" rows="30" v-model="fileContent"></textarea>
        </div>

        <div v-if="selectionType === 'folder'">
          <br />
          <h3>Folder metadata:</h3>
          <br />
          <div v-if=" ! folderMetadata ">
            <h2>No metadata found</h2>
            <p>Metadata is relevant convenient to maintain your datalake well documented. Also, if documentation is clear, SQL AI assistant will give you more accurate results</p>
            <!-- Button create metadata -->
            <button class="btn btn-primary m-1 opcion-style" @click="createMetadata">
              Create metadata
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
      bucket: 'madiva-datalake',
      path: null,
      content: [],
      selectedElement: null,
      selectionType: null,
      fileContent: null,
      folderMetadata: null,

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
          success: 'S3 search finished',
          error: 'Error searching in S3'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.content = response.data.results;
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
    async clickS3Element(item) {
      this.content = [];
      this.selectedElement = item;
      if (this.isFolder(item)) {
        this.path = item;
        this.selectionType = "folder";
        this.getContent();
      } else {
        this.selectedElement = item;
        this.selectionType = "file";
        await this.getFilePreview(item);
      }
    },
    ////////////////////////////////////////////////////////////////
    async getFilePreview(item) {
      const fileExtension = item.toLowerCase().split('.').pop();
      console.log("fileExtension:" + fileExtension);
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
      this.getContent();
    },
    ////////////////////////////////////////////////////////////////
    async createMetadata() {
      const fetchData = () => axios.get(`${apiUrl}/s3/createMetadata`, {
        params: {
          bucket: this.bucket,
          path: this.selectedElement,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Creating metadata, please wait...',
          success: 'Metadata created',
          error: 'Error creating metadata'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.folderMetadata = response.data;
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