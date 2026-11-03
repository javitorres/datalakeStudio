<template>
  <div class="row compact-load-view compact-panel">

    <ul class="nav nav-tabs compact-tabs">
      <!-- Upload file  -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeTab === 'uploadFile' }" aria-current="page" href="#"
          @click.prevent="activeTab = 'uploadFile'">{{ t('LoadDataPanel.tabs.upload') }}</a>
      </li>

      <!-- Load from S3  -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeTab === 'loadS3' }" aria-current="page" href="#"
          @click.prevent="activeTab = 'loadS3'">{{ t('LoadDataPanel.tabs.s3') }}</a>
      </li>

      <!-- Load from URL -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeTab === 'loadUrl' }" aria-current="page" href="#"
          @click.prevent="activeTab = 'loadUrl'">{{ t('LoadDataPanel.tabs.url') }}</a>
      </li>

      <!-- Load from Path -->
      <li class="nav-item">
        <a :class="{ 'nav-link': true, active: activeTab === 'loadPath' }" aria-current="page" href="#"
          @click.prevent="activeTab = 'loadPath'">{{ t('LoadDataPanel.tabs.path') }}</a>
      </li>
    </ul>

    <!-- Upload file ########################################################### -->
    <div v-if="activeTab == 'uploadFile'">
      <div class="col-md-6">
        <div class="mb-3 compact-input-group mt-2">
          <input class="form-control" type="file" id="formFile" ref="fileInputUpload">
        </div>

        <!-- Table name input -->
        <div class="input-group mb-3 compact-input-group">
          <span class="input-group-text" id="basic-addon1">{{ t('LoadDataPanel.table') }}</span>
          <input id="tableNameInputUpload" type="text" class="form-control" :placeholder="t('LoadDataPanel.tableName')"
            :aria-label="t('LoadDataPanel.tableName')" aria-describedby="basic-addon1" v-model="tableNameInputUpload">
        </div>

        <div class="col-md-2" v-if="tableNameInputUpload">
          <!-- Load file button -->
          <button class="btn btn-sm btn-primary" @click="uploadFile(tableNameInputUpload, fileInputUpload)">
            {{ t('LoadDataPanel.loadFile') }}
          </button>
        </div> <!-- col-md-2 -->
      </div>
    </div>

    <!-- Load from S3 ########################################################### -->
    <div v-if="activeTab == 'loadS3'">

      <div class="col-md-6">
        <div class="input-group mb-3 compact-input-group mt-2">
          <span class="input-group-text" id="basic-addon1">{{ t('LoadDataPanel.s3Bucket') }}</span>
          <input id="bucket" type="text" class="form-control" :placeholder="t('LoadDataPanel.s3BucketPlaceholder')" :aria-label="t('LoadDataPanel.s3Bucket')"
            aria-describedby="basic-addon1" v-model="bucket">
        </div>
      </div>

      <div class="col-md-6">
        <div class="input-group mb-3 compact-input-group">
          <span class="input-group-text" id="basic-addon1">{{ t('LoadDataPanel.s3File') }}</span>
          <input id="fileInput" type="text" class="form-control" :placeholder="t('LoadDataPanel.s3FilePlaceholder')" :aria-label="t('LoadDataPanel.file')"
            aria-describedby="basic-addon1" v-model="fileInputS3" @input="findFileInS3">
        </div>
      </div> <!-- col-md-6 -->

      <div class="col-md-4" v-if="fileInputS3">
        <!-- Table name input -->
        <div class="input-group mb-3 compact-input-group">
          <span class="input-group-text" id="basic-addon1">{{ t('LoadDataPanel.table') }}</span>
          <input id="tableNameInput" type="text" class="form-control" :placeholder="t('LoadDataPanel.tableName')" :aria-label="t('LoadDataPanel.tableName')"
            aria-describedby="basic-addon1" v-model="tableNameInputS3">
        </div>
      </div> <!-- col-md-4 -->

      <div class="col-md-2" v-if="fileInputS3 && tableNameInputS3">
        <!-- Load file button -->
        <button class="btn btn-sm btn-primary" @click="loadFile(tableNameInputS3, fileInputS3)">
          {{ t('LoadDataPanel.loadFile') }}
        </button>
      </div> <!-- col-md-2 -->

      <div class="row">
        <div class="col-md-6">
          <div class="row">
            <div v-if="S3Files && S3Files.length > 0">
              <ul class="list-unstyled compact-chip-list">
                <li v-for="S3File in S3Files" :key="S3File.id">
                  <button class="btn btn-sm btn-outline-primary compact-chip-btn" @click="clickS3File(S3File, true)">
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
        <p>{{ t('LoadDataPanel.example') }}</p>
        <ul>
          <li>https://raw.githubusercontent.com/javitorres/GenericCross/main/public/data/iris.csv</li>
        </ul>

        <div class="input-group mb-3 compact-input-group">
          <span class="input-group-text" id="basic-addon1">{{ t('LoadDataPanel.urlToLoad') }}</span>
          <input id="fileInputUrl" type="text" class="form-control"
            :placeholder="t('LoadDataPanel.pathPlaceholder')" :aria-label="t('LoadDataPanel.file')"
            aria-describedby="basic-addon1" v-model="fileInputUrl">

        </div>

        <div class="col-md-4" v-if="fileInputUrl">
          <!-- Table name input -->
          <div class="input-group mb-3 compact-input-group">
            <span class="input-group-text" id="basic-addon1">{{ t('LoadDataPanel.table') }}</span>
            <input id="tableNameInputUrl" type="text" class="form-control" :placeholder="t('LoadDataPanel.tableName')"
              :aria-label="t('LoadDataPanel.tableName')" aria-describedby="basic-addon1" v-model="tableNameInputUrl">
          </div>
        </div> <!-- col-md-4 -->

        <div class="col-md-2" v-if="fileInputUrl && tableNameInputUrl">
          <!-- Load file button -->
          <button class="btn btn-sm btn-primary" @click="loadFile(tableNameInputUrl, fileInputUrl)">
            {{ t('LoadDataPanel.loadFile') }}
          </button>
        </div> <!-- col-md-2 -->
      </div>
    </div>

    <!-- Load from PATH ###########################################################  -->
    <div v-if="activeTab == 'loadPath'">
      <div class="col-md-6">
        <p>{{ t('LoadDataPanel.examples') }}</p>
        <ul>
          <li>/home/mydata/myfile.csv</li>
          <li>/home/mydata/*.csv</li>
        </ul>

        <div class="input-group mb-3 compact-input-group">
          <span class="input-group-text" id="basic-addon1">{{ t('LoadDataPanel.pathToLoad') }}</span>
          <input id="fileInputUrl" type="text" class="form-control"
            :placeholder="t('LoadDataPanel.pathPlaceholder')" :aria-label="t('LoadDataPanel.file')"
            aria-describedby="basic-addon1" v-model="fileInputPath">

        </div>

        <div class="col-md-4" v-if="fileInputPath">
          <!-- Table name input -->
          <div class="input-group mb-3 compact-input-group">
            <span class="input-group-text" id="basic-addon1">{{ t('LoadDataPanel.table') }}</span>
            <input id="tableNameInputUrl" type="text" class="form-control" :placeholder="t('LoadDataPanel.tableName')"
              :aria-label="t('LoadDataPanel.tableName')" aria-describedby="basic-addon1" v-model="tableNameInputPath">
          </div>
        </div> <!-- col-md-4 -->

        <div class="col-md-2" v-if="fileInputPath && tableNameInputPath">
          <!-- Load file button -->
          <button class="btn btn-sm btn-primary" @click="loadFile(tableNameInputPath, fileInputPath)">
            {{ t('LoadDataPanel.loadFile') }}
          </button>
        </div> <!-- col-md-2 -->
      </div>
    </div>

  </div> <!-- row -->
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '../services/api';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

const emit = defineEmits(['tableCreated']);
const { t } = useI18n();

const activeTab = ref('uploadFile');
const bucket = ref('');
const fileInputS3 = ref('');
const fileInputUrl = ref('');
const fileInputPath = ref('');
const tableNameInputUpload = ref('');
const tableNameInputS3 = ref('');
const tableNameInputUrl = ref('');
const tableNameInputPath = ref('');
const S3Files = ref([]);
const fileInputUpload = ref(null);

function uploadFile() {
  const file = fileInputUpload.value?.files?.[0];
  if (!file) {
    return;
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('tableName', tableNameInputUpload.value);

  const fetchData = () => api.post(`/database/uploadFile`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  toast.promise(
    fetchData(),
    {
      pending: t('LoadDataPanel.uploading'),
      success: t('LoadDataPanel.uploadDone'),
      error: t('LoadDataPanel.uploadError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    if (response.status == 'error') {
      toast.error(t('LoadDataPanel.couldNotLoad', { status: response.data.status }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      emit('tableCreated');
    }
    emit('tableCreated');
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('LoadDataPanel.errorDetail', { message: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('LoadDataPanel.errorDetail', { message: String(error.response.data) }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

function getProperty(path, defaultValue = '') {
  try {
    return path.split('.').reduce((o, i) => o[i], this);
  }
  catch (e) {
    return defaultValue;
  }
}

async function findFileInS3() {
  if (fileInputS3.value.length < 3) {
    S3Files.value = [];
    return;
  }

  S3Files.value = [];

  const fetchData = () => api.get(`/s3/s3Search`, {
    params: {
      bucket: bucket.value,
      fileName: fileInputS3.value,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: t('LoadDataPanel.searchingS3'),
      success: t('LoadDataPanel.s3SearchDone'),
      error: t('LoadDataPanel.s3SearchError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    S3Files.value = response.data.results;
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('LoadDataPanel.errorDetail', { message: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('LoadDataPanel.errorDetail', { message: String(error.response.data) }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

function clickS3File(S3File) {
  fileInputS3.value = S3File;
  S3Files.value = [];
}

async function loadFile(tableNameInput, fileInput) {
  const fetchData = () => api.get(`/database/loadFile`, {
    params: {
      tableName: tableNameInput,
      fileName: fileInput,
    },
  });

  toast.promise(
    fetchData(),
    {
      pending: t('LoadDataPanel.creatingTable'),
      success: t('LoadDataPanel.tableCreated'),
      error: t('LoadDataPanel.createTableError')
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then(() => {
    emit('tableCreated');
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error(t('LoadDataPanel.errorDetail', { message: error.response.data.message }), { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error(t('LoadDataPanel.errorDetail', { message: String(error.response.data) }), { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

</script>
<style scoped>
.compact-load-view {
  font-size: 13px;
  row-gap: 8px;
}

.compact-load-view p,
.compact-load-view li {
  font-size: 12px;
}
</style>
