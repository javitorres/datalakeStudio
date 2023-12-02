<template>
  <p>DatalakeStudioPro</p><br/>
  <p>{{ message }}</p>
</template>

<script>
import axios from 'axios';

//import axios from 'axios';
//import L from 'leaflet';

export default {
  name: 'DatalakeStudio',
  data() {
    return {
      message: 'Hello Vue 3!',
      serverHost: 'localhost',
      serverPort: '3000',
    };
  },
  methods: {
    getProperty(path, defaultValue = '') {
      try {
        return path.split('.').reduce((o, i) => o[i], this);
      } catch (e) {
        return defaultValue;
      }
    },
    initDatabase() {
      console.log('initDatabase');
      axios.get(`http://${this.serverHost}:${this.serverPort}/init`);
    }
  }
}

      
</script>
