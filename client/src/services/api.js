import axios from 'axios';
import { API_URL } from '../../config';

// Central axios instance. All calls to the Datalake Studio backend must go
// through this instance so they share a single base URL and the auth handling
// below. Because the JWT is attached here (and not on the global axios), it is
// only ever sent to API_URL and never leaks to third-party hosts.
const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses (expired/invalid token). Login/register attempts are
// left alone so their own error handling can run.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
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

export default api;
