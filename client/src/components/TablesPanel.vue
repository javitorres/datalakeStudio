<template>
  <div v-if="tables && tables.length > 0" class="tables-panel">
    <div class="panel-header">
      <h4 class="panel-title">Show Tables</h4>
      <span class="table-counter">{{ tables.length }} tables</span>
    </div>

    <div class="table-selector">
      <button
        v-for="table in tables"
        :key="table"
        class="btn table-chip"
        :class="selectedTable === table ? 'table-chip-active' : 'table-chip-idle'"
        @click="selectTable(table)"
      >
        <i class="bi bi-table"></i>
        {{ table }}
      </button>

      <button v-if="selectedTable" class="btn table-chip table-chip-close" @click="selectedTable = null">
        <i class="bi bi-x-square"></i>
        Close table view
      </button>
    </div>

    <div v-if="selectedTable" class="action-toolbar">
      <button class="btn btn-sm btn-danger toolbar-button" @click="confirmDelete">
        <i class="bi bi-x-octagon"></i>
        Delete table
      </button>
      <button class="btn btn-sm btn-success toolbar-button" @click="confirmDownload">
        <i class="bi bi-cloud-arrow-down"></i>
        Download data
      </button>
    </div>

    <div class="inspector-container" v-if="selectedTable">
      <TableInspector :tableName="selectedTable" :showOptions="showOptions" />
    </div>
  </div>

  <div v-else class="empty-state">
    <h2>No tables to show. Load some data</h2>
  </div>

  <div v-if="showDialog" class="modal fade show" style="display: block" aria-modal="true" role="dialog">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Attention</h5>
          <button type="button" class="btn-close" @click="showDialog = false" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p>Are you sure you want to drop table {{ selectedTable }}?</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showDialog = false">Cancel</button>
          <button type="button" class="btn btn-danger" @click="deleteTable">Yes, delete it</button>
        </div>
      </div>
    </div>
  </div>

  <div v-if="showDownloadDialog" class="modal fade show" style="display: block" aria-modal="true" role="dialog">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Download data</h5>
          <button type="button" class="btn-close" @click="showDownloadDialog = false" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p>Downloading {{ selectedTable }}, select format:</p>
          <button class="btn btn-success m-1 opcion-style" @click="download('csv')"><i class="bi bi-filetype-csv"></i> CSV</button>
          <button class="btn btn-success m-1 opcion-style" @click="download('parquet')"><i class="bi bi-table"></i> Parquet</button>
          <button class="btn btn-success m-1 opcion-style" @click="download('excel')"><i class="bi bi-filetype-xlsx"></i> Excel</button>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showDownloadDialog = false">Cancel</button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="showDialog" class="modal-backdrop fade show"></div>
</template>

<script setup>
import { ref } from 'vue';
import TableInspector from './TableInspector.vue';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

defineProps({
  tables: Object,
});

const emit = defineEmits(['deleteTable']);

const showDialog = ref(false);
const showDownloadDialog = ref(false);
const showOptions = ref(true);
const selectedTable = ref(null);

function selectTable(table) {
  selectedTable.value = table;
}

function confirmDelete() {
  showDialog.value = true;
}

function confirmDownload() {
  showDownloadDialog.value = true;
}

function download(format) {
  const fetchData = async () => await axios.get(`${apiUrl}/database/exportData`, {
    params: {
      format: format,
      tableName: selectedTable.value,
    },
    responseType: 'blob'
  });

  toast.promise(
    fetchData(),
    {
      pending: 'Exporting data, please wait...',
      success: 'Data exported successfully',
      error: 'Error creating export'
    },
    { position: toast.POSITION.BOTTOM_RIGHT }
  ).then((response) => {
    showDownloadDialog.value = false;

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'exported_data.' + format);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function deleteTable() {
  emit('deleteTable', selectedTable.value);
  selectedTable.value = null;
  showDialog.value = false;
}
</script>

<style scoped>
.tables-panel {
  font-size: 13px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.panel-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #2b2d31;
}

.table-counter {
  font-size: 0.78rem;
  background: #e3e7ef;
  color: #4f5660;
  padding: 3px 8px;
  border-radius: 999px;
}

.table-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.table-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border-radius: 7px;
  padding: 5px 9px;
  font-size: 12px;
  line-height: 1.2;
  border: 1px solid transparent;
}

.table-chip-idle {
  background: #f2f3f5;
  color: #313338;
  border-color: #e3e5e8;
}

.table-chip-active {
  background: #dce8ff;
  color: #0f3d91;
  border-color: #9fc0ff;
}

.table-chip-close {
  background: #f7f7f8;
  color: #5c6675;
  border-color: #d9dce2;
}

.action-toolbar {
  display: flex;
  gap: 8px;
  padding: 8px;
  border-radius: 8px;
  background: #f6f7fb;
  border: 1px solid #e4e6ec;
  margin-bottom: 12px;
}

.toolbar-button {
  font-size: 12px;
  padding: 5px 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.inspector-container {
  background: #ffffff;
  border: 1px solid #e4e6ec;
  border-radius: 10px;
  padding: 10px;
}

.empty-state {
  font-size: 13px;
}

.modal {
  display: block;
  position: fixed;
  z-index: 1050;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-backdrop {
  z-index: 1040;
}

.modal-content {
  background-color: #fefefe;
  margin: 12% auto;
  padding: 16px;
  border: 1px solid #d4d7dd;
  width: 80%;
}

@media (max-width: 768px) {
  .action-toolbar {
    flex-wrap: wrap;
  }
}
</style>
