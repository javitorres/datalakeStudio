<template>
  <section class="chat-page compact-panel">
    <header class="chat-topbar">
      <div>
        <h2 class="compact-title mb-1">ChatGPT Assistant</h2>
        <p class="compact-muted mb-0">Pregunta por voz o texto y genera consultas SQL con respuesta contextual.</p>
      </div>
      <div class="chat-toggles">
        <div class="form-check form-switch">
          <input
            id="blindModeSwitch"
            class="form-check-input"
            type="checkbox"
            role="switch"
            :checked="blindMode"
            @click="blindMode = !blindMode"
          >
          <label class="form-check-label compact-muted" for="blindModeSwitch">Blind mode</label>
        </div>
        <div class="form-check form-switch">
          <input
            id="ttsSwitch"
            class="form-check-input"
            type="checkbox"
            role="switch"
            :checked="tts"
            @click="tts = !tts"
          >
          <label class="form-check-label compact-muted" for="ttsSwitch">TTS</label>
        </div>
      </div>
    </header>

    <div class="chat-layout">
      <main class="chat-main">
        <div v-if="blindMode" class="chat-blind-state compact-card">
          <p class="compact-muted mb-0">Blind mode está activo. El historial visual está oculto.</p>
        </div>

        <div v-else class="chat-feed">
          <article
            v-for="(message, index) in conversation"
            :key="index"
            class="chat-message"
            :class="message.speaker === 'user' ? 'chat-message-user' : 'chat-message-bot'"
          >
            <div v-if="message.text">
              <p class="chat-role">{{ message.speaker === 'user' ? 'You' : 'ChatGPT' }}</p>
              <p class="chat-text">{{ message.text }}</p>
            </div>

            <div v-if="message.table" class="chat-table-result">
              <p class="compact-muted mb-1">Query result</p>
              <TableInspector :tableName="tableName" :showOptions="false" />
            </div>
          </article>

          <div v-if="!conversation.length" class="compact-card">
            <p class="compact-muted mb-0">Todavia no hay mensajes. Empieza con una pregunta.</p>
          </div>
        </div>
      </main>

      <aside class="chat-side">
        <div class="compact-card recorder-card">
          <h3 class="compact-title mb-2">Voice input</h3>
          <recorder-widget :time="2" buttonColor="green" @newRecording="processRecording" />
        </div>

        <div class="compact-card tips-card">
          <h3 class="compact-title mb-2">Tips</h3>
          <ul class="tips-list">
            <li>Haz preguntas concretas sobre una tabla o métrica.</li>
            <li>Si el resultado no cuadra, reformula con filtros.</li>
            <li>Usa TTS para respuesta hablada.</li>
          </ul>
        </div>
      </aside>
    </div>

    <footer class="chat-composer compact-input-group">
      <span class="input-group-text">Text Question</span>
      <input
        v-model="textQuestion"
        placeholder="Type your question here"
        class="form-control"
        @keyup.enter="processTextQuestion(textQuestion)"
      >
      <button @click="processTextQuestion(textQuestion)" class="btn btn-sm btn-primary">Ask</button>
    </footer>
  </section>
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
const userQuestion = ref(null);
const conversation = ref([]);
const chatGPTInput = ref(null);
const query = ref(null);
const data = ref(null);
const questionForGptInterpretation = ref(null);
const interpretation = ref(null);
const tableName = ref('__lastQuery');
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
    if (response.data.transcription == 'EMPTY_AUDIO') {
      toast.error('Info: ' + 'Audio is empty, please check your microphone', { position: toast.POSITION.BOTTOM_RIGHT });
      return;
    } else {
      userQuestion.value = response.data.transcription;
      conversation.value.push({ speaker: 'user', text: userQuestion.value });
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
  if (!nextTextQuestion || !String(nextTextQuestion).trim()) {
    return;
  }
  userQuestion.value = nextTextQuestion;
  conversation.value.push({ speaker: 'user', text: userQuestion.value });
  chatGPTInput.value = userQuestion.value;
  textQuestion.value = '';
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
    conversation.value.push({ speaker: 'bot', text: query.value });
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
    conversation.value.push({ speaker: 'bot', table: data.value });
    if (data.value) {
      questionForGptInterpretation.value = 'User question is: ' + userQuestion.value + ' and ChatGPT answer is: ' + query.value + ' and SQL result: ' + data.value + '. Please give me a verbalized answer to the questoin using the provided data';
      askChatGPTGenericQuestion(questionForGptInterpretation.value);
    } else {
      conversation.value.push({ speaker: 'bot', text: 'It seems there is something wrong with the query, please checkit' });
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
    conversation.value.push({ speaker: 'bot', text: interpretation.value });
    if (tts.value) {
      getText2Speech(interpretation.value);
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

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: calc(100vh - 130px);
}

.chat-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.chat-toggles {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.chat-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 10px;
  min-height: 0;
  flex: 1;
}

.chat-main {
  min-height: 0;
}

.chat-feed {
  border: 1px solid #e4e6ec;
  border-radius: 10px;
  padding: 10px;
  background: #fbfcff;
  max-height: 62vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-message {
  border: 1px solid #dbe0ea;
  border-radius: 10px;
  padding: 8px;
}

.chat-message-user {
  background: #e4edff;
  border-color: #b8cdfa;
}

.chat-message-bot {
  background: #ffffff;
}

.chat-role {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #4f5660;
  margin-bottom: 4px;
}

.chat-text {
  font-size: 12px;
  line-height: 1.35;
  margin-bottom: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-table-result {
  margin-top: 6px;
  border-top: 1px dashed #dbe0ea;
  padding-top: 6px;
}

.chat-side {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recorder-card,
.tips-card {
  padding: 8px;
}

.tips-list {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: #4f5660;
}

.chat-composer {
  position: sticky;
  bottom: 0;
  z-index: 3;
  background: #f8f9fc;
  border: 1px solid #dbe0ea;
  border-radius: 10px;
  padding: 8px;
}

.chat-blind-state {
  padding: 12px;
}

@media (max-width: 1200px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }

  .chat-feed {
    max-height: 50vh;
  }
}
</style>
