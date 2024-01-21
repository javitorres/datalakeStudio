<template>
  <!--<p>Latfield: {{ latField }}</p>
  <p>Lonfield: {{ lonField }}</p>
  <p>Center: {{ center }}</p>
  -->
  
  <div id="map" style="height: 800px; width: 1200px"></div>
</template>

<script >
import "leaflet/dist/leaflet.css";
import L from "leaflet";



export default {
  name: 'Map',
  components: {

  },

  props: {
    // Data is CSV data
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
      coordinatesTest: [ 39.43155944206688,-0.6758788926090215 ],

      jsonData: [],
    };
  },

  mounted() {
    // Crea el mapa
    const map = L.map('map').setView(this.center, this.zoom);

    console.log("Data:" + this.data);
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
      // if undefined
      if (lat == "" || lon == "" || lat == undefined || lon == undefined) {
        continue;
      }
      lat=parseFloat(lat);
      lon=parseFloat(lon);

      var jsonObj = {
        // coordinates: [50, 50] as L.LatLngExpression,
        coordinates: [lat, lon],
      };
      this.jsonData.push(jsonObj);
      // Calculate center with average of lat and lon
      this.center[0] += lat;
      this.center[1] += lon;
      console.log("Lat: " + lat + " Lon: " + lon + " Center: " + this.center);
      // Create new object L.LatLngExpression(lat, lon);

    }
    this.center[0] /= dataLines.length;
    this.center[1] /= dataLines.length;
    console.log("Center: " + this.center);
    // Set center of map
    map.setView(this.center, this.zoom);

    // Calculate bounds
    var bounds = [];
    for (const item of this.jsonData) {
      bounds.push(item.coordinates);
    }
    console.log("Bounds: " + bounds);
    // Set bounds of map
    map.fitBounds(bounds);

    // Añade un tile layer al mapa
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Añade marcadores al mapa (opcional)
    for (const item of this.jsonData) {
      L.marker(item.coordinates).addTo(map);
    }

  },
};
</script>

<style></style>