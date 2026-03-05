<template>
  <Login v-if="!isAuthenticated" @login-success="onLoginSuccess" />
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

const isAuthenticated = ref(false);
const username = ref('');

onMounted(async () => {
  const token = localStorage.getItem('token');
  const storedUsername = localStorage.getItem('username');
  if (token && storedUsername) {
    // Validate token is still valid
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
