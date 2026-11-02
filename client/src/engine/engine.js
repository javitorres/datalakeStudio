// Contract shared by the engines the app can run on. Components never talk to an engine's transport
// (HTTP, worker) directly: they call the functions in src/data, which build the SQL once and run it on
// whichever engine is active.
//
// An engine implements:
//   mode                     'remote' (Python backend) or 'local' (DuckDB in the browser)
//   capabilities             which optional features this engine can serve (see CAPABILITIES)
//   query(sql)               -> array of plain row objects (JSON-safe values, ISO dates)
//   queryArrow(sql)          -> Apache Arrow table
//   exec(sql)                runs statements that return nothing worth reading
//   loadFile({ file, url, tableName })
//                            creates a table from a File the user picked or from a URL
//   exportTable(tableName, format)
//                            -> Blob with the table as 'csv' or 'parquet'
//   listDatabases()          -> { databases: [names], current: name }
//   useDatabase(name)        makes that database the active one
//   createDatabase(name)
//   mosaicConnector()        connector for the Mosaic coordinator
//   runUserQuery(sql)        optional: runs a SQL workspace script and keeps its result as __lastQuery.
//                            When missing, src/data/tables.js does it with plain SQL.

// Features beyond plain SQL, each one shown only when the active engine can serve it
export const CAPABILITIES = [
  's3',          // browse S3 buckets and load files from them
  'remoteDb',    // query remote PostgreSQL databases
  'publishApi',  // publish queries as REST endpoints
  'apiEnrichment', // enrich tables by calling external APIs
  'auth',        // users and login
  'serverAi',    // AI assistant with the server's OpenAI key
  'serverPath',  // load files from a path on the server
  'maps',        // map view (its queries still run on the backend's /maps endpoints)
  'h3',          // H3 aggregation on maps
  'spatial',     // geometry columns and shapefiles
  'persistent',  // databases survive a page reload
];

export function capabilities(enabled) {
  return Object.fromEntries(CAPABILITIES.map((name) => [name, Boolean(enabled[name])]));
}
