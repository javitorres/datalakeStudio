<template>
  <Login v-if="usesServer && authEnabled && !isAuthenticated" @login-success="onLoginSuccess" />
  <PublishedDashboard v-else-if="publishedPath" :path="publishedPath" />
  <DatalakeStudio v-else :username="username" @logout="onLogout" />
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import "bootstrap/dist/css/bootstrap.min.css";
import Login from './components/Login.vue';
import DatalakeStudio from './components/DatalakeStudio.vue';
import PublishedDashboard from './components/PublishedDashboard.vue';
import api from './services/api';
import { canChooseEngine, useEngine } from './engine';
import { publishedPathFromHash } from './lib/dashboards';

// A published dashboard opened by its link (#/d/iris/flower_analysis). They live on the backend: the
// build that only runs in the browser has none.
const publishedPath = ref(canChooseEngine ? publishedPathFromHash() : null);
const onHashChange = () => { publishedPath.value = canChooseEngine ? publishedPathFromHash() : null; };

// Without users (DuckDB in the browser) the login screen never shows, not even while loading. A
// published dashboard is the server's, whatever engine the app runs on.
const usesServer = computed(() => useEngine().capabilities.auth || Boolean(publishedPath.value));
const authEnabled = ref(true);
const isAuthenticated = ref(false);
const username = ref('');
let checked = false;

onMounted(() => {
  window.addEventListener('hashchange', onHashChange);
  checkAuth();
});
onUnmounted(() => window.removeEventListener('hashchange', onHashChange));
watch(usesServer, checkAuth);

async function checkAuth() {
  // In the browser there are no users: the data lives on this machine
  if (!usesServer.value || checked) return;
  checked = true;

  // Check if auth is enabled
  try {
    const resp = await api.get(`/auth/auth-enabled`);
    authEnabled.value = resp.data.enabled;
  } catch {
    authEnabled.value = true; // Default to requiring auth if server unreachable
  }

  if (!authEnabled.value) {
    isAuthenticated.value = false;
    username.value = 'default';
    return;
  }

  const token = localStorage.getItem('token');
  const storedUsername = localStorage.getItem('username');
  if (token && storedUsername) {
    try {
      const response = await api.get(`/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      isAuthenticated.value = true;
      username.value = response.data.username;
    } catch {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
    }
  }
}

function onLoginSuccess(data) {
  localStorage.setItem('token', data.token);
  localStorage.setItem('username', data.username);
  isAuthenticated.value = true;
  username.value = data.username;
}

function onLogout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  isAuthenticated.value = false;
  username.value = '';
}
</script>

<style>
</style>
