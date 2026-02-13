<template>
  <div class="recorder-shell">
    <div class="recorder-button-wrap">
      <button class="btn btn-sm btn-danger recorder-btn" v-if="recording" name="stop" @click="toggleRecording">
        <i class="bi bi-mic-fill"></i>
      </button>

      <button class="btn btn-sm btn-primary recorder-btn" v-else name="mic" @click="toggleRecording">
        <i class="bi bi-mic"></i>
      </button>
    </div>
    <div class="recorder-time">{{ recordedTime }}</div>
    <div class="recorder-success">{{ successMessage }}</div>
    <div class="recorder-help">{{ instructionMessage }}</div>
    <div class="recorder-error">{{ errorMessage }}</div>
    <!--<figure class="mt-8">
      <audio controls :src="recordedAudio" type="audio/mpeg" class="mx-auto">
        Your browser does not support the
        <code>audio</code> element.
      </audio>
      <figcaption class="text-sm mt-2">Listen to your recording before submitting.</figcaption>
    </figure>-->
    <!--<submit-button @submit="sendData" :color="buttonColor" />-->
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue';
import Recorder from "../lib/Recorder";
import convertTimeMMSS from "../lib/Utils";

const INSTRUCTION_MESSAGE = "Click to start recording message";
const INSTRUCTION_MESSAGE_STOP = "Click icon again to stop recording";
const ERROR_MESSAGE = "Failed to use microphone. Please refresh and try again and permit the use of a microphone.";
const SUCCESS_MESSAGE = "Recorded";
const SUCCESS_MESSAGE_SUBMIT = "Successfully submitted audio message";
const ERROR_SUBMITTING_MESSAGE = "Error submitting audio message";

const props = defineProps({
  time: { type: Number, default: 1 },
  bitRate: { type: Number, default: 128 },
  sampleRate: { type: Number, default: 44100 },
  backendEndpoint: { type: String },
  buttonColor: { type: String, default: "green" },
  afterRecording: { type: Function },
  successfulUpload: { type: Function },
  failedUpload: { type: Function },
  customUpload: { type: Function, default: null }
});
const emit = defineEmits(["newRecording"]);

const recording = ref(false);
const recordedAudio = ref(null);
const recordedBlob = ref(null);
const recorder = ref(null);
const successMessage = ref(null);
const errorMessage = ref(null);
const instructionMessage = ref(INSTRUCTION_MESSAGE);

const buttonClass = computed(() => {
  return "mx-auto h-14 w-14 fill-current text-black cursor-pointer rounded-50 border-2 m-4 p-2";
});

const recordedTime = computed(() => {
  if (props.time && recorder.value?.duration >= props.time * 60) {
    toggleRecording();
  }
  return convertTimeMMSS(recorder.value?.duration);
});

onBeforeUnmount(() => {
  if (recording.value) {
    stopRecording();
  }
});

function toggleRecording() {
  recording.value = !recording.value;
  if (recording.value) {
    initRecorder();
  } else {
    stopRecording();
  }
}

function initRecorder() {
  recorder.value = new Recorder({
    micFailed,
    bitRate: props.bitRate,
    sampleRate: props.sampleRate,
  });
  recorder.value.start();
  successMessage.value = null;
  errorMessage.value = null;
  instructionMessage.value = INSTRUCTION_MESSAGE_STOP;
}

function stopRecording() {
  recorder.value.stop();
  const recordList = recorder.value.recordList();
  recordedAudio.value = recordList[0].url;
  recordedBlob.value = recordList[0].blob;
  if (recordedAudio.value) {
    successMessage.value = SUCCESS_MESSAGE;
    instructionMessage.value = null;
    sendData();
  }
  if (props.afterRecording) {
    props.afterRecording();
  }
}

async function sendData() {
  if (!recordedBlob.value) {
    return;
  }

  if (props.customUpload) {
    await props.customUpload(recordedBlob.value);
  } else {
    emit("newRecording", recordedBlob.value);
  }
}

function micFailed() {
  recording.value = false;
  instructionMessage.value = INSTRUCTION_MESSAGE;
  errorMessage.value = ERROR_MESSAGE;
}
</script>

<style scoped>
.recorder-shell {
  border: 1px solid #dbe0ea;
  border-radius: 10px;
  padding: 10px;
  text-align: center;
  background: #fff;
}

.recorder-button-wrap {
  margin-bottom: 6px;
}

.recorder-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  font-size: 1.15rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.recorder-time {
  font-size: 0.92rem;
  font-weight: 600;
  color: #2f3440;
}

.recorder-success {
  font-size: 12px;
  font-weight: 600;
  color: #1f8a4d;
}

.recorder-help {
  font-size: 12px;
  color: #5c6675;
}

.recorder-error {
  font-size: 12px;
  color: #cf2f36;
}
</style>
