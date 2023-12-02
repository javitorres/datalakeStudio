
<template>
  <DatalakeStudio></DatalakeStudio>
</template>

<script>
  import "bootstrap/dist/css/bootstrap.min.css";
  import DatalakeStudio from './components/DatalakeStudio.vue'

  export default {
    name: 'App',
    components: {
      DatalakeStudio
    }
}
</script>


<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
