<template>
  
  
      <div ref="plotlyChart" style="height: 800px; width: 100%"></div>
  
  
</template>

<script setup>
import { ref, onMounted, defineProps, nextTick } from 'vue';
import axios from 'axios';
import Plotly from 'plotly.js-dist';

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
const plotData = ref({ data: [], layout: {} });
const plotlyChart = ref(null);

///////////////////////////////////////////////////
// Mount
///////////////////////////////////////////////////
onMounted(async () => {
  await loadMap();
  await nextTick(); // Esperar a que el DOM se actualice completamente
  renderPlotlyChart(); // Renderizar el gráfico después de cargar los datos y el DOM
});

///////////////////////////////////////////////////
// Métodos
///////////////////////////////////////////////////
const loadMap = async () => {
  try {
    var response = await axios.get(`http://localhost:8000/maps?table=${props.table}&level=5`);
    console.log('Map data loaded:', response.data);
    var mapData = JSON.parse(response.data);
    console.log('Map data parsed:', mapData);
    plotData.value =  mapData || { data: [], layout: {} }; // Asegurarse de que los datos tengan una estructura predeterminada
    console.log('Map loaded:', plotData.value);
  } catch (error) {
    console.error('Error loading map:', error);
  }
};

const renderPlotlyChart = () => {
  
  if (plotlyChart.value && plotData.value.data && plotData.value.data.length) {
    console.log('Rendering plotly chart:', plotData.value);
    Plotly.newPlot(plotlyChart.value, plotData.value.data, plotData.value.layout).then(() => {
      console.log('Plotly chart rendered successfully');
    }).catch((error) => {
      console.error('Error rendering plotly chart:', error);
    });
  } else {
    console.log('Plotly chart container or data not ready:', plotlyChart.value, plotData.value);
  }
};
</script>

<style></style>
