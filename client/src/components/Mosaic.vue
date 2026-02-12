<template>
  <div class="row">

    <div id="view"></div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import { socketConnector, restConnector, wasmConnector } from '@uwdata/mosaic-core';
import { createAPIContext } from '@uwdata/vgplot';
import { parseSpec, astToDOM } from '@uwdata/mosaic-spec';
import yaml from 'yaml';

const props = defineProps({
  table: String,
  selectedFields: Array,
  schema: Object,
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

watch(() => props.table, async () => {
  await dropCubes();
  await reload();
}, { immediate: true });

watch(() => props.selectedFields, async () => {
  await reload();
}, { deep: true, immediate: true });

watch(() => props.schema, async () => {
  await reload();
}, { deep: true, immediate: true });

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

function getYaml(table, selectedFields, schema) {
  const yamlSpec = {
    meta: {
      title: `Cross-Filter ${table.charAt(0).toUpperCase() + table.slice(1)}`,
      description: `Histograms showing ${selectedFields.join(', ')} for ${table}.`,
    },
    data: {
      [table]: { file: `data/${table}.parquet` }
    },
    params: {
      brush: { select: "crossfilter" }
    },
    vconcat: createColumns(selectedFields, schema, table)
  };

  return yamlSpec;
}

function createColumns(selectedFields, schema, table) {
  const mid = Math.ceil(selectedFields.length / 2);
  const leftColumn = selectedFields.slice(0, mid);
  const rightColumn = selectedFields.slice(mid);

  const createPlots = (fields) => {
    return fields.map(field => {
      if (schema[field]) {
        if (schema[field].startsWith('int') || schema[field].startsWith('float')) {
          return {
            plot: [
              {
                mark: "rectY",
                data: { from: table, filterBy: "$brush" },
                x: { bin: field },
                y: { count: null },
                fill: "steelblue",
                inset: 0.5
              },
              {
                select: "intervalX",
                as: "$brush"
              }
            ],
            xDomain: "Fixed",
            yTickFormat: "s",
            width: 600,
            height: 200
          };
        } else if (schema[field] === "varchar" || schema[field] === "string" || schema[field] === "object") {
          if (schema[field].cardinality && schema[field].cardinality > 100) {
            return null;
          }
          return {
            plot: [
              {
                mark: "rectX",
                data: { from: table, filterBy: "$brush" },
                x: { count: null },
                y: field,
                fill: "steelblue",
                inset: 0.5
              },
              {
                select: "intervalY",
                as: "$brush"
              }
            ],
            xDomain: "Fixed",
            yTickFormat: "s",
            width: 600,
            height: 200
          };
        }
      }
      return null;
    }).filter(plot => plot !== null);
  };

  return [{
    hconcat: [
      { vconcat: createPlots(leftColumn) },
      { vconcat: createPlots(rightColumn) }
    ]
  }];
}

async function dropCubes() {
  const url = 'http://localhost:8000/database/restConnector/dropCubes';
  const response = await fetch(url);
  const data = await response.json();
  console.log('Drop Cubes:', data);
}
</script>

<style scoped>
</style>
