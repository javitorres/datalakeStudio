<template>
  <hr>
  <h1 v-on:click="expanded = !expanded">{{ expanded ? "-" : "+" }} Query</h1>
  <div class="row" v-if="expanded">
    <div class="row">
      <div class="col-md-4">
        <br />
        <div class="row">
          <div class="col-md-3">
            <h4>Ask ChatGPT</h4>
          </div>

          <div class="col-md-6">
            <input type="text" class="form-control" id="chatGPTInput" placeholder="Ask ChatGPT" v-model="chatGPTInput">
          </div>

          <div class="col-md-3">
            <button v-if="!loading" type="button" class="btn btn-primary" @click="askChatGPT">Ask ChatGPT</button>
          </div>
        </div>

        <br />

        <!-- ChatGPT Response -->
        <div v-if="!loading && chatGPTOutput">
          <input type="text" class="form-control" id="chatGPTOutput" v-model="chatGPTOutput">
          <button type="button" class="btn btn-primary" @click="useChatGPTAnswer">Run this query</button>
        </div>
        <h4>Query</h4>
        <div class="form-group">
          <codemirror v-model="query" :options="cmOption" style="height: 300px;" />
        </div>
        <button type="button" class="btn btn-primary" @click="runQuery">Run Query</button>

        <br />
        <!-- Create table from query -->
        <div class="form-group" v-if="sampleData">
          <br />
          <label for="tableNameInput">Create table from query</label>
          <div class="row">
            <div class="md-col-4">
              <input type="text" class="form-control" id="tableNameInput" placeholder="New table name"
                v-model="tableFromQuery">
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
        </div>

        <div class="row">
          <div class="col-md-12">
            <div ref="table"></div>
          </div>
        </div>

      </div>
    </div>
    <GenericCross 
      v-if="sampleData && chartConfig" 
      :key="genericCrossKey"
      :dataStr="sampleData" 
      :chartConfig="chartConfig">
    
    </GenericCross>
  </div>
</template>

<script>
import { Codemirror } from 'vue-codemirror'
import axios from 'axios';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import GenericCross from './GenericCross.vue';

export default {
  name: 'QueryPanel',

  components: {
    Codemirror,
    GenericCross
  },
  data() {
    return {
      expanded: true,
      error: '',
      info: '',
      loading: false,
      serverHost: 'localhost',
      serverPort: '8000',
      query: 'SELECT * FROM homecenter',
      sampleData: null,

      tabulator: null,
      table: null,
      tableFromQuery: '',

      chatGPTInput: 'dame askingprice medio',
      chatGPTOutput: '',

      lastQuerySchema: null,
      chartConfig: null,
      genericCrossKey: 0,

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
        hintOptions: {
          completeSingle: false
        }
      }
    };
  },
  props: {
    tables: Object,
    secrets: Object,

  },
  emits: ['tableCreated'],
  methods: {

    async getLastQuerySchema() {
      try {
        const response = await axios.get(`http://${this.serverHost}:${this.serverPort}/lastQuerySchema`);

        if (response.status === 200) {
          console.log("Schema loaded:", response.data);
          return response.data;
        } else {
          this.error = `Error: HTTP ${response.message}`;
          return null;
        }
      } catch (error) {
        this.error = `Error: ${error.message}`;
        return null;
      }
    },

    async runQuery(table) {
      try {
        const response = await axios.get(`http://${this.serverHost}:${this.serverPort}/runQuery`, {
          params: { query: this.query, },
        });

        if (response.status === 200) {
          this.error = '';
          
          this.sampleData = response.data;

          var columns = [];
          for (var key in this.sampleData[0]) {
            columns.push({ title: key, field: key });
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
      } catch (error) {
        this.error = `Error: ${error.message}`;
      } finally {
        this.loading = false;
      };
      this.lastQuerySchema = await this.getLastQuerySchema();

      var charts = [];
      for (var key in this.lastQuerySchema) {
        var chart = {
          title: key,
          type: this.lastQuerySchema[key],
          fields: key
        };
        if (chart.type === 'object' || chart.type === 'bool') {
          chart.type = 'categorical';
        } else if (chart.type === 'int64' || chart.type === 'float64') {
          chart.type = 'numerical';
        } else if (chart.type === 'datetime64[ns]') {
          chart.type = 'date';
        } else {
          chart.type = 'categorical';
        }
        charts.push(chart);
      }
      this.chartConfig = {
        charts: charts
      };

      // Invalidate GenericCross to force re-render
      this.genericCrossKey++;

      //console.log("Config:" + JSON.stringify(this.chartConfig));
    },
    ///////////////////////////////////////////////////////
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
    ///////////////////////////////////////////////////////
    async askChatGPT() {
      this.loading = true;
      var response = await axios.get(`http://${this.serverHost}:${this.serverPort}/askGPT`, {
        params: {
          question: this.chatGPTInput,
        },
      }).then((response) => {
        if (response.status === 200) {
          this.error = '';
          this.chatGPTOutput = response.data;
        } else {
          this.error = `Error: HTTP ${response.message}`;
        }
      }).catch((error) => {
        this.error = `Error: ${error.message}`;
      }).finally(() => {
        this.loading = false;
      });
    },
    ///////////////////////////////////////////////////////
    async useChatGPTAnswer() {
      this.query = this.chatGPTOutput;
      this.runQuery();
    },


  }
}

</script>
<style scoped></style>