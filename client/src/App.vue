<template>
  <Login v-if="authEnabled && !isAuthenticated" @login-success="onLoginSuccess" />
  <DatalakeStudio v-else :username="username" @logout="onLogout" />
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import "bootstrap/dist/css/bootstrap.min.css";
import Login from './components/Login.vue';
import DatalakeStudio from './components/DatalakeStudio.vue';
import { API_HOST, API_PORT } from '../config';

const apiUrl = `${API_HOST}:${API_PORT}`;

const authEnabled = ref(true);
const isAuthenticated = ref(false);
const username = ref('');

onMounted(async () => {
  // Check if auth is enabled
  try {
    const resp = await axios.get(`${apiUrl}/auth/auth-enabled`);
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
      const response = await axios.get(`${apiUrl}/auth/me`, {
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
