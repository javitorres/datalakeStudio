<template>
  <div class="row">

    <div id="view"></div>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue';
import { parseSpec } from '@uwdata/mosaic-spec';
import { API_URL } from '../../config';
import { useMosaic } from '../composables/useMosaic';

const props = defineProps({
  table: String,
  selectedFields: Array,
  schema: Object,
});

const { selectedConnector, vg, loadDOM, setupMosaic } = useMosaic();

onMounted(async () => {
  setupMosaic();
  await reload();
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

async function reload() {
  if (!vg.value) return;
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

function getYaml(table, selectedFields, schema) {
  const yamlSpec = {
    meta: {
      title: `Cross-Filter ${table.charAt(0).toUpperCase() + table.slice(1)}`,
      description: `Histograms showing ${selectedFields.join(', ')} for ${table}.`,
    },
    data: {
      [table]: { query: `SELECT * FROM ${table}` }
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
  const response = await fetch(`${API_URL}/database/dropCubes`);
  await response.json();
}
</script>

<style scoped>
</style>
