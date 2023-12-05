<template>
 <div class="row">
   <div class="col-md-4">
     <h4>Query</h4>
     <div class="form-group">
       <codemirror
          v-model="query"
          :options="cmOption"
          style="height: 300px;"
                />
     </div>
     <button type="button" class="btn btn-primary" @click="runQuery">Run Query</button>

     <br/>
     <!-- Create table from query -->
      <div class="form-group">
        <label for="tableNameInput">Create table from query</label>
        <div class="row">
          

          <div class="md-col-4">
            <input type="text" class="form-control" id="tableNameInput" v-model="tableFromQuery">
          </div>

          <div class="md-col-2">
            <button type="button" class="btn btn-primary" @click="createTable">Create table</button>
          </div>

        </div>
        
        
      </div>
   </div>

    <div class="col-md-8">
      <div class="row">
        <div class="col-md-2">
          <div class="spinner-border" role="status" v-if="loading">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
  
        <div class="col-md-10">
          <div class="alert alert-danger" role="alert" v-if="error">
            {{ error }}
          </div>
          <div class="alert primary alert" role="alert" v-if="info">
            {{ info }}
          </div>
        </div>
      </div>
  
      <div class="row">
        <div class="col-md-12">
          <div ref="table"></div>
        </div>
      </div>

  </div>
  </div>

</template>

<script>
import { Codemirror } from 'vue-codemirror'
import axios from 'axios';
import {TabulatorFull as Tabulator} from 'tabulator-tables';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';



export default {
  name: 'QueryPanel',
  components: {
    Codemirror,
  },
  data() {
    return {
      error: '',
      info: '',
      loading: false,
      serverHost: 'localhost',
      serverPort: '8080',
      query: 'SELECT * FROM homecenter',
      sampleData: [],

      tabulator: null,
      table: [],
      tableFromQuery: '',

      cmOption: {
          tabSize: 4,
          styleActiveLine: true,
          lineNumbers: true,
          line: true,
          foldGutter: true,
          styleSelectedText: true,
          mode: 'text/python',
          keyMap: "sublime",
          matchBrackets: true,
          showCursorWhenSelecting: true,
          theme: "monokai",
          extraKeys: { "Ctrl": "autocomplete" },
          hintOptions:{
            completeSingle: false
          }
        }
    };
  },
  props: {
    
  },
  emits: ['tableCreated'],
  methods: {

    async runQuery(table) {
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/runQuery`, {
        params: {
          query: this.query,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          this.sampleData = response.data;
          var columns = [];
          for (var key in this.sampleData[0]) {
            columns.push({title: key, field: key});
          }
          var table = new Tabulator(this.$refs.table, {
          data: this.sampleData,
          reactiveData: true,
          importFormat: "csv",
          autoColumns: true,
          
      });

        } else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: ${error.message}`;
      }).finally(() => {
        this.loading = false;
      });
    },

    async createTable() {
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/createTableFromQuery`, {
        params: {
          query: this.query,
          tableName: this.tableFromQuery,
        },
      }).then((response) => {
        if (response.status === 200) {
          toast.success('Table created successfully');
          this.$emit('tableCreated');
        } else {
          toast.error('Table creation error::' + response.message);
        }
      }).catch((error) => {
        toast.error('Table creation error:' + error);
      }).finally(() => {
        this.loading = false;
      });
      
    },
    
}
}

</script>
<style scoped>
</style>