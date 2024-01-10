<template>
  <div class="main-container"> <!-- Contenedor Flex Principal -->

    <!-- Menú Lateral -->
    <div class="side-menu custom-padding">
      <!-- Side Menu https://getbootstrap.com/docs/5.0/examples/sidebars/ -->
      <div class="d-flex flex-column flex-shrink-0 bg-light" style="width: 4.5rem;">
        <a href="/" class="d-block p-3 link-dark text-decoration-none" 
        title="DatalakeStudio" data-bs-toggle="tooltip"
        @click.prevent="activeMenu = 'welcome'"
          data-bs-placement="right">
            <img src="../assets/logo.svg" alt="Logo" width="45" height="45" class="rounded mx-auto d-block">
          
          <span class="visually-hidden">Icon-only</span>
        </a>
        <ul class="nav nav-pills nav-flush flex-column mb-auto text-center">
          <li class="nav-item">
            <a href="#" class="nav-link py-3 border-bottom" :class="{ active: activeMenu === 'loadData' }"
              @click.prevent="activeMenu = 'loadData'" title="Load data from files" aria-current="page" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-box-arrow-down"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-3 border-bottom" :class="{ active: activeMenu === 'remoteDb' }"
              @click.prevent="activeMenu = 'remoteDb'" title="Load data from external Database" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-database-down"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-3 border-bottom" :class="{ active: activeMenu === 'showTables' }"
              @click.prevent="activeMenu = 'showTables'" title="Show tables" data-bs-toggle="tooltip" data-bs-placement="right">
              <h2><i class="bi bi-table"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-3 border-bottom" :class="{ active: activeMenu === 'queries' }"
              @click.prevent="activeMenu = 'queries'" title="Queries" data-bs-toggle="tooltip" data-bs-placement="right">
              <h2><i class="bi bi-filetype-sql"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-3 border-bottom" :class="{ active: activeMenu === 'apiRetriever' }"
              @click.prevent="activeMenu = 'apiRetriever'" title="Get data from Api " data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-globe2"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-3 border-bottom" :class="{ active: activeMenu === 'apiServer' }"
              @click.prevent="activeMenu = 'apiServer'" title="Expose data via API" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-boxes"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-3 border-bottom" :class="{ active: activeMenu === 's3' }"
              @click.prevent="activeMenu = 's3'" title="Explore your S3 buckets" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <h2><i class="bi bi-bucket"></i></h2>
            </a>
          </li>

          <li>
            <a href="#" class="nav-link py-3 border-bottom" :class="{ active: activeMenu === 'chatgpt' }"
              @click.prevent="activeMenu = 'chatgpt'" title="Talk with ChatGpt (Experimental)" data-bs-toggle="tooltip"
              data-bs-placement="right">
              <img src="../assets/ChatGPT.svg" alt="Logo" width="45" height="45" class="rounded mx-auto d-block">
            </a>
          </li>


          
        </ul>
      </div>
    </div>

    <!-- Contenido Principal -->
    
      <div class="container-fluid" style="padding-left: 2rem;">
        <keep-alive>
          <component :is="currentComponent" v-bind="currentProps" v-on="currentListeners"></component>
        </keep-alive>
      </div> <!-- container-fluid -->
    
  </div>
</template>

<script>
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

import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'DatalakeStudio',

  components: {
    Welcome,
    LoadDataPanel,
    TablesPanel,
    QueryPanel,
    RemoteDbPanel,
    ApiRetriever,
    ApiServer,
    ChatGptAgent,
    S3Explorer,
  },

  data() {
    return {
      activeMenu: 'welcome',

      tables: [],

    };
  },

  mounted() {
    this.getTables();
  },

  computed: {
    currentComponent() {
      switch (this.activeMenu) {
        case 'welcome':
          return 'Welcome';
        case 'loadData':
          return 'LoadDataPanel';
        case 'remoteDb':
          return 'RemoteDbPanel';
        case 'showTables':
          return 'TablesPanel';
        case 'queries':
          return 'QueryPanel';
        case 'apiRetriever':
          return 'ApiRetriever';
        case 'apiServer':
          return 'ApiServer';
        case 'chatgpt':
          return 'ChatGptAgent';
        case 's3':
          return 'S3Explorer';
        default:
          return 'Welcome';
      }
    },
    currentProps() {
      switch (this.activeMenu) {
        case 'loadData':
          return {  };
        case 'remoteDb':
          return {  };
        case 'showTables':
          return { tables: this.tables };
        case 'queries':
          return { tables: this.tables };
        case 'apiRetriever':
          return { tables: this.tables };
        case 'apiServer':
          return {  };
        case 'chatgpt':
          return {  };
        case 's3':
          return {  };
        default:
          return {  };
      }
    },
    currentListeners() {
      switch (this.activeMenu) {
        case 'loadData':
          return { tableCreated: this.tableCreated, };
        case 'remoteDb':
          return { tableCreated: this.tableCreated, };
        case 'showTables':
          return { deleteTable: this.deleteTable, };
        case 'queries':
          return { tableCreated: this.tableCreated, };
        case 'apiRetriever':
          return { tableCreated: this.tableCreated, };
        case 'apiServer':
          return {  };
        case 'chatgpt':
          return {  };
        case 's3':
          return { tableCreated: this.tableCreated, };
        default:
          return {  };
      }
    },
  },
  

  methods: {
    ////////////////////////////////////////////////////////////////
    async getTables() {
      await axios.get(`${apiUrl}/database/getTables`, {
        params: {
        },
      }).then((response) => {
        this.tables = response.data;

      }).catch((error) => {
        toast.error(`Error: HTTP ${response.data}`);
      }).finally(() => {

      });
    },
    ////////////////////////////////////////////////////////////////
    async deleteTable(table) {
      var response = await axios.get(`${apiUrl}/database/deleteTable`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
        if (response.status === 200) {
          toast.success('Table deleted successfully');
          this.getTables();
        } else {
          toast.error(`Error: HTTP ${response.message}`);
        }
      }).catch((error) => {
        toast.error(`Error: HTTP ${error.message}`);
      }).finally(() => {

      });
    },
    ////////////////////////////////////////////////////////////////
    async tableCreated() {
      this.getTables();
    },
  },

}
</script>
<style>
.main-container {
  display: flex;
  /* Activa Flexbox */
}

.side-menu {
  width: 4.5rem;
  /* Ancho fijo para el menú */
  flex-shrink: 0;
  /* Evita que el menú se encoja */
}

.content-container {
  flex-grow: 1;
  /* Permite que el contenido ocupe el espacio restante */
}

.custom-padding {
  padding-right: 2rem;
}
</style>