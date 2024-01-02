<template>
  <div class="row" v-if="tables && tables.length > 0">
    <div class="col-md-6">
      <h3>Select Dataset</h3>
      <div class="row">
        <!-- Table selector -->
        <div class="row">
          <div class="col-md-6">
            <div class="form-group">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">Select table</span>
                
              <select class="form-control" id="tableSelector" v-model="table">
                <option v-for="table in tables" :key="table.id" :value="table">{{ table }}</option>
              </select>
              </div>
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
      <!-- Search API or use a known endpoint -->
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
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Service name</span>
        <input id="apiServiceName" type="text" class="form-control" placeholder="Service name" aria-label="File"
          aria-describedby="basic-addon1" v-model="apiServiceName" @input="searchService(apiServiceName)">
        </div>
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

        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Method name</span>
        <input id="methodPath" type="text" class="form-control" placeholder="Method name" aria-label="File"
          aria-describedby="basic-addon1" v-model="methodPath" @input="searchMethod(service, methodPath)">
        </div>

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
                  <p><b>Param:</b> {{ param.name }} ({{ param.schema.type }}). {{ param.required ? "Required" : "Optional"
                  }}
                  </p>
                </li>
              </div>
            </ul>
          </div>
        </div>

        <div v-if="mode === 'write'">
          <p>write</p>
        </div>
      </div>
    </div>

    <div class="row" v-if="methodInfo">
      <div class="col-md-4">
        <p><i class="bi bi-puzzle"></i> Field mapping </p>
        <p>Select the field to map with the API parameter</p>

        <div v-for="param in methodInfo.parameters" :key="param.name">
          <label :for="'fieldSelector-' + param.name">{{ param.name }}</label>
          <select class="form-control" :id="'fieldSelector-' + param.name" v-model="selectedFields[param.name]" @change="buildQueryString">
            <option value="">None</option>
            <option v-for="(type, field) in schema" :key="field" :value="field">{{ field }}</option>
          </select>
          <br />
        </div>
      </div>

      <div class="col-md-4">
        <p><i class="bi bi-check-circle"></i> Api response sample</p>
        <p>Sample for first record:</p>
        <!-- Show queryString -->
        <div v-if="fullUrlExample">
          <p><b>Query string:</b> {{ fullUrlExample }}</p>
        </div>
        
        <div v-if="sampleData">
          <!-- text area -->
          <div class="form-group">
            <label for="exampleFormControlTextarea1">Sample response</label>
            <textarea class="form-control" id="exampleFormControlTextarea1" rows="10">{{ sampleResponse }}</textarea>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <p><i class="bi bi-check2-square"></i> Extract fields</p>
        <p>Write field to load, example : data.car.model. If the field is empty the whole response will be loaded in RESPONSE_JSON field</p>
      
        <div>
          <div v-for="(mapping, index) in mappings" :key="index" class="row">
            <div class="col-md-6">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">Json field</span>
                <input v-model="mapping.jsonField" placeholder="Json Field" class="form-control">
              </div>
            </div>
            <div class="col-md-6">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">New field name</span>
                <input v-model="mapping.newFieldName" placeholder="New Field Name" class="form-control">
              </div>
            </div>
          </div>
        
          <button class="btn btn-primary m-1 opcion-style" @click="addMapping">Add new</button>
          <button class="btn btn-primary m-1 opcion-style" @click="deleteAllMappings">Delete all mappings</button>
        </div>
      </div>
    </div> <!-- process config -->
    <div class="row" v-if="table && mappings.length > 0">
      <div class="col-md-3">
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Records to process (empty for all)</span>
            <input v-model="recordsToProcess" placeholder="10" class="form-control">
        </div>
            <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">New table name</span>
            <input v-model="newTableName" placeholder="enrichedTable" class="form-control">
        </div>
        <button v-if="newTableName" class="btn btn-primary m-1 opcion-style" @click="runDataEnrichment()">Run</button>
      </div>
      
    </div>
  </div>
  <div v-else>
    <h2>No tables to enrich with extrnal APIs. Load some data before</h2>
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
      selectedFields: {},
      fullUrl: '',
      fullUrlExample: '',
      sampleData: null,
      sampleResponse: null,

      mappings: [{ jsonField: "", newFieldName: "" }],
      recordsToProcess: 10,
      newTableName: null,

      schema: null,

      table: null,
      mode: 'search',

    };
  },
  props: {
    tables: Object,

  },
  emits: ['tableCreated'],

  watch: {
    table: function (newVal, oldVal) {
      console.log('tableName:', newVal);
      this.getTableSchema(newVal);
    }
  },
  methods: {
    async searchService(apiServiceName) {
      this.methods = [];
      const fetchData = async () => await axios.get(`${apiUrl}/getServices`, {
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
      this.service = service;
      this.selectedFields = {};
      const fetchData = async () => await axios.get(`${apiUrl}/getRepositoryMethodList`, {
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
      this.selectedFields = {};
      console.log('clickMethod', method);
      const fetchData = async () => await axios.get(`${apiUrl}/getMethodInfo`, {
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
      const fetchData = async () => await axios.get(`${apiUrl}/getTableSchema`, {
        params: {
          tableName: table,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Loading table schema, please wait...',
          success: 'Schema loaded',
          error: 'Error loading  schema'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.schema = response.data;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    ////////////////////////////////////////////////////
    async getSampleData(table) {
      this.showSampleData = true;
      this.showProfile = false;
      this.showCrossfilters = false;

      await axios.get(`${apiUrl}/getSampleData`, {
        params: {
          tableName: table,
          type: this.type,
          records: 5,
        },
      }).then((response) => {
          this.sampleData = response.data;
      }).catch((error) => {
        toast.error(`Error: HTTP ${error.message}`);
      }).finally(() => {
        this.loading = false;
      });
    },

    ////////////////////////////////////////////////////
    async buildQueryString() {
      await this.getSampleData(this.table);
      //console.log('sampleData:', this.sampleData);
      var queryString = '';
          // Dividir el CSV en filas y luego en columnas
      const rows = this.sampleData.split('\n');
      const firstRow = rows[0].split(',');
      const secondRow = rows[1].split(',');
      console.log('firstRow:', firstRow);

      var queryString = '';
      for (var key in this.selectedFields) {
        // Utiliza el índice de la clave de selectedFields para encontrar el valor correspondiente en firstRow
        const fieldIndex = Object.keys(this.selectedFields).indexOf(key);
        console.log('fieldIndex:' + fieldIndex + ' firstRow[fieldIndex]:' + firstRow[fieldIndex]);
        if (fieldIndex !== -1 && firstRow[fieldIndex]) {
          queryString += `${key}=${encodeURIComponent(secondRow[fieldIndex])}&`;
        } else {
          queryString += `${key}=${encodeURIComponent(this.selectedFields[key])}&`;
        }
      }

      this.fullUrl = `${this.methodInfo.url}`;
      this.fullUrlExample = `${this.methodInfo.url}?${queryString}`;
      const fetchData = async () => await axios.get(`${this.fullUrlExample}`, {
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Example requet, please wait...',
          success: 'Example loaded',
          error: 'Error loading  sample data'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.sampleResponse = response.data;
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });


    },

    ////////////////////////////////////////////////////
    addMapping() {
      this.mappings.push({ jsonField: "", newFieldName: "" });
    },

    ////////////////////////////////////////////////////
    deleteAllMappings() {
      this.mappings = [];
    },
    /////////////////////////////////////////////////
    async runDataEnrichment(){
      console.log('runDataEnrichment');
      console.log('mappings to json:', JSON.stringify(this.mappings));
      console.log('recordsToProcess:', this.recordsToProcess);

      const fetchData = async () => await axios.post(`${apiUrl}/runApiEnrichment`, {
        tableName: this.table,
        parameters: this.selectedFields,
        mappings: this.mappings,
        recordsToProcess: this.recordsToProcess,
        service: this.service,
        method: this.method,
        url: this.fullUrl,
        newTableName: this.newTableName,
      });
        
      

      toast.promise(
        fetchData(),
        {
          pending: 'Generating new table using API, please wait...',
          success: 'New table created',
          error: 'Error creating table'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        
        this.$emit('tableCreated');
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
  
    

  }
}

</script>
<style scoped></style>