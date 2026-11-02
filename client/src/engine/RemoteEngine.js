import { tableFromIPC } from 'apache-arrow';
import api from '../services/api';
import { capabilities } from './engine';

// Runs everything on the Python backend. SQL goes through /database/restConnector (the Mosaic
// duckdb-server protocol) on the user's own connection, so the server's sandbox still applies.
export class RemoteEngine {
  constructor() {
    this.mode = 'remote';
    this.capabilities = capabilities({
      s3: true, remoteDb: true, publishApi: true, apiEnrichment: true, auth: true, serverAi: true, serverPath: true,
      maps: true, h3: true, spatial: true, persistent: true,
    });
  }

  async query(sql) {
    // The server already turns the result into JSON-safe records (NaN as null, ISO dates)
    const response = await post({ type: 'json', sql });
    return response.data;
  }

  async queryArrow(sql) {
    const response = await post({ type: 'arrow', sql }, { responseType: 'arraybuffer' });
    return tableFromIPC(new Uint8Array(response.data));
  }

  async exec(sql) {
    await post({ type: 'exec', sql });
  }

  // The server splits the script with DuckDB's own parser and recreates __lastQuery if it has to
  // reopen the database, so the workspace keeps using its endpoint
  async runUserQuery(sql) {
    await call(() => api.post('/database/runQuery', { query: sql, rows: 1 }));
  }

  async loadFile({ file, url, tableName }) {
    if (file) {
      const form = new FormData();
      form.append('file', file);
      form.append('tableName', tableName);
      await call(() => api.post('/database/uploadFile', form, { headers: { 'Content-Type': 'multipart/form-data' } }));
    } else {
      await call(() => api.get('/database/loadFile', { params: { tableName, fileName: url } }));
    }
  }

  async exportTable(tableName, format) {
    const response = await call(() => api.get('/database/exportData', {
      params: { tableName, format }, responseType: 'blob',
    }));
    return response.data;
  }

  async listDatabases() {
    const response = await call(() => api.get('/database/getDatabaseList'));
    const databases = response.data || [];
    // The server lists the active database first and also names it in a header
    return { databases, current: response.headers?.['x-current-database'] || databases[0] || null };
  }

  async useDatabase(name) {
    await call(() => api.get('/database/changeDatabase', { params: { databaseName: name } }));
  }

  async createDatabase(name) {
    await call(() => api.get('/database/createDatabase', { params: { databaseName: name } }));
  }

  // Mosaic's own restConnector sends no Authorization header: this one goes through the api instance
  mosaicConnector() {
    return {
      query: async ({ type, sql }) => {
        if (type === 'exec') return this.exec(sql);
        if (type === 'arrow') return this.queryArrow(sql);
        return this.query(sql);
      },
    };
  }
}

function post(body, options) {
  return call(() => api.post('/database/restConnector', body, options));
}

// Turns the backend's error payloads into plain Errors with its message
async function call(request) {
  try {
    return await request();
  } catch (error) {
    throw new Error(await serverMessage(error));
  }
}

async function serverMessage(error) {
  let data = error.response?.data;
  if (data instanceof ArrayBuffer) data = new TextDecoder().decode(data);
  else if (typeof Blob !== 'undefined' && data instanceof Blob) data = await data.text();
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data);
    } catch (_) {
      return data || error.message;
    }
  }
  return data?.message || data?.detail || data?.error || error.message;
}
