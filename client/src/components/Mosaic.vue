<template>
  <div class="row">

    <div class="col-md-3">
      <select v-model="selectedExample" @change="reload">
        <option value="flights-200k">Flights 200k</option>
      </select>
    </div>



    <div class="col-md-3">
      Connector:
      <select v-model="selectedConnector" @change="setConnector">
        <option value="wasm">WASM</option>
        <option value="socket">Socket</option>
        <option value="rest">REST</option>
        <option value="rest_https">REST (HTTPS)</option>
      </select>
    </div>



    <div class="col-md-5">
      <div>
        Spec Type:
        <select v-model="selectedSource" @change="reload">
          <option value="yaml">YAML</option>
          <option value="esm">ESM</option>
        </select>
      </div>
      <div>
        Log Queries:
        <input v-model="queryLog" type="checkbox" @input="setQueryLog" />
      </div>
      <div>
        Query Cache:
        <input v-model="cacheEnabled" type="checkbox" @input="setCache" />
      </div>
      <div>
        Query Consolidation:
        <input v-model="consolidateEnabled" type="checkbox" @input="setConsolidate" />
      </div>
      <div>
        Data Cube Indexes:
        <input v-model="indexEnabled" type="checkbox" @input="setIndex" />
      </div>
      <div>
        Active Index State:
        <button @click="logIndexState">Log</button>
      </div>
    </div>

    <!-- Button for reload this.reload() -->
    <div class="col-md-1">
      <button @click="reload">Reload</button>
    </div>

    <div id="view"></div>
  </div>

</template>

<script>
import { socketConnector, restConnector, wasmConnector } from '@uwdata/mosaic-core';
import { createAPIContext } from '@uwdata/vgplot';
import { parseSpec, astToDOM, astToESM } from '@uwdata/mosaic-spec';
import yaml from 'yaml';

export default {
  name: 'Mosaic',
  data() {
    return {
      selectedExample: 'none',
      selectedConnector: 'rest',
      selectedSource: 'yaml',
      queryLog: false,
      cacheEnabled: true,
      consolidateEnabled: true,
      indexEnabled: true,
      wasm: null,
    };
  },
  mounted() {
    this.initializeVgContext();
    this.setQueryLog();
    this.setCache();
    this.setConsolidate();
    this.setIndex();
    this.setConnector();
  },
  methods: {
    initializeVgContext() {
      this.vg = createAPIContext();
      self.vg = this.vg; // Para hacer accesible la API desde la consola
      this.coordinator = this.vg.context.coordinator;
      this.namedPlots = this.vg.context.namedPlots;
    },
    async setConnector() {
      await this.setDatabaseConnector(this.selectedConnector);
      this.reload();
    },
    clear() {
      this.coordinator.clear();
      this.namedPlots.clear();
    },
    async setDatabaseConnector(type) {
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
          connector = this.wasm || (this.wasm = wasmConnector());
          break;
        default:
          throw new Error(`Unrecognized connector type: ${type}`);
      }
      console.log('Database Connector', type);
      this.coordinator.databaseConnector(connector);
    },
    // Resto de los métodos como se definieron antes
    setQueryLog() {
      this.vg.coordinator().manager.logQueries(this.queryLog);
    },
    setCache() {
      this.vg.coordinator().manager.cache(this.cacheEnabled);
    },
    setConsolidate() {
      this.vg.coordinator().manager.consolidate(this.consolidateEnabled);
    },
    setIndex() {
      this.vg.coordinator().dataCubeIndexer.enabled(this.indexEnabled);
    },
    logIndexState() {
      const { indexes } = this.vg.coordinator().dataCubeIndexer || {};
      if (indexes) {
        console.warn('Data Cube Index Entries', Array.from(indexes.values()));
      } else {
        console.warn('No Active Data Cube Index');
      }
    },
    async reload() {
      this.load(this.selectedExample, this.selectedSource);
    },
    async load(name, source) {
      const view = this.$el.querySelector('#view');
      view.innerHTML = ''; // Clear existing content
      if (name === 'none' && location.search) {
        name = location.search.slice(1);
      }
      if (name !== 'none') {
        const spec = yaml.parse(
          await fetch(`../src/assets/specs/${name}.yaml`).then(res => res.text())
        );
        console.log('Spec', spec);

        const baseURL = location.origin + '/';
        const options = this.selectedConnector === 'wasm' ? { baseURL } : {};

        const ast = parseSpec(spec);
        const el = await (source === 'esm' ? this.loadESM : this.loadDOM)(ast, options);
        view.appendChild(el);
      }
    },
    async loadDOM(ast, options) {
      this.clear();
      const { element } = await astToDOM(ast, { ...options, api: this.vg });
      return element;
    },
    async loadESM(ast, options) {
      const vgplot = new URL('./setup.js', window.location.href).toString();
      const imports = new Map([[vgplot, ['vg', 'clear']]]);
      const preamble = 'clear();';
      const code = astToESM(ast, { ...options, imports, preamble });
      console.log(code);
      const blob = new Blob([code], { type: 'text/javascript' });
      const url = URL.createObjectURL(blob);
      return (await import(/* @vite-ignore */ url)).default;
    },
  },
  components: {
    // Aquí puedes registrar componentes adicionales si los tienes
  },
};
</script>

<style scoped>
/* Puedes incluir los estilos de styles.css aquí o importarlos */
</style>
