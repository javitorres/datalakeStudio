<template>
  <div>
    <br />
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
      <div class="col-5">
        <!-- Selectors for latitude and longitude fields -->
        <div class="input-group">
          <span class="input-group-text">Latitude</span>
          <select class="form-select" v-model="latitudeField">
            <option v-for="field in selectedFields" :value="field">{{ field }}</option>
          </select>

          <span class="input-group-text">Longitude</span>
          <select class="form-select" v-model="longitudeField">
            <option v-for="field in selectedFields" :value="field">{{ field }}</option>
          </select>

        </div>
      </div>
    </div>
    <br />

    <!-- H3 Layer  controls  -->
    <div class="row">
      <div class="col-1">
        <div v-if="geometadata" class="alert alert-light" role="alert">
          <strong>H3 Layer</strong>
        </div>
      </div>

      <!-- Selector del campo a mostrar (de selectedFields) -->
      <div class="col-3">
        <div class="input-group">
          <span class="input-group-text">Show field</span>
          <select class="form-select" v-model="selectedFieldForH3" @change="showFieldInMap()">
            <option v-for="field in numericFields" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>

      <!-- Show data toggle -->
      <div class="col-1">
        <label class="btn btn-outline-primary" @click="toggleData()">{{ showData ? "Hide Data" : "Show data" }}</label>
      </div>
      <!-- Show lines toggle -->
      <div class="col-1">
        <label class="btn btn-outline-primary" @click="toggleOutline()">{{ outline ? "Hide Lines" : "Show lines"
          }}</label>
      </div>


      <!-- Selector for H3 level, from 1 to 10 -->
      <div class="col-2">
        <select class="form-select" v-model="h3Level" @change="reloadH3Map(true)">
          <option v-for="i in 12" :value="i">H3 level {{ i }}</option>
        </select>
      </div>

      <!-- Editor for min and max values in H3 map-->
      <div class="col-3">
        <div class="range-container">
          <div class="range-track"></div>
          <div class="range-highlight" :style="highlightStyle(minValue, maxValue, max)"></div>
          <input type="range" class="form-range" v-model="minValue" :min="min" :max="max"
            @change="changeLimitsH3(geojson)">
          <input type="range" class="form-range" v-model="maxValue" :min="min" :max="max"
            @change="changeLimitsH3(geojson)">
        </div>
        <div class="value-display">
          <span>{{ min }}</span>
          <span>Min {{ minValue }}</span>
          <span>Max {{ maxValue }}</span>
          <span>{{ max }}</span>
        </div>
        <!-- Blue button if limits are seted manually , gray if not -->
        <button class="btn m-1 opcion-style" :class="limitsSetedManually ? 'btn-primary' : 'btn-secondary'"
          @click="reloadH3Map(false, true)">Refresh
        </button>
      </div>
    </div> <!-- End of map controls -->

    <!-- Points control  -->
    <div class="row">
      <div class="col-1">
        <div v-if="geometadata" class="alert alert-light" role="alert">
          <strong>Points</strong>
        </div>
      </div>
      <!-- Selector del campo a mostrar (de selectedFields) -->
      <div class="col-3">
        <div class="input-group">
          <span class="input-group-text">Show field</span>
          <select class="form-select" v-model="selectedFieldForPoints" @change="showFieldInPoints()">
            <option v-for="field in numericFields" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>

      <!-- Show data toggle -->
      <div class="col-1">
        <label class="btn btn-outline-primary" @click="toggleDataPoints()">{{ showDataPoints ? "Hide points" : "Show points"
          }}</label>
      </div>

      <div class="col-3">
        <!-- Bar seelctor for point size -->
        <div class="input-group">
          <span class="input-group-text">Point size</span>
          <select class="form-select" v-model="pointSize" @change="reloadPointsMap(false)">
            <option v-for="i in 10" :value="i">{{ i }}</option>
          </select>
        </div>

      </div>

      <!-- Editor for min and max POINT values -->
      <div class="col-3">
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
        <button class="btn m-1 opcion-style" :class="limitsPointsSetedManually ? 'btn-primary' : 'btn-secondary'"
          @click="reloadPointsMap(false, true)">Refresh
        </button>
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

  <div class="row">
    <div class="col-6">
      <div v-if="geometadata" class="alert alert-light" role="alert">
        <strong>Records:</strong> {{ geometadata.records }}<br>
        <strong>Dataframe Size:</strong> {{ geometadata.dfsize }} Mb<br>
        <strong>Payload Size:</strong> {{ geometadata.objectSize }} Mb<br>
        <strong>Time:</strong> {{ geometadata.time }} seconds
        <strong>Radix:</strong> {{ h3Radix }} meters<br>
      </div>
    </div>

    <div class="col-6">
      <div v-if="geometadata" class="alert alert-light" role="alert">
        
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
import csv2geojson from 'csv2geojson';


export default {
  name: 'MapComponent',
  data() {
    return {
      map: null,
      latitudeField: null,
      longitudeField: null,
      sourceId: 'vector-tiles-source',
      geojson: null,
      token: null,
      outline: true,
      showData: true,
      showDataPoints: false,
      popup: null,
      h3Level: 5,
      mapStyles: {
        light: 'mapbox://styles/mapbox/light-v10',
        dark: 'mapbox://styles/mapbox/dark-v10'
      },
      selectedFieldForH3: null,
      selectedFieldForPoints: null,
      loading: false,
      limitsSetedManually: false,
      geometadata: null,
      min: 0,
      max: 100,
      minValue: 0,
      maxValue: 100,
      minValuePoints: 0,
      maxValuePoints: 100,
      minPoints: 0,
      maxPoints: 100,
      limitsPointsSetedManually: false,
      pointsGeojson: null,
      pointSize: 5,

    };
  },

  computed: {
    numericFields() {
      var n = Object.keys(this.schema).filter(key => this.schema[key] === 'int64' || this.schema[key] === 'float64');
      return n;
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

  props: {
    table: String,
    selectedFields: Array,
    schema: Object,
  },

  watch: {
    selectedFields: {
      handler: 'reloadH3Map',
      deep: true
    },
    minValue(val) {
      val = Number(val);
      if (val > this.maxValue) {
        console.log("minValue (" + val + ") > maxValue (" + this.maxValue + ")");
        this.minValue = this.maxValue;
      }
    },
    maxValue(val) {
      val = Number(val);
      if (val < this.minValue) {
        console.log("maxValue (" + val + ") < minValue (" + this.minValue + ")");
        this.maxValue = this.minValue;
      }
    },
    minValuePoints(val) {
      val = Number(val);
      if (val > this.maxValuePoints) {
        console.log("minValuePoints (" + val + ") > maxValuePoints (" + this.maxValuePoints + ")");
        this.minValuePoints = this.maxValuePoints;
      }
    },
    maxValuePoints(val) {
      val = Number(val);
      if (val < this.minValuePoints) {
        console.log("maxValuePoints (" + val + ") < minValuePoints (" + this.minValuePoints + ")");
        this.maxValuePoints = this.minValuePoints;
      }
    },
  },



  ////////////////////////////
  async mounted() {
    this.token = await this.getToken();
    if (!this.selectedFieldForH3) {
      this.selectedFieldForH3 = this.numericFields[0];
    }
    if (!this.selectedFieldForPoints) {
      this.selectedFieldForPoints = this.numericFields[0];
    }

    if (this.token) {
      this.guessLatitudeLongitude();
      if (this.latitudeField && this.longitudeField) {
        this.geojson = await this.fetchGeojsonData();
        this.pointsGeojson = await this.fetchPointsData();
        this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
        this.setMinMaxPoints(this.pointsGeojson, this.selectedFieldForPoints);
        this.initMap(this.geojson);
      }
    }

  },
  methods: {

    ////////////////////////////
    guessLatitudeLongitude() {
      if (this.selectedFields) {
        const latFields = this.selectedFields.filter(field => field.toLowerCase().includes('lat'));
        const lonFields = this.selectedFields.filter(field => field.toLowerCase().includes('lon'));

        if (latFields.length > 0) {
          this.latitudeField = latFields[0];
        }

        if (lonFields.length > 0) {
          this.longitudeField = lonFields[0];
        }
      }
    },
    
    highlightStyle(minValue, maxValue, max) {
      //console.log("minValue: " + minValue + " maxValue: " + maxValue);
      minValue = Number(minValue);
      maxValue = Number(maxValue);
      const minPercent = (minValue / max) * 100;
      const maxPercent = (maxValue / max) * 100;
      var result = {
        left: minPercent + '%',
        width: (maxPercent - minPercent) + '%'
      }
      //console.log("highlightStyle for minValue "+ minValue +" and maxValue "+ maxValue +":" + JSON.stringify(result));
      return result;
    },
    ////////////////////////////
    async reloadH3Map(reloadData = false, reloadLimits = false) {
      if (reloadData) {
        this.geojson = await this.fetchGeojsonData();
      }
      if (!this.geojson) {
        return;
      }

      if (reloadLimits) {
        this.limitsSetedManually = false;
        this.setMinMaxH3(this.geojson, this.selectedFieldForH3);
      }
      this.reloadLayers('H3');
      this.updateVisibility();
    },
    ////////////////////////////
    async reloadPointsMap(reloadData = false, reloadLimits = false) {
      if (reloadData) {
        this.pointsGeojson = await this.fetchPointsData();
      }
      if (!this.geojson) {
        return;
      }

      if (reloadLimits) {
        this.limitsPointsSetedManually = false;
        this.setMinMaxPoints(this.pointsGeojson, this.selectedFieldForPoints);
      }
      this.reloadLayers('POINTS');
      this.updateVisibility();
    },
    ////////////////////////////
    async fetchGeojsonData() {
      var bbox = "-19.3,26.5,7.8,44.5";
      if (this.map) {
        const bounds = this.map.getBounds();
        bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(',');
      }

      this.loading = true; // Asegúrate de que `loading` se establezca en true antes de la solicitud

      try {
        const response = await axios.get(`http://localhost:8000/maps/geojson`, {
          params: {
            table: this.table,
            fields: this.numericFields,
            level: this.h3Level,
            bbox: bbox,
          },
          paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'comma' });
          },
        });
        this.geometadata = response.data.metadata;

        return response.data.geojson; // Devuelve los datos obtenidos
      } catch (error) {
        toast.error(`Error: HTTP ${error.response ? error.response.status : error.message}`);
        return null; // Devuelve null en caso de error
      } finally {
        this.loading = false; // Asegúrate de que `loading` se establezca en false después de la solicitud
      }
    },
    //////////////////////
    async changeLimitsH3() {
      this.limitsSetedManually = true;
      this.reloadLayers('H3');
    },

    //////////////////////
    async changeLimitPoints() {
      this.limitsPointsSetedManually = true;
      this.reloadLayers('POINTS');
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

        //console.log("fetchPointsData:" + response.data);

        const pointsGeojson = await new Promise((resolve, reject) => {
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
              //console.log("GeoJSON data:", JSON.stringify(data));
              resolve(data);
            }
          });
        });

        if (!pointsGeojson || !pointsGeojson.features || pointsGeojson.features.length === 0) {
          console.log("################ pointsGeojson is null or has no features");
        } else {
          //console.log("POINTS:" + JSON.stringify(pointsGeojson.features.slice(0, 5)));
          return pointsGeojson;
        }
      } catch (error) {
        toast.error(`Error: HTTP ${error.response ? error.response.status : error.message}`);
        console.log("Error fetching points data:" + error);
        return null;
      } finally {
        this.loading = false;
      }
    }
    ,

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
    async showFieldInMap() {
      //console.log("Showing field " + this.showField + " in map");
      await this.reloadH3Map(false, true);
    },
    //////////////////////////////////////////////////
    async showFieldInPoints() {
      //console.log("Showing field " + this.showField + " in map");
      await this.reloadPointsMap(false, true);
    },
    ////////////////////////////
    initMap(geojson) {
      mapboxgl.accessToken = this.token;

      this.map = new mapboxgl.Map({
        container: 'map',
        style: this.mapStyles.light,
        center: [-3.6844602977537817, 40.37148838867168],
        zoom: 5
      });

      this.map.on('load', () => {
        this.reloadLayers('ALL');
        this.addPopup();
      });

      /*this.map.on('style.load', () => {
        this.reloadLayers();
        this.addPopup();
      });*/
    },
    ////////////////////////////
    setMinMaxH3(geojson, field) {
      this.min = 1;
      this.max = -1;
      if (geojson === null) {
        console.log("setMinMaxH3: geojson is null");
        return;
      }
      geojson.features.forEach(feature => {
        const value = feature.properties[field];
        if (!isNaN(value)) {
          if (value < this.min) this.min = value;
          if (value > this.max) this.max = value;
        }
      });

      if (this.min === this.max || this.min > this.max) {
        this.max = this.min + 1;
      }
      this.min = Math.round(this.min * 100) / 100;
      this.max = Math.round(this.max * 100) / 100;
      this.minValue = this.min;
      this.maxValue = this.max;
      //console.log("setMinMaxH3: field:" + field + " min " + this.min + " max " + this.max);
    },
    ////////////////////////////
    setMinMaxPoints(geojson, field) {
      this.minPoints = 1;
      this.maxPoints = -1;

      geojson.features.forEach(feature => {
        const value = feature.properties[field];
        if (!isNaN(value)) {
          if (value < this.minPoints) this.minPoints = value;
          if (value > this.maxPoints) this.maxPoints = value;
        } 
      });

      if (this.minPoints === this.maxPoints || this.minPoints > this.maxPoints) {
        this.maxPoints = this.minPoints + 1;
      }
      this.minPoints = Math.round(this.minPoints * 100) / 100;
      this.maxPoints = Math.round(this.maxPoints * 100) / 100;
      this.minValuePoints = this.minPoints;
      this.maxValuePoints = this.maxPoints;
      //console.log("setMinMaxPoints: field:" + field + " min " + this.minPoints + " max " + this.maxPoints);
    },
    ////////////////////////////
    generateColorScaleForH3(min, max) {
      //console.log("Generating color scale for field " + this.selectedFieldForH3 + " with min " + min + " and max " + max);
      min = Number(min);
      max = Number(max);

      if (!this.selectedFieldForH3) this.selectedFieldForH3 = this.numericFields[0];

      const steps = 25;
      const colorScale = ['interpolate', ['linear'], ['get', this.selectedFieldForH3]];

      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const value = min + t * (max - min);
        const color = this.interpolateColor(t);
        colorScale.push(value, color);
      }
      //console.log("Colorscale for H3: " + colorScale);
      return colorScale;
    },
    ////////////////////////////
    generateColorScaleForPoints(min, max) {
      //console.log("Generating color scale for field " + this.selectedFieldForPoints + " with min " + min + " and max " + max);
      min = Number(min);
      max = Number(max);
      if (!this.selectedFieldForPoints) this.selectedFieldForPoints = this.numericFields[0];

      const steps = 25;
      const colorScale = ['interpolate', ['linear'], ['get', this.selectedFieldForPoints]];

      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const value = min + t * (max - min);
        const color = this.interpolateColor(t);
        colorScale.push(value, color);
      }
      //console.log("Colorscale for points (" + min + "-" + max + "): " + colorScale);
      return colorScale;
    },
    ////////////////////////////
    interpolateColor(t) {
      const r1 = 0, g1 = 0, b1 = 255; // Azul
      const r2 = 255, g2 = 0, b2 = 0; // Rojo

      const r = Math.round(r1 + t * (r2 - r1));
      const g = Math.round(g1 + t * (g2 - g1));
      const b = Math.round(b1 + t * (b2 - b1));

      return `rgb(${r},${g},${b})`;
    },
    ////////////////////////////
    reloadLayers(reloadLayersParam) {
      // if ALL in reloadLayersParam or H3 in reloadLayersParam
      if (!reloadLayersParam || reloadLayersParam === 'ALL' || reloadLayersParam === 'H3') {


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

        const colorScaleH3 = this.generateColorScaleForH3(this.minValue, this.maxValue);

        this.map.addLayer({
          'id': 'h3',
          'type': 'fill',
          'source': 'h3',
          'layout': {},
          'paint': {
            'fill-color': colorScaleH3,
            'fill-opacity': 0.5
          }
        });

        this.map.addLayer({
          'id': 'outline',
          'type': 'line',
          'source': 'h3',
          'layout': {},
          'paint': {
            'line-color': '#000',
            'line-width': 0.5
          }
        });
      }

      // Points Layer
      // Add points layer
      if (!reloadLayersParam || reloadLayersParam === 'ALL' || reloadLayersParam === 'POINTS') {
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


        const colorScalePoints = this.generateColorScaleForPoints(this.minValuePoints, this.maxValuePoints);
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
      this.map.setStyle(styleUrl);
    },
    ////////////////////////////
    toggleOutline() {
      this.outline = !this.outline;
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
    updateVisibility() {
      if (this.outline) {
        this.map.setLayoutProperty('outline', 'visibility', 'visible');
      } else {
        this.map.setLayoutProperty('outline', 'visibility', 'none');
      }

      if (this.showData) {
        this.map.setLayoutProperty('h3', 'visibility', 'visible');
      } else {
        this.map.setLayoutProperty('h3', 'visibility', 'none');
      }

      if (this.showDataPoints) {
        if ( ! this.pointsGeojson) {
          this.reloadMapPoints(true);
        }

        this.map.setLayoutProperty('points', 'visibility', 'visible');
      } else {
        this.map.setLayoutProperty('points', 'visibility', 'none');
      }
    }
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
</style>
