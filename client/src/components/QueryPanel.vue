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
            <button type="button" class="btn btn-primary" @click="askChatGPT">Ask ChatGPT</button>
          </div>
        </div>

        <br />

        <!-- ChatGPT Response -->
        <div v-if="chatGPTOutput">
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

        <div class="row" v-if="querySuccesful">
          <TableInspector :tableName="tableName" :showOptions="showOptions"/>
        </div>

      </div>
    </div>

  </div>
</template>

<script>
import { Codemirror } from 'vue-codemirror'
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import GenericCross from './GenericCross.vue';
import TableInspector from './TableInspector.vue';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

export default {
  name: 'QueryPanel',

  components: {
    Codemirror,
    GenericCross,
    TableInspector
  },
  data() {
    return {
      expanded: false,
      query: 'SELECT * FROM homecenter',
      sampleData: null,

      table: null,
      tableFromQuery: '',

      chatGPTInput: 'dame askingprice medio',
      chatGPTOutput: '',

      tableName: "__lastQuery",
      querySuccesful: false,
      showOptions: true,

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

    async runQuery(table) {
      const fetchData = () => axios.get(`${apiUrl}/runQuery`, {
        params: { query: this.query, },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Running query, please wait...',
          success: 'Query executed',
          error: 'Error running query'
        },
        {position: toast.POSITION.BOTTOM_RIGHT}
      ).then((response) => {
          this.sampleData = response.data;
          this.querySuccesful = true;
      }).catch((error) => {
        if (error.response.data.message){
          toast.error('Info' + `Error: ${error.response.data.message}`, {position: toast.POSITION.BOTTOM_RIGHT});
        }else{
          toast.error('Info:' + `Error: ${error.response.data}`, {position: toast.POSITION.BOTTOM_RIGHT});
        }
      });
    },
    ///////////////////////////////////////////////////////
    async createTable() {
      const fetchData = () => axios.get(`${apiUrl}/createTableFromQuery`, {
        params: {
          query: this.query,
          tableName: this.tableFromQuery,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Creating table from query, please wait...',
          success: 'Table created',
          error: 'Error creting table from query'
        },
        {position: toast.POSITION.BOTTOM_RIGHT}
      ).then((response) => {
        this.$emit('tableCreated');
      }).catch((error) => {
        if (error.response.data.message){
          toast.error('Info' + `Error: ${error.response.data.message}`, {position: toast.POSITION.BOTTOM_RIGHT});
        }else{
          toast.error('Info:' + `Error: ${error.response.data}`, {position: toast.POSITION.BOTTOM_RIGHT});
        }
      });

    },
    ///////////////////////////////////////////////////////
    async askChatGPT() {
      const fetchData = () => axios.get(`${apiUrl}/askGPT`, {
        params: {
          question: this.chatGPTInput,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Asking ChatGPT, please wait...',
          success: 'ChatGPT answered',
          error: 'Error asking ChatGPT'
        },
        {position: toast.POSITION.BOTTOM_RIGHT}
      ).then((response) => {
        this.chatGPTOutput = response.data;
      }).catch((error) => {
        if (error.response.data.message){
          toast.error('Info' + `Error: ${error.response.data.message}`, {position: toast.POSITION.BOTTOM_RIGHT});
        }else{
          toast.error('Info:' + `Error: ${error.response.data}`, {position: toast.POSITION.BOTTOM_RIGHT});
        }
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