<template>
  <div class="row">
    <!--<p>DataSelector values: {{ values }}</p>
    <p>count: {{ count }}</p>-->

    <div id="view"></div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { socketConnector, restConnector, wasmConnector } from '@uwdata/mosaic-core';
import { createAPIContext } from '@uwdata/vgplot';
import { parseSpec, astToDOM } from '@uwdata/mosaic-spec';
import yaml from 'yaml';

const props = defineProps({
  values: {
    type: Array,
    default: () => []
  },
  count: {
    type: Array,
    default: () => []
  },
});

const selectedConnector = ref('rest');
const queryLog = ref(false);
const cacheEnabled = ref(true);
const consolidateEnabled = ref(true);
const indexEnabled = ref(true);
const wasm = ref(null);
const vg = ref(null);
const coordinator = ref(null);
const namedPlots = ref(null);

onMounted(() => {
  initializeVgContext();
  setQueryLog();
  setCache();
  setConsolidate();
  setIndex();
  setConnector();
});

function initializeVgContext() {
  vg.value = createAPIContext();
  self.vg = vg.value;
  coordinator.value = vg.value.context.coordinator;
  namedPlots.value = vg.value.context.namedPlots;
}

async function setConnector() {
  await setDatabaseConnector(selectedConnector.value);
  reload();
}

function clear() {
  coordinator.value.clear();
  namedPlots.value.clear();
}

async function setDatabaseConnector(type) {
  let connector;
  switch (type) {
    case 'socket':
      connector = socketConnector();
      break;
    case 'rest':
      connector = restConnector('http://localhost:8000/database/restConnector/');
      break;
    case 'rest_https':
      connector = restConnector('https://localhost:8000/database/restConnector/');
      break;
    case 'wasm':
      connector = wasm.value || (wasm.value = wasmConnector());
      break;
    default:
      throw new Error(`Unrecognized connector type: ${type}`);
  }
  coordinator.value.databaseConnector(connector);
}

function setQueryLog() {
  vg.value.coordinator().manager.logQueries(queryLog.value);
}

function setCache() {
  vg.value.coordinator().manager.cache(cacheEnabled.value);
}

function setConsolidate() {
  vg.value.coordinator().manager.consolidate(consolidateEnabled.value);
}

function setIndex() {
  vg.value.coordinator().dataCubeIndexer.enabled(indexEnabled.value);
}

function logIndexState() {
  const { indexes } = vg.value.coordinator().dataCubeIndexer || {};
  if (indexes) {
    console.warn('Data Cube Index Entries', Array.from(indexes.values()));
  } else {
    console.warn('No Active Data Cube Index');
  }
}

async function reload() {
  await load(props.table);
}

async function load(name) {
  const view = document.getElementById('view');

  if (view) {
    view.innerHTML = '';
  }

  if (name === 'none' && location.search) {
    name = location.search.slice(1);
  }
  if (name !== 'none') {
    const spec = getYaml(props.table, props.selectedFields, props.schema);
    const baseURL = location.origin + '/';
    const options = selectedConnector.value === 'wasm' ? { baseURL } : {};

    const ast = parseSpec(spec);
    const el = await loadDOM(ast, options);
    if (view) {
      view.appendChild(el);
    }
  }
}

async function loadDOM(ast, options) {
  const { element } = await astToDOM(ast, { ...options, api: vg.value });
  return element;
}

function getYaml() {
  const spec = {
    data: {
      values: props.values,
    },
    mark: 'bar',
    encoding: {
      x: { field: 'a', type: 'ordinal' },
      y: { field: 'b', type: 'quantitative' },
    },
  };
  return yaml.stringify(spec);
}
</script>

<style scoped>
</style>
