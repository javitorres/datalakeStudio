<template>
  <div class="main-container"> <!-- Contenedor Flex Principal -->

    <!-- Menú Lateral -->
    <div class="side-menu custom-padding">
      <!-- Side Menu https://getbootstrap.com/docs/5.0/examples/sidebars/ -->
      <div class="d-flex flex-column flex-shrink-0 compact-sidebar">
        <a href="/" class="d-block p-3 link-dark text-decoration-none" 
        title="DatalakeStudio" data-bs-toggle="tooltip"
        @click.prevent="activeMenu = 'welcome'"
          data-bs-placement="right">
            <img src="../assets/logo.svg" alt="Logo" width="38" height="38" class="rounded mx-auto d-block sidebar-logo">
          
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

    <!-- User menu (bottom-left) -->
    <div v-if="username && username !== 'default'" class="user-menu-wrapper">
      <div class="user-menu-popup" v-if="showUserMenu">
        <button class="user-menu-item" @click="showAbout = true; showUserMenu = false">
          <i class="bi bi-info-circle me-2"></i>About
        </button>
        <button class="user-menu-item text-danger" @click="$emit('logout'); showUserMenu = false">
          <i class="bi bi-box-arrow-left me-2"></i>Logout
        </button>
      </div>
      <button class="user-menu-btn" @click="showUserMenu = !showUserMenu" :title="username">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      </button>
    </div>

    <!-- About modal -->
    <div v-if="showAbout" class="about-overlay" @click.self="showAbout = false">
      <div class="about-modal">
        <div class="text-center mb-3">
          <img src="../assets/logo.svg" alt="Logo" width="48" height="48">
          <h5 class="mt-2 mb-1">Datalake Studio</h5>
          <small class="text-muted">Your personal data workspace</small>
        </div>
        <div class="small text-muted">
          <p class="mb-1"><strong>User:</strong> {{ username }}</p>
        </div>
        <div class="text-end mt-3">
          <button class="btn btn-sm btn-outline-secondary" @click="showAbout = false">Close</button>
        </div>
      </div>
    </div>

    <!-- Contenido Principal -->
    <div class="container-fluid content-shell">
      <header class="workspace-topbar">
        <div class="workspace-heading">
          <span class="workspace-icon"><i :class="activeMenuMeta.icon"></i></span>
          <div><span class="workspace-kicker">Datalake Studio</span><h1>{{ activeMenuMeta.label }}</h1></div>
        </div>
        <div class="workspace-status">
          <span class="status-dot"></span>
          <span>{{ tables.length }} {{ tables.length === 1 ? 'table' : 'tables' }}</span>
          <span v-if="username && username !== 'default'" class="workspace-user">{{ username }}</span>
        </div>
      </header>
      <keep-alive>
        <component :is="currentComponent" v-bind="currentProps" v-on="currentListeners"></component>
      </keep-alive>
    </div> <!-- container-fluid -->
    
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import api from '../services/api';

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

const props = defineProps({
  username: { type: String, default: '' }
});

const activeMenu = ref('welcome');
const tables = ref([]);
const showUserMenu = ref(false);
const showAbout = ref(false);

const menuMetadata = {
  welcome: { label: 'Overview', icon: 'bi bi-grid-1x2' },
  changeDatabase: { label: 'Databases', icon: 'bi bi-database' },
  loadData: { label: 'Load data', icon: 'bi bi-cloud-arrow-down' },
  remoteDb: { label: 'Remote database', icon: 'bi bi-database-down' },
  showTables: { label: 'Table explorer', icon: 'bi bi-table' },
  queries: { label: 'SQL workspace', icon: 'bi bi-filetype-sql' },
  apiRetriever: { label: 'API enrichment', icon: 'bi bi-globe2' },
  apiServer: { label: 'Published APIs', icon: 'bi bi-boxes' },
  s3: { label: 'S3 explorer', icon: 'bi bi-bucket' },
  chatgpt: { label: 'AI data assistant', icon: 'bi bi-stars' }
};
const activeMenuMeta = computed(() => menuMetadata[activeMenu.value] || menuMetadata.welcome);

function onClickOutside(e) {
  if (showUserMenu.value && !e.target.closest('.user-menu-wrapper')) {
    showUserMenu.value = false;
  }
}

onMounted(() => {
  getTables();
  document.addEventListener('click', onClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside);
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
  await api.get(`/database/getTables`, {
    params: {},
  }).then((response) => {
    tables.value = response.data;
  }).catch(() => {
    toast.error('Error loading tables');
  });
}

async function deleteTable(table) {
  await api.get(`/database/deleteTable`, {
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

.user-menu-wrapper {
  position: fixed;
  bottom: 1rem;
  left: 1rem;
  z-index: 1050;
}

.user-menu-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid #d1d5db;
  background: white;
  color: #4b5563;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: background 0.15s, box-shadow 0.15s;
}

.user-menu-btn:hover {
  background: #f3f4f6;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.user-menu-popup {
  position: absolute;
  bottom: 48px;
  left: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  min-width: 140px;
  padding: 4px 0;
  overflow: hidden;
}

.user-menu-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 14px;
  border: none;
  background: none;
  font-size: 0.85rem;
  color: #374151;
  cursor: pointer;
  text-align: left;
}

.user-menu-item:hover {
  background: #f3f4f6;
}

.user-menu-item.text-danger {
  color: #dc3545;
}

.about-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1060;
}

.about-modal {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 320px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

@media (max-width: 992px) {
  .content-shell {
    padding-left: 0.5rem;
  }
}

/* 2026 workspace shell */
.main-container { min-height: calc(100vh - 28px); gap: 14px; }
.side-menu { width: 64px; }
.custom-padding { padding-right: 0; }
.compact-sidebar {
  --sidebar-icon-size: 1.08rem;
  position: sticky; top: 14px;
  width: 64px; min-height: calc(100vh - 28px);
  border: 0; border-radius: 15px;
  background: #17211f;
  box-shadow: 0 16px 40px rgba(18,43,37,.16);
}
.compact-sidebar > a { height: 68px; display:grid !important; place-items:center; padding:0 !important; border-bottom:1px solid rgba(255,255,255,.08); }
.sidebar-logo { filter: brightness(0) invert(1); opacity:.82; }
.compact-sidebar .nav-link { position:relative; min-height:47px; display:grid; place-items:center; padding:0 !important; color:#80918d; border:0 !important; border-radius:8px; margin:3px 8px; }
.compact-sidebar .nav-link:hover { color:#d8eee8; background:#22332f; }
.compact-sidebar .nav-link.active { color:#bde9de; background:#29443e; box-shadow:inset 0 0 0 1px rgba(169,226,212,.08); }
.compact-sidebar .nav-link.active::before { content:''; position:absolute; left:-8px; width:3px; height:20px; border-radius:0 3px 3px 0; background:#64c3ad; }
.compact-nav-link h2 { display:flex; }
.content-shell { flex:1; min-width:0; padding:0; }
.workspace-topbar { min-height:67px; display:flex; align-items:center; justify-content:space-between; gap:18px; margin-bottom:14px; padding:10px 17px; border:1px solid var(--ds-line); border-radius:13px; background:rgba(255,255,255,.88); box-shadow:0 8px 28px rgba(31,67,58,.045); backdrop-filter:blur(12px); }
.workspace-heading { display:flex; align-items:center; gap:12px; }
.workspace-icon { width:38px; height:38px; display:grid; place-items:center; border-radius:10px; background:var(--ds-mint); color:var(--ds-teal); font-size:16px; }
.workspace-kicker { display:block; color:#86938f; font-size:9px; font-weight:750; letter-spacing:.13em; text-transform:uppercase; }
.workspace-heading h1 { margin:1px 0 0; color:var(--ds-ink); font-size:1.03rem; font-weight:750; letter-spacing:-.02em; }
.workspace-status { display:flex; align-items:center; gap:8px; color:#72807c; font-size:11px; }
.status-dot { width:7px; height:7px; border-radius:50%; background:#1aa382; box-shadow:0 0 0 4px rgba(26,163,130,.11); }
.workspace-user { margin-left:7px; padding:5px 9px; border-radius:20px; background:#edf3f1; color:#485955; font-weight:650; }
.user-menu-wrapper { bottom:24px; left:26px; }
.user-menu-btn { width:35px; height:35px; border-color:#344943; background:#22322f; color:#a9bbb6; box-shadow:none; }
.user-menu-btn:hover { color:#fff; background:#2d4540; box-shadow:none; }
.user-menu-popup { bottom:43px; border-color:var(--ds-line); border-radius:10px; box-shadow:var(--ds-shadow); }
.about-overlay { background:rgba(12,27,23,.48); backdrop-filter:blur(3px); }
.about-modal { border:1px solid var(--ds-line); border-radius:14px; box-shadow:0 24px 70px rgba(12,31,26,.25); }
@media(max-width:768px){
  .main-container{flex-direction:column;gap:9px}.side-menu{width:100%}.compact-sidebar{position:static;width:100%;min-height:54px;flex-direction:row!important}.compact-sidebar>a{display:none!important}.compact-sidebar ul{flex-direction:row!important;overflow-x:auto}.compact-sidebar .nav-link{width:43px;min-height:40px;margin:7px 2px}.compact-sidebar .nav-link.active::before{display:none}.content-shell{padding:0}.workspace-topbar{min-height:58px}.workspace-status>span:not(.status-dot){display:none}.user-menu-wrapper{display:none}
}
</style>
