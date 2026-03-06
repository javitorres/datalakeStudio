<template>
  <div class="compact-panel compact-db-view">
    <h2 class="compact-title">Select database</h2>
    <p class="compact-muted mb-2">Choose the active local database for this session.</p>
    <div v-if="databases" class="col-md-12">
      <div class="db-grid">
        <div v-for="db in databases" :key="db" class="m-0">
          <button
            type="button"
            class="btn db-card"
            :class="isActiveDatabase(db) ? 'db-card-active' : 'db-card-idle'"
            @click="changeDatabase(db)"
          >
            <span class="db-card-top">
              <i class="bi bi-database"></i>
              <span class="db-badge" v-if="isActiveDatabase(db)">ACTIVE</span>
            </span>
            <span class="db-name">{{ db.toUpperCase() }}</span>
          </button>
        </div>
      </div>
    </div>

    <h2 class="compact-title mt-3">Create new database</h2>
    <div class="row align-items-start g-2">
      <div class="col-md-4 compact-input-group">
        <input type="text" class="form-control" v-model="newDatabaseName" placeholder="Database name">
      </div>
      <div class="col-md-3" v-if="newDatabaseName">
        <button type="button" class="btn btn-sm btn-primary" @click="createDatabase()">Create new database</button>
      </div>
      <div class="col-md-5" v-if="newDatabaseName && !newDatabaseName.endsWith('.db')">
        <p class="text-danger">Database name must end with .db</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';


import { API_HOST, API_PORT } from '../../config';

const apiUrl = `${API_HOST}:${API_PORT}`;

const databases = ref(null);
const activeDatabase = ref(null);
const newDatabaseName = ref('newdatabase.db');

onMounted(() => {
  getDatabaseList();
});

const emit = defineEmits(['changedDatabase']);

const getDatabaseList = async () => {
  try {
    const response = await axios.get(`${apiUrl}/database/getDatabaseList`);
    databases.value = response.data;
    // Preferred source: explicit header from backend.
    activeDatabase.value = response.headers['x-current-database'] || null;
    if (!activeDatabase.value && Array.isArray(databases.value) && databases.value.length > 0) {
      // Backward compatibility fallback.
      activeDatabase.value = databases.value[0];
    }
  } catch (error) {
    toast.error('Error getting database list');
  }
};

function isActiveDatabase(db) {
  return activeDatabase.value === db;
}

const changeDatabase = async (databaseName) => {
  try {
    await axios.get(`${apiUrl}/database/changeDatabase`, {
      params: {
        databaseName: databaseName
      }
    });
    toast.success('Database changed');
    activeDatabase.value = databaseName;
    getDatabaseList();
    emit('changedDatabase', databaseName);
  } catch (error) {
    toast.error('Error changing database: ' + error);
    
  }
};

const createDatabase = async () => {
  if (!newDatabaseName.value.endsWith('.db')) {
    toast.error('Database name must end with .db');
    return;
  }
  try {
    await axios.get(`${apiUrl}/database/createDatabase`, {
      params: {
        databaseName: newDatabaseName.value
      }
    });
    toast.success('Database created');
    newDatabaseName.value = '';
    getDatabaseList();
  } catch (error) {
    toast.error('Error creating database');
  }
};
</script>

<style scoped>
.compact-db-view {
  font-size: 13px;
}

.db-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 8px;
}

.db-card {
  width: 100%;
  min-height: 70px;
  border-radius: 10px;
  border: 1px solid transparent;
  padding: 8px 10px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.db-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}

.db-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(30, 86, 185, 0.15);
  color: #1e56b9;
  font-weight: 700;
}

.db-name {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  word-break: break-word;
}

.db-card-idle {
  background: #f7f8fb;
  border-color: #dbe0ea;
  color: #2f3440;
}

.db-card-idle:hover {
  background: #eef2fb;
  border-color: #c3d2ef;
}

.db-card-active {
  background: linear-gradient(180deg, #e8f0ff 0%, #dce9ff 100%);
  border-color: #a9c3f6;
  color: #163d87;
}
</style>
