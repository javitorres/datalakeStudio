<template>
  
  <!-- Show conversation -->
  <div v-if="conversation && !blindMode">
    <div v-for="(message, index) in conversation" :key="index">
      <div v-if="message.speaker == 'user'">
        <div class="row">
          <div class="col-md-10">
            <div class="input-group mb-3">
              <span class="input-group-text" id="basic-addon1">Question</span>
              <input v-model="message.text" placeholder="Text" class="form-control">
            </div>
          </div>
        </div>
      </div>
      <div v-if="message.speaker == 'bot'">
        <div class="row">
          <div class="col-md-10" v-if="message.text">
            <div class="input-group mb-3">
              <span class="input-group-text" id="basic-addon1">ChatGPT</span>
              <input v-model="message.text" placeholder="Text" class="form-control">
            </div>
          </div>

          <div class="col-md-10" v-if="message.table">
            <TableInspector :tableName="tableName" :showOptions="false" />
          </div>


        </div>
      </div>
    </div>
  </div>

  <div class="md-col-6">
    <recorder-widget :time="2" buttonColor="green" @newRecording="processRecording" />
  </div>
  <div class="form-check form-switch">
    <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckChecked" :checked="blindMode" @click="blindMode=!blindMode">
    <label class="form-check-label" for="flexSwitchCheckChecked">Blind mode</label>
  </div>
  <div class="form-check form-switch">
    <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckChecked" :checked="tts" @click="tts=!tts">
    <label class="form-check-label" for="flexSwitchCheckChecked">TTS</label>
  </div>
</template>

<script>
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

import RecorderWidget from './RecorderWidget.vue';
import TableInspector from './TableInspector.vue';
//import 'vue-audio-tapir/dist/vue-audio-tapir.css';

export default {
  name: 'ChatGptAgent',

  components: {
    RecorderWidget,
    TableInspector
  },

  data() {
    return {
      blindMode: true,
      tts: true,
      url: apiUrl,
      userQuestion: null,
      conversation: [],
      chatGPTInput: null,
      query: null,
      data: null,
      questionForGptInterpretation: null,
      interpretation: null,
      tableName: "__lastQuery",
      showOptions: true,
    };
  },
  props: {},

  methods: {
    ///////////////////////////////////////////////////////
    async processRecording(recordedBlob) {
      let formData = new FormData();
      formData.append('file', recordedBlob, 'audio.wav');

      const config = {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      };

      const fetchData = async () => await axios.post(`${apiUrl}/gpt/askGPTWhisper`, formData, config);

      toast.promise(
        fetchData(),
        {
          pending: 'Speech to text, please wait...',
          success: 'Audio processed',
          error: 'Error in speech2text'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.userQuestion = response.data.transcription;
        this.conversation.push({ "speaker": "user", "text": this.userQuestion });
        this.chatGPTInput = this.userQuestion;
        this.askChatGPT();

      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },

    ///////////////////////////////////////////////////////
    async askChatGPT() {
      const fetchData = () => axios.get(`${apiUrl}/gpt/askGPT`, {
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
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.query = response.data;
        this.conversation.push({ "speaker": "bot", "text": this.query });
        this.chatGPTInput = null;
        this.runQuery();
      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },
    ///////////////////////////////////////////////////////
    async runQuery() {
      this.queryError = null;
      this.querySuccesful = false;
      const fetchData = () => axios.post(`${apiUrl}/database/runQuery`, {
        query: this.query,
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Running query, please wait...',
          success: 'Query executed',
          error: 'Error running query'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.data = response.data;
        // this.data is CSV data, print number of rows
        console.log("Number of rows: " + this.data.split('\n').length );
        this.conversation.push({ "speaker": "bot", "table": this.data });
        if (this.data) {
          this.questionForGptInterpretation = "User question is: " + this.userQuestion + " and ChatGPT answer is: " + this.query + " and SQL result: " + this.data + ". Please give me a verbalized answer to the questoin using the provided data";
          this.askChatGPTGenericQuestion(this.questionForGptInterpretation);
        }else{
          this.conversation.push({ "speaker": "bot", "text": "It seems there is something wrong with the query, please checkit" });
        }
      }).catch((error) => {
        if (error.response.data.message) {
          this.queryError = error.response.data.message;
        } else {
          this.queryError = error.response.data;
        }
        
      });
    
    },
    ///////////////////////////////////////////////////////
    async askChatGPTGenericQuestion(question) {
      const fetchData = () => axios.get(`${apiUrl}/gpt/genericQuestion`, {
        params: {
          question: question,
        },
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Asking ChatGPT, please wait...',
          success: 'ChatGPT answered',
          error: 'Error asking ChatGPT'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        this.interpretation = response.data.answer;
        this.conversation.push({ "speaker": "bot", "text": this.interpretation });
        if (this.tts){
          this.getText2Speech(this.interpretation)
        }

      }).catch((error) => {
        if (error.response.data.message) {
          toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
        } else {
          toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
        }
      });
    },

    /////////////////////////////////////////////////
    async getText2Speech(text) {
      const fetchData = () => axios.get(`${apiUrl}/gpt/text2speech`, {
        params: {
          text: text,
        },
        responseType: 'blob' // Asegúrate de obtener la respuesta como un blob
      });

      toast.promise(
        fetchData(),
        {
          pending: 'Text to speech, please wait...',
          success: 'Text to speech processed',
          error: 'Error in text2speech'
        },
        { position: toast.POSITION.BOTTOM_RIGHT }
      ).then((response) => {
        // Crear una URL de objeto a partir del blob de audio
        const url = window.URL.createObjectURL(new Blob([response.data]));
        var audio = new Audio(url);
        audio.play();
      }).catch((error) => {
        const errorMessage = error.response?.data?.message || 'Error desconocido';
        toast.error('Info: ' + errorMessage, { position: toast.POSITION.BOTTOM_RIGHT });
      });
    }

  },




}


</script>

<style scoped></style>