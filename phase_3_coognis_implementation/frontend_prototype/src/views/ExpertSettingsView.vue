<template>
  <section class="user-settings" aria-labelledby="expert-settings-title">
    <BasePageHeader
      eyebrow="Expert workspace"
      title="Expert settings"
      description="Manage the account details tied to your authenticated expert profile."
      header-class="user-settings__header"
    />

    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" role="alert" />

    <BaseLoadingState
      v-if="isLoading"
      class="user-settings__loading"
      label="Loading expert settings..."
    />

    <div v-else class="row g-4">
      <div class="col-xl-7">
        <BaseCard
          title="Account details"
          card-class="h-auto"
          card-header-class="pb-0"
        >
          <form class="row g-3" novalidate @submit.prevent="handleSubmit">
            <div class="col-md-6">
              <label class="form-label" for="expert-settings-first-name">First name</label>
              <input
                id="expert-settings-first-name"
                v-model.trim="form.first_name"
                class="form-control"
                :class="{ 'is-invalid': errors.first_name }"
                type="text"
                autocomplete="given-name"
                :disabled="isSubmitting"
                @blur="validateFieldState('first_name')"
              />
              <div v-if="errors.first_name" class="invalid-feedback d-block">{{ errors.first_name }}</div>
            </div>

            <div class="col-md-6">
              <label class="form-label" for="expert-settings-last-name">Last name</label>
              <input
                id="expert-settings-last-name"
                v-model.trim="form.last_name"
                class="form-control"
                :class="{ 'is-invalid': errors.last_name }"
                type="text"
                autocomplete="family-name"
                :disabled="isSubmitting"
                @blur="validateFieldState('last_name')"
              />
              <div v-if="errors.last_name" class="invalid-feedback d-block">{{ errors.last_name }}</div>
            </div>

            <div class="col-12">
              <label class="form-label" for="expert-settings-email">Email</label>
              <input
                id="expert-settings-email"
                v-model.trim="form.email"
                class="form-control"
                :class="{ 'is-invalid': errors.email }"
                type="email"
                autocomplete="email"
                :disabled="isSubmitting"
                @blur="validateFieldState('email')"
              />
              <div v-if="errors.email" class="invalid-feedback d-block">{{ errors.email }}</div>
            </div>

            <div class="col-12 pt-4">
              <div class="card base-card">
                <div class="card-body">
                  <div class="form-check form-switch">
                    <input
                      id="expert-settings-ai-consent"
                      v-model="form.ai_profiling_consent"
                      class="form-check-input"
                      type="checkbox"
                      role="switch"
                      :disabled="isSubmitting"
                    />
                    <label class="form-check-label" for="expert-settings-ai-consent">
                      AI profiling consent
                    </label>
                  </div>
                  <p class="text-body-secondary mb-0">
                    Allows COOGNIS to use profiling-based personalization and expert matching signals for your expert account.
                  </p>
                </div>
              </div>
            </div>

            <div class="col-12 pb-4">
              <div class="card base-card">
                <div class="card-body">
                  <div class="form-check form-switch">
                    <input
                      id="expert-settings-gdpr-consent"
                      v-model="form.gdpr_consent"
                      class="form-check-input"
                      type="checkbox"
                      role="switch"
                      :disabled="isSubmitting"
                    />
                    <label class="form-check-label" for="expert-settings-gdpr-consent">
                      GDPR consent
                    </label>
                  </div>
                  <p class="text-body-secondary mb-0">
                    Confirms consent for lawful storage and processing of the expert account data needed to operate within COOGNIS.
                  </p>
                </div>
              </div>
            </div>

            <div class="col-12 d-flex flex-wrap gap-3">
              <button class="btn btn-primary" type="submit" :disabled="isSubmitting">
                {{ isSubmitting ? 'Saving...' : 'Save settings' }}
              </button>
              <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="resetForm">
                Reset
              </button>
            </div>
          </form>
        </BaseCard>
      </div>

      <div class="col-xl-5">
        <BaseCard
          title="Account state"
          card-class="h-auto mb-4"
          card-header-class="pb-0"
        >
          <dl class="user-settings__meta-list mb-0">
            <div v-if="this.currentUser.registration_status !== 'approved'" class="user-settings__meta-item">
              <dt>Registration status</dt>
              <dd>
                <span class="badge" :class="registrationStatusClass">
                  {{ registrationStatusLabel }}
                </span>
              </dd>
            </div>
            <div class="user-settings__meta-item">
              <dt>Profiling consent</dt>
              <dd>
                <span class="badge" :class="currentUser.ai_profiling_consent ? 'text-bg-success' : 'text-bg-secondary'">
                  {{ currentUser.ai_profiling_consent ? 'Granted' : 'Withdrawn' }}
                </span>
              </dd>
            </div>
            <div class="user-settings__meta-item">
              <dt>GDPR consent</dt>
              <dd>
                <span class="badge" :class="currentUser.gdpr_consent ? 'text-bg-success' : 'text-bg-secondary'">
                  {{ currentUser.gdpr_consent ? 'Granted' : 'Withdrawn' }}
                </span>
              </dd>
            </div>
            <div class="user-settings__meta-item">
              <dt>Two-factor authentication</dt>
              <dd>
                <span class="badge" :class="currentUser.two_factor_enabled ? 'text-bg-success' : 'text-bg-secondary'">
                  {{ currentUser.two_factor_enabled ? 'Enabled' : 'Disabled' }}
                </span>
              </dd>
            </div>
          </dl>
        </BaseCard>

        <ChangePasswordCard card-class="mb-4 h-auto" />

        <BaseCard
          title="Cookie settings"
          subtitle="Strictly necessary cookies remain enabled. Optional categories can be reviewed and changed when needed."
          card-class="mb-4 h-auto"
          card-header-class="pb-0"
        >
          <button class="btn btn-outline-primary" type="button" @click="openCookieSettingsModal">
            Manage cookie settings
          </button>
        </BaseCard>

      </div>
    </div>

    <BaseModal
      :visible="isCookieSettingsModalOpen"
      eyebrow="Privacy"
      title="Cookie settings"
      modal-id="expert-cookie-settings-modal"
      dialog-class="modal-dialog-centered"
      @close="closeCookieSettingsModal"
    >
      <CookieConsentSettingsSection id-prefix="expert-cookie-settings-modal" :show-card="false" />
    </BaseModal>
  </section>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BaseModal from '@/components/BaseModal.vue';
import ChangePasswordCard from '@/components/ChangePasswordCard.vue';
import CookieConsentSettingsSection from '@/components/CookieConsentSettingsSection.vue';
import BaseLoadingState from '@/components/BaseLoadingState.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import authService from '@/services/authService';
import authStore from '@/store/authStore';
import { email, required, validateField, validateFields } from '@/utils/formValidation';

export default {
  name: 'ExpertSettingsView',
  components: {
    BaseAlert,
    BaseCard,
    BaseModal,
    ChangePasswordCard,
    CookieConsentSettingsSection,
    BaseLoadingState,
    BasePageHeader,
  },
  data() {
    return {
      isLoading: true,
      isSubmitting: false,
      isCookieSettingsModalOpen: false,
      successMessage: '',
      errorMessage: '',
      form: {
        first_name: '',
        last_name: '',
        email: '',
        ai_profiling_consent: false,
        gdpr_consent: false,
      },
      errors: {
        first_name: '',
        last_name: '',
        email: '',
      },
    };
  },
  computed: {
    currentUser() {
      return authStore.state.currentUser || {};
    },
    fullName() {
      const fullName = `${this.currentUser.first_name || ''} ${this.currentUser.last_name || ''}`.trim();

      return fullName || this.currentUser.email || 'Expert account';
    },
    registrationStatusLabel() {
      return (this.currentUser.registration_status || 'approved').replace(/_/g, ' ');
    },
    registrationStatusClass() {
      const status = this.currentUser.registration_status || 'approved';

      if (status === 'approved') {
        return 'text-bg-success';
      }

      if (status === 'pending_approval') {
        return 'text-bg-warning';
      }

      if (status === 'rejected') {
        return 'text-bg-danger';
      }

      return 'text-bg-secondary';
    },
    validationRules() {
      return {
        first_name: [required('First name is required.')],
        last_name: [required('Last name is required.')],
        email: [required('Email is required.'), email('Enter a valid email address.')],
      };
    },
  },
  async created() {
    await this.loadCurrentUser();
  },
  methods: {
    populateForm(user = this.currentUser) {
      this.form.first_name = user.first_name || '';
      this.form.last_name = user.last_name || '';
      this.form.email = user.email || '';
      this.form.ai_profiling_consent = Boolean(user.ai_profiling_consent);
      this.form.gdpr_consent = Boolean(user.gdpr_consent);
    },
    resetForm() {
      this.successMessage = '';
      this.errorMessage = '';
      this.errors = {
        first_name: '',
        last_name: '',
        email: '',
      };
      this.populateForm();
    },
    validateFieldState(fieldName) {
      this.errors = validateField(fieldName, this.form, this.errors, this.validationRules);
      return !this.errors[fieldName];
    },
    validateForm() {
      this.errors = validateFields(Object.keys(this.validationRules), this.form, this.validationRules);
      return Object.values(this.errors).every((value) => !value);
    },
    async loadCurrentUser() {
      this.isLoading = true;
      this.errorMessage = '';

      const response = await authService.fetchCurrentUser();

      if (response.success) {
        const user = response.data?.user || response.data || {};
        authStore.setCurrentUser(user);
        this.populateForm(user);
      } else {
        this.errorMessage = response.error?.message || 'Unable to load expert settings.';
        this.populateForm();
      }

      this.isLoading = false;
    },
    openCookieSettingsModal() {
      this.isCookieSettingsModalOpen = true;
    },
    closeCookieSettingsModal() {
      this.isCookieSettingsModalOpen = false;
    },
    async handleSubmit() {
      if (!this.validateForm()) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await authService.updateCurrentUserSettings({
        first_name: this.form.first_name,
        last_name: this.form.last_name,
        email: this.form.email,
        ai_profiling_consent: this.form.ai_profiling_consent,
        gdpr_consent: this.form.gdpr_consent,
      });

      if (response.success) {
        const user = response.data?.user || response.data || {};
        authStore.setCurrentUser(user);
        this.populateForm(user);
        this.successMessage = 'Expert account settings updated successfully.';
      } else {
        this.errorMessage = response.error?.message || 'Unable to update expert settings.';
      }

      this.isSubmitting = false;
    },
  },
};
</script>
