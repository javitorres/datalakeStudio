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
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.login-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
}

.login-title {
  font-weight: 700;
  color: #2f3440;
}

.separator {
  text-align: center;
  border-bottom: 1px solid #dee2e6;
  line-height: 0.1em;
  margin: 0.8rem 0 0;
}

.separator-text {
  background: white;
  padding: 0 10px;
  color: #6c757d;
  font-size: 0.85rem;
}
</style>
