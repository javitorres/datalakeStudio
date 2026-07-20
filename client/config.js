// Environment-driven configuration.
// Override at build/run time with VITE_* variables (e.g. in a .env file):
//   VITE_API_URL=https://datalake.example.com/api
//   VITE_GOOGLE_CLIENT_ID=...
// When VITE_API_URL is not set, it is derived from VITE_API_HOST/VITE_API_PORT,
// falling back to the local development defaults.
const env = import.meta.env || {};

export const API_HOST = env.VITE_API_HOST || "http://localhost";
export const API_PORT = env.VITE_API_PORT || 8000;
export const API_URL = env.VITE_API_URL || `${API_HOST}:${API_PORT}`;
export const GOOGLE_CLIENT_ID = env.VITE_GOOGLE_CLIENT_ID || "";
