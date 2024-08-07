<template>
  <div>
    <!-- Tile dark or light button -->
    <div class="btn-group" role="group" aria-label="Basic radio toggle button group">
      <input type="radio" class="btn-check" name="btnradio" id="btnradio1" autocomplete="off" checked>
      <label class="btn btn-outline-primary" for="btnradio1" @click="changeTile('dark')">Dark</label>

      <input type="radio" class="btn-check" name="btnradio2" id="btnradio2" autocomplete="off">
      <label class="btn btn-outline-primary" for="btnradio2" @click="changeTile('light')">Light</label>
    </div>
    <div id="map" style="height: 800px; width: 1200px"></div>
  </div>
</template>

<script>
import "mapbox-gl/dist/mapbox-gl.css";
import mapboxgl from 'mapbox-gl';
import axios from 'axios';

export default {
  name: 'MapComponent',
  data() {
    return {
      map: null,
      sourceId: 'vector-tiles-source',
    };
  },
  mounted() {
    this.initMap();
  },
  methods: {
    async initMap() {
      mapboxgl.accessToken = 'pk.eyJ1IjoibWFkaXZhbWFwcyIsImEiOiJjbHo5dXVmdDkwY2ltMmxxejlpY2owZ3F6In0.mS7eefJK9EH-K45vXemDjQ'; // Reemplaza con tu token de acceso de Mapbox

      this.map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/light-v10',
        center: [-0.09, 51.505],
        zoom: 13
      });

      this.map.on('load', () => {
        this.addVectorTileSourceAndLayer();
      });
    },
    changeTile(theme) {
      if (theme === 'dark') {
        this.map.setStyle('mapbox://styles/mapbox/dark-v10');
      } else {
        this.map.setStyle('mapbox://styles/mapbox/light-v10');
      }

      this.map.on('styledata', () => {
        this.addVectorTileSourceAndLayer();
      });
    },
    addVectorTileSourceAndLayer() {
      if (this.map.getSource(this.sourceId)) {
        this.map.removeLayer('vector-tiles-layer');
        this.map.removeSource(this.sourceId);
      }

      this.map.addSource(this.sourceId, {
        type: 'vector',
        tiles: [
          'http://localhost:8000/maps/tiles/homecenter/{z}/{x}/{y}.pbf' // Reemplaza esta URL con la ubicación de tus tiles vectoriales
        ],
        minzoom: 0,
        maxzoom: 14
      });

      this.map.addLayer({
        id: 'vector-tiles-layer',
        type: 'fill',
        source: this.sourceId,
        'source-layer': 'your-source-layer-name', // Reemplaza con el nombre de tu capa de fuente
        paint: {
          'fill-color': 'rgba(255, 0, 0, 0.5)',
          'fill-outline-color': 'rgba(0, 0, 0, 1)'
        }
      });
    }
  }
}
</script>

<style scoped>
#map {
  height: 100%;
  width: 100%;
}
</style>
