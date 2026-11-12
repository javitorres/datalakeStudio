// Where the dashboards are kept: on the server for each user, where they can also be published for the
// other users, or in this browser when the app runs on DuckDB in the browser (then they are only the
// user's own). A dashboard is { id, title, database, created, updated, published, spec, history }.
import api from '../services/api';
import { useEngine } from '../engine';

const STORAGE_KEY = 'datalakeStudio.dashboards';
const MAX_LOCAL = 50;

function onServer() {
  return useEngine().mode === 'remote';
}

// Whether dashboards can be published (it needs the backend)
export function canPublish() {
  return onServer();
}

// Every dashboard, with its specification: { id: dashboard }
function readLocal() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch (_) {
    return {};
  }
}

function writeLocal(dashboards) {
  const kept = Object.values(dashboards).sort((a, b) => b.updated - a.updated).slice(0, MAX_LOCAL);
  // Throws when the browser storage is full: the caller reports it
  localStorage.setItem(STORAGE_KEY, JSON.stringify(Object.fromEntries(kept.map((d) => [d.id, d]))));
}

const summary = ({ spec, history, ...dashboard }) => dashboard; // eslint-disable-line no-unused-vars

// The backend's error payloads as plain Errors with its message
async function call(request) {
  try {
    return (await request()).data;
  } catch (error) {
    const data = error.response?.data;
    throw new Error(data?.message || data?.detail?.[0]?.msg || (typeof data?.detail === 'string' && data.detail) || error.message);
  }
}

// The dashboards without their specification, most recent first
export async function listDashboards() {
  if (onServer()) return call(() => api.get('/dashboards'));
  return Object.values(readLocal()).map(summary).sort((a, b) => b.updated - a.updated);
}

export async function getDashboard(id) {
  if (onServer()) return call(() => api.get(`/dashboards/${id}`));
  const dashboard = readLocal()[id];
  if (!dashboard) throw new Error(`Dashboard ${id} not found`);
  return dashboard;
}

// Saves the dashboard and returns it without its specification
export async function saveDashboard(id, { title, spec, history = [] }) {
  if (onServer()) return call(() => api.put(`/dashboards/${id}`, { title, spec, history }));
  const dashboards = readLocal();
  const now = Date.now() / 1000;
  dashboards[id] = {
    id, title, database: useEngine().databaseName || null, created: dashboards[id]?.created ?? now, updated: now,
    published: null, spec, history,
  };
  writeLocal(dashboards);
  return summary(dashboards[id]);
}

export async function deleteDashboard(id) {
  if (onServer()) {
    await call(() => api.delete(`/dashboards/${id}`));
    return;
  }
  const dashboards = readLocal();
  delete dashboards[id];
  writeLocal(dashboards);
}

// Publishes the saved dashboard under a path (iris/flower_analysis) with the SQL its widgets and
// filters run on the server. Returns the dashboard without its specification.
export function publishDashboard(id, path, queries) {
  return call(() => api.put(`/dashboards/${id}/publish`, { path, queries }));
}

export function unpublishDashboard(id) {
  return call(() => api.delete(`/dashboards/${id}/publish`));
}

// Published dashboards of every user of the server: [{ path, title, owner, published }]
export function listPublished() {
  return call(() => api.get('/d'));
}

// A published dashboard: { path, title, owner, published, spec } (the spec without its SQL)
export function getPublished(path) {
  return call(() => api.get(`/d/${path}`));
}

// The rows of a widget or filter of a published dashboard, for the filters the viewer set
export function queryPublished(path, query, filters = {}) {
  return call(() => api.post(`/d/${path}`, { query, filters }));
}

// The link to a published dashboard in this app
export function publishedUrl(path) {
  return `${window.location.origin}${window.location.pathname}#/d/${path}`;
}

// The path of the published dashboard the page was opened at (#/d/iris/flower_analysis), if any
export function publishedPathFromHash(hash = window.location.hash) {
  const match = /^#\/d\/([A-Za-z0-9_\-/]+)$/.exec(hash || '');
  return match ? match[1].replace(/\/+$/, '') : null;
}
