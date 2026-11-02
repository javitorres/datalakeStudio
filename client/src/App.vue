<template>
  <Login v-if="authEnabled && !isAuthenticated" @login-success="onLoginSuccess" />
  <DatalakeStudio v-else :username="username" @logout="onLogout" />
</template>

<script setup>
import { ref, onMounted } from 'vue';
import "bootstrap/dist/css/bootstrap.min.css";
import Login from './components/Login.vue';
import DatalakeStudio from './components/DatalakeStudio.vue';
import api from './services/api';
import { useEngine } from './engine';

// Without users (DuckDB in the browser) the login screen never shows, not even while loading
const authEnabled = ref(useEngine().capabilities.auth);
const isAuthenticated = ref(false);
const username = ref('');

onMounted(async () => {
  // In the browser there are no users: the data lives on this machine
  if (!authEnabled.value) return;

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
});

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
