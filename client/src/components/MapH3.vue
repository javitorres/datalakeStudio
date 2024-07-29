<template>
  <div>
    <div v-html="mapHtml"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps } from 'vue';
import axios from 'axios';
import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

///////////////////////////////////////////////////
// Props
///////////////////////////////////////////////////
const props = defineProps({
  table: String
});

///////////////////////////////////////////////////
// Data
///////////////////////////////////////////////////
// Propiedades reactivas
const mapHtml = ref('');

///////////////////////////////////////////////////
// Mount
///////////////////////////////////////////////////
onMounted(async () => {
  await loadMap();
});

///////////////////////////////////////////////////
// Métodos
///////////////////////////////////////////////////
const loadMap = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/maps?table=${props.table}&level=5`);
    mapHtml.value = response.data;
  } catch (error) {
    console.error('Error loading map:', error);
  }
};
</script>

<style></style>
