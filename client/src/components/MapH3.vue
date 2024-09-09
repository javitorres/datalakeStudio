<template>


  <div>
    <!--<button class="btn m-1 opcion-style btn-primary" @click="renderChart()">Render chart</button>-->
    <div id="chart"></div>
    <br />
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
          <select class="form-select" v-model="latitudeField">
            <option v-for="field in selectedFields" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>

      <div class="col-3">
        <div v-if="selectedFields" class="input-group">
          <span class="input-group-text">Longitude</span>
          <select class="form-select" v-model="longitudeField">
            <option v-for="field in selectedFields" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>

      <div class="col-3">
        <div v-if="selectedFields" class="input-group">
          <span class="input-group-text">Geom</span>
          <select class="form-select" v-model="geomField">
            <option v-for="field in selectedFields" :value="field">{{ field }}</option>
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
          <input class="form-check-input" type="checkbox" v-model="showData" @change="updateVisibility()">
        </div>
        <br />
        <!-- Selector del campo a mostrar (de selectedFields) -->
        <div class="input-group">
          <span class="input-group-text">Show field</span>
          <select class="form-select" v-model="selectedFieldForH3" @change="showField('H3')">
            <option v-for="field in numericFields" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>
      <!-- Show data toggle -->

      <!-- Selector for H3 level, from 1 to 10 -->
      <div class="col-2">
        <div class="row">
          <div class="input-group">
            <span class="input-group-text">H3 Level</span>
            <select class="form-select" v-model="h3Level" @change="reloadMap('H3', true)">
              <option v-for="i in 12" :value="i">{{ i }}</option>
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
              <div class="range-highlight" :style="highlightStyle(minValue, maxValue, max)"></div>
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
          <input class="form-check-input" type="checkbox" v-model="showDataPoints" @change="updateVisibility()">
        </div>
        <br />

        <!-- Selector del campo a mostrar (de selectedFields) -->
        <div class="input-group" v-if="showDataPoints">
          <span class="input-group-text">Show field</span>
          <select class="form-select" v-model="selectedFieldForPoints" @change="showField('POINTS')">
            <option v-for="field in numericFields" :value="field">{{ field }}</option>
          </select>
        </div>

      </div>


      <div class="col-2">
        <div class="row">
          <!-- Bar seelctor for point size -->
          <div class="input-group">
            <span class="input-group-text">Point size</span>
            <select class="form-select" v-model="pointSize" @change="reloadMap('POINTS', false)">
              <option v-for="i in 10" :value="i">{{ i }}</option>
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
              <div class="range-highlight" :style="highlightStyle(minValuePoints, maxValuePoints, maxPoints)"></div>
              <input type="range" class="form-range" v-model="minValuePoints" :min="minPoints" :max="maxPoints"
                @change="changeLimitPoints(geojson)">
              <input type="range" class="form-range" v-model="maxValuePoints" :min="minPoints" :max="maxPoints"
                @change="changeLimitPoints(geojson)">
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
      <div id="map" style="height: 800px; width: 100%"></div>
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
import axios from 'axios';
import { toast } from 'vue3-toastify';
import qs from 'qs';
import csv2geojson, { csv } from 'csv2geojson';
import * as vg from "@uwdata/vgplot";
import DataSelector from './DataSelector.vue';

export default {
  name: 'MapH3',

  props: {
    table: String,
    selectedFields: Array,
    schema: Object,
  },
  components: {
    DataSelector
  },

  data() {
    return {
      map: null,
      numericFields: [],
      latitudeField: null,
      longitudeField: null,
      geomField: null,
      percentilesH3: null,
      sourceId: 'vector-tiles-source',
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
      mapStyles: {
        light: 'mapbox://styles/mapbox/light-v10',
        dark: 'mapbox://styles/mapbox/dark-v10'
      },
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
      chartInstance: null,

    };
  },

  computed: {

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
      async handler(newVal, oldVal) {
        if (oldVal) {
          this.geojson = await this.fetchGeojsonData();
          this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
          this.reloadMap('H3');
        }
      },
      immediate: true
    },
    selectedFields: {
      async handler(newVal, oldVal) {
        await this.reloadMap('H3');
      },
      deep: true,
      immediate: true
    },
    schema: {
      async handler(newVal, oldVal) {
        this.setNumericFields();
      },
      deep: true,
      immediate: true
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
    this.token = await this.getToken();

    if (this.token) {
      this.guessLatitudeLongitude();
    }

    this.renderChart();
  },
  methods: {
    ////////////////////////////
    setNumericFields() {
      var n = Object.keys(this.schema).filter(key => this.schema[key].startsWith('int') || this.schema[key].startsWith('float'));
      this.numericFields = n;
    },
    ////////////////////////////
    guessLatitudeLongitude() {
      if (this.selectedFields) {
        const latFields = this.selectedFields.filter(field => field.toLowerCase().includes('lat'));
        const lonFields = this.selectedFields.filter(field => field.toLowerCase().includes('lon'));
        const geomFields = this.selectedFields.filter(field => field.toLowerCase().includes('geom'));

        if (latFields && latFields.length > 0) {
          this.latitudeField = latFields[0];
        }

        if (lonFields && lonFields.length > 0) {
          this.longitudeField = lonFields[0];
        }

        if (geomFields && geomFields.length > 0) {
          this.geomField = geomFields[0];
        }
      }
    },
    ////////////////////////////
    highlightStyle(minValue, maxValue, max) {
      const minPercent = (Number(minValue) / max) * 100;
      const maxPercent = (Number(maxValue) / max) * 100;
      var result = {
        left: minPercent + '%',
        width: (maxPercent - minPercent) + '%'
      }
      return result;
    },
    ////////////////////////////
    async reloadMap(layer, reloadData = false, reloadLimits = false) {
      console.log("Reloading map for layer: " + layer);
      if (layer === 'H3') {
        if (reloadData) this.geojson = await this.fetchGeojsonData();
        if (this.geojson && reloadLimits) {
          this.limitsSetedManually = false;
          this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
        }
      } else if (layer === 'POINTS') {
        if (reloadData) this.pointsGeojson = await this.fetchPointsData();
        if (this.pointsGeojson && reloadLimits) {
          this.limitsPointsSetedManually = false;
          this.setMinMaxPoints(this.pointsGeojson, this.selectedFieldForPoints);
        }

        this.reloadLayers(layer);
        this.updateVisibility();
      }
    },
    ////////////////////////////
    async fetchGeojsonData() {
      var bbox = "-19.3,26.5,7.8,44.5";
      if (this.map) {
        const bounds = this.map.getBounds();
        bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(',');
      }

      this.loading = true;

      try {
        const response = await axios.get(`http://localhost:8000/maps/geojson`, {
          params: {
            table: this.table,
            latitudeField: this.latitudeField,
            longitudeField: this.longitudeField,
            geomField: this.geomField,
            fields: this.numericFields,
            level: this.h3Level,
            bbox: bbox,
          },
          paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'comma' });
          },
        });
        this.geometadata = response.data.metadata;

        return response.data.geojson;
      } catch (error) {
        toast.error(`Error: HTTP ${error.response ? error.response.status : error.message}`);
        console.log("Error fetching geojson data:" + error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    //////////////////////
    async changeLimits(layer) {
      if (layer === 'H3') this.limitsSetedManually = true;
      else if (layer === 'POINTS') this.limitsPointsSetedManually = true;
      this.reloadLayers(layer);
    },
    ////////////////////////////
    async fetchPointsData() {
      var bbox = "-19.3,26.5,7.8,44.5";
      if (this.map) {
        const bounds = this.map.getBounds();
        bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(',');
      }

      this.loading = true;

      try {
        const response = await axios.get(`http://localhost:8000/maps/csv`, {
          params: {
            table: this.table,
            latitudeField: this.latitudeField,
            longitudeField: this.longitudeField,
            fields: this.numericFields,
            bbox: bbox,
          },
          paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'comma' });
          },
        });

        this.csvData = response.data;
        const pointsGeojson = await new Promise((resolve, reject) => {
          // Get number of records in the response
          this.totalPoints = response.data.split(/\r\n|\r|\n/).length - 2;

          csv2geojson.csv2geojson(response.data, {
            latfield: 'latitude',
            lonfield: 'longitude',
            delimiter: ',',
            // comma separated list of fields in this.numericFields to include in properties
            numericFields: this.numericFields.join(','),
          }, function (err, data) {
            if (err) {
              console.log("Error:", err);
              reject(err);
            } else {
              resolve(data);
            }
          });
        });

        if (!pointsGeojson || !pointsGeojson.features || pointsGeojson.features.length === 0) {
          console.log("################ pointsGeojson is null or has no features");
        } else {
          return pointsGeojson;
        }
      } catch (error) {
        toast.error(`Error: HTTP ${error.response ? error.response.status : error.message}`);
        console.log("Error fetching points data:" + error);
        return null;
      } finally {
        this.loading = false;
      }
    },

    ////////////////////////////
    async getToken() {
      try {
        const response = await axios.get('http://localhost:8000/maps/mapbox_token');
        return response.data.token;
      } catch (error) {
        toast.error(`Error retrieving token: ${error.response?.data?.message || error.response?.data || error.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        return null;
      }
    },
    //////////////////////////////////////////////////
    async showField(layer) {
      await this.reloadMap(layer, false, true);
    },

    ////////////////////////////
    initMap() {
      console.log("Initializing map");
      mapboxgl.accessToken = this.token;

      this.map = new mapboxgl.Map({
        container: 'map',
        style: this.selectedStyle,
        center: [-3.6844602977537817, 40.37148838867168],
        zoom: 5
      });

      this.map.on('load', () => {
        this.reloadLayers();
        this.addPopup();
        //this.updateVisibility();
      });
    },
    ////////////////////////////
    setMinMaxH3(geojson, field) {
      this.min = 1;
      this.max = -1;
      this.maxCount = -1;
      if (geojson === null) {
        console.log("setMinMaxH3: geojson is null");
        return;
      }
      var percentiles = this.getPercentiles(geojson, field);
      this.min = Math.round(percentiles.p0, 2);
      this.max = Math.round(percentiles.p100, 2);
      this.minValue = Math.round(percentiles.p25, 2);
      this.maxValue = Math.round(percentiles.p75, 2);
      this.maxCount = this.getMaxCount(geojson, field);
      this.percentilesH3 = percentiles;

      this.changeLimits('H3');
    },
    ////////////////////////////
    setMinMaxPoints(geojson, field) {
      this.minPoints = 1;
      this.maxPoints = -1;

      var percentiles = this.getPercentiles(geojson, field);
      this.minPoints = Math.round(percentiles.p0, 2);
      this.maxPoints = Math.round(percentiles.p100, 2);
      this.minValuePoints = Math.round(percentiles.p25, 2);
      this.maxValuePoints = Math.round(percentiles.p75, 2);

      this.changeLimits('POINTS');
    },
    //////////////////////
    getPercentiles(geojson, field) {
      let values = [];

      geojson.features.forEach(feature => {
        const value = feature.properties[field];
        if (!isNaN(value)) {
          values.push(value);
        }
      });

      values.sort((a, b) => a - b);

      const getPercentile = (arr, p) => {
        const index = (p / 100) * (arr.length - 1);
        const lower = Math.floor(index);
        const upper = Math.ceil(index);
        const weight = index - lower;
        return arr[lower] * (1 - weight) + arr[upper] * weight;
      };

      // Build histogram, where each position has the number of elements in the range
      let histogram = new Array(100).fill(0);

      values.forEach(value => {
        const percentile = getPercentile(values, value);
        const index = Math.floor((percentile / getPercentile(values, 100)) * 100);
        histogram[index] += 1;
      });
      // Save percentiles 0 to 99 in an array
      var allPercentiles = [];
      for (let i = 0; i < 100; i++) {
        allPercentiles.push(getPercentile(values, i));
      }

      let percentiles = {
        p0: getPercentile(values, 0),
        p25: getPercentile(values, 25),
        p50: getPercentile(values, 50),
        p75: getPercentile(values, 75),
        p100: getPercentile(values, 100),
        percentiles: allPercentiles,
        histogram: histogram
      };

      return percentiles;
    },
    ////////////////////////////
    getMaxCount(geojson, field) {
      var maxCount = -1;
      geojson.features.forEach(feature => {
        const value = feature.properties[field];
        if (feature.properties.count > maxCount) {
          maxCount = feature.properties.count;
        }
      });

      return maxCount;
    },
    ////////////////////////////
    generateColorScale(min, max, field, layer) {
      min = Number(min);
      max = Number(max);

      if (field == null) {
        console.log("generateColorScale: field or layer is None");
        return ['literal', '#FF0000'];
      }

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
      if (this.map === null) {
        console.log("Map is null. Cannot reload layers");
        return;
      }
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
              'fill-extrusion-opacity': 0.5
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
            'line-width': Number(this.pointsOpacity)
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
            'circle-opacity': 0.5
          }
        });
      }
    },
    ////////////////////////////
    addPopup() {
      // Initialize the popup
      this.popup = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: false
      });

      this.map.on('mousemove', 'h3', (e) => {
        this.map.getCanvas().style.cursor = 'pointer';
        const coordinates = e.lngLat;
        const properties = e.features[0].properties;

        this.popup
          .setLngLat(coordinates)
          .setHTML(`<strong>H3 Properties:</strong><br>${Object.keys(properties).map(key => `${key}: ${properties[key]}`).join('<br>')}`)
          .addTo(this.map);
      });

      // Pop up of points layer
      this.map.on('mousemove', 'points', (e) => {
        this.map.getCanvas().style.cursor = 'pointer';
        const coordinates = e.lngLat;
        const properties = e.features[0].properties;

        this.popup
          .setLngLat(coordinates)
          .setHTML(`<strong>Point Properties:</strong><br>${Object.keys(properties).map(key => `${key}: ${properties[key]}`).join('<br>')}`)
          .addTo(this.map);
      });

      this.map.on('mouseleave', 'h3', () => {
        this.map.getCanvas().style.cursor = '';
        this.popup.remove();
      });
      this.map.on('mouseleave', 'points', () => {
        this.map.getCanvas().style.cursor = '';
        this.popup.remove();
      });
    },
    ////////////////////////////
    changeTile(style) {
      const styleUrl = style === 'dark' ? this.mapStyles.dark : this.mapStyles.light;
      this.selectedStyle = styleUrl;
      if (this.map) {
        this.map.setStyle(styleUrl);
        this.map.once('styledata', () => {
          this.reloadLayers();  // Vuelve a cargar todas las capas personalizadas
          this.addPopup();  // Vuelve a agregar los popups
          this.updateVisibility();  // Actualiza la visibilidad de las capas
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
      if (this.showData && !this.geojson) {
        this.geojson = await this.fetchGeojsonData();
        //this.selectedFieldForH3 = this.numericFields[0];
      }

      if (this.showDataPoints && !this.pointsGeojson) {
        this.pointsGeojson = await this.fetchPointsData();
        //this.selectedFieldForPoints = this.numericFields[0];
      }

      if (!this.map) {
        await this.initMap();
      }

      if (this.map.getLayer('outline')) {
        if (!this.geojson) {
          this.geojson = await this.fetchGeojsonData();
          this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
          this.reloadLayers('H3');
        }
        if (this.outline) {
          this.map.setLayoutProperty('outline', 'visibility', 'visible');
        } else {
          this.map.setLayoutProperty('outline', 'visibility', 'none');
        }
      }


      if (this.map.getLayer('h3')) {
        if (this.showData) {
          if (!this.geojson) {
            this.geojson = await this.fetchGeojsonData();
            this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
            this.reloadLayers('H3');
          }
          this.map.setLayoutProperty('h3', 'visibility', 'visible');
        } else {
          this.map.setLayoutProperty('h3', 'visibility', 'none');
        }
      }

      if (this.map.getLayer('points')) {
        if (this.showDataPoints) {
          if (!this.pointsGeojson) {
            //this.reloadMapPoints(true);
            this.pointsGeojson = await this.fetchPointsData();
            this.setMinMaxPoints(this.pointsGeojson, this.selectedFieldForPoints);
            this.reloadLayers('POINTS');
          }
          this.map.setLayoutProperty('points', 'visibility', 'visible');
        } else {
          this.map.setLayoutProperty('points', 'visibility', 'none');
        }
      }
    },
    ////////////////////////////
    changeH3Opacity() {
      this.map.setPaintProperty('h3', 'fill-extrusion-opacity', Number(this.h3Opacity));
    },
    ////////////////////////////
    changePointsOpacity() {
      this.map.setPaintProperty('points', 'circle-opacity', Number(this.pointsOpacity));
    },
    ////////////////////////////
    convertCsvToJson(csvString) {
      const lines = csvString.split('\n');
      const headers = lines[0].split(',');

      return lines.slice(1).map(line => {
        const values = line.split(',');
        const obj = {};
        headers.forEach((header, index) => {
          obj[header] = values[index];
        });
        return obj;
      });
    },

    ////////////////////////////
    async renderChart() {
      if (this.csvData === null) {
        console.log("CSV data is null. Cannot render chart");
        return;
      }

      console.log(this.csvData.split(/\r\n|\r|\n/).slice(0, 3));
      const jsonData = this.convertCsvToJson(this.csvData);
      const data = vg.from(jsonData); 
      this.chartInstance = vg.plot(
        vg.lineY(
          vg.from("aapl"),
          { x: "longitud", y: "AskingPriceVenta" }
        ),
        vg.width(680),
        vg.height(200)
      );

      document.getElementById("chart").appendChild(this.chartInstance);
    },
  }
};
</script>

<style scoped>
#map {
  height: 100%;
  width: 100%;
}

.loading-overlay {
  position: fixed;
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

#chart {
  margin-top: 20px;
}
</style>
