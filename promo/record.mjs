// Records the promo segments: node promo/record.mjs [segment ...]  (all of them by default)
// Needs the app on :8080 (npm run dev) and the backend on :8000 with a throwaway data folder: the
// segments drop and create tables. Each segment becomes promo/work/segs/<name>.mp4; see promo/README.md.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Browser, sleep } from './cdp.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WORK = path.join(HERE, 'work');
const APP = 'http://localhost:8080/';
const API = 'http://localhost:8000';
const TRIPS_URL = 'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet';
const ZONES_URL = 'https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip';
const ZONES_ZIP = path.join(WORK, 'taxi_zones.zip');

// Typed in the SQL workspace: each trip with its pickup zone, borough and coordinates (zone centroid)
const PICKUPS_SQL = `SELECT t.*, z.zone, z.borough,
ST_Y(z.c) AS lat, ST_X(z.c) AS lon
FROM trips t
JOIN (SELECT *, ST_Transform(ST_Centroid(geom), 'EPSG:2263', 'EPSG:4326', always_xy := true) AS c
FROM taxi_zones) z ON t.PULocationID = z.LocationID`;
// Saved beforehand and published as an endpoint
const TOP_ZONES_SQL = `SELECT zone, count(*) AS trips, round(avg(tip_amount), 2) AS avg_tip
FROM pickups
WHERE borough = '{borough}'
GROUP BY zone ORDER BY trips DESC LIMIT 5`;

const api = async (route, init) => {
  const r = await fetch(API + route, init);
  if (!r.ok) throw new Error(`${route}: ${r.status} ${await r.text()}`);
  return r.headers.get('content-type')?.includes('json') ? r.json() : r.text();
};
const sql = (query) => api('/database/restConnector', {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'exec', sql: query }),
});
const tables = () => api('/database/getTables');

async function ensureData({ trips = true, zones = true, pickups = true } = {}) {
  if (!fs.existsSync(ZONES_ZIP)) {
    fs.mkdirSync(WORK, { recursive: true });
    fs.writeFileSync(ZONES_ZIP, Buffer.from(await (await fetch(ZONES_URL)).arrayBuffer()));
  }
  let have = await tables();
  if (trips && !have.includes('trips')) {
    await api(`/database/loadFile?fileName=${encodeURIComponent(TRIPS_URL)}&tableName=trips`);
  }
  if (zones && !have.includes('taxi_zones')) {
    const form = new FormData();
    form.append('file', new Blob([fs.readFileSync(ZONES_ZIP)]), 'taxi_zones.zip');
    form.append('tableName', 'taxi_zones');
    await api('/database/uploadFile', { method: 'POST', body: form });
  }
  have = await tables();
  if (pickups && !have.includes('pickups')) {
    await api(`/database/createTableFromQuery?tableName=pickups&query=${encodeURIComponent(PICKUPS_SQL)}`);
  }
}

const nav = (b, title) => b.click(`a[title="${title}"]`);

// Opens a table in the explorer and waits for its sample rows
async function openTable(b, name) {
  await nav(b, 'Show tables');
  await sleep(500);
  await b.click('button', name);
  await b.waitFor('document.querySelectorAll(".tabulator-row").length > 3', 60000);
  await sleep(600);
}

async function setSelect(b, label, value) {
  // Native dropdowns don't show in the screencast: point at the select and set its value
  const id = `promo-${label.replace(/\W/g, '')}`;
  await b.eval(`(() => {
    const group = [...document.querySelectorAll('div')].reverse()
      .find((d) => d.querySelector(':scope > select') && d.textContent.includes(${JSON.stringify(label)}));
    group.querySelector('select').id = ${JSON.stringify(id)};
  })()`);
  await b.click(`#${id}`);
  await sleep(300);
  await b.eval(`(() => { const s = document.getElementById(${JSON.stringify(id)}); s.value = ${JSON.stringify(value)};
    s.dispatchEvent(new Event('change', { bubbles: true })); })()`);
}

// Scrolls the page smoothly to the offset the expression returns, and waits for it to settle
async function smoothScroll(b, topExpr, ms = 1200) {
  await b.eval(`window.scrollTo({top: ${topExpr}, behavior: 'smooth'})`);
  await sleep(ms);
}

const SEGMENTS = {
  // Landing view, behind the opening title and the end card
  async overview(b) {
    await b.goto(APP);
    await sleep(1500);
    await b.rec();
    await b.moveTo(500, 470, 2200);
    await sleep(900);
    await b.moveTo(900, 230, 2200);
    await sleep(1500);
  },

  // A 3M-row Parquet straight from a URL, then a zipped shapefile from disk
  async load(b) {
    await sql('DROP TABLE IF EXISTS pickups; DROP TABLE IF EXISTS trips; DROP TABLE IF EXISTS taxi_zones');
    await ensureData({ trips: false, zones: false, pickups: false });
    await b.goto(APP);
    await sleep(800);
    await b.rec();
    await nav(b, 'Load data from files');
    await sleep(500);
    await b.click('a', 'Load from URL');
    await sleep(400);
    await b.click('input[aria-label="File"]');
    await b.type(TRIPS_URL, 45);
    await sleep(300);
    await b.click('input[placeholder="Table name"]');
    await b.type('trips', 10);
    await sleep(300);
    await b.click('button', 'Load file');
    await b.waitFor('document.body.innerText.includes("1 table")', 120000);
    await sleep(1800);
    await b.click('a', 'Upload file');
    await sleep(500);
    const { root } = await b.send('DOM.getDocument');
    const { nodeId } = await b.send('DOM.querySelector', { nodeId: root.nodeId, selector: 'input[type=file]' });
    await b.click('input[type=file]');
    await b.send('DOM.setFileInputFiles', { nodeId, files: [ZONES_ZIP] });
    await sleep(500);
    await b.click('#tableNameInputUpload');
    await b.type('taxi_zones', 10);
    await sleep(300);
    await b.click('button', 'Load file');
    await b.waitFor('document.body.innerText.includes("2 tables")', 120000);
    await sleep(2200);
  },

  // Join 3M trips with the zone shapes, then keep the result as a table
  async sql(b) {
    await ensureData({ pickups: false });
    await sql('DROP TABLE IF EXISTS pickups');
    await b.goto(APP);
    await sleep(800);
    await b.rec();
    await nav(b, 'Queries');
    await sleep(600);
    await b.click('button', 'Clear');
    await sleep(300);
    await b.click('.cm-content');
    await b.type(PICKUPS_SQL, 32);
    await b.key('Escape');
    await sleep(500);
    await b.click('button.run-query');
    await b.waitFor('document.querySelectorAll(".tabulator-row").length > 3', 120000);
    await sleep(600);
    // The result grid renders below the editor
    await smoothScroll(b, 'document.querySelector(".tabulator").getBoundingClientRect().top + scrollY - 160', 1400);
    await sleep(2200);
    await smoothScroll(b, '0', 1000);
    await b.click('#tableNameInput');
    await b.type('pickups', 10);
    await sleep(300);
    await b.click('button', 'Create table');
    await b.waitFor('document.body.innerText.includes("3 tables")', 120000);
    await sleep(2000);
  },

  // Rows, profile
  async explore(b) {
    await ensureData();
    await b.goto(APP);
    await sleep(800);
    await b.rec();
    await openTable(b, 'pickups');
    await sleep(800);
    await b.click('button', 'Random');
    await sleep(1500);
    await b.scroll(900, 520, 1400);
    await sleep(800);
    await b.click('span', 'Profile');
    await b.waitFor('document.body.innerText.includes("p75") || document.body.innerText.includes("mean")', 60000);
    await sleep(2500);
  },

  // Cross-filter: dragging one histogram filters the others
  async charts(b) {
    await ensureData();
    await b.goto(APP);
    await sleep(800);
    await openTable(b, 'pickups');
    await b.rec();
    await b.click('button[title="Deselect all fields"]');
    await sleep(300);
    for (const field of ['borough', 'trip_distance', 'fare_amount', 'passenger_count']) {
      await b.click('.field-chip', field, { ms: 350, pause: 120 });
      await sleep(150);
    }
    await b.click('span', 'Charts');
    await b.waitFor('document.querySelectorAll(".chart canvas").length >= 4', 60000);
    await sleep(2200);
    // Right handle of the dataZoom slider under the first histogram (trip_distance)
    const r = await b.eval(`(() => { const w = document.querySelector('.chart-wrapper'); w.scrollIntoView({block: 'center', behavior: 'instant'});
      const b = w.querySelector('.chart').getBoundingClientRect(); return {l: b.left, r: b.right, bottom: b.bottom}; })()`);
    await sleep(600);
    await b.drag(r.r - 20, r.bottom - 15, r.l + 50 + (r.r - r.l - 70) * 0.35, r.bottom - 15, 1400);
    await sleep(2500);
    // The other charts follow the filter
    await smoothScroll(b, 'scrollY + 420', 1400);
    await sleep(2500);
  },

  // H3 hexagons over New York, extruded by pickups
  async map(b) {
    await ensureData();
    await b.goto(APP);
    await sleep(800);
    await openTable(b, 'pickups');
    await b.click('span', 'Map');
    await b.waitFor('document.querySelector(".mapboxgl-canvas")', 60000);
    await sleep(2000);
    // The map opens over Spain: frame New York while it is still below the fold
    await b.eval(`(() => { const el = document.querySelector('.mapboxgl-map');
      const map = el.__vueParentComponent?.proxy?.map || el.parentElement.__vueParentComponent?.proxy?.map;
      window.__promoMap = map; map.jumpTo({center: [-73.93, 40.70], zoom: 10.2, pitch: 0, bearing: 0}); })()`);
    await sleep(1500);
    await b.rec();
    await setSelect(b, 'Latitude', 'lat');
    await sleep(400);
    await setSelect(b, 'Longitude', 'lon');
    await sleep(700);
    await smoothScroll(b, 'document.querySelector(".map-setup-card").getBoundingClientRect().top + scrollY - 90');
    await setSelect(b, 'H3 Level', '8');
    await sleep(500);
    await b.eval(`[...document.querySelectorAll('.form-check')].find((d) => d.textContent.includes('H3 Data'))
      .querySelector('input').id = 'promo-h3'`);
    await b.click('#promo-h3');
    await sleep(600);
    await b.click('button.map-refresh');
    await sleep(1500);
    await smoothScroll(b, 'document.querySelector(".mapboxgl-map").getBoundingClientRect().bottom + scrollY - innerHeight + 4');
    await b.moveTo(1150, 690, 600);
    await sleep(1500);
    await b.eval('__promoMap.easeTo({pitch: 50, bearing: -20, zoom: 10.6, duration: 6000})');
    await sleep(6800);
  },

  // A saved query published as a REST endpoint with a parameter
  async api(b) {
    await ensureData();
    for (const e of await api('/apiserver/listEndpoints')) await api(`/apiserver/deleteEndpoint?id_endpoint=${e.id_endpoint}`);
    for (const q of await api('/queries/searchQuery?query=')) await api(`/queries/deleteQuery?id_query=${q.id_query}`);
    await api('/queries/saveSqlQuery', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: TOP_ZONES_SQL, sqlQueryName: 'Top zones by borough', description: 'Busiest pickup zones' }) });
    await b.goto(APP);
    // The query search toasts on every keystroke: keep them off the screen
    await b.eval(`new MutationObserver(() => document.querySelectorAll('.Toastify__toast').forEach((t) => {
      if (t.textContent.includes('SQL queries loaded')) t.style.display = 'none';
    })).observe(document.body, {childList: true, subtree: true})`);
    await sleep(800);
    await b.rec();
    await nav(b, 'Expose data via API');
    await sleep(700);
    await b.click('button', 'Create new endpoint');
    await sleep(900);
    await b.click('button', 'Edit');
    await sleep(700);
    await b.click('input[placeholder="Query name"]');
    await b.type('top zones', 14);
    await sleep(700);
    await b.click('li.list-group-item', 'Top zones');
    await sleep(1200);
    // The parameter fields appear once the SQL is edited
    await b.click('.cm-line', 'LIMIT 5');
    await b.key('End');
    await b.type(' ', 5);
    await sleep(600);
    await b.click('input[placeholder="Write an example value for testing"]');
    await b.type('Manhattan', 14);
    await b.eval(`(() => { const g = [...document.querySelectorAll('.input-group')].find((d) => d.textContent.includes('Endpoint'));
      g.querySelector('input').id = 'promo-endpoint'; })()`);
    await b.click('#promo-endpoint');
    await b.eval("document.getElementById('promo-endpoint').select()");
    await b.type('topZones', 14);
    await sleep(400);
    await setSelect(b, 'Status', 'DEV');
    await sleep(500);
    await b.click('button', 'Save and Test endpoint');
    await b.waitFor('document.querySelector("textarea")?.value.includes("avg_tip")', 60000);
    await b.scroll(700, 500, 900);
    await sleep(2500);
    // What another app gets: headless Chrome has no address bar, so show the request above the JSON
    const url = `${API}/api/topZones?borough=Brooklyn`;
    await b.goto(url);
    await b.eval(`(() => { const data = JSON.parse(document.body.innerText);
      document.body.innerHTML = '';
      Object.assign(document.body.style, {margin: 0, padding: '56px 72px', background: '#f3f7f5', font: '26px/1.5 monospace', color: '#17211f'});
      const get = document.createElement('div');
      get.innerHTML = '<b style="color:#fff;background:#0d846f;border-radius:8px;padding:4px 12px;margin-right:16px">GET</b>' + ${JSON.stringify(url)};
      get.style.marginBottom = '28px';
      const pre = document.createElement('pre');
      pre.textContent = JSON.stringify(data, null, 2);
      Object.assign(pre.style, {margin: 0, padding: '28px 36px', background: '#fff', border: '1px solid #d9e5e1', borderRadius: '14px', font: 'inherit', fontSize: '22px'});
      document.body.append(get, pre); })()`);
    await sleep(3500);
  },
};

const names = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(SEGMENTS);
const b = new Browser({ width: 1280, height: 720, scale: 1.5 });
await b.launch();
await b.send('Emulation.setLocaleOverride', { locale: 'en-US' });
try {
  for (const name of names) {
    const out = path.join(WORK, 'segs', `${name}.mp4`);
    let started = false;
    b.rec = async () => {
      if (started) return;   // a navigation mid-segment keeps recording
      started = true;
      await b.startRecording(path.join(WORK, 'frames', name));
    };
    await SEGMENTS[name](b);
    const { frames, seconds } = await b.stopRecording(out);
    console.log(`${name}: ${seconds.toFixed(1)} s, ${frames} frames -> ${out}`);
  }
} finally {
  await b.close();
}
