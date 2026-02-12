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

<script setup>
import { onMounted, ref } from 'vue';
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const dark = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const light = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

const props = defineProps({
  data: String,
  latField: String,
  lonField: String,
});

const zoom = ref(13);
const center = ref([40.42081414105578, -3.681776576195117]);
const tileType = ref(dark);
const map = ref(null);
const circles = ref([]);
const jsonData = ref([]);

onMounted(() => {
  createMap();
});

function createMap() {
  map.value = L.map('map').setView(center.value, zoom.value);

  var lines = props.data.split("\n");
  var fieldNames = lines[0].split(",");
  var latIndex = fieldNames.indexOf(props.latField);
  var lonIndex = fieldNames.indexOf(props.lonField);
  var dataLines = lines.slice(1);
  jsonData.value = [];
  for (var i = 0; i < dataLines.length; i++) {
    var fields = dataLines[i].split(",");
    var lat = fields[latIndex];
    var lon = fields[lonIndex];
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
    jsonData.value.push(jsonObj);
    center.value[0] += lat;
    center.value[1] += lon;
  }
  center.value[0] /= dataLines.length;
  center.value[1] /= dataLines.length;
  map.value.setView(center.value, zoom.value);

  var bounds = [];
  for (const item of jsonData.value) {
    bounds.push(item.coordinates);
  }
  map.value.fitBounds(bounds);

  L.tileLayer(tileType.value, {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  circles.value = [];
  for (const item of jsonData.value) {
    const circle = L.circle(item.coordinates, {
      color: 'red',
      fillColor: '#f03',
      fillOpacity: 0.5,
      radius: 100 * zoom.value
    }).addTo(map.value)
      .bindPopup(item.info.join("<br>"))
      .openPopup();
    circles.value.push(circle);
  }

  map.value.on('zoomend', adjustCircleSize);
}

function changeTile(nextTileType) {
  if (nextTileType == "dark") {
    tileType.value = dark;
  } else {
    tileType.value = light;
  }
  map.value.remove();
  createMap();
}

function adjustCircleSize() {
  const zoomLevel = map.value.getZoom();
  const newRadius = 166810.05 * Math.pow(0.599, zoomLevel);

  circles.value.forEach(circle => {
    circle.setRadius(newRadius);
  });
}
</script>

<style></style>
