const env = import.meta.env || {};
export const API_HOST = env.VITE_API_HOST || "http://localhost";
export const API_PORT = env.VITE_API_PORT || 8000;
export const API_URL = env.VITE_API_URL || `${API_HOST}:${API_PORT}`;
export const GOOGLE_CLIENT_ID = env.VITE_GOOGLE_CLIENT_ID || "";
// 'local': DuckDB in the browser only (the public build, `vite --mode public`, no backend).
// 'remote': the Python backend, and the user can still switch to the browser engine.
export const ENGINE = env.VITE_ENGINE === "local" || env.MODE === "public" ? "local" : "remote";
