<template>
  <div class="row">
    <!--<p>DataSelector values: {{ values }}</p>
    <p>count: {{ count }}</p>-->

    <div id="view"></div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { parseSpec } from '@uwdata/mosaic-spec';
import yaml from 'yaml';
import { useMosaic } from '../composables/useMosaic';

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

const { selectedConnector, vg, loadDOM, setupMosaic } = useMosaic();

onMounted(async () => {
  setupMosaic();
  await reload();
});

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
