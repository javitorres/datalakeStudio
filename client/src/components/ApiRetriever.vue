<template>
  <hr>
  <h1 v-on:click="expanded = !expanded">{{ expanded ? "-" : "+" }} Get data from external API</h1>
  <div class="row" v-if="expanded">

    <div class="col-md-6">
      <h3>Dataset</h3>
      <div class="row" v-if="tables && tables.length > 0">
        <!-- Table selector -->
        <div class="row">
          <div class="col-md-6">
            <div class="form-group">
              <label for="tableSelector">Select table</label>
              <select class="form-control" id="tableSelector" v-model="table">
                <option v-for="table in tables" :key="table.id" :value="table">{{ table }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Sample data-->
        <div class="row" v-if="table">
          <TableInspector :tableName="table" :showOptions="showOptions" />
        </div>
      </div>
    </div>

    <div class="col-md-6" v-if="table">
      <h3>API configuration</h3>
      <div class="form-check">
        <input class="form-check-input" type="radio" name="flexRadioDefault" id="flexRadioDefault1" v-model="mode"
          value="search">
        <label class="form-check-label" for="flexRadioDefault1">Search the API</label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="radio" name="flexRadioDefault" id="flexRadioDefault2" v-model="mode"
          value="write">
        <label class="form-check-label" for="flexRadioDefault2">Write directly the API URL</label>
      </div>


      <div v-if="mode === 'search'">
        <p>Search services</p>
        <input id="apiServiceName" type="text" class="form-control" placeholder="Service name" aria-label="File"
          aria-describedby="basic-addon1" v-model="apiServiceName" @input="searchService(apiServiceName)">
      </div>

      <div v-if="services && services.length > 0">
        <ul class="list-unstyled d-flex flex-wrap">
          <li v-for="service in services" :key="service.id">
            <button class="btn btn-primary m-1 opcion-style" @click="searchMethod(service, '')">
              {{ service }}
            </button>
          </li>
        </ul>
      </div>

      <div v-if="service">
        Service: {{ service }}

        <p>Search method</p>
        <input id="methodPath" type="text" class="form-control" placeholder="Method name" aria-label="File"
          aria-describedby="basic-addon1" v-model="methodPath" @input="searchMethod(service, methodPath)">

        <!-- Methods found -->
        <ul class="list-unstyled d-flex flex-wrap" v-if="methods">
          <li v-for="method in methods" :key="method.id">
            <button class="btn btn-primary m-1 opcion-style" @click="clickMethod(service, method)">
              {{ method.controller }} - {{ method.method }} - {{ method.path }}
            </button>
          </li>
        </ul>

        <!-- Method selected info -->
        <div v-if="methodInfo">

          <!--<p>Summary: {{ methodInfo.summary }}</p>-->
          <p><b>Method:</b> {{ methodInfo.method }}</p>
          <p><b>URL:</b> {{ methodInfo.url }}</p>

          <p><b>Query parameters:</b></p>
          <div v-if="methodInfo.method === 'GET'">

            <ul>
              <div v-for="param in methodInfo.parameters">
                <li>
                  <p><b>Param:</b> {{ param.name }} ({{ param.schema.type }}). {{ param.required ? "Required" : "Optional" }}
                  </p>
                </li>
              </div>
            </ul>
          </div>
        </div>

      </div>

     <div v-if="mode === 'write'">
        <p>write</p>
      </div>
    </div>











    <div class="row"  v-if="methodInfo">
      <div class="col-md-4">
        <p><i class="bi bi-puzzle"></i> Field mapping </p>

        <div v-for="param in methodInfo.parameters">
          <label for="tableSelector">{{ param.name }}</label>
              <select class="form-control" id="tableSelector" v-model="table">
                <option v-for="(type, field) in schema" :key="field.id" :value="field">{{ field }}</option>
              </select>
              <br/>
        
        
        </div>



      </div>

      <div class="col-md-4">
        <p><i class="bi bi-check-circle"></i> Api response excample</p>
      </div>

      <div class="col-md-4">
        <p><i class="bi bi-check2-square"></i> Extract fields</p>
      </div>
    </div>
  </div>
</template>

<script>
import { Codemirror } from 'vue-codemirror'
import TableInspector from './TableInspector.vue';

import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'ApiRetriever',

  components: {
    Codemirror,
    TableInspector
  },
  data() {
    return {
      expanded: true,
      showOptions: false,

      apiServiceName: '',
      services: [],
      service: '',
      methodPath: '',
      methods: [],
      method: '',
      methodInfo: null,

      schema: null,

      table: null,
      mode: 'search',

    };
  },
  props: {
    tables: Object,

  },
  emits: [],

  watch: {
    table: function (newVal, oldVal) {
      console.log('tableName:', newVal);
      this.getTableSchema(newVal);
    }
  },
  methods: {
    async searchService(apiServiceName) {
      console.log('searchService', apiServiceName);
      this.methods = [];
      const fetchData = () => axios.get(`${apiUrl}/getServices`, {
        params: {
          serviceName: apiServiceName,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Searching service, please wait...',
          //success: 'Service  listed',
          error: 'Error Searching  service'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.services = response.data;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },

    ////////////////////////////////////////////////////
    async searchMethod(service, methodPath) {
      console.log('searchMethod ' + service + ' methodPath ' + methodPath);
      this.service = service;
      const fetchData = () => axios.get(`${apiUrl}/getRepositoryMethodList`, {
        params: {
          serviceName: service,
          methodPath: methodPath
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Loading service, please wait...',
          //success: 'Service  listed',
          error: 'Error loading  service'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.methods = response.data;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    ////////////////////////////////////////////////////
    async clickMethod(service, method) {
      this.method = method;
      console.log('clickMethod', method);
      const fetchData = () => axios.get(`${apiUrl}/getMethodInfo`, {
        params: {
          serviceName: service,
          methodPath: method.path,
          methodMethod: method.method,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Loading method info, please wait...',
          //success: 'Service  listed',
          error: 'Error loading  method'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.methodInfo = response.data;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    ////////////////////////////////////////////////////
    async getTableSchema(table) {
      await axios.get(`${apiUrl}/getTableSchema`, {
        params: {
          tableName: table,
        },
      }).then((response) => {
          this.schema = response.data;
      }).catch((error) => {
        toast.error(`Error: HTTP ${response.message}`);
      }).finally(() => {
        this.loading = false;
      });

    },

  }
}

</script>
<style scoped></style>