<template>
  <!-- Tile dark or light button -->
  <div class="btn-group" role="group" aria-label="Basic radio toggle button group">
    <input type="radio" class="btn-check" name="btnradio" id="btnradio1" autocomplete="off" checked>
    <label class="btn btn-outline-primary" for="btnradio1" @click="changeTile('dark')">Dark</label>

    <input type="radio" class="btn-check" name="btnradio" id="btnradio2" autocomplete="off">
    <label class="btn btn-outline-primary" for="btnradio2" @click="changeTile('light')">Light</label>
  </div>
  <div id="map" style="height: 800px; width: 1200px"></div>
</template>

<script >
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const dark = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const light = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

export default {
  name: 'Map',
  components: {
  },

  props: {
    // CSV data
    data: String,
    // latField is the name of the field in the CSV data that contains the latitude
    latField: String,
    // lonField is the name of the field in the CSV data that contains the longitude
    lonField: String,
  },
  data() {
    return {
      zoom: 13,
      center: [40.42081414105578, -3.681776576195117],
      coordinatesTest: [39.43155944206688, -0.6758788926090215],
      tileType: dark,
      map: null,

      jsonData: [],
    };
  },

  mounted() {
    this.createMap();
  },
  ////////////////////////////
  methods: {
    createMap() {
      // Create map
      this.map = L.map('map').setView(this.center, this.zoom);

      const customIcon = L.divIcon({
        html: '<i class="bi bi-dot" style="font-size: 24px; color: red;"></i>',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      // Convert CSV data to JSON
      var lines = this.data.split("\n");
      var fieldNames = lines[0].split(",");
      var latIndex = fieldNames.indexOf(this.latField);
      var lonIndex = fieldNames.indexOf(this.lonField);
      var dataLines = lines.slice(1);
      this.jsonData = [];
      for (var i = 0; i < dataLines.length; i++) {
        var fields = dataLines[i].split(",");
        var lat = fields[latIndex];
        var lon = fields[lonIndex];
        // var fields with field names and values
        fields = fieldNames.map((fieldName, index) => {
          return fieldName + ": " + fields[index];
        });
        
        if (lat == "" || lon == "" || lat == undefined || lon == undefined) {
          continue;
        }
        lat = parseFloat(lat);
        lon = parseFloat(lon);

        var jsonObj = {
          coordinates: [lat, lon],
          info: fields
        };
        this.jsonData.push(jsonObj);
        this.center[0] += lat;
        this.center[1] += lon;

      }
      this.center[0] /= dataLines.length;
      this.center[1] /= dataLines.length;
      this.map.setView(this.center, this.zoom);

      // Bounds
      var bounds = [];
      for (const item of this.jsonData) {
        bounds.push(item.coordinates);
      }
      this.map.fitBounds(bounds);

      L.tileLayer(this.tileType, {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
      }).addTo(this.map);

      // saves the circles in an array  to be able to change their size when zoom changes
      this.circles = [];

      for (const item of this.jsonData) {
        const circle = L.circle(item.coordinates, {
          color: 'red',
          fillColor: '#f03',
          fillOpacity: 0.5,
          radius: 100 * this.zoom
        }).addTo(this.map)
          .bindPopup(item.info.join("<br>"))
          .openPopup();
        this.circles.push(circle);
      }

      // event listener to adjust circle size when zoom changes
      this.map.on('zoomend', this.adjustCircleSize);
    },
    ////////////////////////////
    changeTile(tileType) {
      console.log("Changing to tile " + tileType);
      if (tileType == "dark") {
        this.tileType = dark;
      } else {
        this.tileType = light;
      }
      this.map.remove();
      this.createMap();
    },
    ////////////////////////////
    adjustCircleSize() {
      const zoomLevel = this.map.getZoom();
      const newRadius = 166810.05 * Math.pow(0.599, zoomLevel);

      this.circles.forEach(circle => {
        circle.setRadius(newRadius);
      });
    },
  }
};
</script>

<style></style>