<template>
  <div class="text-center font-sans w-96 mx-auto rounded-lg shadow-lg border-solid border-2 p-8">
    <div>
      <button class="btn btn-danger m-1 opcion-style" v-if="recording" name="stop" @click="toggleRecording">
        <h1><i class="bi bi-mic-fill" style="color: red;"></i></h1></button>

      <button class="btn btn-primary m-1 opcion-style" v-else name="mic" @click="toggleRecording">
        <h1><i class="bi bi-mic"></i></h1></button>
    </div>
    <br />
    <div>{{ recordedTime }}</div>
    <div class="text-sm font-bold">{{ successMessage }}</div>
    <div class="text-sm">{{ instructionMessage }}</div>
    <div class="text-sm text-red-400">{{ errorMessage }}</div>
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
