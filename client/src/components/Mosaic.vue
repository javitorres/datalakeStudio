<template>
  <div class="row">

    <div id="view"></div>
  </div>
</template>

<script>
import { socketConnector, restConnector, wasmConnector } from '@uwdata/mosaic-core';
import { createAPIContext } from '@uwdata/vgplot';
import { parseSpec, astToDOM } from '@uwdata/mosaic-spec';
import yaml from 'yaml';

export default {
  name: 'Mosaic',

  props: {
    table: String,
    selectedFields: Array,
    schema: Object,
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
    table: {
      async handler(newVal, oldVal) {
        this.dropCubes();
        this.reload();
      },
      immediate: true
    },
    selectedFields: {
      async handler(newVal, oldVal) {
        this.reload();
      },
      deep: true,
      immediate: true
    },
    schema: {
      async handler(newVal, oldVal) {
        this.reload();
      },
      deep: true,
      immediate: true
    },
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
        view.innerHTML = ''; // Clear existing content
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

    getYaml(table, selectedFields, schema) {
      const yaml = {
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
        vconcat: this.createColumns(selectedFields, schema, table)
      };

      return yaml;
    },
    createColumns(selectedFields, schema, table) {
      // Divide the fields into two groups
      const mid = Math.ceil(selectedFields.length / 2);
      const leftColumn = selectedFields.slice(0, mid);
      const rightColumn = selectedFields.slice(mid);

      // Create the visualizations for each column
      const createPlots = (fields) => {
        return fields.map(field => {
          if (schema[field]) {
            if (schema[field].startsWith('int') || schema[field].startsWith('float')) {
              // Numeric field: histogram
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
              // Categorical field: (Commented out, since arc doesn't work)
              /*return {
                  plot: [
                      {
                          mark: "arc",
                          data: { from: table, filterBy: "$brush" },
                          theta: { field: field, type: "nominal", aggregate: "count" },
                          color: { field: field, type: "nominal" },
                          inset: 0.5
                      }
                  ],
                  width: 400,
                  height: 400
              };*/
            }
          }
          return null;
        }).filter(plot => plot !== null);
      };

      // Return a horizontal concatenation of the two columns
      return [{
        hconcat: [
          { vconcat: createPlots(leftColumn) },
          { vconcat: createPlots(rightColumn) }
        ]
      }];
    }
  },
  ////////////////////////////////////////////////////////////////////////////
  async dropCubes() {
    // Call dropCubes endpoint (GET)
    const url = 'http://localhost:8000/database/restConnector/dropCubes';
    const response = await fetch(url);
    const data = await response.json();
    console.log('Drop Cubes:', data);

  }

};
</script>

<style scoped>
/* Puedes incluir los estilos de styles.css aquí o importarlos */
</style>
