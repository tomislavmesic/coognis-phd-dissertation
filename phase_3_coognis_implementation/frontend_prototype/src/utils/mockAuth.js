const MOCK_AUTH_ENABLED = import.meta.env.VITE_ENABLE_MOCK_AUTH === 'true';
const MOCK_AUTH_REQUIRE_2FA = import.meta.env.VITE_MOCK_AUTH_REQUIRE_2FA !== 'false';
const MOCK_2FA_CODE = import.meta.env.VITE_MOCK_AUTH_2FA_CODE || '123456';
const PROTOTYPE_ROLE = String(import.meta.env.VITE_PROTOTYPE_ROLE || 'user').toLowerCase();
const PROTOTYPE_EMAIL =
  import.meta.env.VITE_PROTOTYPE_EMAIL ||
  `${PROTOTYPE_ROLE === 'admin' ? 'admin' : PROTOTYPE_ROLE === 'expert' ? 'expert' : 'user'}@prototype.local`;
const PROTOTYPE_DEBUG_PANELS =
  import.meta.env.VITE_PROTOTYPE_DEBUG_PANELS === 'true';

const STORAGE_KEYS = {
  currentUser: 'synexis.mock.currentUser',
  pendingTwoFactor: 'synexis.mock.pendingTwoFactor',
};

function hasStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function readStorage(key) {
  if (!hasStorage()) {
    return null;
  }

  const rawValue = window.localStorage.getItem(key);

  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue);
  } catch {
    return null;
  }
}

function writeStorage(key, value) {
  if (!hasStorage()) {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
}

function removeStorage(key) {
  if (!hasStorage()) {
    return;
  }

  window.localStorage.removeItem(key);
}

function delay(ms = 200) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function resolveMockRole(email = '') {
  const normalizedEmail = String(email).toLowerCase();

  if (normalizedEmail.includes('admin')) {
    return 'admin';
  }

  if (normalizedEmail.includes('expert')) {
    return 'expert';
  }

  return 'user';
}

function resolveMockDashboardPath(role) {
  if (role === 'expert') {
    return '/expert';
  }

  if (role === 'admin') {
    return '/admin';
  }

  return '/user';
}

function shouldRequireTwoFactor(email = '') {
  if (!MOCK_AUTH_REQUIRE_2FA) {
    return false;
  }

  return !String(email).toLowerCase().includes('no2fa');
}

function createMockUser(payload = {}) {
  const email = payload.email || 'user@example.com';
  const role = payload.role || resolveMockRole(email);

  return {
    id: payload.id || `mock-${role}`,
    first_name: payload.first_name || role.charAt(0).toUpperCase() + role.slice(1),
    last_name: payload.last_name || 'Demo',
    email,
    role,
    ai_profiling_consent:
      typeof payload.ai_profiling_consent === 'boolean' ? payload.ai_profiling_consent : true,
    gdpr_consent: typeof payload.gdpr_consent === 'boolean' ? payload.gdpr_consent : true,
    can_access_chat_debug_panels: Boolean(payload.can_access_chat_debug_panels),
  };
}

function createPrototypeUser() {
  return createMockUser({
    email: PROTOTYPE_EMAIL,
    role: PROTOTYPE_ROLE,
    can_access_chat_debug_panels: PROTOTYPE_DEBUG_PANELS,
  });
}

function getMockCurrentUser() {
  const storedUser = readStorage(STORAGE_KEYS.currentUser);

  if (storedUser) {
    return storedUser;
  }

  if (!MOCK_AUTH_ENABLED) {
    return null;
  }

  const prototypeUser = createPrototypeUser();
  setMockCurrentUser(prototypeUser);
  return prototypeUser;
}

function setMockCurrentUser(user) {
  writeStorage(STORAGE_KEYS.currentUser, user);
}

function clearMockCurrentUser() {
  removeStorage(STORAGE_KEYS.currentUser);
}

function getMockPendingTwoFactor() {
  return readStorage(STORAGE_KEYS.pendingTwoFactor);
}

function setMockPendingTwoFactor(challenge) {
  writeStorage(STORAGE_KEYS.pendingTwoFactor, challenge);
}

function clearMockPendingTwoFactor() {
  removeStorage(STORAGE_KEYS.pendingTwoFactor);
}

function clearMockAuth() {
  clearMockCurrentUser();
  clearMockPendingTwoFactor();
}

export {
  MOCK_AUTH_ENABLED,
  MOCK_2FA_CODE,
  clearMockAuth,
  clearMockCurrentUser,
  clearMockPendingTwoFactor,
  createMockUser,
  delay,
  getMockCurrentUser,
  getMockPendingTwoFactor,
  resolveMockDashboardPath,
  resolveMockRole,
  setMockCurrentUser,
  setMockPendingTwoFactor,
  shouldRequireTwoFactor,
  createPrototypeUser,
};
