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
          <button v-if="bucket" class="btn btn-primary m-1 opcion-style" @click="getContent">
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
        <h3>s3://{{ bucket }}/{{ selectedElement }}</h3>

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
            <p>Metadata is convenient to maintain your datalake well documented. Also, if documentation is clear, SQL AI assistant will give you more accurate results</p>
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

            <div class="form-floating mb-3">
              <textarea v-model="folderMetadata.owner" style="height: 20px" class="form-control" placeholder="Leave a comment here" id="floatingTextarea"></textarea>
              <label for="floatingInput">Owner/s (space separated)</label>
            </div>

            <div class="form-floating mb-3">
              <textarea v-model="folderMetadata.schema" style="height: 200px" class="form-control" placeholder="Leave a comment here" id="floatingTextarea"></textarea>
              <label for="floatingInput">Schema</label>
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

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

const emit = defineEmits(['tableCreated']);

const bucket = ref('');
const path = ref(null);
const content = ref([]);
const selectedElement = ref(null);
const selectionType = ref(null);
const fileContent = ref(null);
const folderMetadata = ref(null);
const loading = ref(false);
const newTableName = ref(null);

function itemWithoutPath(item) {
  if (item == null) {
    return '';
  }
  const regex = new RegExp(path.value, 'g');
  return item.replace(regex, '');
}

async function getContent() {
  if (path.value == null) {
    path.value = '';
  }

  const fetchData = () => axios.get(`${apiUrl}/s3/getContent`, {
    params: {
      bucket: bucket.value,
      path: path.value,
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
    content.value = response.data.content;
    folderMetadata.value = response.data.metadata;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

function isFolder(item) {
  return item.endsWith('/');
}

function getOnlyFileNameWithOutExtension(fileName) {
  return fileName.split('/').pop().split('.').slice(0, -1).join('.');
}

async function clickS3Element(item) {
  loading.value = true;
  selectedElement.value = item;
  if (isFolder(item)) {
    content.value = [];
    path.value = item;
    selectionType.value = 'folder';
    getContent();
  } else {
    newTableName.value = getOnlyFileNameWithOutExtension(item);
    selectionType.value = 'file';
    await getFilePreview(item);
  }
  loading.value = false;
}

async function getFilePreview(item) {
  const fileExtension = item.toLowerCase().split('.').pop();
  if (!['csv', 'txt', 'json'].includes(fileExtension)) {
    fileContent.value = `File preview not available for this file type (${fileExtension}). Only .csv, .txt and .json files are supported.`;
    return;
  }

  const fetchData = () => axios.get(`${apiUrl}/s3/getFilePreview`, {
    params: {
      bucket: bucket.value,
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
    fileContent.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function back() {
  content.value = [];
  if (isFolder(selectedElement.value)) {
    const folders = path.value.split('/').filter(Boolean);
    folders.pop();

    selectionType.value = 'folder';
    selectedElement.value = path.value;
    path.value = folders.join('/');
    path.value = `${path.value}/`;
    if (path.value == '/') {
      path.value = '';
    }
  } else {
    selectionType.value = 'folder';
    selectedElement.value = path.value;
  }

  getContent();
}

function createEmptyMetadata() {
  folderMetadata.value = {
    description: '',
  };
}

async function updateMetadata() {
  folderMetadata.value.path = path.value;
  folderMetadata.value.bucket = bucket.value;

  const fetchData = () => axios.post(`${apiUrl}/s3/updateMetadata`, folderMetadata.value);

  toast.promise(
    fetchData(),
    {
      pending: 'Updating metadata, please wait...',
      success: 'Metadata updated',
      error: 'Error updating metadata'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    getContent();
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function loadFile(tableNameInput, fileInput) {
  const fetchData = () => axios.get(`${apiUrl}/database/loadFile`, {
    params: {
      tableName: tableNameInput,
      fileName: `s3://${bucket.value}/${fileInput}`,
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
  ).then(() => {
    emit('tableCreated');
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}
</script>

<style scoped></style>
