<template>
  <component
    :is="showCard ? BaseCard : 'div'"
    v-bind="cardBindings"
  >
    <div class="cookie-consent__modal-copy mb-4">
      <p class="mb-0">
        Strictly necessary cookies support authentication, session integrity, and core security behavior. Optional
        categories below are stored only after a consent decision is saved.
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
          <input :id="`${idPrefix}-necessary`" class="form-check-input" type="checkbox" checked disabled />
          <label class="form-check-label" :for="`${idPrefix}-necessary`">Always on</label>
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
            :id="`${idPrefix}-preferences`"
            v-model="draftCategories.preferences"
            class="form-check-input"
            type="checkbox"
          />
          <label class="form-check-label" :for="`${idPrefix}-preferences`">
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
            :id="`${idPrefix}-analytics`"
            v-model="draftCategories.analytics"
            class="form-check-input"
            type="checkbox"
          />
          <label class="form-check-label" :for="`${idPrefix}-analytics`">
            {{ draftCategories.analytics ? 'Enabled' : 'Disabled' }}
          </label>
        </div>
      </div>
    </div>

    <div class="cookie-consent__actions mt-4">
      <button class="btn btn-outline-secondary" type="button" @click="rejectAll">Reject all</button>
      <button class="btn btn-outline-primary" type="button" @click="acceptAll">Accept all</button>
      <button class="btn btn-primary" type="button" @click="saveSettings">Save selection</button>
    </div>
  </component>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue';
import cookieConsentService from '@/services/cookieConsentService';

export default {
  name: 'CookieConsentSettingsSection',
  components: {
    BaseCard,
  },
  props: {
    idPrefix: {
      type: String,
      default: 'cookie-settings',
    },
    showCard: {
      type: Boolean,
      default: true,
    },
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
    cardBindings() {
      if (!this.showCard) {
        return {};
      }

      return {
        title: 'Cookie settings',
        subtitle: 'Strictly necessary cookies stay enabled. Optional categories can be reviewed and changed at any time.',
        cardClass: 'h-auto',
      };
    },
    consentState() {
      return cookieConsentService.state;
    },
  },
  created() {
    cookieConsentService.initializeConsent();
    this.syncDraftFromState();
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
    saveSettings() {
      cookieConsentService.saveCategories(this.draftCategories);
      this.syncDraftFromState();
    },
  },
};
</script>
