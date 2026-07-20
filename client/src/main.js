import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import 'bootstrap-icons/font/bootstrap-icons.css'

// Auth handling and the API base URL live on the shared axios instance in
// ./services/api.js. Components must import that instance rather than the
// global axios so the JWT is only ever sent to our backend.

createApp(App).mount('#app')
