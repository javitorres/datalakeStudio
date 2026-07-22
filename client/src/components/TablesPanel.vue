<template>
  <div v-if="tables && tables.length > 0" class="tables-panel">
    <div class="panel-header">
      <div class="explorer-intro">
        <span class="explorer-kicker">Database objects</span>
        <h4 class="panel-title">Choose a table to explore</h4>
        <p>Inspect columns, sample rows, profile values and build visual analyses.</p>
      </div>
      <span class="table-counter">{{ tables.length }} tables</span>
    </div>

    <div class="selector-toolbar">
      <div class="table-search">
        <i class="bi bi-search"></i>
        <input v-model="tableFilter" type="search" placeholder="Filter tables..." aria-label="Filter tables">
      </div>
      <span v-if="tableFilter">{{ filteredTables.length }} matches</span>
    </div>

    <div class="table-selector">
      <button
        v-for="table in filteredTables"
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
import { computed, ref } from 'vue';
import TableInspector from './TableInspector.vue';
import api from '../services/api';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

const props = defineProps({
  tables: Object,
});

const emit = defineEmits(['deleteTable']);

const showDialog = ref(false);
const showDownloadDialog = ref(false);
const showOptions = ref(true);
const selectedTable = ref(null);
const tableFilter = ref('');
const filteredTables = computed(() => {
  const query = tableFilter.value.trim().toLowerCase();
  return query ? props.tables.filter((table) => table.toLowerCase().includes(query)) : props.tables;
});

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
  const fetchData = async () => await api.get(`/database/exportData`, {
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
.tables-panel{font-size:13px;padding:16px;border:1px solid var(--ds-line);border-radius:13px;background:#fff;box-shadow:0 8px 28px rgba(31,67,58,.045)}
.panel-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid var(--ds-line)}
.panel-title{margin:0;color:var(--ds-ink);font-size:1rem;font-weight:750;letter-spacing:-.02em}
.table-counter{padding:4px 9px;border-radius:999px;background:var(--ds-mint);color:var(--ds-teal-dark);font-size:.68rem;font-weight:750}
.table-selector{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:13px}
.table-chip{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border:1px solid transparent;border-radius:8px;font-size:11px;font-weight:650;line-height:1.2}
.table-chip-idle{border-color:#dfe7e4;background:#f5f8f7;color:#485753}.table-chip-idle:hover{border-color:#a9cec4;background:#edf6f3;color:var(--ds-teal-dark)}
.table-chip-active{border-color:#80c0b0;background:var(--ds-teal);color:#fff;box-shadow:0 5px 14px rgba(13,132,111,.18)}
.table-chip-close{border-color:#dde5e2;background:#fff;color:#75817d}
.action-toolbar{display:flex;gap:8px;margin-bottom:13px;padding:9px;border:1px solid var(--ds-line);border-radius:10px;background:#f6f9f8}
.toolbar-button{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;font-size:11px}
.inspector-container{padding:12px;border:1px solid var(--ds-line);border-radius:11px;background:#fbfcfc}
.empty-state{min-height:300px;display:grid;place-items:center;border:1px dashed #c8d7d2;border-radius:13px;background:#f8fbfa;color:#7b8884;text-align:center}.empty-state h2{font-size:1rem;font-weight:650}
.modal{display:block;position:fixed;z-index:1050;inset:0;width:100%;height:100%;background:rgba(12,27,23,.48);backdrop-filter:blur(3px)}.modal-backdrop{z-index:1040}.modal-content{margin:12% auto;padding:16px;width:80%;border:1px solid var(--ds-line);border-radius:14px;background:#fff}
@media(max-width:768px){.action-toolbar{flex-wrap:wrap}.tables-panel{padding:12px}}
.explorer-intro{display:grid}.explorer-kicker{color:#899692;font-size:8px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}.explorer-intro p{margin:3px 0 0;color:var(--ds-muted);font-size:9px}.selector-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:9px}.selector-toolbar>span{color:#84918e;font-size:9px}.table-search{width:min(300px,100%);display:flex;align-items:center;gap:7px;padding:6px 9px;border:1px solid #dce6e3;border-radius:8px;background:#f8faf9;color:#87938f}.table-search:focus-within{border-color:#79bdaa;box-shadow:0 0 0 3px rgba(13,132,111,.08)}.table-search input{width:100%;padding:0;border:0;outline:0;background:transparent;color:var(--ds-ink);font-size:10px}.table-selector{max-height:112px;overflow:auto;padding:2px}</style>