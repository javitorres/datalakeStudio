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
      <div class="col-md-6">
        <div v-if="path == null">
          <button class="btn btn-primary m-1 opcion-style" @click="getContent">
            List S3 content
          </button>
        </div>
        <div v-else>
          <h3>{{ path }}</h3>
          <h3 v-if="path!=''" @click="backFolder()"><i class="bi bi-arrow-up"></i> Back</h3>
          <!-- For every content in content -->
          <div v-for="item in content" :key="item.id">
            <p @click="clickS3Element(item)">
              <i v-if="isFolder(item)" class="bi bi-folder"></i>
              <i v-else class="bi bi-file"></i>
              {{ item }}
            </p>
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
      selectedFile: null,

    };
  },
  props: {


  },

  methods: {
    async getContent() {
      if (this.path == null) {
        this.path = '';
      }

      this.S3Files = [];
      var response = '';

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
      if (this.isFolder(item)) {
        this.path = item;
        this.getContent();
      } else {
        this.selectedFile = item;
      }
    },
    ////////////////////////////////////////////////////////////////
    async backFolder() {
      var path = this.path;
      var index = path.lastIndexOf('/');
      this.path = path.substring(0, index);
      this.getContent();
    },



  }
}

</script>

<style scoped></style>