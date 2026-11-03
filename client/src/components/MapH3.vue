<template>
  <div class="geo">
    <!-- Controls: where the data is, then each layer with its own switch -->
    <aside class="geo-panel">
      <section class="geo-section">
        <header class="section-head">
          <h5><i class="bi bi-geo-alt"></i> {{ $t('MapH3.location.title') }}</h5>
          <span v-if="hasLocation" class="section-ok"><i class="bi bi-check-circle-fill"></i> {{ $t('MapH3.location.ready') }}</span>
        </header>
        <div class="field-grid">
          <label class="field">
            <span>{{ $t('MapH3.location.latitude') }}</span>
            <select class="form-select form-select-sm" v-model="latitudeField" @change="coordinatesChanged">
              <option :value="null">{{ $t('MapH3.location.none') }}</option>
              <option v-for="field in selectedFields" :key="field" :value="field">{{ field }}</option>
            </select>
          </label>
          <label class="field">
            <span>{{ $t('MapH3.location.longitude') }}</span>
            <select class="form-select form-select-sm" v-model="longitudeField" @change="coordinatesChanged">
              <option :value="null">{{ $t('MapH3.location.none') }}</option>
              <option v-for="field in selectedFields" :key="field" :value="field">{{ field }}</option>
            </select>
          </label>
          <label class="field field-wide">
            <span>{{ $t('MapH3.location.geometry') }} <small>{{ $t('MapH3.location.geometryHelp') }}</small></span>
            <select class="form-select form-select-sm" v-model="geomField" @change="coordinatesChanged">
              <option :value="null">{{ $t('MapH3.location.none') }}</option>
              <option v-for="field in selectedFields" :key="field" :value="field">{{ field }}</option>
            </select>
          </label>
        </div>
      </section>

      <!-- Areas: H3 hexagons from latitude/longitude, or the shapes of the geometry column -->
      <section class="layer-card" :class="{ on: showData, off: !hasLocation }">
        <header class="layer-head">
          <span class="layer-icon layer-icon-h3"><i :class="hasCoordinates || !geomField ? 'bi bi-hexagon-fill' : 'bi bi-pentagon-fill'"></i></span>
          <div class="layer-title">
            <strong>{{ hasCoordinates || !geomField ? $t('MapH3.h3.title') : $t('MapH3.h3.geomTitle') }}</strong>
            <small>{{ !hasLocation ? $t('MapH3.needsLocation') : hasCoordinates ? $t('MapH3.h3.summary') : $t('MapH3.h3.geomSummary') }}</small>
          </div>
          <div class="form-check form-switch m-0">
            <input class="form-check-input" type="checkbox" role="switch" v-model="showData" :disabled="!canRenderH3"
              :aria-label="$t('MapH3.h3.title')" @change="updateVisibility()">
          </div>
        </header>
        <div v-if="showData && hasLocation" class="layer-body">
          <label class="field">
            <span>{{ $t('MapH3.colorBy') }}</span>
            <select class="form-select form-select-sm" v-model="selectedFieldForH3" @change="showField('H3')">
              <option value="count">{{ $t('MapH3.recordCount') }}</option>
              <option v-for="field in numericFields" :key="field" :value="field">{{ $t('MapH3.average', { field }) }}</option>
            </select>
          </label>
          <MapColorScale v-model:low="minValue" v-model:high="maxValue" v-model:colorLow="colorPickerH3Low"
            v-model:colorHigh="colorPickerH3High" :min="min" :max="max" :histogram="percentilesH3?.histogram"
            :disabled="!percentilesH3" @change="changeLimits('H3')" @reset="resetLimits('H3')" />
          <label v-if="hasCoordinates" class="field">
            <span>
              {{ $t('MapH3.resolution') }}
              <span class="resolution-value">
                <b>{{ $t('MapH3.resolutionValue', { level: h3Level, size: h3SizeLabel }) }}</b>
                <button type="button" class="chip" :class="{ active: !levelChosen }" :title="$t('MapH3.autoLevelHelp')" @click="autoLevel">{{ $t('MapH3.autoLevel') }}</button>
              </span>
            </span>
            <input type="range" class="form-range" min="1" max="12" step="1" v-model.number="h3Level" @change="levelChosen = true; reloadMap('H3', true, true)">
            <span class="range-ends"><small>{{ $t('MapH3.coarse') }}</small><small>{{ $t('MapH3.fine') }}</small></span>
          </label>
          <label class="field">
            <span>{{ $t('MapH3.opacity') }} <b>{{ Math.round(h3Opacity * 100) }}%</b></span>
            <input type="range" class="form-range" min="0" max="1" step="0.05" v-model.number="h3Opacity" @input="changeH3Opacity()">
          </label>
          <div class="field-row">
            <div class="segmented" role="group" :aria-label="$t('MapH3.style')">
              <button type="button" :class="{ active: !show3D }" @click="setShow3D(false)">{{ $t('MapH3.flat') }}</button>
              <button type="button" :class="{ active: show3D }" :title="$t('MapH3.extrudedHelp')" @click="setShow3D(true)">{{ $t('MapH3.extruded') }}</button>
            </div>
            <div class="form-check form-switch m-0">
              <input class="form-check-input" type="checkbox" role="switch" id="h3Borders" v-model="outline" @change="toggleOutline()">
              <label class="form-check-label" for="h3Borders">{{ $t('MapH3.borders') }}</label>
            </div>
          </div>
        </div>
      </section>

      <section class="layer-card" :class="{ on: showDataPoints, off: !hasCoordinates }">
        <header class="layer-head">
          <span class="layer-icon layer-icon-points"><i class="bi bi-circle-fill"></i></span>
          <div class="layer-title">
            <strong>{{ $t('MapH3.points.title') }}</strong>
            <small>{{ hasCoordinates ? $t('MapH3.points.summary') : $t('MapH3.needsCoordinates') }}</small>
          </div>
          <div class="form-check form-switch m-0">
            <input class="form-check-input" type="checkbox" role="switch" v-model="showDataPoints" :disabled="!canRenderPoints"
              :aria-label="$t('MapH3.points.title')" @change="updateVisibility()">
          </div>
        </header>
        <div v-if="showDataPoints && hasCoordinates" class="layer-body">
          <label class="field">
            <span>{{ $t('MapH3.colorBy') }}</span>
            <select class="form-select form-select-sm" v-model="selectedFieldForPoints" @change="showField('POINTS')">
              <option :value="null">{{ $t('MapH3.singleColor') }}</option>
              <option v-for="field in numericFields" :key="field" :value="field">{{ field }}</option>
            </select>
          </label>
          <MapColorScale v-if="selectedFieldForPoints" v-model:low="minValuePoints" v-model:high="maxValuePoints"
            v-model:colorLow="colorPickerPointsLow" v-model:colorHigh="colorPickerPointsHigh" :min="minPoints" :max="maxPoints"
            :histogram="percentilesPoints?.histogram" :disabled="!percentilesPoints"
            @change="changeLimits('POINTS')" @reset="resetLimits('POINTS')" />
          <label v-else class="field field-inline">
            <span>{{ $t('MapH3.color') }}</span>
            <input type="color" class="form-control form-control-color" v-model="colorPickerPointsHigh" @change="reloadLayers('POINTS')">
          </label>
          <label class="field">
            <span>{{ $t('MapH3.pointSize') }} <b>{{ pointSize }} px</b></span>
            <input type="range" class="form-range" min="1" max="10" step="1" v-model.number="pointSize" @input="changePointSize()">
          </label>
          <label class="field">
            <span>{{ $t('MapH3.opacity') }} <b>{{ Math.round(pointsOpacity * 100) }}%</b></span>
            <input type="range" class="form-range" min="0" max="1" step="0.05" v-model.number="pointsOpacity" @input="changePointsOpacity()">
          </label>
        </div>
      </section>
    </aside>

    <!-- The map, with what explains it on top -->
    <div class="geo-stage">
      <div ref="map" class="geo-map"></div>

      <div class="map-overlay map-overlay-top-left">
        <div class="segmented segmented-floating" role="group" :aria-label="$t('MapH3.basemap')">
          <button type="button" :class="{ active: basemap === 'light' }" @click="changeTile('light')"><i class="bi bi-sun"></i> {{ $t('MapH3.light') }}</button>
          <button type="button" :class="{ active: basemap === 'dark' }" @click="changeTile('dark')"><i class="bi bi-moon"></i> {{ $t('MapH3.dark') }}</button>
        </div>
      </div>

      <div class="map-overlay map-overlay-top">
        <div v-if="loading" class="map-pill"><span class="spinner-border spinner-border-sm"></span> {{ mapStatusText }}</div>
        <button v-else-if="stale" type="button" class="map-pill map-pill-action" @click="refreshVisibleLayers">
          <i class="bi bi-arrow-repeat"></i> {{ $t('MapH3.searchArea') }}
        </button>
      </div>

      <div class="map-overlay map-overlay-messages">
        <div v-if="mapError" class="map-banner map-banner-error" role="alert">
          <i class="bi bi-exclamation-triangle"></i><span>{{ mapErrorText }}</span>
        </div>
        <div v-else-if="!loading && mapLoaded && !hasLocation" class="map-banner">
          <i class="bi bi-geo-alt"></i><span>{{ $t('MapH3.noLocation') }}</span>
        </div>
        <div v-else-if="!loading && mapLoaded && !showData && !showDataPoints" class="map-banner">
          <i class="bi bi-layers"></i><span>{{ $t('MapH3.nothingOn') }}</span>
        </div>
      </div>

      <div v-if="legend.length" class="map-overlay map-overlay-bottom-left map-legend">
        <div v-for="entry in legend" :key="entry.layer" class="legend-entry">
          <span class="legend-name">{{ entry.title }}</span>
          <template v-if="entry.field">
            <span class="legend-field">{{ entry.field }}</span>
            <span class="legend-ramp" :style="{ background: `linear-gradient(90deg, ${entry.colorLow}, ${entry.colorHigh})` }"></span>
            <span class="legend-values"><span>≤ {{ formatNumber(entry.low) }}</span><span>≥ {{ formatNumber(entry.high) }}</span></span>
          </template>
          <span v-else class="legend-single"><i :style="{ background: entry.colorHigh }"></i></span>
        </div>
      </div>

      <div v-if="stats.length" class="map-overlay map-overlay-bottom-right map-stats">
        <span v-for="stat in stats" :key="stat">{{ stat }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import "mapbox-gl/dist/mapbox-gl.css";
import "maplibre-gl/dist/maplibre-gl.css";
import mapboxgl from 'mapbox-gl';
import api from '../services/api';
import { useEngine } from '../engine';
import { dataExtent, mapCells, mapGeometries, mapPoints } from '../data/maps';
import { uiType } from '../data/types';
import MapColorScale from './MapColorScale.vue';

// The average edge of an H3 hexagon, in km, by level
const H3_EDGE_KM = [1281.256, 483.056, 182.512, 68.979, 26.071, 9.8540, 3.7245, 1.4064, 0.5314, 0.2007, 0.0758, 0.0286, 0.0108, 0.0040, 0.0015, 0.0005];

const rasterStyle = (tiles, attribution, paint = {}) => ({
  version: 8,
  sources: {
    basemap: { type: 'raster', tiles: [tiles], tileSize: 256, attribution }
  },
  layers: [{ id: 'basemap', type: 'raster', source: 'basemap', paint }]
});

const OSM_TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const OSM_ATTRIBUTION = '© OpenStreetMap contributors';
const openMapStyles = {
  light: rasterStyle(OSM_TILES, OSM_ATTRIBUTION),
  // The same tiles inverted (CARTO's dark tiles now need an API key): light streets on a dark ground,
  // with the hues turned back so water stays blue
  dark: rasterStyle(OSM_TILES, OSM_ATTRIBUTION, {
    'raster-brightness-min': 0.85,
    'raster-brightness-max': 0.08,
    'raster-hue-rotate': 180,
    'raster-saturation': -0.5,
    'raster-contrast': 0.1
  })
};

export default {
  name: 'MapH3',

  props: {
    table: String,
    selectedFields: Array,
    schema: Object,
    filter: { type: String, default: '' },
  },
  components: {
    MapColorScale
  },

  data() {
    return {
      map: null,
      appliedFilter: '',
      numericFields: [],
      latitudeField: null,
      longitudeField: null,
      geomField: null,
      percentilesH3: null,
      percentilesPoints: null,
      geojson: null,
      token: null,
      h3Opacity: 0.7,
      pointsOpacity: 0.8,
      totalPoints: 0,
      colorPickerH3Low: '#ffeda0',
      colorPickerH3High: '#e31a1c',
      colorPickerPointsLow: '#c7e9b4',
      colorPickerPointsHigh: '#0d846f',
      show3D: true,
      outline: false,
      // The hexagons show as soon as there is a location: the map has something to say at once
      showData: true,
      showDataPoints: false,
      basemap: 'dark',
      // Until the user picks a cell size, it follows the zoom
      levelChosen: false,
      // The map moved since the layers were loaded: they may miss what is now in view
      stale: false,
      loadedBbox: null,
      popup: null,
      h3Level: 5,
      mapStyles: openMapStyles,
      selectedStyle: null,
      selectedFieldForH3: null,
      selectedFieldForPoints: null,
      loading: false,
      limitsSetedManually: false,
      geometadata: null,
      min: 0,
      max: 100,
      maxCount: 1,
      minValue: 0,
      maxValue: 100,
      minValuePoints: 0,
      maxValuePoints: 100,
      minPoints: 0,
      maxPoints: 100,
      limitsPointsSetedManually: false,
      pointsGeojson: null,
      pointSize: 4,
      mapError: null,
      mapLoaded: false,
      activeRequests: 0,
      h3RequestId: 0,
      pointsRequestId: 0,
      extentRequestId: 0,
      popupHandlersBound: false,

    };
  },

  computed: {
    hasCoordinates() {
      return Boolean(this.latitudeField && this.longitudeField);
    },
    hasLocation() {
      return this.hasCoordinates || Boolean(this.geomField);
    },
    canRenderH3() {
      return Boolean(this.mapLoaded && this.hasLocation);
    },
    locationKey() {
      return [this.table, this.latitudeField, this.longitudeField, this.geomField].join("|");
    },
    canRenderPoints() {
      return Boolean(this.mapLoaded && this.hasCoordinates);
    },
    mapStatusText() {
      if (!this.mapLoaded) return this.$t('MapH3.status.loadingBasemap');
      return this.$t('MapH3.status.loadingData');
    },
    // The color scale of each visible layer, for the legend on the map
    legend() {
      const entries = [];
      if (this.showData && this.geojson?.features?.length) {
        entries.push({
          layer: 'H3',
          title: this.hasCoordinates || !this.geomField ? this.$t('MapH3.h3.title') : this.$t('MapH3.h3.geomTitle'),
          field: this.selectedFieldForH3 === 'count' ? this.$t('MapH3.recordCount') : this.$t('MapH3.average', { field: this.selectedFieldForH3 }),
          low: this.minValue, high: this.maxValue,
          colorLow: this.colorPickerH3Low, colorHigh: this.colorPickerH3High,
        });
      }
      if (this.showDataPoints && this.pointsGeojson?.features?.length) {
        entries.push({
          layer: 'POINTS',
          title: this.$t('MapH3.points.title'),
          field: this.selectedFieldForPoints,
          low: this.minValuePoints, high: this.maxValuePoints,
          colorLow: this.colorPickerPointsLow, colorHigh: this.colorPickerPointsHigh,
        });
      }
      return entries;
    },
    stats() {
      const stats = [];
      if (this.showData && this.geojson) {
        const features = this.geojson.features || [];
        if (this.hasCoordinates) {
          const rows = features.reduce((sum, feature) => sum + (Number(feature.properties?.count) || 0), 0);
          stats.push(this.$t('MapH3.stats.cells', { n: this.formatNumber(features.length), rows: this.formatNumber(rows) }));
        } else {
          stats.push(this.$t('MapH3.stats.geometries', { n: this.formatNumber(features.length) }));
        }
      }
      if (this.showDataPoints && this.pointsGeojson) {
        stats.push(this.$t('MapH3.stats.points', { n: this.formatNumber(this.totalPoints) }));
      }
      if (this.showData && this.geometadata?.time != null) {
        stats.push(this.$t('MapH3.stats.time', { value: this.geometadata.time }));
      }
      return stats;
    },
    // The size of the hexagons of the chosen level
    h3SizeLabel() {
      const meters = this.h3Radix;
      return meters >= 1000
        ? this.$t('MapH3.units.km', { value: this.formatNumber(meters / 1000, meters >= 10000 ? 0 : 1) })
        : this.$t('MapH3.units.m', { value: this.formatNumber(meters, 0) });
    },
    // mapError holds either a server/Mapbox message (text) or a translation key, so the
    // message follows the language selector.
    mapErrorText() {
      if (!this.mapError) return '';
      return this.mapError.text || this.$t(this.mapError.key);
    },

    h3Radix() {
      if (this.h3Level >= 0 && this.h3Level <= 15) {
        var meters = H3_EDGE_KM[this.h3Level] * 1000;
        meters = Math.round(meters * 100) / 100;
        return meters;
      } else {
        throw new Error("Nivel H3 inválido: " + this.h3Level);
      }
    },
  },

  watch: {
    table: {
      handler(newVal, oldVal) {
        if (oldVal && newVal !== oldVal) {
          this.geojson = null;
          this.pointsGeojson = null;
          this.geometadata = null;
          this.guessLatitudeLongitude();
        }
      }
    },
    selectedFields: {
      handler() {
        this.setNumericFields();
        this.guessLatitudeLongitude();
      },
      deep: true,
      immediate: true
    },
    schema: {
      handler() {
        this.setNumericFields();
      },
      deep: true,
      immediate: true
    },
    // Another table or other location columns: show the area where their data is
    locationKey() {
      this.fitToData();
    },
    filter() {
      // Cross-filter changed: drop cached layers and reload with the new predicate.
      this.geojson = null;
      this.pointsGeojson = null;
      this.refreshVisibleLayers();
    },
    minValue(val) {
      if (Number(val) > this.maxValue) this.minValue = this.maxValue;
    },
    maxValue(val) {
      if (Number(val) < this.minValue) this.maxValue = this.minValue;
    },
    minValuePoints(val) {
      if (Number(val) > this.maxValuePoints) this.minValuePoints = this.maxValuePoints;
    },
    maxValuePoints(val) {
      if (Number(val) < this.minValuePoints) this.maxValuePoints = this.minValuePoints;
    },
  },

  ////////////////////////////
  async mounted() {
    this.selectedStyle = this.mapStyles[this.basemap];
    this.setNumericFields();
    this.guessLatitudeLongitude();
    this.token = await this.getToken();
    if (this.token) {
      this.mapStyles = {
        light: 'mapbox://styles/mapbox/light-v10',
        dark: 'mapbox://styles/mapbox/dark-v10'
      };
      this.selectedStyle = this.mapStyles[this.basemap];
    }
    await this.initMap();
  },
  beforeUnmount() {
    this.h3RequestId += 1;
    this.pointsRequestId += 1;
    this.resizeObserver?.disconnect();
    if (this.popup) this.popup.remove();
    if (this.map) this.map.remove();
    this.map = null;
  },
  activated() {
    // Kept alive across tab switches: the container was display:none while hidden,
    // so tell Mapbox to recompute its size when the Map tab becomes visible again.
    this.$nextTick(() => {
      if (this.map) this.map.resize();
      if (this.pendingFit) {
        this.pendingFit = false;
        this.fitToData();
      }
      // The cross-filter may have changed while the map was hidden (deactivated
      // components don't reliably run watchers), so reload if it no longer matches.
      if (this.filter !== this.appliedFilter) {
        this.geojson = null;
        this.pointsGeojson = null;
        this.refreshVisibleLayers();
      }
    });
  },
  methods: {
    ////////////////////////////
    setNumericFields() {
      const schema = this.schema || {};
      const selected = new Set(this.selectedFields || Object.keys(schema));
      this.numericFields = Object.keys(schema).filter((field) => {
        return selected.has(field) && uiType(schema[field]) === "numeric";
      });

      // The hexagons start colored by how many rows they hold, the points with a single color
      if (!this.numericFields.includes(this.selectedFieldForH3)) {
        this.selectedFieldForH3 = "count";
      }
      if (!this.numericFields.includes(this.selectedFieldForPoints)) {
        this.selectedFieldForPoints = null;
      }
    },
    formatNumber(value, digits = 2) {
      const number = Number(value);
      if (!Number.isFinite(number)) return "";
      return number.toLocaleString(this.$i18n?.locale, { maximumFractionDigits: digits });
    },
    ////////////////////////////
    guessLatitudeLongitude() {
      const fields = this.selectedFields || [];
      const normalized = (field) => field.toLowerCase().replace(/[^a-z0-9]/g, "");
      const findField = (exactNames, suffixes = []) => fields.find((field) => {
        const name = normalized(field);
        return exactNames.includes(name) ||
          exactNames.some((prefix) => prefix.length > 1 && name.startsWith(prefix)) ||
          suffixes.some((suffix) => name.endsWith(suffix));
      });

      if (!fields.includes(this.latitudeField)) {
        this.latitudeField = findField(["lat", "latitude", "y"], ["latitude", "lat"]) || null;
      }
      if (!fields.includes(this.longitudeField)) {
        this.longitudeField = findField(["lon", "lng", "long", "longitude", "x"],
          ["longitude", "lon", "lng"]) || null;
      }
      if (!fields.includes(this.geomField)) {
        this.geomField = findField(["geom", "geometry", "wkt"], ["geometry", "geom"]) || null;
      }
    },
    ////////////////////////////
    errorFrom(text, key) {
      return text ? { text: String(text) } : { key };
    },
    beginRequest() {
      this.activeRequests += 1;
      this.loading = true;
    },
    endRequest() {
      this.activeRequests = Math.max(0, this.activeRequests - 1);
      this.loading = this.activeRequests > 0;
    },
    async coordinatesChanged() {
      this.h3RequestId += 1;
      this.pointsRequestId += 1;
      this.geojson = null;
      this.pointsGeojson = null;
      this.geometadata = null;
      this.percentilesH3 = null;
      this.percentilesPoints = null;
      this.limitsSetedManually = false;
      this.limitsPointsSetedManually = false;
      this.mapError = null;
      if (!this.hasCoordinates) this.showDataPoints = false;
      // The layers of the previous columns go away until the new ones load
      this.applyLayerVisibility();
      await this.refreshVisibleLayers();
    },
    // Loads the visible layers for the area in view, keeping the color ranges the user chose
    async refreshVisibleLayers() {
      if (!this.hasLocation || !this.mapLoaded) return;
      this.appliedFilter = this.filter;
      if (!this.levelChosen) this.h3Level = this.levelForView();
      // One after the other: a layer with nothing in view moves the map to the data, and the next
      // one then loads that area instead of racing it
      if (this.showData) await this.reloadMap("H3", true, !this.limitsSetedManually);
      if (this.showDataPoints && this.hasCoordinates) await this.reloadMap("POINTS", true, !this.limitsPointsSetedManually);
    },
    ////////////////////////////
    async reloadMap(layer, reloadData = false, reloadLimits = false, refitted = false) {
      if (layer === "H3") {
        if (!this.canRenderH3) return;
        if (reloadData || !this.geojson) this.geojson = await this.fetchGeojsonData();
        // Nothing in the visible area: move to where the data is and ask again
        if (!this.geojson?.features?.length && !refitted && await this.fitToData()) {
          return this.reloadMap(layer, true, reloadLimits, true);
        }
        if (!this.geojson) return;
        if (reloadLimits || !this.percentilesH3) {
          this.limitsSetedManually = false;
          this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
        }
      } else if (layer === "POINTS") {
        if (!this.canRenderPoints) return;
        if (reloadData || !this.pointsGeojson) this.pointsGeojson = await this.fetchPointsData();
        if (!this.pointsGeojson?.features?.length && !refitted && await this.fitToData()) {
          return this.reloadMap(layer, true, reloadLimits, true);
        }
        if (!this.pointsGeojson) return;
        if (reloadLimits || !this.percentilesPoints) {
          this.limitsPointsSetedManually = false;
          this.setMinMaxPoints(this.pointsGeojson, this.selectedFieldForPoints);
        }
      }

      this.reloadLayers(layer);
      this.applyLayerVisibility();
    },
    ////////////////////////////
    async fetchGeojsonData() {
      const requestId = ++this.h3RequestId;
      const bbox = this.currentBbox();
      this.loadedBbox = bbox.split(",").map(Number);
      this.stale = false;
      this.beginRequest();
      this.mapError = null;

      try {
        const options = { table: this.table, fields: this.numericFields, bbox, filter: this.filter || "" };
        let response;
        if (this.latitudeField && this.longitudeField) {
          response = await mapCells(useEngine(), {
            ...options, latitudeField: this.latitudeField, longitudeField: this.longitudeField, level: Number(this.h3Level)
          });
        } else if (this.geomField) {
          response = await mapGeometries(useEngine(), { ...options, geomField: this.geomField });
        } else {
          throw new Error(this.$t("MapH3.errors.selectColumns"));
        }
        if (requestId !== this.h3RequestId) return null;
        this.geometadata = response.metadata;
        const result = response.geojson;
        if (!result?.features?.length) this.mapError = { key: "MapH3.errors.noSpatialRecords" };
        return result;
      } catch (error) {
        if (requestId !== this.h3RequestId) return null;
        this.mapError = this.errorFrom(error.message, "MapH3.errors.h3Load");
        return null;
      } finally {
        this.endRequest();
      }
    },
    // Moves the map to the area where the data is (the map opens over Spain). Returns whether it moved.
    async fitToData() {
      if (!this.map || !this.mapLoaded || !this.hasLocation) return false;
      const requestId = ++this.extentRequestId;
      try {
        const extent = await dataExtent(useEngine(), {
          table: this.table,
          latitudeField: this.hasCoordinates ? this.latitudeField : null,
          longitudeField: this.hasCoordinates ? this.longitudeField : null,
          geomField: this.geomField,
          filter: this.filter || ""
        });
        if (!extent || requestId !== this.extentRequestId) return false;
        // Hidden (another tab of the explorer): it has no size to fit to yet, so do it when shown
        if (!this.map.getContainer().offsetWidth) {
          this.pendingFit = true;
          return false;
        }
        this.map.fitBounds([[extent.west, extent.south], [extent.east, extent.north]],
          { padding: 40, maxZoom: 14, duration: 0 });
        return true;
      } catch (error) {
        // The map just stays where it is
        return false;
      }
    },
    currentBbox() {
      if (!this.map) return "-19.3,26.5,7.8,44.5";
      const bounds = this.map.getBounds();
      return [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(",");
    },
    //////////////////////
    async changeLimits(layer) {
      if (layer === 'H3') this.limitsSetedManually = true;
      else if (layer === 'POINTS') this.limitsPointsSetedManually = true;
      this.reloadLayers(layer);
    },
    // The H3 level whose hexagons look about 30 pixels wide at the current zoom
    levelForView() {
      if (!this.map) return this.h3Level;
      const latitude = this.map.getCenter().lat * Math.PI / 180;
      // MapLibre and Mapbox GL use 512-pixel tiles
      const metersPerPixel = 78271.517 * Math.cos(latitude) / Math.pow(2, this.map.getZoom());
      let best = this.h3Level;
      let bestDistance = Infinity;
      for (let level = 1; level <= 12; level++) {
        const pixels = H3_EDGE_KM[level] * 1000 / metersPerPixel;
        const distance = Math.abs(Math.log(pixels / 30));
        if (distance < bestDistance) {
          best = level;
          bestDistance = distance;
        }
      }
      return best;
    },
    async autoLevel() {
      this.levelChosen = false;
      const level = this.levelForView();
      if (level === this.h3Level) return;
      this.h3Level = level;
      await this.reloadMap('H3', true, true);
    },
    // Back to the range taken from the data
    resetLimits(layer) {
      if (layer === 'H3' && this.geojson) {
        this.limitsSetedManually = false;
        this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
      } else if (layer === 'POINTS' && this.pointsGeojson) {
        this.limitsPointsSetedManually = false;
        this.setMinMaxPoints(this.pointsGeojson, this.selectedFieldForPoints);
      }
      this.reloadLayers(layer);
    },
    ////////////////////////////
    async fetchPointsData() {
      const requestId = ++this.pointsRequestId;
      const bbox = this.currentBbox();
      this.loadedBbox = bbox.split(",").map(Number);
      this.stale = false;
      this.beginRequest();
      this.mapError = null;

      try {
        const pointsGeojson = await mapPoints(useEngine(), {
          table: this.table,
          latitudeField: this.latitudeField,
          longitudeField: this.longitudeField,
          fields: this.numericFields,
          bbox,
          filter: this.filter || ""
        });
        if (requestId !== this.pointsRequestId) return null;
        this.totalPoints = pointsGeojson?.features?.length || 0;
        if (!this.totalPoints) this.mapError = { key: "MapH3.errors.noPoints" };
        return pointsGeojson;
      } catch (error) {
        if (requestId !== this.pointsRequestId) return null;
        this.mapError = this.errorFrom(error.message, "MapH3.errors.pointsLoad");
        return null;
      } finally {
        this.endRequest();
      }
    },

    ////////////////////////////
    async getToken() {
      // Only the backend has a Mapbox token: in the browser the map uses the OSM/Carto basemaps
      if (useEngine().mode !== "remote") return null;
      try {
        const response = await api.get('/maps/mapbox_token');
        return response.data.token;
      } catch (error) {
        if (error.response?.status !== 503) {
          this.mapError = this.errorFrom(error.response?.data?.detail, "MapH3.errors.config");
        }
        return null;
      }
    },
    //////////////////////////////////////////////////
    async showField(layer) {
      await this.reloadMap(layer, false, true);
    },

    ////////////////////////////
    async initMap() {
      // Mapbox GL won't draw any map without a token: the open basemaps go through MapLibre, its
      // open-source fork with the same API
      if (this.token) {
        mapboxgl.accessToken = this.token;
        this.gl = mapboxgl;
      } else {
        this.gl = (await import('maplibre-gl')).default;
      }

      this.map = new this.gl.Map({
        container: this.$refs.map,
        style: this.selectedStyle,
        center: [-3.6844602977537817, 40.37148838867168],
        zoom: 5,
        // 3D needs a tilted map to be seen
        pitch: this.show3D ? 50 : 0
      });

      this.map.addControl(new this.gl.NavigationControl(), "top-right");
      // The map follows its box, which also changes without a window resize (the filters beside it)
      if (typeof ResizeObserver !== "undefined") {
        this.resizeObserver = new ResizeObserver(() => this.map?.resize());
        this.resizeObserver.observe(this.$refs.map);
      }
      this.map.on("load", async () => {
        this.mapLoaded = true;
        this.mapError = null;
        this.reloadLayers();
        this.addPopup();
        this.applyLayerVisibility();
        await this.fitToData();
        await this.refreshVisibleLayers();
      });
      // Layers hold only what was in view when they loaded: offer to load the new area
      this.map.on("moveend", () => {
        const loaded = (this.showData && this.geojson) || (this.showDataPoints && this.pointsGeojson);
        if (!loaded || this.loading) return;
        const [west, south, east, north] = this.currentBbox().split(",").map(Number);
        const [loadedWest, loadedSouth, loadedEast, loadedNorth] = this.loadedBbox || [];
        const outside = !this.loadedBbox || west < loadedWest || south < loadedSouth || east > loadedEast || north > loadedNorth;
        // Zooming in keeps the data, but the automatic cell size would change
        const otherLevel = this.showData && this.hasCoordinates && !this.levelChosen && this.levelForView() !== this.h3Level;
        this.stale = outside || otherLevel;
      });
      this.map.on("error", (event) => {
        this.mapError = this.errorFrom(event?.error?.message, "MapH3.errors.basemap");
      });
    },
    ////////////////////////////
    setMinMaxH3(geojson, field) {
      const percentiles = this.getPercentiles(geojson, field);
      if (!percentiles) {
        this.percentilesH3 = null;
        this.min = 0;
        this.max = 1;
        this.minValue = 0;
        this.maxValue = 1;
        this.maxCount = 1;
        return;
      }
      this.min = this.roundValue(percentiles.p0);
      this.max = this.roundValue(percentiles.p100);
      // The extremes would wash out the colors of everything else
      this.minValue = this.roundValue(percentiles.percentiles[5]);
      this.maxValue = this.roundValue(percentiles.percentiles[95]);
      this.maxCount = this.getMaxCount(geojson);
      this.percentilesH3 = percentiles;
    },
    ////////////////////////////
    setMinMaxPoints(geojson, field) {
      const percentiles = this.getPercentiles(geojson, field);
      if (!percentiles) {
        this.percentilesPoints = null;
        this.minPoints = 0;
        this.maxPoints = 1;
        this.minValuePoints = 0;
        this.maxValuePoints = 1;
        return;
      }
      this.minPoints = this.roundValue(percentiles.p0);
      this.maxPoints = this.roundValue(percentiles.p100);
      this.minValuePoints = this.roundValue(percentiles.percentiles[5]);
      this.maxValuePoints = this.roundValue(percentiles.percentiles[95]);
      this.percentilesPoints = percentiles;
    },
    roundValue(value) {
      return Math.round(Number(value) * 100) / 100;
    },
    //////////////////////
    getPercentiles(geojson, field) {
      if (!geojson?.features?.length || !field) return null;
      const values = geojson.features
        .map((feature) => feature.properties?.[field])
        .filter((value) => value !== null && value !== "")
        .map(Number)
        .filter(Number.isFinite)
        .sort((a, b) => a - b);
      if (!values.length) return null;

      const percentile = (p) => {
        const index = (p / 100) * (values.length - 1);
        const lower = Math.floor(index);
        const upper = Math.ceil(index);
        return values[lower] + (values[upper] - values[lower]) * (index - lower);
      };

      const low = values[0];
      const high = values[values.length - 1];
      const span = high - low;
      const histogram = new Array(100).fill(0);
      values.forEach((value) => {
        const index = span === 0 ? 0 : Math.min(99, Math.floor(((value - low) / span) * 100));
        histogram[index] += 1;
      });

      return {
        p0: percentile(0),
        p25: percentile(25),
        p50: percentile(50),
        p75: percentile(75),
        p100: percentile(100),
        percentiles: Array.from({ length: 100 }, (_, index) => percentile(index)),
        histogram
      };
    },
    ////////////////////////////
    getMaxCount(geojson) {
      return Math.max(1, ...geojson.features.map((feature) => Number(feature.properties?.count) || 0));
    },
    ////////////////////////////
    generateColorScale(min, max, field, layer) {
      min = Number(min);
      max = Number(max);

      // Not colored by a field: all in the high color
      if (field == null || !Number.isFinite(min) || !Number.isFinite(max)) {
        return ['literal', this.interpolateColor(1, layer)];
      }
      if (min === max) return ['literal', this.interpolateColor(0.5, layer)];

      const steps = 25;
      const colorScale = ['interpolate', ['linear'], ['get', field]];

      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const value = min + t * (max - min);
        const color = this.interpolateColor(t, layer);
        colorScale.push(value, color);
      }
      return colorScale;
    },

    ////////////////////////////
    hexToRgb(hex) {
      const bigint = parseInt(hex.slice(1), 16);
      const r = (bigint >> 16) & 255;
      const g = (bigint >> 8) & 255;
      const b = bigint & 255;
      return [r, g, b];
    },
    ////////////////////////////
    interpolateColor(t, layer) {
      let r1, g1, b1, r2, g2, b2;
      [r1, g1, b1] = this.hexToRgb(this.colorPickerH3Low);
      [r2, g2, b2] = this.hexToRgb(this.colorPickerH3High);

      if (layer === 'points') {
        [r1, g1, b1] = this.hexToRgb(this.colorPickerPointsLow);
        [r2, g2, b2] = this.hexToRgb(this.colorPickerPointsHigh);
      }

      const r = Math.round(r1 + t * (r2 - r1));
      const g = Math.round(g1 + t * (g2 - g1));
      const b = Math.round(b1 + t * (b2 - b1));

      return `rgb(${r},${g},${b})`;
    },
    ////////////////////////////
    reloadLayers(reloadLayersParam) {
      // mapLoaded follows the load and style.load events: isStyleLoaded() is still false inside
      // style.load and while tiles load, and the layers were silently skipped
      if (!this.map || !this.mapLoaded) return;
      // if ALL in reloadLayersParam or H3 in reloadLayersParam
      if (this.geojson && (!reloadLayersParam || reloadLayersParam === 'H3')) {
        // H3 Layers
        if (this.map.getLayer('h3')) {
          this.map.removeLayer('h3');
        }
        if (this.map.getLayer('outline')) {
          this.map.removeLayer('outline');
        }
        if (this.map.getSource('h3')) {
          this.map.removeSource('h3');
        }
        this.map.addSource('h3', {
          'type': 'geojson',
          'data': this.geojson
        });

        const colorScaleH3 = this.generateColorScale(this.minValue, this.maxValue, this.selectedFieldForH3, 'h3');
        // The fullest cell rises a few times its own edge, whatever the level
        const heightScaleH3 = ['interpolate', ['linear'], ['get', 'count'], 0, 0, this.maxCount, this.h3Radix * 3];
        // The points stay on top of the areas
        const beforePoints = this.map.getLayer('points') ? 'points' : undefined;

        if (this.show3D) {
          this.map.addLayer({
            'id': 'h3',
            'type': 'fill-extrusion',
            'source': 'h3',
            'layout': {},
            'paint': {
              'fill-extrusion-color': colorScaleH3,
              'fill-extrusion-height': heightScaleH3,
              'fill-extrusion-opacity': Number(this.h3Opacity)
            }
          }, beforePoints);
        } else {
          this.map.addLayer({
            'id': 'h3',
            'type': 'fill',
            'source': 'h3',
            'layout': {},
            'paint': {
              'fill-color': colorScaleH3,
              'fill-opacity': Number(this.h3Opacity)
            }
          }, beforePoints);
        }

        this.map.addLayer({
          'id': 'outline',
          'type': 'line',
          'source': 'h3',
          'layout': {
            'visibility': 'none'
          },
          'paint': {
            'line-color': '#000',
            'line-width': 1
          }
        }, beforePoints);
      }

      // Points Layer
      // Add points layer
      if (this.pointsGeojson && (!reloadLayersParam || reloadLayersParam === 'POINTS')) {
        if (this.map.getLayer('points')) {
          this.map.removeLayer('points');
        }
        if (this.map.getSource('points')) {
          this.map.removeSource('points');
        }
        this.map.addSource('points', {
          'type': 'geojson',
          'data': this.pointsGeojson
        });

        const colorScalePoints = this.generateColorScale(this.minValuePoints, this.maxValuePoints, this.selectedFieldForPoints, 'points');
        this.map.addLayer({
          'id': 'points',
          'type': 'circle',
          'source': 'points',
          'layout': {},
          'paint': {
            'circle-color': colorScalePoints,
            'circle-radius': this.pointSize,
            'circle-opacity': Number(this.pointsOpacity),
            // A white edge sets each point apart from the areas and the base map
            'circle-stroke-width': 0.6,
            'circle-stroke-color': '#ffffff',
            'circle-stroke-opacity': Number(this.pointsOpacity)
          }
        });
      }
    },
    ////////////////////////////
    escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#039;");
    },
    popupContent(title, properties) {
      const rows = Object.entries(properties || {})
        .map(([key, value]) => this.escapeHtml(key) + ": " + this.escapeHtml(value))
        .join("<br>");
      return "<strong>" + this.escapeHtml(title) + "</strong><br>" + rows;
    },
    addPopup() {
      if (this.popupHandlersBound) return;
      this.popupHandlersBound = true;
      this.popup = new this.gl.Popup({ closeButton: false, closeOnClick: false });

      const showPopup = (titleKey) => (event) => {
        const feature = event.features?.[0];
        if (!feature) return;
        this.map.getCanvas().style.cursor = "pointer";
        this.popup
          .setLngLat(event.lngLat)
          .setHTML(this.popupContent(this.$t(titleKey), feature.properties))
          .addTo(this.map);
      };
      this.map.on("mousemove", "h3", showPopup("MapH3.popup.h3"));
      this.map.on("mousemove", "points", showPopup("MapH3.popup.point"));

      const hidePopup = () => {
        this.map.getCanvas().style.cursor = "";
        this.popup.remove();
      };
      this.map.on("mouseleave", "h3", hidePopup);
      this.map.on("mouseleave", "points", hidePopup);
    },
    ////////////////////////////
    changeTile(style) {
      if (style === this.basemap) return;
      this.basemap = style;
      const styleUrl = style === 'dark' ? this.mapStyles.dark : this.mapStyles.light;
      this.selectedStyle = styleUrl;
      if (this.map) {
        this.mapLoaded = false;
        // A full reload: MapLibre diffs two style objects without firing style.load
        this.map.setStyle(styleUrl, { diff: false });
        this.map.once("style.load", () => {
          this.mapLoaded = true;
          this.reloadLayers();
          this.applyLayerVisibility();
        });
      }
    },
    ////////////////////////////
    toggleOutline() {
      this.updateVisibility();
    },
    ////////////////////////////
    toggleData() {
      this.showData = !this.showData;
      this.updateVisibility();
    },
    ////////////////////////////
    toggleDataPoints() {
      this.showDataPoints = !this.showDataPoints;
      this.updateVisibility();
    },
    ////////////////////////////
    async updateVisibility() {
      if (!this.mapLoaded) return;
      if (this.showData && !this.geojson) {
        await this.reloadMap("H3", true, true);
      }
      if (this.showDataPoints && !this.pointsGeojson && this.hasCoordinates) {
        await this.reloadMap("POINTS", true, true);
      }
      this.applyLayerVisibility();
    },
    applyLayerVisibility() {
      if (!this.map || !this.mapLoaded) return;
      if (this.map.getLayer("h3")) {
        this.map.setLayoutProperty("h3", "visibility", this.showData && this.geojson ? "visible" : "none");
      }
      if (this.map.getLayer("outline")) {
        this.map.setLayoutProperty("outline", "visibility", this.showData && this.geojson && this.outline ? "visible" : "none");
      }
      if (this.map.getLayer("points")) {
        this.map.setLayoutProperty("points", "visibility", this.showDataPoints && this.pointsGeojson ? "visible" : "none");
      }
    },
    ////////////////////////////
    changeH3Opacity() {
      if (!this.map?.getLayer("h3")) return;
      const property = this.show3D ? "fill-extrusion-opacity" : "fill-opacity";
      this.map.setPaintProperty("h3", property, Number(this.h3Opacity));
    },
    ////////////////////////////
    changePointSize() {
      if (!this.map?.getLayer("points")) return;
      this.map.setPaintProperty("points", "circle-radius", Number(this.pointSize));
    },
    // 3D needs a tilted map to be seen
    setShow3D(value) {
      this.show3D = value;
      this.reloadLayers('H3');
      this.applyLayerVisibility();
      this.map?.easeTo({ pitch: value ? 50 : 0, duration: 600 });
    },
    ////////////////////////////
    changePointsOpacity() {
      if (!this.map?.getLayer("points")) return;
      this.map.setPaintProperty("points", "circle-opacity", Number(this.pointsOpacity));
      this.map.setPaintProperty("points", "circle-stroke-opacity", Number(this.pointsOpacity));
    },
    ////////////////////////////
  }
};
</script>

<style scoped>
.geo { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 12px; height: max(560px, calc(100vh - 230px)); padding: 0 14px 14px; }

/* Controls */
.geo-panel > * { flex-shrink: 0; }
.geo-panel { display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow-y: auto; padding-right: 2px; }
.geo-section, .layer-card { border: 1px solid var(--ds-line); border-radius: 12px; background: var(--ds-surface); }
.geo-section { padding: 12px; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.section-head h5 { margin: 0; font-size: 13px; font-weight: 750; }
.section-head h5 i { color: var(--ds-teal); }
.section-ok { color: var(--ds-teal-dark); font-size: 11px; font-weight: 700; }
.field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.field { display: grid; gap: 4px; margin: 0; }
.field-wide { grid-column: 1 / -1; }
.field > span { display: flex; justify-content: space-between; gap: 6px; color: var(--ds-muted); font-size: 11px; font-weight: 700; }
.field > span small { font-weight: 500; }
.field > span b { color: var(--ds-ink); font-weight: 700; font-variant-numeric: tabular-nums; }
.field-inline { grid-template-columns: 1fr auto; align-items: center; }
.field .form-select { font-size: 12px; }
.field .form-range { height: 1rem; }
.resolution-value { display: inline-flex; align-items: center; gap: 6px; }
.chip { padding: 0 7px; border: 1px solid var(--ds-line); border-radius: 999px; background: #fff; color: var(--ds-muted); font-size: 10px; font-weight: 700; line-height: 16px; }
.chip.active { border-color: var(--ds-teal); background: var(--ds-mint); color: var(--ds-teal-dark); }
.field .form-range::-webkit-slider-thumb { background: var(--ds-teal); }
.field .form-range::-moz-range-thumb { background: var(--ds-teal); }
.range-ends { display: flex; justify-content: space-between; margin-top: -4px; color: #98a5a1; font-size: 10px; }
.field-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.field-row .form-check-label { color: var(--ds-muted); font-size: 12px; font-weight: 700; }

.layer-card { overflow: hidden; transition: border-color .15s, box-shadow .15s; }
.layer-card.on { border-color: #9ccfc1; box-shadow: 0 6px 18px rgba(13, 132, 111, .08); }
.layer-card.off .layer-head { opacity: .6; }
.layer-head { display: grid; grid-template-columns: 32px 1fr auto; align-items: center; gap: 10px; padding: 11px 12px; }
.layer-icon { display: grid; place-items: center; width: 32px; height: 32px; border-radius: 9px; font-size: 14px; }
.layer-icon-h3 { background: #fff1e6; color: #e8590c; }
.layer-icon-points { background: var(--ds-mint); color: var(--ds-teal); font-size: 9px; }
.layer-title { display: grid; min-width: 0; }
.layer-title strong { font-size: 13px; font-weight: 750; }
.layer-title small { overflow: hidden; color: var(--ds-muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.layer-head .form-check-input { width: 2.2em; height: 1.2em; cursor: pointer; }
.layer-head .form-check-input:checked { border-color: var(--ds-teal); background-color: var(--ds-teal); }
.layer-body { display: grid; gap: 12px; padding: 12px; border-top: 1px solid var(--ds-line); background: var(--ds-surface-muted); }

.segmented { display: inline-flex; padding: 2px; border: 1px solid var(--ds-line); border-radius: 8px; background: #fff; }
.segmented button { padding: 3px 10px; border: 0; border-radius: 6px; background: transparent; color: var(--ds-muted); font-size: 12px; font-weight: 700; }
.segmented button.active { background: var(--ds-teal); color: #fff; }

/* Map */
.geo-stage { position: relative; min-height: 0; overflow: hidden; border: 1px solid var(--ds-line); border-radius: 12px; background: #e9eeec; }
.geo-map { position: absolute; inset: 0; }
.map-overlay { position: absolute; z-index: 2; pointer-events: none; }
.map-overlay > * { pointer-events: auto; }
.map-overlay-top-left { top: 10px; left: 10px; }
.map-overlay-top { top: 10px; left: 50%; transform: translateX(-50%); }
/* Below the base map switch and clear of the zoom buttons */
.map-overlay-messages { top: 54px; left: 10px; right: 52px; display: grid; justify-items: start; }
.map-overlay-messages .map-banner { max-width: 440px; }
.map-overlay-bottom-left { bottom: 28px; left: 10px; }
.map-overlay-bottom-right { right: 10px; bottom: 28px; }
.segmented-floating { box-shadow: 0 4px 14px rgba(23, 33, 31, .14); }
.map-pill { display: inline-flex; align-items: center; gap: 7px; padding: 7px 14px; border: 0; border-radius: 999px; background: #fff; box-shadow: 0 4px 14px rgba(23, 33, 31, .18); color: var(--ds-ink); font-size: 12px; font-weight: 700; }
.map-pill .spinner-border { width: 14px; height: 14px; border-width: 2px; color: var(--ds-teal); }
.map-pill-action { background: var(--ds-teal); color: #fff; }
.map-pill-action:hover { background: var(--ds-teal-dark); }
.map-banner { display: flex; align-items: center; gap: 8px; padding: 9px 12px; border: 1px solid var(--ds-line); border-radius: 10px; background: rgba(255, 255, 255, .95); box-shadow: 0 4px 14px rgba(23, 33, 31, .12); color: var(--ds-ink-soft); font-size: 12px; }
.map-banner i { color: var(--ds-teal); }
.map-banner-error { border-color: #efc9cd; background: #fff4f5; color: #a9404d; }
.map-banner-error i { color: inherit; }
.map-legend { display: grid; gap: 10px; min-width: 190px; max-width: 240px; padding: 10px 12px; border-radius: 10px; background: rgba(255, 255, 255, .95); box-shadow: 0 4px 14px rgba(23, 33, 31, .14); }
.legend-entry { display: grid; gap: 3px; }
.legend-name { color: var(--ds-muted); font-size: 10px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; }
.legend-field { overflow: hidden; font-size: 12px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.legend-ramp { height: 8px; border-radius: 4px; }
.legend-values { display: flex; justify-content: space-between; color: var(--ds-muted); font-size: 11px; font-variant-numeric: tabular-nums; }
.legend-single i { display: inline-block; width: 12px; height: 12px; border-radius: 50%; }
.map-stats { display: flex; gap: 10px; padding: 5px 10px; border-radius: 999px; background: rgba(23, 33, 31, .78); color: #fff; font-size: 11px; font-variant-numeric: tabular-nums; }

@media (max-width: 900px) {
  .geo { grid-template-columns: 1fr; height: auto; }
  .geo-panel { overflow: visible; }
  /* The map first: the controls follow it */
  .geo-stage { order: -1; height: 60vh; min-height: 380px; }
}
</style>
