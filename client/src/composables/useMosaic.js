import { ref } from 'vue';
import { socketConnector, restConnector, wasmConnector } from '@uwdata/mosaic-core';
import { createAPIContext } from '@uwdata/vgplot';
import { astToDOM } from '@uwdata/mosaic-spec';
import { API_URL } from '../../config';

// Shared Mosaic/vgplot plumbing used by both Mosaic.vue and DataSelector.vue.
// Each component keeps its own reload()/load()/getYaml() (they render different
// specs); everything below is the identical boilerplate they used to duplicate.
export function useMosaic() {
  const selectedConnector = ref('rest');
  const queryLog = ref(false);
  const cacheEnabled = ref(true);
  const consolidateEnabled = ref(true);
  const indexEnabled = ref(true);
  const wasm = ref(null);
  const vg = ref(null);
  const coordinator = ref(null);
  const namedPlots = ref(null);

  function initializeVgContext() {
    vg.value = createAPIContext();
    // Exposed on the global scope because MapH3's renderChart() reads window.vg.
    self.vg = vg.value;
    coordinator.value = vg.value.context.coordinator;
    namedPlots.value = vg.value.context.namedPlots;
  }

  function setDatabaseConnector(type) {
    let connector;
    switch (type) {
      case 'socket':
        connector = socketConnector();
        break;
      case 'rest':
      case 'rest_https':
        connector = restConnector(`${API_URL}/database/restConnector`);
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

  function clear() {
    coordinator.value.clear();
    namedPlots.value.clear();
  }

  function logIndexState() {
    const { indexes } = vg.value.coordinator().dataCubeIndexer || {};
    if (indexes) {
      console.warn('Data Cube Index Entries', Array.from(indexes.values()));
    } else {
      console.warn('No Active Data Cube Index');
    }
  }

  async function loadDOM(ast, options) {
    const { element } = await astToDOM(ast, { ...options, api: vg.value });
    return element;
  }

  // Standard boot sequence (everything except the component-specific reload()).
  function setupMosaic() {
    initializeVgContext();
    setQueryLog();
    setCache();
    setConsolidate();
    setIndex();
    setDatabaseConnector(selectedConnector.value);
  }

  return {
    selectedConnector,
    queryLog,
    cacheEnabled,
    consolidateEnabled,
    indexEnabled,
    wasm,
    vg,
    coordinator,
    namedPlots,
    initializeVgContext,
    setDatabaseConnector,
    setQueryLog,
    setCache,
    setConsolidate,
    setIndex,
    clear,
    logIndexState,
    loadDOM,
    setupMosaic,
  };
}
