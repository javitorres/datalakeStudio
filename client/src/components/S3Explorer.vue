<template>
  <div class="row compact-panel compact-s3-view">
    <div class="col-md-6">
      <div class="col-md-6">
        <div class="input-group mb-3 compact-input-group">
          <span class="input-group-text" id="basic-addon1">{{ t('S3Explorer.bucket') }}</span>
          <input id="bucket" type="text" class="form-control" :placeholder="t('S3Explorer.bucketPlaceholder')" :aria-label="t('S3Explorer.bucket')"
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
          <button v-if="bucket" class="btn btn-sm btn-primary m-1" @click="getContent">
            {{ t('S3Explorer.listContent') }}
          </button>
        </div>
        <div v-else>
          <h3 class="compact-title">{{ t('S3Explorer.folder', { path: path ? path : '/' }) }}</h3>
          <h3 v-if="path != ''" class="back-link" @click="back()"><i class="bi bi-arrow-left"> {{ t('S3Explorer.back') }}</i></h3>
          <!-- For every content in content -->
          <p class="compact-muted" v-if=" content.length == 1">{{ t('S3Explorer.emptyFolder') }}</p>
          <div v-for="item in content" :key="item.id">
            <h4 class="s3-item" @click="clickS3Element(item)" v-if="item != path">
              <i v-if="isFolder(item)" class="bi bi-folder folder-item"> {{ itemWithoutPath(item) }}</i>
              <i v-if="!isFolder(item)" class="bi bi-file-earmark-text-fill file-item"> {{ itemWithoutPath(item) }}</i>
            </h4>
          </div>
        </div>
      </div>

    </div>
    <div class="col-md-6">
      <div v-if="selectedElement != null">
        <h3 class="compact-title">s3://{{ bucket }}/{{ selectedElement }}</h3>

        <div v-if="selectionType === 'file'">
          <h3 class="compact-title">{{ t('S3Explorer.filePreview') }}</h3>
          <textarea class="form-control" id="exampleFormControlTextarea1" v-model="fileContent"></textarea>
          <div class="input-group mb-3 compact-input-group mt-2">
            <span class="input-group-text" id="basic-addon1">{{ t('S3Explorer.loadAsTable') }}</span>
            <input id="bucket" type="text" class="form-control" :placeholder="t('S3Explorer.tableName')" :aria-label="t('S3Explorer.tableName')" aria-describedby="basic-addon1" v-model="newTableName">
            <button class="btn btn-sm btn-primary" @click="loadFile(newTableName, selectedElement)">
              {{ t('S3Explorer.loadFile', { name: newTableName }) }}
            </button>
          </div>

        </div>

        <div v-if="selectionType === 'folder'">
          <h3 class="compact-title">{{ t('S3Explorer.folderInfo') }}</h3>
          <div v-if=" ! folderMetadata ">
            <h2>{{ t('S3Explorer.noMetadata') }}</h2>
            <p class="compact-muted">{{ t('S3Explorer.metadataHelp') }}</p>
            <!-- Button create metadata -->
            <button class="btn btn-sm btn-primary" @click="createEmptyMetadata">
              {{ t('S3Explorer.createMetadata') }}
            </button>
          </div>
          <div v-else>

            <div class="form-floating mb-3">
              <textarea v-model="folderMetadata.description" style="height: 200px" class="form-control" :placeholder="t('S3Explorer.commentPlaceholder')" id="floatingTextarea"></textarea>
              <label for="floatingInput">{{ t('S3Explorer.description') }}</label>
            </div>

            <div class="form-floating mb-3">
              <textarea v-model="folderMetadata.owner" style="height: 20px" class="form-control" :placeholder="t('S3Explorer.commentPlaceholder')" id="floatingTextarea"></textarea>
              <label for="floatingInput">{{ t('S3Explorer.owners') }}</label>
            </div>

            <div class="form-floating mb-3">
              <textarea v-model="folderMetadata.schema" style="height: 200px" class="form-control" :placeholder="t('S3Explorer.commentPlaceholder')" id="floatingTextarea"></textarea>
              <label for="floatingInput">{{ t('S3Explorer.schema') }}</label>
            </div>

            <button class="btn btn-sm btn-primary" @click="updateMetadata">
              {{ t('S3Explorer.updateMetadata') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '../services/api';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

const emit = defineEmits(['tableCreated']);

const { t } = useI18n();

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

  const fetchData = () => api.get(`/s3/getContent`, {
    params: {
      bucket: bucket.value,
      path: path.value,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: t('S3Explorer.toast.listing'),
      success: '',
      error: t('S3Explorer.toast.listError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT, timeout: 1000 }
  ).then((response) => {
    content.value = response.data.content;
    folderMetadata.value = response.data.metadata;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('S3Explorer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('S3Explorer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
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
    fileContent.value = t('S3Explorer.previewNotAvailable', { extension: fileExtension });
    return;
  }

  const fetchData = () => api.get(`/s3/getFilePreview`, {
    params: {
      bucket: bucket.value,
      path: item,
    },
  });

  return toast.promise(
    fetchData(),
    {
      pending: t('S3Explorer.toast.gettingFile'),
      success: t('S3Explorer.toast.fileRetrieved'),
      error: t('S3Explorer.toast.fileError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    fileContent.value = response.data;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('S3Explorer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('S3Explorer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
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

  const fetchData = () => api.post(`/s3/updateMetadata`, folderMetadata.value);

  toast.promise(
    fetchData(),
    {
      pending: t('S3Explorer.toast.updatingMetadata'),
      success: t('S3Explorer.toast.metadataUpdated'),
      error: t('S3Explorer.toast.metadataError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    getContent();
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('S3Explorer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('S3Explorer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function loadFile(tableNameInput, fileInput) {
  const fetchData = () => api.get(`/database/loadFile`, {
    params: {
      tableName: tableNameInput,
      fileName: `s3://${bucket.value}/${fileInput}`,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: t('S3Explorer.toast.creatingTable'),
      success: t('S3Explorer.toast.tableCreated'),
      error: t('S3Explorer.toast.tableError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    emit('tableCreated');
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('S3Explorer.errorDetail', { detail: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('S3Explorer.errorDetail', { detail: error.response.data }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}
</script>

<style scoped>
.compact-s3-view {
  font-size: 13px;
}

.back-link {
  cursor: pointer;
  color: #2755a2;
  font-size: 1rem;
}

.s3-item {
  cursor: pointer;
  font-size: 0.95rem;
}

.folder-item {
  color: #2d65c5;
}

.file-item {
  color: #1f8a4d;
}
</style>
