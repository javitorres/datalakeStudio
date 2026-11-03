<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-lang" role="radiogroup" :aria-label="t('Login.language')">
        <button
          v-for="lang in LANGUAGES"
          :key="lang.code"
          type="button"
          class="login-lang-btn"
          :class="{ 'login-lang-active': locale === lang.code }"
          role="radio"
          :aria-checked="locale === lang.code"
          :title="lang.label"
          @click="setLocale(lang.code)"
        >{{ lang.code.toUpperCase() }}</button>
      </div>
      <div class="text-center mb-4">
        <img src="../assets/logo.svg" :alt="t('Login.logoAlt')" width="60" height="60" class="mb-2">
        <h4 class="login-title">Datalake Studio</h4>
        <p class="text-muted small">{{ t('Login.subtitle') }}</p>
      </div>

      <div v-if="errorMessage" class="alert alert-danger py-2 small">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success py-2 small">{{ successMessage }}</div>

      <!-- Reset Password Form -->
      <template v-if="view === 'reset'">
        <div class="mb-3">
          <label class="form-label small">{{ t('Login.newPassword') }}</label>
          <input type="password" class="form-control" v-model="newPassword" @keyup.enter="resetPassword"
            :placeholder="t('Login.newPasswordPlaceholder')" autocomplete="new-password">
        </div>
        <div class="d-grid gap-2">
          <button class="btn btn-primary" @click="resetPassword" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
            {{ t('Login.resetPassword') }}
          </button>
          <button class="btn btn-link btn-sm text-muted" @click="view = 'login'; errorMessage = ''">
            {{ t('Login.backToLogin') }}
          </button>
        </div>
      </template>

      <!-- Forgot Password Form -->
      <template v-else-if="view === 'forgot'">
        <div class="mb-3">
          <label class="form-label small">{{ t('Login.email') }}</label>
          <input type="email" class="form-control" v-model="forgotEmail" @keyup.enter="forgotPassword"
            :placeholder="t('Login.emailPlaceholder')" autocomplete="email">
        </div>
        <div class="d-grid gap-2">
          <button class="btn btn-primary" @click="forgotPassword" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
            {{ t('Login.sendResetLink') }}
          </button>
          <button class="btn btn-link btn-sm text-muted" @click="view = 'login'; errorMessage = ''; successMessage = ''">
            {{ t('Login.backToLogin') }}
          </button>
        </div>
      </template>

      <!-- Normal Login/Register Form -->
      <template v-else>
        <div class="mb-3">
          <label class="form-label small">{{ t('Login.username') }}</label>
          <input type="text" class="form-control" v-model="username" @keyup.enter="handleSubmit"
            :placeholder="t('Login.usernamePlaceholder')" autocomplete="username">
        </div>
        <div class="mb-3">
          <label class="form-label small">{{ t('Login.password') }}</label>
          <input type="password" class="form-control" v-model="password" @keyup.enter="handleSubmit"
            :placeholder="t('Login.passwordPlaceholder')" autocomplete="current-password">
        </div>

        <div class="d-grid gap-2">
          <button class="btn btn-primary" @click="login" :disabled="loading">
            <span v-if="loading && mode === 'login'" class="spinner-border spinner-border-sm me-1"></span>
            {{ t('Login.signIn') }}
          </button>
          <button class="btn btn-outline-secondary btn-sm" @click="register" :disabled="loading">
            <span v-if="loading && mode === 'register'" class="spinner-border spinner-border-sm me-1"></span>
            {{ t('Login.createAccount') }}
          </button>
        </div>

        <div v-if="mailConfigured" class="text-center mt-2">
          <button class="btn btn-link btn-sm text-muted p-0" @click="view = 'forgot'; errorMessage = ''; successMessage = ''">
            {{ t('Login.forgotPassword') }}
          </button>
        </div>

        <!-- Google Sign-In -->
        <div v-if="googleClientId" class="mt-3">
          <div class="separator">
            <span class="separator-text">{{ t('Login.or') }}</span>
          </div>
          <div ref="googleButtonRef" class="d-flex justify-content-center mt-3"></div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { LANGUAGES, setLocale } from '../i18n';
import api from '../services/api';

const { t, locale } = useI18n();
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
const MIN_PASSWORD_LENGTH = 4;

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
    successMessage.value = t('Login.emailVerified', { username: resp.data.username });
  } catch (error) {
    errorMessage.value = error.response?.data?.error || t('Login.verificationFailed');
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
    errorMessage.value = error.response?.data?.error || t('Login.googleFailed');
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
    errorMessage.value = t('Login.missingCredentials');
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
      errorMessage.value = t('Login.connectionError');
    }
  } finally {
    loading.value = false;
  }
}

async function register() {
  errorMessage.value = '';
  successMessage.value = '';
  if (!username.value || !password.value) {
    errorMessage.value = t('Login.missingCredentials');
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
      successMessage.value = t('Login.accountCreated');
    } else {
      emit('loginSuccess', response.data);
    }
  } catch (error) {
    if (error.response?.status === 409) {
      errorMessage.value = error.response.data.error || t('Login.usernameExists');
    } else if (error.response?.data?.error) {
      errorMessage.value = error.response.data.error;
    } else {
      errorMessage.value = t('Login.registrationFailed');
    }
  } finally {
    loading.value = false;
  }
}

async function forgotPassword() {
  errorMessage.value = '';
  successMessage.value = '';
  if (!forgotEmail.value) {
    errorMessage.value = t('Login.missingEmail');
    return;
  }
  loading.value = true;
  try {
    await api.post(`/auth/forgot-password`, { email: forgotEmail.value });
    successMessage.value = t('Login.resetLinkSent');
  } catch {
    errorMessage.value = t('Login.resetEmailError');
  } finally {
    loading.value = false;
  }
}

async function resetPassword() {
  errorMessage.value = '';
  successMessage.value = '';
  if (!newPassword.value) {
    errorMessage.value = t('Login.missingNewPassword');
    return;
  }
  if (newPassword.value.length < MIN_PASSWORD_LENGTH) {
    errorMessage.value = t('Login.passwordTooShort', { min: MIN_PASSWORD_LENGTH });
    return;
  }
  loading.value = true;
  try {
    await api.post(`/auth/reset-password`, {
      token: resetToken.value,
      password: newPassword.value
    });
    successMessage.value = t('Login.passwordResetDone');
    view.value = 'login';
  } catch (error) {
    errorMessage.value = error.response?.data?.error || t('Login.resetFailed');
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
.login-lang { position:absolute; top:14px; right:14px; display:flex; gap:2px; }
.login-lang-btn { padding:2px 6px; border:0; border-radius:5px; background:transparent; color:#9aa6a3; font-size:10px; font-weight:750; letter-spacing:.06em; }
.login-lang-btn:hover { color:#455651; }
.login-lang-active { background:#e6f5f0; color:#0d846f; }
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