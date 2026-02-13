<template>
  <div class="main-container"> <!-- Contenedor Flex Principal -->

    <!-- Menú Lateral -->
    <div class="side-menu custom-padding">
      <!-- Side Menu https://getbootstrap.com/docs/5.0/examples/sidebars/ -->
      <div class="d-flex flex-column flex-shrink-0 bg-light compact-sidebar">
        <a href="/" class="d-block p-3 link-dark text-decoration-none" 
        title="DatalakeStudio" data-bs-toggle="tooltip"
        @click.prevent="activeMenu = 'welcome'"
          data-bs-placement="right">
            <img src="../assets/logo.svg" alt="Logo" width="45" height="45" class="rounded mx-auto d-block">
          
          <span class="visually-hidden">Icon-only</span>
        </a>
        <ul class="nav nav-pills nav-flush flex-column mb-auto text-center">
          <li class="nav-item">
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 'changeDatabase' }"
              @click.prevent="activeMenu = 'changeDatabase'" title="Change database" aria-current="page" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-database"></i></h2>
            </a>
          </li>

          <li class="nav-item">
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 'loadData' }"
              @click.prevent="activeMenu = 'loadData'" title="Load data from files" aria-current="page" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-box-arrow-down"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 'remoteDb' }"
              @click.prevent="activeMenu = 'remoteDb'" title="Load data from external Database" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-database-down"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 'showTables' }"
              @click.prevent="activeMenu = 'showTables'" title="Show tables" data-bs-toggle="tooltip" data-bs-placement="right">
              <h2><i class="bi bi-table"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 'queries' }"
              @click.prevent="activeMenu = 'queries'" title="Queries" data-bs-toggle="tooltip" data-bs-placement="right">
              <h2><i class="bi bi-filetype-sql"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 'apiRetriever' }"
              @click.prevent="activeMenu = 'apiRetriever'" title="Get data from Api " data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-globe2"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 'apiServer' }"
              @click.prevent="activeMenu = 'apiServer'" title="Expose data via API" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-boxes"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 's3' }"
              @click.prevent="activeMenu = 's3'" title="Explore your S3 buckets" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-bucket"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-2 border-bottom compact-nav-link" :class="{ active: activeMenu === 'chatgpt' }"
              @click.prevent="activeMenu = 'chatgpt'" title="Talk with ChatGpt (Experimental)" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <img src="../assets/ChatGPT.svg" alt="Logo" class="rounded mx-auto d-block compact-menu-img">
            </a>
          </li>
        </ul>
      </div>
    </div>

    <!-- Contenido Principal -->
    <div class="container-fluid content-shell">
      <keep-alive>
        <component :is="currentComponent" v-bind="currentProps" v-on="currentListeners"></component>
      </keep-alive>
    </div> <!-- container-fluid -->
    
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import axios from 'axios';

import Welcome from './Welcome.vue';
import LoadDataPanel from './LoadDataPanel.vue';
import TablesPanel from './TablesPanel.vue';
import QueryPanel from './QueryPanel.vue';
import RemoteDbPanel from './RemoteDbPanel.vue';
import ApiRetriever from './ApiRetriever.vue';
import ApiServer from './ApiServer.vue';
import ChatGptAgent from './ChatGptAgent.vue';
import S3Explorer from './S3Explorer.vue';
import ChangeDatabase from './ChangeDatabase.vue';

import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

const activeMenu = ref('welcome');
const tables = ref([]);

onMounted(() => {
  getTables();
});

const currentComponent = computed(() => {
  switch (activeMenu.value) {
    case 'welcome':
      return Welcome;
    case 'changeDatabase':
      return ChangeDatabase;
    case 'loadData':
      return LoadDataPanel;
    case 'remoteDb':
      return RemoteDbPanel;
    case 'showTables':
      return TablesPanel;
    case 'queries':
      return QueryPanel;
    case 'apiRetriever':
      return ApiRetriever;
    case 'apiServer':
      return ApiServer;
    case 'chatgpt':
      return ChatGptAgent;
    case 's3':
      return S3Explorer;
    default:
      return Welcome;
  }
});

const currentProps = computed(() => {
  switch (activeMenu.value) {
    case 'showTables':
      return { tables: tables.value };
    case 'queries':
      return { tables: tables.value };
    case 'apiRetriever':
      return { tables: tables.value };
    default:
      return {};
  }
});

const currentListeners = computed(() => {
  switch (activeMenu.value) {
    case 'loadData':
      return { tableCreated };
    case 'remoteDb':
      return { tableCreated };
    case 'showTables':
      return { deleteTable };
    case 'queries':
      return { tableCreated };
    case 'apiRetriever':
      return { tableCreated };
    case 's3':
      return { tableCreated };
    case 'changeDatabase':
      return { changedDatabase };
    default:
      return {};
  }
});

async function getTables() {
  await axios.get(`${apiUrl}/database/getTables`, {
    params: {},
  }).then((response) => {
    tables.value = response.data;
  }).catch(() => {
    toast.error('Error loading tables');
  });
}

async function deleteTable(table) {
  await axios.get(`${apiUrl}/database/deleteTable`, {
    params: {
      tableName: table,
    },
  }).then((response) => {
    if (response.status === 200) {
      toast.success('Table deleted successfully');
      getTables();
    } else {
      toast.error(`Error: HTTP ${response.message}`);
    }
  }).catch((error) => {
    toast.error(`Error: HTTP ${error.message}`);
  });
}

async function tableCreated() {
  getTables();
}

async function changedDatabase(id) {
  getTables();
}
</script>
<style>
.main-container {
  display: flex;
  min-height: calc(100vh - 4rem);
}

.side-menu {
  width: 4.5rem;
  flex-shrink: 0;
}

.content-container {
  flex-grow: 1;
}

.custom-padding {
  padding-right: 1rem;
}

.compact-sidebar {
  --sidebar-icon-size: 1.2rem;
  width: 4rem;
  border-radius: 10px;
  border: 1px solid #e4e6ec;
  overflow: hidden;
}

.compact-nav-link {
  min-height: 46px;
}

.compact-nav-link h2 {
  font-size: var(--sidebar-icon-size);
  margin: 0;
  line-height: 1;
}

.compact-menu-img {
  width: var(--sidebar-icon-size);
  height: var(--sidebar-icon-size);
}

.content-shell {
  padding-left: 1rem;
  padding-right: 0.5rem;
}

@media (max-width: 992px) {
  .content-shell {
    padding-left: 0.5rem;
  }
}
</style>
