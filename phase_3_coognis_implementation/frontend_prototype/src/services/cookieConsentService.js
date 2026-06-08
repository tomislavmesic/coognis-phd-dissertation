import { reactive } from 'vue';

const STORAGE_KEY = 'coognis.cookie-consent.v1';
const POLICY_VERSION = '2026-05-04';

const DEFAULT_CATEGORIES = {
  necessary: true,
  preferences: false,
  analytics: false,
};

const state = reactive({
  initialized: false,
  decided: false,
  visible: false,
  settingsOpen: false,
  policyVersion: POLICY_VERSION,
  categories: {
    ...DEFAULT_CATEGORIES,
  },
  updatedAt: null,
});

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function normalizeStoredValue(rawValue) {
  if (!rawValue || typeof rawValue !== 'object') {
    return null;
  }

  const categories = rawValue.categories || {};
  return {
    decided: Boolean(rawValue.decided),
    visible: false,
    settingsOpen: false,
    policyVersion: typeof rawValue.policyVersion === 'string' ? rawValue.policyVersion : POLICY_VERSION,
    categories: {
      necessary: true,
      preferences: Boolean(categories.preferences),
      analytics: Boolean(categories.analytics),
    },
    updatedAt: typeof rawValue.updatedAt === 'string' ? rawValue.updatedAt : null,
  };
}

function persistState() {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      decided: state.decided,
      policyVersion: state.policyVersion,
      categories: {
        necessary: true,
        preferences: state.categories.preferences,
        analytics: state.categories.analytics,
      },
      updatedAt: state.updatedAt,
    })
  );
}

function applyDecision(categories) {
  state.categories = {
    necessary: true,
    preferences: Boolean(categories.preferences),
    analytics: Boolean(categories.analytics),
  };
  state.decided = true;
  state.visible = false;
  state.settingsOpen = false;
  state.updatedAt = new Date().toISOString();
  persistState();
}

function initializeConsent() {
  if (state.initialized) {
    return;
  }

  if (canUseStorage()) {
    const rawValue = window.localStorage.getItem(STORAGE_KEY);
    if (rawValue) {
      try {
        const parsed = JSON.parse(rawValue);
        const normalized = normalizeStoredValue(parsed);
        if (normalized) {
          Object.assign(state, normalized);
        }
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }
  }

  if (!state.decided) {
    state.visible = true;
  }

  state.initialized = true;
}

function openSettings() {
  state.settingsOpen = true;
}

function closeSettings() {
  state.settingsOpen = false;
}

function acceptAll() {
  applyDecision({
    preferences: true,
    analytics: true,
  });
}

function rejectAll() {
  applyDecision({
    preferences: false,
    analytics: false,
  });
}

function saveCategories(categories) {
  applyDecision(categories);
}

export default {
  state,
  initializeConsent,
  openSettings,
  closeSettings,
  acceptAll,
  rejectAll,
  saveCategories,
};
