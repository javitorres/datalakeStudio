<template>
  <div class="map-h3-shell">
    <section class="map-setup-card">
      <div>
        <span class="map-kicker">Map setup</span>
        <h4>Choose the location columns</h4>
        <p>{{ mapStatusText }}</p>
      </div>
      <button class="map-refresh" :disabled="!hasLocation || loading || !mapLoaded" @click="refreshVisibleLayers">
        <i class="bi bi-arrow-clockwise"></i> Refresh visible area
      </button>
    </section>
    <div v-if="mapError" class="map-message map-message-error" role="alert">
      <i class="bi bi-exclamation-triangle"></i><span>{{ mapError }}</span>
    </div>
    <div v-else-if="!hasLocation" class="map-message">
      <i class="bi bi-geo-alt"></i><span>Select latitude and longitude, or a geometry column, to enable map layers.</span>
    </div>
    <!-- General controls  -->
    <div class="row">
      <div class="col-2">
        <!-- Tile dark or light button -->
        <div class="col-2">
          <div class="btn-group" role="group" aria-label="Basic radio toggle button group">
            <input type="radio" class="btn-check" name="btnradio" id="btnradio1" autocomplete="off">
            <label class="btn btn-outline-primary" for="btnradio1" @click="changeTile('dark')">Dark</label>
            <input type="radio" class="btn-check" name="btnradio" id="btnradio2" autocomplete="off" checked>
            <label class="btn btn-outline-primary" for="btnradio2" @click="changeTile('light')">Light</label>
          </div>
        </div>
      </div>

      <div class="col-3">
        <!-- Selectors for latitude, longitude and geom fields -->
        <div v-if="selectedFields" class="input-group">
          <span class="input-group-text">Latitude</span>
          <select class="form-select" v-model="latitudeField" @change="coordinatesChanged">
            <option :value="null">Select latitude</option>
            <option v-for="field in selectedFields" :key="field" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>

      <div class="col-3">
        <div v-if="selectedFields" class="input-group">
          <span class="input-group-text">Longitude</span>
          <select class="form-select" v-model="longitudeField" @change="coordinatesChanged">
            <option :value="null">Select longitude</option>
            <option v-for="field in selectedFields" :key="field" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>

      <div class="col-3">
        <div v-if="selectedFields" class="input-group">
          <span class="input-group-text">Geom</span>
          <select class="form-select" v-model="geomField" @change="coordinatesChanged">
            <option :value="null">No geometry column</option>
            <option v-for="field in selectedFields" :key="field" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>

    </div>
    <hr /><br />

    <!-- H3 Layer  controls  -->
    <div class="row">
      <div class="col-5">
        <div class="form-check form-switch">
          <label class="form-check-label">H3 Data / Geom</label>
          <input class="form-check-input" type="checkbox" v-model="showData" :disabled="!canRenderH3 || loading" @change="updateVisibility()">
        </div>
        <br />
        <!-- Selector del campo a mostrar (de selectedFields) -->
        <div class="input-group">
          <span class="input-group-text">Show field</span>
          <select class="form-select" v-model="selectedFieldForH3" @change="showField('H3')">
            <option value="count">Record count</option>
            <option v-for="field in numericFields" :key="field" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>
      <!-- Show data toggle -->

      <!-- Selector for H3 level, from 1 to 10 -->
      <div class="col-2">
        <div class="row">
          <div class="input-group">
            <span class="input-group-text">H3 Level</span>
            <select class="form-select" v-model="h3Level" @change="reloadMap('H3', true, true)">
              <option v-for="i in 12" :key="i" :value="i">{{ i }}</option>
            </select>
          </div>
        </div>
        <br />

        <div class="row">
          <!-- H3 Opacity -->
          <div class="col-6">
            <label for="customRange1" class="form-label">Opacity {{ h3Opacity }}</label>
          </div>
          <div class="col-6">
            <input type="range" class="form-range" min="0" max="1" step="0.05" v-model="h3Opacity"
              @change="changeH3Opacity()">
          </div>
        </div>
        <br />

        <div class="row">
          <div class="col-6">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" v-model="outline" @change="toggleOutline()">
              <label class="form-check-label">Lines</label>
            </div>
          </div>

          <!-- Disable 3D -->
          <div class="col-6">
            <div class="col-3">
              <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" v-model="show3D" @change="reloadLayers()">
                <label class="form-check-label">3D</label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Editor for min and max values in H3 map-->
      <div class="col-5">
        <div class="row">
          <div class="col-3">
            <div class="input-group">
              <span class="input-group-text">Low</span>
              <input type="color" class="form-control form-control-color" id="exampleColorInput"
                v-model="colorPickerH3Low" title="Choose your color" @change="reloadLayers('H3')">
            </div>
          </div>
          <div class="col-6"></div>
          <div class="col-3">
            <div class="input-group">
              <input type="color" class="form-control form-control-color" id="exampleColorInput"
                v-model="colorPickerH3High" title="Choose your color" @change="reloadLayers('H3')">
              <span class="input-group-text">High</span>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col-12">
            <div class="range-container">
              <div class="range-track"></div>
              <div class="range-highlight" :style="highlightStyle(minValue, maxValue, min, max)"></div>
              <input type="range" class="form-range" v-model="minValue" :min="min" :max="max"
                @change="changeLimits('H3')">
              <input type="range" class="form-range" v-model="maxValue" :min="min" :max="max"
                @change="changeLimits('H3')">
            </div>
            <div class="value-display">
              <span>Absolute Min<br />{{ min }}</span>
              <span>Selected Min<br />{{ minValue }}</span>
              <span>Selected Max<br />{{ maxValue }}</span>
              <span>Absolute Max<br />{{ max }}</span>
            </div>
          </div>

          <div v-if="percentilesH3">

            <DataSelector :values="percentilesH3.percentiles" :count="percentilesH3.histogram">

            </DataSelector>
          </div>
        </div>
        <!-- Blue button if limits are seted manually , gray if not -->
        <!--
        <button class="btn m-1 opcion-style" :class="limitsSetedManually ? 'btn-primary' : 'btn-secondary'"
          @click="reloadH3Map(false, true)">Refresh
        </button>
        -->
      </div>
    </div> <!-- End of H3 map controls -->

    <hr /><br />

    <!-- Points control  -->
    <div class="row">
      <div class="col-5">
        <div class="form-check form-switch">
          <label class="form-check-label">Points</label>
          <input class="form-check-input" type="checkbox" v-model="showDataPoints" :disabled="!canRenderPoints || loading" @change="updateVisibility()">
        </div>
        <br />

        <!-- Selector del campo a mostrar (de selectedFields) -->
        <div class="input-group" v-if="showDataPoints">
          <span class="input-group-text">Show field</span>
          <select class="form-select" v-model="selectedFieldForPoints" @change="showField('POINTS')">
            <option v-for="field in numericFields" :key="field" :value="field">{{ field }}</option>
          </select>
        </div>

      </div>


      <div class="col-2">
        <div class="row">
          <!-- Bar seelctor for point size -->
          <div class="input-group">
            <span class="input-group-text">Point size</span>
            <select class="form-select" v-model="pointSize" @change="reloadMap('POINTS', false)">
              <option v-for="i in 10" :key="i" :value="i">{{ i }}</option>
            </select>
          </div>
        </div>
        <br />

        <!-- Points Opacity -->
        <div class="row">
          <div class="col-6">
            <label for="customRange1" class="form-label">Opacity {{ pointsOpacity }}</label>
          </div>

          <div class="col-6">
            <input type="range" class="form-range" min="0" max="1" step="0.05" v-model="pointsOpacity"
              @change="changePointsOpacity()">
          </div>
        </div>
      </div>

      <!-- Editor for min and max POINT values -->
      <div class="col-5">
        <div class="row">
          <div class="col-3">
            <div class="input-group">
              <span class="input-group-text">Low</span>
              <input type="color" class="form-control form-control-color" id="exampleColorInput"
                v-model="colorPickerPointsLow" title="Choose your color" @change="reloadLayers('POINTS')">
            </div>
          </div>
          <div class="col-6"></div>
          <div class="col-3">
            <div class="input-group">

              <input type="color" class="form-control form-control-color" id="exampleColorInput"
                v-model="colorPickerPointsHigh" title="Choose your color" @change="reloadLayers('POINTS')">
              <span class="input-group-text">High</span>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col-12">
            <div class="range-container">
              <div class="range-track"></div>
              <div class="range-highlight" :style="highlightStyle(minValuePoints, maxValuePoints, minPoints, maxPoints)"></div>
              <input type="range" class="form-range" v-model="minValuePoints" :min="minPoints" :max="maxPoints"
                @change="changeLimits('POINTS')">
              <input type="range" class="form-range" v-model="maxValuePoints" :min="minPoints" :max="maxPoints"
                @change="changeLimits('POINTS')">
            </div>
            <div class="value-display">
              <span>Absolute Min<br />{{ minPoints }}</span>
              <span>Selected Min<br /> {{ minValuePoints }}</span>
              <span>Selected Max<br /> {{ maxValuePoints }}</span>
              <span>Absolute Max<br />{{ maxPoints }}</span>
            </div>
            <!--<button class="btn m-1 opcion-style" :class="limitsPointsSetedManually ? 'btn-primary' : 'btn-secondary'"
          @click="reloadPointsMap(false, true)">Refresh
        </button>
        -->
          </div>
        </div>
      </div>
    </div>
  </div> <!-- End of points controls -->

  <br />
  <div v-if="loading" class="loading-overlay">
    <div class="spinner"></div>
  </div>

  <div class="row">
    <div class="col-12">
      <div id="map" style="height: 620px; width: 100%"></div>
    </div>
  </div>
  <br />

  <div class="row">
    <div class="col-6">
      <div v-if="geometadata" class="alert alert-light" role="alert">
        <strong><b>H3 Layer</b></strong><br>
        <strong>Records:</strong> {{ geometadata.records }}<br>
        <strong>Dataframe Size:</strong> {{ geometadata.dfsize }} Mb<br>
        <strong>Payload Size:</strong> {{ geometadata.objectSize }} Mb<br>
        <strong>Time:</strong> {{ geometadata.time }} seconds<br>
        <strong>H3 Radix:</strong> {{ h3Radix }} meters<br>
      </div>
    </div>

    <div class="col-6">
      <div v-if="geometadata" class="alert alert-light" role="alert">
        <strong><b>Points Layer</b></strong><br>
        <strong>Points:</strong> {{ totalPoints }}<br>

      </div>
    </div>
  </div>

</template>

<script>
import "mapbox-gl/dist/mapbox-gl.css";
import mapboxgl from 'mapbox-gl';
import api from '../services/api';
import { toast } from 'vue3-toastify';
import qs from 'qs';
import csv2geojson from 'csv2geojson';
import DataSelector from './DataSelector.vue';

const rasterStyle = (tiles, attribution) => ({
  version: 8,
  sources: {
    basemap: { type: 'raster', tiles: [tiles], tileSize: 256, attribution }
  },
  layers: [{ id: 'basemap', type: 'raster', source: 'basemap' }]
});

const openMapStyles = {
  light: rasterStyle(
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    '© OpenStreetMap contributors'
  ),
  dark: rasterStyle(
    'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    '© OpenStreetMap contributors © CARTO'
  )
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
    DataSelector
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
      geojson: null,
      token: null,
      h3Opacity: 0.5,
      pointsOpacity: 0.5,
      totalPoints: 0,
      colorPickerH3Low: '#0000ff',
      colorPickerH3High: '#ff0000',
      colorPickerPointsLow: '#000000',
      colorPickerPointsHigh: '#00ff00',
      show3D: true,
      outline: false,
      showData: false,
      showDataPoints: false,
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
      csvData: null,
      pointsGeojson: null,
      pointSize: 5,
      mapError: null,
      mapLoaded: false,
      activeRequests: 0,
      h3RequestId: 0,
      pointsRequestId: 0,
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
    canRenderPoints() {
      return Boolean(this.mapLoaded && this.hasCoordinates);
    },
    mapStatusText() {
      if (!this.mapLoaded) return 'Loading the base map…';
      if (this.loading) return 'Loading data for the visible map area…';
      if (!this.token) return this.hasLocation
        ? 'Using the open basemap. Enable H3 or points to display data.'
        : 'Using the open basemap; select location columns to continue.';
      if (!this.hasLocation) return 'The coordinate columns could not be detected automatically.';
      if (this.showData || this.showDataPoints) return 'Move the map and refresh to query the current visible area.';
      return 'Coordinates are ready. Enable H3 or points to display data.';
    },

    h3Radix() {
      const h3RadixValues = [1281.256, 483.056, 182.512, 68.979, 26.071, 9.8540, 3.7245, 1.4064, 0.5314, 0.2007, 0.0758, 0.0286, 0.0108, 0.0040, 0.0015, 0.0005];

      if (this.h3Level >= 0 && this.h3Level <= 15) {
        var meters = h3RadixValues[this.h3Level] * 1000;
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
    this.selectedStyle = this.mapStyles.light;
    this.setNumericFields();
    this.guessLatitudeLongitude();
    this.token = await this.getToken();
    if (this.token) {
      this.mapStyles = {
        light: 'mapbox://styles/mapbox/light-v10',
        dark: 'mapbox://styles/mapbox/dark-v10'
      };
      this.selectedStyle = this.mapStyles.light;
    }
    this.initMap();
  },
  beforeUnmount() {
    this.h3RequestId += 1;
    this.pointsRequestId += 1;
    if (this.popup) this.popup.remove();
    if (this.map) this.map.remove();
    this.map = null;
  },
  activated() {
    // Kept alive across tab switches: the container was display:none while hidden,
    // so tell Mapbox to recompute its size when the Map tab becomes visible again.
    this.$nextTick(() => {
      if (this.map) this.map.resize();
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
        const type = String(schema[field] || "");
        return selected.has(field) && /(int|float|double|decimal|numeric|real)/i.test(type);
      });

      if (!this.selectedFieldForH3 ||
          (this.selectedFieldForH3 !== "count" && !this.numericFields.includes(this.selectedFieldForH3))) {
        this.selectedFieldForH3 = this.numericFields[0] || "count";
      }
      if (!this.numericFields.includes(this.selectedFieldForPoints)) {
        this.selectedFieldForPoints = this.numericFields[0] || null;
      }
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
    highlightStyle(minValue, maxValue, min, max) {
      const range = Number(max) - Number(min);
      if (!Number.isFinite(range) || range <= 0) return { left: "0%", width: "100%" };
      const minPercent = Math.max(0, Math.min(100, ((Number(minValue) - Number(min)) / range) * 100));
      const maxPercent = Math.max(minPercent, Math.min(100, ((Number(maxValue) - Number(min)) / range) * 100));
      return { left: minPercent + "%", width: (maxPercent - minPercent) + "%" };
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
      this.mapError = null;
      if (!this.hasCoordinates) this.showDataPoints = false;
      await this.refreshVisibleLayers();
    },
    async refreshVisibleLayers() {
      if (!this.hasLocation || !this.mapLoaded) return;
      this.appliedFilter = this.filter;
      const tasks = [];
      if (this.showData) tasks.push(this.reloadMap("H3", true, true));
      if (this.showDataPoints && this.hasCoordinates) tasks.push(this.reloadMap("POINTS", true, true));
      await Promise.all(tasks);
    },
    ////////////////////////////
    async reloadMap(layer, reloadData = false, reloadLimits = false) {
      if (layer === "H3") {
        if (!this.canRenderH3) return;
        if (reloadData || !this.geojson) this.geojson = await this.fetchGeojsonData();
        if (!this.geojson) return;
        if (reloadLimits || !this.percentilesH3) {
          this.limitsSetedManually = false;
          this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
        }
      } else if (layer === "POINTS") {
        if (!this.canRenderPoints) return;
        if (reloadData || !this.pointsGeojson) this.pointsGeojson = await this.fetchPointsData();
        if (!this.pointsGeojson) return;
        if (reloadLimits) {
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
      this.beginRequest();
      this.mapError = null;

      try {
        const response = await api.get("/maps/geojson", {
          params: {
            table: this.table,
            latitudeField: this.latitudeField || "",
            longitudeField: this.longitudeField || "",
            geomField: this.geomField || "",
            fields: this.numericFields,
            level: Number(this.h3Level),
            bbox,
            filter: this.filter || ""
          },
          paramsSerializer: params => qs.stringify(params, { arrayFormat: "comma" })
        });
        if (requestId !== this.h3RequestId) return null;
        this.geometadata = response.data.metadata;
        const result = response.data.geojson;
        if (!result?.features?.length) this.mapError = "No spatial records were found in the visible area.";
        return result;
      } catch (error) {
        if (requestId !== this.h3RequestId) return null;
        this.mapError = error.response?.data?.detail || "The H3 layer could not be loaded.";
        toast.error(this.mapError);
        return null;
      } finally {
        this.endRequest();
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
    ////////////////////////////
    async fetchPointsData() {
      const requestId = ++this.pointsRequestId;
      this.beginRequest();
      this.mapError = null;

      try {
        const response = await api.get("/maps/csv", {
          params: {
            table: this.table,
            latitudeField: this.latitudeField,
            longitudeField: this.longitudeField,
            fields: this.numericFields,
            bbox: this.currentBbox(),
            filter: this.filter || ""
          },
          paramsSerializer: params => qs.stringify(params, { arrayFormat: "comma" })
        });
        if (requestId !== this.pointsRequestId) return null;

        this.csvData = response.data;
        const pointsGeojson = await new Promise((resolve, reject) => {
          csv2geojson.csv2geojson(response.data, {
            latfield: "latitude",
            lonfield: "longitude",
            delimiter: ",",
            numericFields: this.numericFields.join(",")
          }, (error, data) => error ? reject(error) : resolve(data));
        });
        if (requestId !== this.pointsRequestId) return null;
        this.totalPoints = pointsGeojson?.features?.length || 0;
        if (!this.totalPoints) this.mapError = "No points were found in the visible area.";
        return pointsGeojson;
      } catch (error) {
        if (requestId !== this.pointsRequestId) return null;
        this.mapError = error.response?.data?.detail || "The point layer could not be loaded.";
        toast.error(this.mapError);
        return null;
      } finally {
        this.endRequest();
      }
    },

    ////////////////////////////
    async getToken() {
      try {
        const response = await api.get('/maps/mapbox_token');
        return response.data.token;
      } catch (error) {
        if (error.response?.status !== 503) {
          this.mapError = error.response?.data?.detail || "Map configuration could not be loaded.";
        }
        return null;
      }
    },
    //////////////////////////////////////////////////
    async showField(layer) {
      await this.reloadMap(layer, false, true);
    },

    ////////////////////////////
    initMap() {
      mapboxgl.accessToken = this.token || '';

      this.map = new mapboxgl.Map({
        container: 'map',
        style: this.selectedStyle,
        center: [-3.6844602977537817, 40.37148838867168],
        zoom: 5
      });

      this.map.addControl(new mapboxgl.NavigationControl(), "top-right");
      this.map.on("load", () => {
        this.mapLoaded = true;
        this.mapError = null;
        this.reloadLayers();
        this.addPopup();
        this.applyLayerVisibility();
      });
      this.map.on("error", (event) => {
        this.mapError = event?.error?.message || "The base map could not be loaded.";
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
      this.minValue = this.roundValue(percentiles.p25);
      this.maxValue = this.roundValue(percentiles.p75);
      this.maxCount = this.getMaxCount(geojson);
      this.percentilesH3 = percentiles;
    },
    ////////////////////////////
    setMinMaxPoints(geojson, field) {
      const percentiles = this.getPercentiles(geojson, field);
      if (!percentiles) {
        this.minPoints = 0;
        this.maxPoints = 1;
        this.minValuePoints = 0;
        this.maxValuePoints = 1;
        return;
      }
      this.minPoints = this.roundValue(percentiles.p0);
      this.maxPoints = this.roundValue(percentiles.p100);
      this.minValuePoints = this.roundValue(percentiles.p25);
      this.maxValuePoints = this.roundValue(percentiles.p75);
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

      if (field == null || !Number.isFinite(min) || !Number.isFinite(max)) {
        return ['literal', '#FF0000'];
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
      if (!this.map || !this.mapLoaded || !this.map.isStyleLoaded()) return;
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
        const heightScaleH3 = ['interpolate', ['linear'], ['get', 'count'], 0, 0, this.maxCount, 500000];

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
          });
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
          });
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
        });
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
            'circle-opacity': Number(this.pointsOpacity)
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
      this.popup = new mapboxgl.Popup({ closeButton: false, closeOnClick: false });

      const showPopup = (title) => (event) => {
        const feature = event.features?.[0];
        if (!feature) return;
        this.map.getCanvas().style.cursor = "pointer";
        this.popup
          .setLngLat(event.lngLat)
          .setHTML(this.popupContent(title, feature.properties))
          .addTo(this.map);
      };
      this.map.on("mousemove", "h3", showPopup("H3 properties"));
      this.map.on("mousemove", "points", showPopup("Point properties"));

      const hidePopup = () => {
        this.map.getCanvas().style.cursor = "";
        this.popup.remove();
      };
      this.map.on("mouseleave", "h3", hidePopup);
      this.map.on("mouseleave", "points", hidePopup);
    },
    ////////////////////////////
    changeTile(style) {
      const styleUrl = style === 'dark' ? this.mapStyles.dark : this.mapStyles.light;
      this.selectedStyle = styleUrl;
      if (this.map) {
        this.mapLoaded = false;
        this.map.setStyle(styleUrl);
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
      if (!this.map || !this.mapLoaded || !this.map.isStyleLoaded()) return;
      if (this.map.getLayer("h3")) {
        this.map.setLayoutProperty("h3", "visibility", this.showData ? "visible" : "none");
      }
      if (this.map.getLayer("outline")) {
        this.map.setLayoutProperty("outline", "visibility", this.showData && this.outline ? "visible" : "none");
      }
      if (this.map.getLayer("points")) {
        this.map.setLayoutProperty("points", "visibility", this.showDataPoints ? "visible" : "none");
      }
    },
    ////////////////////////////
    changeH3Opacity() {
      if (!this.map?.getLayer("h3")) return;
      const property = this.show3D ? "fill-extrusion-opacity" : "fill-opacity";
      this.map.setPaintProperty("h3", property, Number(this.h3Opacity));
    },
    ////////////////////////////
    changePointsOpacity() {
      if (!this.map?.getLayer("points")) return;
      this.map.setPaintProperty("points", "circle-opacity", Number(this.pointsOpacity));
    },
    ////////////////////////////
  }
};
</script>

<style scoped>
#map {
  height: 100%;
  width: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  border: 16px solid #f3f3f3;
  border-top: 16px solid #3498db;
  border-radius: 50%;
  width: 120px;
  height: 120px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.range-container {
  position: relative;
  width: 100%;
}

.range-track {
  position: absolute;
  height: 5px;
  background-color: #ccc;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  width: 100%;
  z-index: 1;
}

.range-highlight {
  position: absolute;
  height: 5px;
  background-color: #007bff;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
}

input[type="range"] {
  position: relative;
  z-index: 3;
  width: 100%;
  background: transparent;
}

.value-display {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}


.map-h3-shell{position:relative;padding:0 14px 14px;background:#fff}
.map-setup-card{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 10px;padding:13px 14px;border:1px solid var(--ds-line);border-radius:11px;background:linear-gradient(120deg,#f8fbfa,#edf7f4)}.map-kicker{color:#81908b;font-size:7px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.map-setup-card h4{margin:2px 0;font-size:.86rem;font-weight:760}.map-setup-card p{margin:0;color:#788681;font-size:8px}.map-refresh{display:flex;align-items:center;gap:6px;padding:7px 10px;border:1px solid #9bcbbc;border-radius:7px;background:#fff;color:var(--ds-teal-dark);font-size:8px;font-weight:750}.map-refresh:disabled{cursor:not-allowed;opacity:.45}.map-message{display:flex;align-items:center;gap:7px;margin:8px 0;padding:8px 10px;border:1px solid #d9e5e1;border-radius:8px;background:#f6faf8;color:#64746f;font-size:8px}.map-message-error{border-color:#efc9cd;background:#fff4f5;color:#a9404d}
.map-h3-shell>div>.row,.map-h3-shell>.row{margin:10px 0;padding:13px;border:1px solid var(--ds-line);border-radius:11px;background:#f8faf9}
.map-h3-shell hr{margin:14px 0;border-color:var(--ds-line);opacity:1}.map-h3-shell .input-group-text{font-size:9px}.map-h3-shell .form-select,.map-h3-shell .form-control{font-size:10px}.map-h3-shell .form-check-label,.map-h3-shell .form-label{color:#53635f;font-size:9px;font-weight:700}
.map-h3-shell #map{overflow:hidden;border:1px solid var(--ds-line);border-radius:12px;box-shadow:0 8px 25px rgba(28,62,53,.08)}
.loading-overlay{background:rgba(244,249,247,.82);backdrop-filter:blur(4px)}.spinner{width:58px;height:58px;border:6px solid #dce9e5;border-top-color:var(--ds-teal);animation:spin .8s linear infinite}
.range-track{background:#d5e1dd}.range-highlight{background:var(--ds-teal)}.value-display{color:#778581;font-size:8px}
@media(max-width:900px){.map-h3-shell .row>[class*=col-]{width:100%;margin-bottom:10px}}
</style>
