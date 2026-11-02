import { capabilities } from './engine';
import { arrowToRows } from './arrowRows';
import { loadFileSql, mainFileInZip, needsSpatial } from '../data/files';
import { quoteIdent } from '../data/sql';

// Runs DuckDB in the browser (DuckDB-WASM in a Web Worker). Databases are files in the browser's
// private storage (OPFS): the data never leaves the user's machine. The engine's bundles are served
// with the app; only DuckDB extensions (spatial, h3, httpfs) are downloaded from duckdb.org when needed.

const CURRENT_DB_KEY = 'datalakeStudio.localDatabase';
const DEFAULT_DATABASE = 'datalakeStudio.db';

export class LocalEngine {
  constructor() {
    this.mode = 'local';
    this.capabilities = capabilities({ maps: true, h3: true, spatial: true, ownAi: true, persistent: hasOpfs() });
    this.db = null;
    this.connection = null;
    this.ready = null;
    this.uploads = 0;
    // OPFS files registered with DuckDB (their handles stay open until they're dropped)
    this.registered = new Set();
    // Extensions loaded into the open database
    this.extensions = new Set();
  }

  // Starts DuckDB the first time it's needed (the WASM module is tens of MB)
  start() {
    if (!this.ready) this.ready = this.boot();
    return this.ready;
  }

  async boot() {
    const duckdb = await import('@duckdb/duckdb-wasm');
    const [mvpModule, mvpWorker, ehModule, ehWorker] = await Promise.all([
      import('@duckdb/duckdb-wasm/dist/duckdb-mvp.wasm?url'),
      import('@duckdb/duckdb-wasm/dist/duckdb-browser-mvp.worker.js?url'),
      import('@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url'),
      import('@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url'),
    ]);
    const bundle = await duckdb.selectBundle({
      mvp: { mainModule: mvpModule.default, mainWorker: mvpWorker.default },
      eh: { mainModule: ehModule.default, mainWorker: ehWorker.default },
    });
    const worker = new Worker(bundle.mainWorker);
    this.duckdb = duckdb;
    this.db = new duckdb.AsyncDuckDB(new duckdb.VoidLogger(), worker);
    await this.db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    // Ask the browser to keep the databases: without it, it may evict OPFS when it runs short of space
    if (this.capabilities.persistent) navigator.storage.persist?.().catch(() => {});
    try {
      await this.openDatabase(this.currentDatabaseName());
    } catch (error) {
      // Only one tab can have a database file open
      if (/Access Handle/i.test(error.message)) {
        throw new Error('Datalake Studio is already open in another tab of this browser. Close it and reload this page.');
      }
      throw error;
    }
  }

  async openDatabase(name) {
    if (this.connection) {
      await this.connection.close();
      this.connection = null;
    }
    try {
      await this.openFile(name);
    } catch (error) {
      if (!this.capabilities.persistent || !/replaying WAL/i.test(error.message)) throw error;
      // The log holds changes the database file already has (left by earlier versions of the app, which
      // couldn't always clear it): keep a copy of it aside and open the database without it. Every
      // write is checkpointed right away, so the database file has the data.
      const backup = await this.setWalAside(name);
      await this.openFile(name);
      this.notice = `The database ${name} couldn't replay its log, so it was opened without it. `
        + `If something you did last is missing, a copy of that log is in ${backup}.`;
    }
    // Opening another database leaves the previous one's OPFS handles open, and then that file can't
    // be opened again in this tab: release them
    if (this.capabilities.persistent && this.databaseName && this.databaseName !== name) {
      await this.releaseFiles(opfsFiles(this.databaseName));
    }
    this.connection = await this.db.connect();
    this.databaseName = name;
    try {
      localStorage.setItem(CURRENT_DB_KEY, name);
    } catch (_) { /* storage blocked: the default database is used next time */ }
  }

  async openFile(name) {
    const { DuckDBAccessMode } = this.duckdb;
    if (this.capabilities.persistent) await this.registerFiles(opfsFiles(name));
    await this.db.open({
      path: this.capabilities.persistent ? 'opfs://' + name : ':memory:',
      accessMode: DuckDBAccessMode.READ_WRITE,
      // Decimals as doubles and timestamps as milliseconds: values JavaScript can show as they are
      query: { castDecimalToDouble: true, castTimestampToDate: true },
    });
  }

  // Moves a database's WAL to a dated copy next to it and returns the copy's name
  async setWalAside(name) {
    const wal = name + '.wal';
    await this.releaseFiles(opfsFiles(name));
    const root = await navigator.storage.getDirectory();
    const backup = `${wal}.unreplayed-${new Date().toISOString().replace(/[:.]/g, '-')}`;
    const content = await (await root.getFileHandle(wal)).getFile();
    const writable = await (await root.getFileHandle(backup, { create: true })).createWritable();
    await writable.write(content);
    await writable.close();
    await root.removeEntry(wal);
    return backup;
  }

  // A message for the user about something the engine did on its own (once)
  takeNotice() {
    const notice = this.notice;
    this.notice = null;
    return notice;
  }

  // DuckDB-WASM only registers the database files that aren't empty when it opens them. An empty WAL
  // (a database opened once and never written) is then left unregistered: DuckDB can't write to it
  // ("File is not opened in write mode") and its handle is never released. Register both files.
  async registerFiles(paths) {
    const root = await navigator.storage.getDirectory();
    for (const path of paths) {
      if (this.registered.has(path)) continue;
      const handle = await root.getFileHandle(path.slice('opfs://'.length), { create: true });
      await this.db.registerFileHandle(path, handle, this.duckdb.DuckDBDataProtocol.BROWSER_FSACCESS, true);
      this.registered.add(path);
    }
  }

  async releaseFiles(paths) {
    await this.db.dropFiles(paths);
    for (const path of paths) this.registered.delete(path);
  }

  currentDatabaseName() {
    try {
      return localStorage.getItem(CURRENT_DB_KEY) || DEFAULT_DATABASE;
    } catch (_) {
      return DEFAULT_DATABASE;
    }
  }

  async queryArrow(sql) {
    await this.start();
    try {
      return await this.connection.query(sql);
    } catch (error) {
      throw new Error(error.message);
    }
  }

  async query(sql) {
    return arrowToRows(await this.queryArrow(sql));
  }

  async exec(sql) {
    await this.queryArrow(sql);
    // Writes reach OPFS once the WAL is checkpointed: do it now so a closed tab loses nothing
    if (this.capabilities.persistent && /^\s*(create|drop|alter|insert|update|delete|copy)/i.test(sql)) {
      await this.checkpoint();
    }
  }

  async checkpoint() {
    try {
      await this.connection.query('CHECKPOINT');
    } catch (_) { /* a checkpoint can't run inside a transaction: the next one will */ }
  }

  // Runs any statement (PRAGMA, EXPLAIN, SET...) and keeps what it returns as a temporary table
  async materialize(sql, tableName) {
    const result = await this.queryArrow(sql);
    const staging = '__materialize_' + Date.now();
    await this.connection.insertArrowTable(result, { name: staging, create: true });
    try {
      await this.connection.query(`CREATE OR REPLACE TEMP TABLE ${quoteIdent(tableName)} AS SELECT * FROM ${quoteIdent(staging)}`);
    } finally {
      await this.connection.query(`DROP TABLE IF EXISTS ${quoteIdent(staging)}`);
    }
  }

  async loadFile({ file, url, tableName }) {
    await this.start();
    if (!file) {
      // The browser only reads what the user picks: a path on their disk (or on a server) isn't reachable
      if (!/^https?:\/\//i.test(url.trim())) {
        throw new Error(`The browser can't open "${url}" by its path. Use Upload file to pick the file from your computer.`);
      }
      try {
        return await this.loadPath(tableName, url);
      } catch (error) {
        // DuckDB reads URLs with the browser's own requests: the server must allow it (CORS)
        if (/NetworkError|Failed to load|CORS/i.test(error.message)) {
          throw new Error(`The server of ${hostOf(url)} doesn't let browsers read this file (CORS). `
            + 'Download it and load it with Upload file.');
        }
        throw error;
      }
    }
    const { DuckDBDataProtocol } = this.duckdb;
    const prefix = `upload_${++this.uploads}_`;
    const registered = [];
    try {
      let path;
      if (/\.zip$/i.test(file.name)) {
        const { unzipSync } = await import('fflate');
        const entries = unzipSync(new Uint8Array(await file.arrayBuffer()));
        const names = Object.keys(entries).filter((name) => !name.endsWith('/'));
        const main = mainFileInZip(names);
        if (!main) throw new Error('The zip file has no file that can be loaded');
        // A shapefile is read together with its .shx, .dbf and .prj: register them all side by side
        for (const name of names) {
          await this.db.registerFileBuffer(prefix + name, entries[name]);
          registered.push(prefix + name);
        }
        path = prefix + main;
      } else {
        path = prefix + file.name;
        await this.db.registerFileHandle(path, file, DuckDBDataProtocol.BROWSER_FILEREADER, true);
        registered.push(path);
      }
      await this.loadPath(tableName, path);
    } finally {
      for (const name of registered) await this.db.dropFile(name);
    }
  }

  async loadPath(tableName, path) {
    if (needsSpatial(path)) await this.loadExtension('spatial');
    await this.exec(loadFileSql(tableName, path));
  }

  // Downloads the extension from duckdb.org the first time (h3 is a community extension)
  async loadExtension(name) {
    await this.start();
    if (this.extensions.has(name)) return;
    const repository = name === 'h3' ? ' FROM community' : '';
    await this.queryArrow(`INSTALL ${name}${repository}; LOAD ${name};`);
    this.extensions.add(name);
  }

  async exportTable(tableName, format) {
    await this.start();
    const file = `export_${Date.now()}.${format}`;
    const options = format === 'parquet' ? '(FORMAT PARQUET)' : '(FORMAT CSV, HEADER)';
    if (!['csv', 'parquet'].includes(format)) throw new Error('Format not supported: ' + format);
    await this.queryArrow(`COPY (SELECT * FROM ${quoteIdent(tableName)}) TO '${file}' ${options}`);
    try {
      const buffer = await this.db.copyFileToBuffer(file);
      return new Blob([buffer], { type: format === 'csv' ? 'text/csv' : 'application/octet-stream' });
    } finally {
      await this.db.dropFile(file);
    }
  }

  async listDatabases() {
    await this.start();
    const names = new Set([this.databaseName]);
    if (this.capabilities.persistent) {
      const root = await navigator.storage.getDirectory();
      for await (const [name, handle] of root.entries()) {
        if (handle.kind === 'file' && name.endsWith('.db')) names.add(name);
      }
    }
    // The active database first, as the backend lists them
    const others = [...names].filter((name) => name !== this.databaseName).sort();
    return { databases: [this.databaseName, ...others], current: this.databaseName };
  }

  async useDatabase(name) {
    await this.start();
    if (!this.capabilities.persistent || name === this.databaseName) return;
    await this.checkpoint();
    const previous = this.databaseName;
    try {
      await this.openDatabase(name);
    } catch (error) {
      // Back to the previous database (its files are still registered)
      await this.releaseFiles(opfsFiles(name)).catch(() => {});
      this.databaseName = null;
      await this.openDatabase(previous);
      throw new Error(openErrorMessage(error));
    } finally {
      // The extensions were loaded into the previous database
      this.extensions.clear();
    }
  }

  async createDatabase(name) {
    if (!/^[A-Za-z0-9_-]+\.db$/.test(name)) {
      throw new Error('Use letters, numbers, - and _ in the database name, ending in .db');
    }
    if (!this.capabilities.persistent) throw new Error('This browser cannot keep databases');
    const root = await navigator.storage.getDirectory();
    await root.getFileHandle(name, { create: true });
  }

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

// DuckDB-WASM reports a failed open as JSON inside the message
function openErrorMessage(error) {
  const match = error.message.match(/"exception_message":"((?:[^"\\]|\\.)*)"/);
  return match ? JSON.parse('"' + match[1] + '"') : error.message;
}

// A database and its write-ahead log
function opfsFiles(name) {
  return ['opfs://' + name, 'opfs://' + name + '.wal'];
}

function hostOf(url) {
  try {
    return new URL(url).host;
  } catch (_) {
    return url;
  }
}

function hasOpfs() {
  return typeof navigator !== 'undefined' && typeof navigator.storage?.getDirectory === 'function';
}
