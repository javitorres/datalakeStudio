<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="text-center mb-4">
        <img src="../assets/logo.svg" alt="Logo" width="60" height="60" class="mb-2">
        <h4 class="login-title">Datalake Studio</h4>
        <p class="text-muted small">Sign in to access your data workspace</p>
      </div>

      <div v-if="errorMessage" class="alert alert-danger py-2 small">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success py-2 small">{{ successMessage }}</div>

      <!-- Reset Password Form -->
      <template v-if="view === 'reset'">
        <div class="mb-3">
          <label class="form-label small">New Password</label>
          <input type="password" class="form-control" v-model="newPassword" @keyup.enter="resetPassword"
            placeholder="Enter new password" autocomplete="new-password">
        </div>
        <div class="d-grid gap-2">
          <button class="btn btn-primary" @click="resetPassword" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
            Reset Password
          </button>
          <button class="btn btn-link btn-sm text-muted" @click="view = 'login'; errorMessage = ''">
            Back to login
          </button>
        </div>
      </template>

      <!-- Forgot Password Form -->
      <template v-else-if="view === 'forgot'">
        <div class="mb-3">
          <label class="form-label small">Email</label>
          <input type="email" class="form-control" v-model="forgotEmail" @keyup.enter="forgotPassword"
            placeholder="Enter your email" autocomplete="email">
        </div>
        <div class="d-grid gap-2">
          <button class="btn btn-primary" @click="forgotPassword" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
            Send Reset Link
          </button>
          <button class="btn btn-link btn-sm text-muted" @click="view = 'login'; errorMessage = ''; successMessage = ''">
            Back to login
          </button>
        </div>
      </template>

      <!-- Normal Login/Register Form -->
      <template v-else>
        <div class="mb-3">
          <label class="form-label small">Username</label>
          <input type="text" class="form-control" v-model="username" @keyup.enter="handleSubmit"
            placeholder="Enter username" autocomplete="username">
        </div>
        <div class="mb-3">
          <label class="form-label small">Password</label>
          <input type="password" class="form-control" v-model="password" @keyup.enter="handleSubmit"
            placeholder="Enter password" autocomplete="current-password">
        </div>

        <div class="d-grid gap-2">
          <button class="btn btn-primary" @click="login" :disabled="loading">
            <span v-if="loading && mode === 'login'" class="spinner-border spinner-border-sm me-1"></span>
            Sign In
          </button>
          <button class="btn btn-outline-secondary btn-sm" @click="register" :disabled="loading">
            <span v-if="loading && mode === 'register'" class="spinner-border spinner-border-sm me-1"></span>
            Create Account
          </button>
        </div>

        <div v-if="mailConfigured" class="text-center mt-2">
          <button class="btn btn-link btn-sm text-muted p-0" @click="view = 'forgot'; errorMessage = ''; successMessage = ''">
            Forgot password?
          </button>
        </div>

        <!-- Google Sign-In -->
        <div v-if="googleClientId" class="mt-3">
          <div class="separator">
            <span class="separator-text">or</span>
          </div>
          <div ref="googleButtonRef" class="d-flex justify-content-center mt-3"></div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import api from '../services/api';

const username = ref('');
const password = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const loading = ref(false);
const mode = ref('');
const googleClientId = ref('');
const googleButtonRef = ref(null);
const mailConfigured = ref(false);
const view = ref('login');  // 'login' | 'forgot' | 'reset'
const forgotEmail = ref('');
const newPassword = ref('');
const resetToken = ref('');

const emit = defineEmits(['loginSuccess']);

onMounted(async () => {
  // Check URL params for verify/reset tokens
  const params = new URLSearchParams(window.location.search);

  const verifyToken = params.get('verify');
  if (verifyToken) {
    await verifyEmail(verifyToken);
    window.history.replaceState({}, '', window.location.pathname);
  }

  const resetParam = params.get('reset');
  if (resetParam) {
    resetToken.value = resetParam;
    view.value = 'reset';
    window.history.replaceState({}, '', window.location.pathname);
  }

  // Load Google client ID and mail config in parallel
  try {
    const [googleResp, mailResp] = await Promise.all([
      api.get(`/auth/google-client-id`).catch(() => null),
      api.get(`/auth/mail-configured`).catch(() => null),
    ]);
    if (googleResp?.data?.client_id) {
      googleClientId.value = googleResp.data.client_id;
      await nextTick();
      initGoogleSignIn(googleResp.data.client_id);
    }
    if (mailResp?.data?.configured) {
      mailConfigured.value = true;
    }
  } catch {
    // Services not available
  }
});

async function verifyEmail(token) {
  try {
    const resp = await api.get(`/auth/verify-email`, { params: { token } });
    successMessage.value = `Email verified for ${resp.data.username}. You can now sign in.`;
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Verification failed';
  }
}

function initGoogleSignIn(clientId) {
  if (!window.google?.accounts?.id) {
    setTimeout(() => initGoogleSignIn(clientId), 200);
    return;
  }
  window.google.accounts.id.initialize({
    client_id: clientId,
    callback: handleGoogleResponse,
  });
  window.google.accounts.id.renderButton(googleButtonRef.value, {
    theme: 'outline',
    size: 'large',
    width: '100%',
    text: 'signin_with',
  });
}

async function handleGoogleResponse(response) {
  errorMessage.value = '';
  successMessage.value = '';
  loading.value = true;
  mode.value = 'google';
  try {
    const result = await api.post(`/auth/google`, {
      credential: response.credential,
    });
    emit('loginSuccess', result.data);
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Google sign-in failed';
  } finally {
    loading.value = false;
  }
}

function handleSubmit() {
  login();
}

async function login() {
  errorMessage.value = '';
  successMessage.value = '';
  if (!username.value || !password.value) {
    errorMessage.value = 'Please enter username and password';
    return;
  }
  loading.value = true;
  mode.value = 'login';
  try {
    const response = await api.post(`/auth/login`, {
      username: username.value,
      password: password.value
    });
    emit('loginSuccess', response.data);
  } catch (error) {
    if (error.response?.data?.error) {
      errorMessage.value = error.response.data.error;
    } else {
      errorMessage.value = 'Connection error. Is the server running?';
    }
  } finally {
    loading.value = false;
  }
}

async function register() {
  errorMessage.value = '';
  successMessage.value = '';
  if (!username.value || !password.value) {
    errorMessage.value = 'Please enter username and password';
    return;
  }
  loading.value = true;
  mode.value = 'register';
  try {
    const response = await api.post(`/auth/register`, {
      username: username.value,
      password: password.value
    });
    if (response.data.message === 'verification_pending') {
      successMessage.value = 'Account created! Check your email to verify your account.';
    } else {
      emit('loginSuccess', response.data);
    }
  } catch (error) {
    if (error.response?.status === 409) {
      errorMessage.value = error.response.data.error || 'Username already exists';
    } else if (error.response?.data?.error) {
      errorMessage.value = error.response.data.error;
    } else {
      errorMessage.value = 'Registration failed. Is the server running?';
    }
  } finally {
    loading.value = false;
  }
}

async function forgotPassword() {
  errorMessage.value = '';
  successMessage.value = '';
  if (!forgotEmail.value) {
    errorMessage.value = 'Please enter your email';
    return;
  }
  loading.value = true;
  try {
    await api.post(`/auth/forgot-password`, { email: forgotEmail.value });
    successMessage.value = 'If that email is registered, a reset link has been sent.';
  } catch {
    errorMessage.value = 'Error sending reset email';
  } finally {
    loading.value = false;
  }
}

async function resetPassword() {
  errorMessage.value = '';
  successMessage.value = '';
  if (!newPassword.value) {
    errorMessage.value = 'Please enter a new password';
    return;
  }
  if (newPassword.value.length < 4) {
    errorMessage.value = 'Password must be at least 4 characters';
    return;
  }
  loading.value = true;
  try {
    await api.post(`/auth/reset-password`, {
      token: resetToken.value,
      password: newPassword.value
    });
    successMessage.value = 'Password reset successfully. You can now sign in.';
    view.value = 'login';
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Reset failed';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-wrapper {
  position:relative; display:flex; align-items:center; justify-content:center; min-height:100vh; overflow:hidden;
  padding:28px; background:radial-gradient(circle at 18% 16%,rgba(104,194,173,.22),transparent 25rem),radial-gradient(circle at 90% 90%,rgba(104,194,173,.13),transparent 28rem),#13201d;
}
.login-wrapper::before { content:''; position:absolute; inset:0; opacity:.12; background-image:linear-gradient(#b7ded3 1px,transparent 1px),linear-gradient(90deg,#b7ded3 1px,transparent 1px); background-size:48px 48px; mask-image:radial-gradient(circle at center,#000,transparent 72%); }
.login-wrapper::after { content:'DATA  →  INSIGHT  →  API'; position:absolute; left:35px; bottom:26px; color:#79938d; font-size:9px; font-weight:750; letter-spacing:.2em; }
.login-card { position:relative; z-index:1; width:100%; max-width:410px; padding:35px; border:1px solid rgba(207,231,224,.78); border-radius:18px; background:rgba(255,255,255,.97); box-shadow:0 35px 90px rgba(4,18,14,.38); }
.login-card img { width:70px; height:70px; padding:14px; border-radius:18px; background:#e6f5f0; }
.login-title { margin-top:8px; color:#17211f; font-size:1.35rem; font-weight:750; letter-spacing:-.025em; }
.login-card .text-muted { color:#74817d !important; }
.login-card .form-label { margin-bottom:6px; color:#455651; font-size:10px !important; font-weight:750; letter-spacing:.06em; text-transform:uppercase; }
.login-card .form-control { min-height:43px; border-radius:9px; background:#f8faf9; }
.login-card .btn { min-height:41px; border-radius:9px; }
.login-card .btn-primary { box-shadow:0 8px 18px rgba(13,132,111,.2); }
.separator { text-align:center; border-bottom:1px solid #dfe8e5; line-height:.1em; margin:1rem 0 0; }
.separator-text { padding:0 10px; color:#84908d; background:white; font-size:.75rem; }
@media(max-width:520px){.login-wrapper{padding:15px}.login-card{padding:27px 22px}.login-wrapper::after{display:none}}
</style>