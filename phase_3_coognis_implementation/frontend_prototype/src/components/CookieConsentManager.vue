<template>
  <div v-if="isReady">
    <div v-if="showBanner" class="cookie-consent">
      <div class="cookie-consent__panel">
        <div class="cookie-consent__copy">
          <p class="cookie-consent__eyebrow mb-2">Cookie settings</p>
          <h2 class="cookie-consent__title">Control optional cookies</h2>
          <p class="cookie-consent__text mb-0">
            COOGNIS uses strictly necessary cookies for authentication and security. Optional cookies are used only for
            preferences and analytics if consent is given.
          </p>
        </div>

        <div class="cookie-consent__actions">
          <button class="btn btn-outline-secondary" type="button" @click="rejectAll">Reject all</button>
          <button class="btn btn-outline-primary" type="button" @click="openSettings">Customize</button>
          <button class="btn btn-primary" type="button" @click="acceptAll">Accept all</button>
        </div>
      </div>
    </div>

    <BaseModal
      :visible="isSettingsOpen"
      eyebrow="Privacy"
      title="Cookie settings"
      modal-id="cookie-settings-modal"
      dialog-class="modal-dialog-centered"
      @close="closeSettings"
    >
      <div class="cookie-consent__modal-copy mb-4">
        <p class="mb-0">
          Strictly necessary cookies are always on because they keep login, security, and core application behavior
          working. Optional categories can be enabled or disabled below.
        </p>
      </div>

      <div class="cookie-consent__category-list">
        <div class="cookie-consent__category">
          <div>
            <h3 class="cookie-consent__category-title">Strictly necessary</h3>
            <p class="cookie-consent__category-text mb-0">
              Required for authentication, session integrity, CSRF/session protection, and other core security
              functions.
            </p>
          </div>
          <div class="form-check form-switch">
            <input id="cookie-category-necessary" class="form-check-input" type="checkbox" checked disabled />
            <label class="form-check-label" for="cookie-category-necessary">Always on</label>
          </div>
        </div>

        <div class="cookie-consent__category">
          <div>
            <h3 class="cookie-consent__category-title">Preferences</h3>
            <p class="cookie-consent__category-text mb-0">
              Stores optional experience preferences so the interface can remember non-essential choices between visits.
            </p>
          </div>
          <div class="form-check form-switch">
            <input
              id="cookie-category-preferences"
              v-model="draftCategories.preferences"
              class="form-check-input"
              type="checkbox"
            />
            <label class="form-check-label" for="cookie-category-preferences">
              {{ draftCategories.preferences ? 'Enabled' : 'Disabled' }}
            </label>
          </div>
        </div>

        <div class="cookie-consent__category">
          <div>
            <h3 class="cookie-consent__category-title">Analytics</h3>
            <p class="cookie-consent__category-text mb-0">
              Allows anonymous usage measurement and product analytics when those tools are enabled in the future.
            </p>
          </div>
          <div class="form-check form-switch">
            <input
              id="cookie-category-analytics"
              v-model="draftCategories.analytics"
              class="form-check-input"
              type="checkbox"
            />
            <label class="form-check-label" for="cookie-category-analytics">
              {{ draftCategories.analytics ? 'Enabled' : 'Disabled' }}
            </label>
          </div>
        </div>
      </div>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" @click="rejectAll">Reject all</button>
        <button class="btn btn-outline-primary" type="button" @click="acceptAll">Accept all</button>
        <button class="btn btn-primary" type="button" @click="saveSettings">Save selection</button>
      </template>
    </BaseModal>
  </div>
</template>

<script>
import BaseModal from '@/components/BaseModal.vue';
import cookieConsentService from '@/services/cookieConsentService';

export default {
  name: 'CookieConsentManager',
  components: {
    BaseModal,
  },
  data() {
    return {
      draftCategories: {
        necessary: true,
        preferences: false,
        analytics: false,
      },
    };
  },
  computed: {
    consentState() {
      return cookieConsentService.state;
    },
    isReady() {
      return this.consentState.initialized;
    },
    showBanner() {
      return this.consentState.visible && !this.consentState.settingsOpen;
    },
    isSettingsOpen() {
      return this.consentState.settingsOpen;
    },
  },
  created() {
    cookieConsentService.initializeConsent();
    this.syncDraftFromState();
  },
  watch: {
    isSettingsOpen(value) {
      if (value) {
        this.syncDraftFromState();
      }
    },
  },
  methods: {
    syncDraftFromState() {
      this.draftCategories = {
        necessary: true,
        preferences: Boolean(this.consentState.categories.preferences),
        analytics: Boolean(this.consentState.categories.analytics),
      };
    },
    acceptAll() {
      cookieConsentService.acceptAll();
      this.syncDraftFromState();
    },
    rejectAll() {
      cookieConsentService.rejectAll();
      this.syncDraftFromState();
    },
    openSettings() {
      this.syncDraftFromState();
      cookieConsentService.openSettings();
    },
    closeSettings() {
      cookieConsentService.closeSettings();
    },
    saveSettings() {
      cookieConsentService.saveCategories(this.draftCategories);
      this.syncDraftFromState();
    },
  },
};
</script>
