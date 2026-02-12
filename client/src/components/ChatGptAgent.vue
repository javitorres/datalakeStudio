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

  <!-- text question for chat -->
  <div class="row">
    <div class="col-md-10">
      <div class="input-group mb-3">
        <span class="input-group-text" id="basic-addon2">Text Question</span>
        <input v-model="textQuestion" placeholder="Type your question here" class="form-control">
        <button @click="processTextQuestion(textQuestion)" class="btn btn-primary">Ask</button>
      </div>
    </div>
  </div>

  <div class="form-check form-switch">
    <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckChecked" :checked="blindMode"
      @click="blindMode = !blindMode">
    <label class="form-check-label" for="flexSwitchCheckChecked">Blind mode</label>
  </div>
  <div class="form-check form-switch">
    <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckChecked" :checked="tts"
      @click="tts = !tts">
    <label class="form-check-label" for="flexSwitchCheckChecked">TTS</label>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { API_HOST, API_PORT } from '../../config';
const apiUrl = `${API_HOST}:${API_PORT}`;

import RecorderWidget from './RecorderWidget.vue';
import TableInspector from './TableInspector.vue';
const blindMode = ref(true);
const tts = ref(true);
const url = ref(apiUrl);
const userQuestion = ref(null);
const conversation = ref([]);
const chatGPTInput = ref(null);
const query = ref(null);
const data = ref(null);
const questionForGptInterpretation = ref(null);
const interpretation = ref(null);
const tableName = ref("__lastQuery");
const showOptions = ref(true);
const textQuestion = ref(null);
const queryError = ref(null);
const querySuccesful = ref(false);

async function processRecording(recordedBlob) {
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
    if (response.data.transcription == "EMPTY_AUDIO") {
      toast.error('Info: ' + "Audio is empty, please check your microphone", { position: toast.POSITION.BOTTOM_RIGHT });
      return;
    } else {
      userQuestion.value = response.data.transcription;
      conversation.value.push({ "speaker": "user", "text": userQuestion.value });
      chatGPTInput.value = userQuestion.value;
      askChatGPT();
    }
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function processTextQuestion(nextTextQuestion) {
  userQuestion.value = nextTextQuestion;
  conversation.value.push({ "speaker": "user", "text": userQuestion.value });
  chatGPTInput.value = userQuestion.value;
  askChatGPT();
}

async function askChatGPT() {
  const fetchData = () => axios.get(`${apiUrl}/gpt/askGPT`, {
    params: {
      question: chatGPTInput.value,
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
    query.value = response.data;
    conversation.value.push({ "speaker": "bot", "text": query.value });
    chatGPTInput.value = null;
    runQuery();
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function runQuery() {
  queryError.value = null;
  querySuccesful.value = false;
  const fetchData = () => axios.post(`${apiUrl}/database/runQuery`, {
    query: query.value,
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
    data.value = response.data;
    console.log("Number of rows: " + data.value.split('\n').length);
    conversation.value.push({ "speaker": "bot", "table": data.value });
    if (data.value) {
      questionForGptInterpretation.value = "User question is: " + userQuestion.value + " and ChatGPT answer is: " + query.value + " and SQL result: " + data.value + ". Please give me a verbalized answer to the questoin using the provided data";
      askChatGPTGenericQuestion(questionForGptInterpretation.value);
    } else {
      conversation.value.push({ "speaker": "bot", "text": "It seems there is something wrong with the query, please checkit" });
    }
  }).catch((error) => {
    if (error.response.data.message) {
      queryError.value = error.response.data.message;
    } else {
      queryError.value = error.response.data;
    }
  });
}

async function askChatGPTGenericQuestion(questionText) {
  const fetchData = () => axios.get(`${apiUrl}/gpt/genericQuestion`, {
    params: {
      question: questionText,
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
    interpretation.value = response.data.answer;
    conversation.value.push({ "speaker": "bot", "text": interpretation.value });
    if (tts.value) {
      getText2Speech(interpretation.value)
    }
  }).catch((error) => {
    if (error.response.data.message) {
      toast.error('Info' + `Error: ${error.response.data.message}`, { position: toast.POSITION.BOTTOM_RIGHT });
    } else {
      toast.error('Info:' + `Error: ${error.response.data}`, { position: toast.POSITION.BOTTOM_RIGHT });
    }
  });
}

async function getText2Speech(text) {
  const fetchData = () => axios.get(`${apiUrl}/gpt/text2speech`, {
    params: {
      text: text,
    },
    responseType: 'blob'
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
    const audioUrl = window.URL.createObjectURL(new Blob([response.data]));
    var audio = new Audio(audioUrl);
    audio.play();
  }).catch((error) => {
    const errorMessage = error.response?.data?.message || 'Error desconocido';
    toast.error('Info: ' + errorMessage, { position: toast.POSITION.BOTTOM_RIGHT });
  });
}
</script>

<style scoped></style>
