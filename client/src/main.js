import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import 'bootstrap-icons/font/bootstrap-icons.css'
import axios from 'axios'

// Global Axios interceptor: attach JWT token to every request
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global Axios interceptor: handle 401 responses (expired/invalid token)
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't clear on login/register attempts
      const url = error.config?.url || '';
      if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

createApp(App).mount('#app')
