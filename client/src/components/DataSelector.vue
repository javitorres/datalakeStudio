<template>
  <div class="row">
    <!--<p>DataSelector values: {{ values }}</p>
    <p>count: {{ count }}</p>-->

    <div id="view"></div>
  </div>
</template>

<script>
import { socketConnector, restConnector, wasmConnector } from '@uwdata/mosaic-core';
import { createAPIContext } from '@uwdata/vgplot';
import { parseSpec, astToDOM } from '@uwdata/mosaic-spec';
import yaml from 'yaml';

export default {
  name: 'DataSelector',

  props: {
    values: [],
    count: [],
    
  },

  data() {
    return {
      selectedConnector: 'rest', // 'socket', 'rest', 'rest_https', 'wasm'
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
  watch: {
    
  },
  ////////////////////////////////////////////////////////////////////////////
  methods: {
    initializeVgContext() {
      this.vg = createAPIContext();
      self.vg = this.vg; // Para hacer accesible la API desde la consola
      this.coordinator = this.vg.context.coordinator;
      this.namedPlots = this.vg.context.namedPlots;
    },
    ////////////////////////////////////////////////////////////////////////////
    async setConnector() {
      await this.setDatabaseConnector(this.selectedConnector);
      this.reload();
    },
    ////////////////////////////////////////////////////////////////////////////
    clear() {
      this.coordinator.clear();
      this.namedPlots.clear();
    },
    ////////////////////////////////////////////////////////////////////////////
    async setDatabaseConnector(type) {
      let connector;
      switch (type) {
        case 'socket':
          console.log('Socket Connector');
          connector = socketConnector();
          break;
        case 'rest':
          console.log('REST Connector');
          connector = restConnector('http://localhost:8000/database/restConnector/');
          break;
        case 'rest_https':
          console.log('REST HTTPS Connector');
          connector = restConnector('https://localhost:8000/database/restConnector/');
          break;
        case 'wasm':
          console.log('WASM Connector');
          connector = this.wasm || (this.wasm = wasmConnector());
          break;
        default:
          throw new Error(`Unrecognized connector type: ${type}`);
      }
      console.log('Database Connector:', type);
      this.coordinator.databaseConnector(connector);
    },
    ////////////////////////////////////////////////////////////////////////////
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
    ////////////////////////////////////////////////////////////////////////////
    async reload() {
      this.load(this.table);
    },
    ////////////////////////////////////////////////////////////////////////////
    async load(name) {
      const view = document.getElementById('view');

      if (view) {
        view.innerHTML = ''; 
      }

      if (name === 'none' && location.search) {
        name = location.search.slice(1);
      }
      if (name !== 'none') {
        const spec = this.getYaml(this.table, this.selectedFields, this.schema);
        console.log('Spec', spec);

        const baseURL = location.origin + '/';
        const options = this.selectedConnector === 'wasm' ? { baseURL } : {};

        const ast = parseSpec(spec);
        const el = await (this.loadDOM)(ast, options);
        if (view) {
          view.appendChild(el);
        }
      }
    },
    ////////////////////////////////////////////////////////////////////////////
    async loadDOM(ast, options) {
      //this.clear();
      const { element } = await astToDOM(ast, { ...options, api: this.vg });
      return element;
    },

    ////////////////////////////////////////////////////////////////////////////
    getYaml() {
      const spec = {
        data: {
          values: this.values,
        },
        mark: 'bar',
        encoding: {
          x: { field: 'a', type: 'ordinal' },
          y: { field: 'b', type: 'quantitative' },
        },
      };
      return yaml.stringify(spec);
    },
  },

    ////////////////////////////////////////////////////////////////////////////
    
  ////////////////////////////////////////////////////////////////////////////


};
</script>

<style scoped>
</style>
