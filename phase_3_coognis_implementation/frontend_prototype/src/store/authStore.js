import { reactive } from 'vue';
import authService from '@/services/authService';
import {
  MOCK_AUTH_ENABLED,
  clearMockAuth,
  clearMockPendingTwoFactor,
  getMockCurrentUser,
  getMockPendingTwoFactor,
  setMockCurrentUser,
  setMockPendingTwoFactor,
} from '@/utils/mockAuth';

const state = reactive({
  currentUser: MOCK_AUTH_ENABLED ? getMockCurrentUser() : null,
  isAuthenticated: MOCK_AUTH_ENABLED ? Boolean(getMockCurrentUser()) : false,
  pendingTwoFactor: MOCK_AUTH_ENABLED ? getMockPendingTwoFactor() : null,
  isSessionResolved: MOCK_AUTH_ENABLED,
  isInitializingSession: false,
});

let sessionInitializationPromise = null;

function normalizeRole(role) {
  if (!role) {
    return null;
  }

  return String(role).toLowerCase();
}

function extractRole(source) {
  if (!source) {
    return null;
  }

  return normalizeRole(source.role || source.user_role || source.account_role);
}

function setCurrentUser(user) {
  state.currentUser = user || null;
  state.isAuthenticated = Boolean(user);
  state.pendingTwoFactor = null;
  state.isSessionResolved = true;

  if (MOCK_AUTH_ENABLED && user) {
    setMockCurrentUser(user);
    clearMockPendingTwoFactor();
  }
}

function setPendingTwoFactor(payload = {}) {
  state.pendingTwoFactor = {
    role: extractRole(payload.user || payload.account || payload),
    user: payload.user || payload.account || null,
    challengeId: payload.challenge_id || payload.challengeId || payload.challenge_token || payload.token || null,
    redirectTo: payload.redirect_to || null,
    email: payload.email || payload.user?.email || null,
    setupRequired: Boolean(payload.setup_required || payload.setupRequired),
    rememberDeviceDays: Number(payload.remember_device_days || payload.rememberDeviceDays || 0) || 0,
  };
  state.currentUser = null;
  state.isAuthenticated = false;
  state.isSessionResolved = true;

  if (MOCK_AUTH_ENABLED) {
    setMockPendingTwoFactor(state.pendingTwoFactor);
  }
}

function clearPendingTwoFactor() {
  state.pendingTwoFactor = null;
  state.isSessionResolved = true;

  if (MOCK_AUTH_ENABLED) {
    clearMockPendingTwoFactor();
  }
}

function clearAuth() {
  state.currentUser = null;
  state.isAuthenticated = false;
  state.pendingTwoFactor = null;
  state.isSessionResolved = true;

  if (MOCK_AUTH_ENABLED) {
    clearMockAuth();
  }
}

async function initializeSession(force = false) {
  if (state.pendingTwoFactor) {
    state.isSessionResolved = true;
    return state.currentUser;
  }

  if (!force && state.isSessionResolved) {
    return state.currentUser;
  }

  if (sessionInitializationPromise) {
    return sessionInitializationPromise;
  }

  state.isInitializingSession = true;

  sessionInitializationPromise = (async () => {
    const response = await authService.fetchCurrentUser();

    if (response.success) {
      const payload = response.data || {};
      const user = payload.user || payload.account || payload;

      state.currentUser = user || null;
      state.isAuthenticated = Boolean(user);
      state.pendingTwoFactor = null;
      state.isSessionResolved = true;

      return state.currentUser;
    }

    state.currentUser = null;
    state.isAuthenticated = false;
    state.pendingTwoFactor = null;
    state.isSessionResolved = true;

    if (MOCK_AUTH_ENABLED) {
      clearMockAuth();
    }

    return null;
  })();

  try {
    return await sessionInitializationPromise;
  } finally {
    sessionInitializationPromise = null;
    state.isInitializingSession = false;
  }
}

function resolveRoleFromPayload(payload) {
  if (!payload) {
    return null;
  }

  return extractRole(payload.user || payload.account || payload) || state.pendingTwoFactor?.role || null;
}

function resolveDashboardPath(role) {
  if (role === 'expert') {
    return '/expert';
  }

  if (role === 'admin') {
    return '/admin';
  }

  return '/user';
}

function hasRequiredRole(role) {
  if (!role) {
    return true;
  }

  return resolveRoleFromPayload(state.currentUser) === normalizeRole(role);
}

export default {
  state,
  setCurrentUser,
  setPendingTwoFactor,
  clearPendingTwoFactor,
  clearAuth,
  initializeSession,
  resolveRoleFromPayload,
  resolveDashboardPath,
  hasRequiredRole,
};
