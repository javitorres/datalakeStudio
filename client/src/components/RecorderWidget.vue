<template>
  <div class="text-center font-sans w-96 mx-auto rounded-lg shadow-lg border-solid border-2 p-8">
    <div>
      <button class="btn btn-primary m-1 opcion-style" v-if="recording" name="stop" @click="toggleRecording">
        <h1><i class="bi bi-stop-fill"></i></h1></button>

      <button class="btn btn-primary m-1 opcion-style" v-else name="mic" @click="toggleRecording">
        <h1><i class="bi bi-record-fill"></i></h1></button>
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

<script>
import Recorder from "../lib/Recorder";
import convertTimeMMSS from "../lib/Utils";

const INSTRUCTION_MESSAGE = "Click to start recording message";
const INSTRUCTION_MESSAGE_STOP = "Click icon again to stop recording";
const ERROR_MESSAGE = "Failed to use microphone. Please refresh and try again and permit the use of a microphone.";
const SUCCESS_MESSAGE = "Recorded";
const SUCCESS_MESSAGE_SUBMIT = "Successfully submitted audio message";
const ERROR_SUBMITTING_MESSAGE = "Error submitting audio message";

export default {
  name: "RecorderWidget",
  props: {
    // in minutes
    time: { type: Number, default: 1 },
    bitRate: { type: Number, default: 128 },
    sampleRate: { type: Number, default: 44100 },
    backendEndpoint: { type: String },
    buttonColor: { type: String, default: "green" },

    // callback functions
    afterRecording: { type: Function },
    successfulUpload: { type: Function },
    failedUpload: { type: Function },
    customUpload: { type: Function, default: null }
  },
  components: {},
  emits: ["newRecording"],
  data() {
    return {
      recording: false,
      recordedAudio: null,
      recordedBlob: null,
      recorder: null,
      successMessage: null,
      errorMessage: null,
      instructionMessage: INSTRUCTION_MESSAGE,
    };
  },
  computed: {
    buttonClass() {
      return "mx-auto h-14 w-14 fill-current text-black cursor-pointer rounded-50 border-2 m-4 p-2";
    },
    recordedTime() {
      if (this.time && this.recorder?.duration >= this.time * 60) {
        this.toggleRecording();
      }
      return convertTimeMMSS(this.recorder?.duration);
    },
  },
  beforeUnmount() {
    if (this.recording) {
      this.stopRecorder();
    }
  },
  methods: {
    toggleRecording() {
      this.recording = !this.recording;
      if (this.recording) {
        this.initRecorder();
      } else {
        this.stopRecording();
      }
    },
    initRecorder() {
      this.recorder = new Recorder({
        micFailed: this.micFailed,
        bitRate: this.bitRate,
        sampleRate: this.sampleRate,
      });
      this.recorder.start();
      this.successMessage = null;
      this.errorMessage = null;
      this.instructionMessage = INSTRUCTION_MESSAGE_STOP;
    },
    stopRecording() {
      this.recorder.stop();
      const recordList = this.recorder.recordList();
      this.recordedAudio = recordList[0].url;
      this.recordedBlob = recordList[0].blob;
      if (this.recordedAudio) {
        this.successMessage = SUCCESS_MESSAGE;
        this.instructionMessage = null;
        this.sendData();
      }
      if (this.afterRecording) {
        this.afterRecording();
      }
    },
    async sendData() {
      if (!this.recordedBlob) {
        return;
      }

      let result = null;
      if (this.customUpload) {
        result = await this.customUpload(this.recordedBlob);
      } else {
        this.$emit("newRecording", this.recordedBlob);
      }
    
    },

    micFailed() {
      this.recording = false;
      this.instructionMessage = INSTRUCTION_MESSAGE;
      this.errorMessage = ERROR_MESSAGE;
    },
  },
};
</script>
