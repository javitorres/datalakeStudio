import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import { i18n } from './i18n'
import 'bootstrap-icons/font/bootstrap-icons.css'
// The same Tabulator version as the JavaScript the components import
import 'tabulator-tables/dist/css/tabulator.min.css'

// Auth handling and the API base URL live on the shared axios instance in
// ./services/api.js. Components must import that instance rather than the
// global axios so the JWT is only ever sent to our backend.

createApp(App).use(i18n).mount('#app')
