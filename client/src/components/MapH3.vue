<template>
  <div>

    <br />
    <div class="row">
      <!-- Selector del campo a mostrar (de selectedFields) -->
      <div class="col-3">
        <div class="input-group">
          <span class="input-group-text">Show field</span>
          <select class="form-select" v-model="showField" @change="showFieldInMap()">
            <option v-for="field in numericFields" :value="field">{{ field }}</option>
          </select>
        </div>
      </div>


      <!-- Tile dark or light button -->
      <div class="col-2">
        <div class="btn-group" role="group" aria-label="Basic radio toggle button group">
          <input type="radio" class="btn-check" name="btnradio" id="btnradio1" autocomplete="off">
          <label class="btn btn-outline-primary" for="btnradio1" @click="changeTile('dark')">Dark</label>

          <input type="radio" class="btn-check" name="btnradio" id="btnradio2" autocomplete="off" checked>
          <label class="btn btn-outline-primary" for="btnradio2" @click="changeTile('light')">Light</label>
        </div>
      </div>

      <!-- Show lines toggle -->
      <div class="col-1">
        <label class="btn btn-outline-primary" @click="toggleOutline()">{{ outline ? "Hide Lines" : "Show lines"
          }}</label>
      </div>
      <!-- Show data toggle -->
      <div class="col-1">
        <label class="btn btn-outline-primary" @click="toggleData()">{{ showData ? "Hide Data" : "Show data" }}</label>
      </div>


      <!-- Selector for H3 level, from 1 to 10 -->
      <div class="col-2">
        <select class="form-select" v-model="h3Level" @change="reloadMap(true)">
          <option v-for="i in 12" :value="i">H3 level {{ i }}</option>
        </select>
      </div>

      <!-- Editor for min and max values -->
      <div class="col-3">
        <div class="input-group">
          <span class="input-group-text">Min</span>
          <input type="number" class="form-control" v-model="minMaxAggField.min" @change="changeLimits(geojson)">
          <span class="input-group-text">Max</span>
          <input type="number" class="form-control" v-model="minMaxAggField.max" @change="changeLimits(geojson)">
          <!-- Reset button -->

          <button class="btn m-1 opcion-style" :class="limitsSetedManually ? 'btn-primary' : 'btn-secondary'"
            @click="reloadMap(false, true)">Refresh</button>
        </div>
      </div>
    </div>
    <br />
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
    </div>

    <div id="map" style="height: 800px; width: 100%"></div>

    <div class="row">
      <div class="col-6">
        <div v-if="geometadata" class="alert alert-light" role="alert">
          <strong>Records:</strong> {{ geometadata.records }}<br>
          <strong>Dataframe Size:</strong> {{ geometadata.dfsize }} Mb<br>
          <strong>Payload Size:</strong> {{ geometadata.objectSize }} Mb<br>
          <strong>Time:</strong> {{ geometadata.time }} seconds
        </div>
      </div>

      <div class="col-6">
        <div v-if="geometadata" class="alert alert-light" role="alert">
          <strong>Radix:</strong> {{ h3Radix }} meters<br>
        </div>
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

export default {
  name: 'MapComponent',
  data() {
    return {
      map: null,
      sourceId: 'vector-tiles-source',
      geojson: null,
      token: null,
      outline: true,
      showData: true,
      popup: null,
      h3Level: 5,
      mapStyles: {
        light: 'mapbox://styles/mapbox/light-v10',
        dark: 'mapbox://styles/mapbox/dark-v10'
      },
      minMaxAggField: { min: null, max: null },
      showField: null,
      loading: false,
      limitsSetedManually: false,
      geometadata: null,
    };
  },

  computed: {
    numericFields() {
      var n = Object.keys(this.schema).filter(key => this.schema[key] === 'int64' || this.schema[key] === 'float64');
      return n;
    },
    h3Radix() {
    // Array con el radio en metros de cada nivel H3
    /*
        Res	Average edge length (Km)
    0	1281.256011
    1	483.0568391
    2	182.5129565
    3	68.97922179
    4	26.07175968
    5	9.854090990
    6	3.724532667
    7	1.406475763
    8	0.531414010
    9	0.200786148
    10	0.075863783
    11	0.028663897
    12	0.010830188
    13	0.004092010
    14	0.001546100
    15	0.000584169

    */
    const h3RadixValues = [
        1281.256011,
        483.0568391,
        182.5129565,
        68.97922179,
        26.07175968,
        9.854090990,
        3.724532667,
        1.406475763,
        0.531414010,
        0.200786148,
        0.075863783,
        0.028663897,
        0.010830188,
        0.004092010,
        0.001546100,
        0.000584169
    ];

    // Verifica que this.h3Level esté dentro del rango válido
    if (this.h3Level >= 0 && this.h3Level <= 15) {
      var meters = h3RadixValues[this.h3Level] * 1000;
      meters = Math.round(meters * 100) / 100;
      return meters;
    } else {
        throw new Error("Nivel H3 inválido: " + this.h3Level);
    }
}

  },

  props: {
    table: String,
    // Array of strings selected
    selectedFields: Array,
    schema: Object,
  },

  watch: {
    selectedFields: {
      handler: 'reloadMap',
      deep: true
    }
  },


  ////////////////////////////
  async mounted() {
    this.token = await this.getToken();
    if (!this.showField) {
      this.showField = this.numericFields[0];
    }

    if (this.token) {
      this.geojson = await this.fetchGeojsonData();
      //this.csvdata = await this.fetchCsvData();
      if (this.minMaxAggField.min === null || this.minMaxAggField.max === null) {
        this.minMaxAggField = this.getMinMax(this.geojson, this.showField);
      }
      this.initMap(this.geojson);
    }
  },
  methods: {
    ////////////////////////////
    async reloadMap(reloadData = false, reloadLimits = false) {
      if (reloadData) {
        this.geojson = await this.fetchGeojsonData();
      }
      if (!this.geojson) {
        return;
      }

      if (reloadLimits) {
        this.limitsSetedManually = false;
        this.minMaxAggField = this.getMinMax(this.geojson, this.showField);
      }
      this.reloadLayers(this.geojson);
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
    async changeLimits(geojson) {
      this.limitsSetedManually = true;
      this.reloadLayers(geojson);
    },


    ////////////////////////////
    async fetchCsvData() {
      const response = await axios.get(`http://localhost:8000/maps/csv?table=${this.table}&fields=${this.fields}&level=${this.h3Level}`);
      return response.data;
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
    async showFieldInMap() {
      console.log("Showing field " + this.showField + " in map");
      await this.reloadMap();
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
        this.reloadLayers(geojson);
        this.addPopup();
      });

      this.map.on('style.load', () => {
        this.reloadLayers(geojson);
        this.addPopup();
      });
    },

    ////////////////////////////
    getMinMax(geojson, field) {
      let min = 100000000;
      let max = -100000000;

      geojson.features.forEach(feature => {
        const value = feature.properties[field];
        if (!isNaN(value)) {
          if (value < min) min = value;
          if (value > max) max = value;
        }
      });


      if (min === max || min > max) {
        max = min + 1;
      }
      return { min, max };
    },
    ////////////////////////////
    generateColorScale(min, max) {
      if (!this.showField) this.showField = this.numericFields[0];

      const steps = 25;
      const colorScale = ['interpolate', ['linear'], ['get', this.showField]];

      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const value = min + t * (max - min);
        const color = this.interpolateColor(t);
        colorScale.push(value, color);
      }

      return colorScale;
    },
    ////////////////////////////
    interpolateColor(t) {
      const r1 = 0, g1 = 0, b1 = 255; // Azul frío
      const r2 = 139, g2 = 0, b2 = 0; // Rojo oscuro

      const r = Math.round(r1 + t * (r2 - r1));
      const g = Math.round(g1 + t * (g2 - g1));
      const b = Math.round(b1 + t * (b2 - b1));

      return `rgb(${r},${g},${b})`;
    },

    ////////////////////////////
    reloadLayers(geojson) {
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
        'data': geojson
      });

      const colorScale = this.generateColorScale(this.minMaxAggField.min, this.minMaxAggField.max);

      this.map.addLayer({
        'id': 'h3',
        'type': 'fill',
        'source': 'h3',
        'layout': {},
        'paint': {
          'fill-color': colorScale,
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
          .setHTML(`<strong>Properties:</strong><br>${Object.keys(properties).map(key => `${key}: ${properties[key]}`).join('<br>')}`)
          .addTo(this.map);
      });

      this.map.on('mouseleave', 'h3', () => {
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
</style>
