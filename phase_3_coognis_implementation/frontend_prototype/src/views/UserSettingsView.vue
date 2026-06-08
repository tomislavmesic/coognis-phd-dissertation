<template>
  <section class="user-settings" aria-labelledby="user-settings-title">
    <BasePageHeader
      eyebrow="User workspace"
      title="User settings"
      description="Manage personal account details, cookie preferences, and privacy-related actions."
      header-class="user-settings__header"
    />

    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" role="alert" />

    <div class="row g-4">
      <div class="col-xl-7">
        <BaseCard
          title="Account details"
          card-class="h-auto mb-4"
          card-header-class="pb-0"
        >
          <form class="row g-3" novalidate @submit.prevent="handleSubmit">
            <div class="col-md-6">
              <label class="form-label" for="user-settings-first-name">First name</label>
              <input
                id="user-settings-first-name"
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
              <label class="form-label" for="user-settings-last-name">Last name</label>
              <input
                id="user-settings-last-name"
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
              <label class="form-label" for="user-settings-email">Email</label>
              <input
                id="user-settings-email"
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

            <div class="col-12 pt-4 pb-4">
              <div class="card base-card">
                <div class="card-body">
                  <div class="form-check form-switch">
                    <input
                      id="user-settings-gdpr-consent"
                      v-model="form.gdpr_consent"
                      class="form-check-input"
                      type="checkbox"
                      role="switch"
                      :disabled="isSubmitting"
                    />
                    <label class="form-check-label" for="user-settings-gdpr-consent">
                      GDPR consent
                    </label>
                  </div>
                  <p class="text-body-secondary mb-0">
                    Confirms consent for lawful storage and processing of the account data needed to operate within
                    COOGNIS.
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

        <BaseCard
          title="Privacy actions"
          subtitle="Withdraw profiling consent or request deletion when stricter account-level privacy changes are needed."
          card-class="h-auto"
          card-header-class="pb-0"
        >
          <div class="d-flex flex-wrap gap-3">
            <button
              class="btn btn-outline-warning flex-grow-1"
              type="button"
              :disabled="isSubmitting || !consentState.ai_profiling_consent"
              @click="openConfirmation('withdrawProfiling')"
            >
              Withdraw AI profiling consent
            </button>

            <button
              class="btn btn-outline-danger flex-grow-1"
              type="button"
              :disabled="isSubmitting"
              @click="openConfirmation('requestDeletion')"
            >
              Request full data deletion
            </button>
          </div>

          <div class="alert alert-warning mt-4 mb-0" role="alert">
            Opting out of AI profiling may reduce personalization quality. Full account deletion removes access and
            starts permanent data removal processing.
          </div>
        </BaseCard>
      </div>

      <div class="col-xl-5">
        <BaseCard
          title="Account state"
          card-header-class="pb-0"
          card-class="h-auto"
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
              <dt>Two-factor authentication</dt>
              <dd>
                <span class="badge" :class="currentUser.two_factor_enabled ? 'text-bg-success' : 'text-bg-secondary'">
                  {{ currentUser.two_factor_enabled ? 'Enabled' : 'Disabled' }}
                </span>
              </dd>
            </div>
          </dl>
        </BaseCard>

        <ChangePasswordCard card-class="mt-4 mb-4 h-auto" />

        <BaseCard
          title="Cookie settings"
          subtitle="Strictly necessary cookies remain enabled. Optional categories can be reviewed and changed when needed."
          card-class="h-auto"
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
      modal-id="user-cookie-settings-modal"
      dialog-class="modal-dialog-centered"
      @close="closeCookieSettingsModal"
    >
      <CookieConsentSettingsSection id-prefix="user-cookie-settings-modal" :show-card="false" />
    </BaseModal>

    <div
      v-if="confirmationModal.visible"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="confirmationTitleId"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h2 :id="confirmationTitleId" class="modal-title h5 mb-0">
              {{ confirmationModal.title }}
            </h2>
            <button class="btn-close" type="button" aria-label="Close" @click="closeConfirmation"></button>
          </div>
          <div class="modal-body">
            <p class="mb-0">{{ confirmationModal.message }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeConfirmation">
              Cancel
            </button>
            <button class="btn" :class="confirmationModal.confirmButtonClass" type="button" :disabled="isSubmitting" @click="confirmAction">
              {{ isSubmitting ? confirmationModal.loadingLabel : confirmationModal.confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="confirmationModal.visible" class="modal-backdrop fade show"></div>
  </section>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BaseModal from '@/components/BaseModal.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import ChangePasswordCard from '@/components/ChangePasswordCard.vue';
import CookieConsentSettingsSection from '@/components/CookieConsentSettingsSection.vue';
import authService from '@/services/authService';
import privacyService from '@/services/privacyService';
import authStore from '@/store/authStore';
import { email, required, validateField, validateFields } from '@/utils/formValidation';

export default {
  name: 'UserSettingsView',
  components: {
    BaseAlert,
    BaseCard,
    BaseModal,
    BasePageHeader,
    ChangePasswordCard,
    CookieConsentSettingsSection,
  },
  data() {
    return {
      isSubmitting: false,
      successMessage: '',
      errorMessage: '',
      isCookieSettingsModalOpen: false,
      form: {
        first_name: '',
        last_name: '',
        email: '',
        gdpr_consent: true,
      },
      errors: {
        first_name: '',
        last_name: '',
        email: '',
      },
      consentState: {
        ai_profiling_consent: true,
        gdpr_consent: true,
      },
      confirmationModal: {
        visible: false,
        action: '',
        title: '',
        message: '',
        confirmLabel: '',
        loadingLabel: '',
        confirmButtonClass: 'btn-primary',
      },
      confirmationTitleId: 'privacy-confirmation-title',
    };
  },
  computed: {
    currentUser() {
      return authStore.state.currentUser || {};
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
  created() {
    this.populateForm();
  },
  methods: {
    populateForm(user = this.currentUser) {
      this.form.first_name = user.first_name || '';
      this.form.last_name = user.last_name || '';
      this.form.email = user.email || '';
      this.form.gdpr_consent = Boolean(user.gdpr_consent);
      this.consentState.ai_profiling_consent = Boolean(user.ai_profiling_consent);
      this.consentState.gdpr_consent = Boolean(user.gdpr_consent);
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
    openConfirmation(action) {
      this.successMessage = '';
      this.errorMessage = '';

      if (action === 'withdrawProfiling') {
        this.confirmationModal = {
          visible: true,
          action,
          title: 'Withdraw AI profiling consent',
          message:
            'This disables adaptive profiling features for the account. Standard platform use remains available, but personalization quality may decrease.',
          confirmLabel: 'Withdraw consent',
          loadingLabel: 'Withdrawing...',
          confirmButtonClass: 'btn-warning',
        };
        return;
      }

      this.confirmationModal = {
        visible: true,
        action,
        title: 'Request full data deletion',
        message:
          'This starts the full data deletion process and may permanently remove access after the request is processed.',
        confirmLabel: 'Request deletion',
        loadingLabel: 'Requesting...',
        confirmButtonClass: 'btn-danger',
      };
    },
    closeConfirmation() {
      this.confirmationModal.visible = false;
    },
    openCookieSettingsModal() {
      this.isCookieSettingsModalOpen = true;
    },
    closeCookieSettingsModal() {
      this.isCookieSettingsModalOpen = false;
    },
    async confirmAction() {
      if (this.confirmationModal.action === 'withdrawProfiling') {
        await this.handleWithdrawProfilingConsent();
        return;
      }

      await this.handleAccountDeletionRequest();
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
        gdpr_consent: this.form.gdpr_consent,
      });

      if (response.success) {
        const user = response.data?.user || response.data || {};
        authStore.setCurrentUser(user);
        this.populateForm(user);
        this.successMessage = 'User account settings updated successfully.';
      } else {
        this.errorMessage = response.error?.message || 'Unable to update user settings.';
      }

      this.isSubmitting = false;
    },
    async handleWithdrawProfilingConsent() {
      this.isSubmitting = true;
      this.errorMessage = '';
      this.successMessage = '';

      const response = await privacyService.updateConsentSettings({
        ai_profiling_consent: false,
      });

      if (response.success) {
        this.consentState.ai_profiling_consent = response.data?.ai_profiling_consent ?? false;
        this.successMessage = response.data?.message || 'AI profiling consent withdrawn successfully.';
        if (authStore.state.currentUser) {
          const updatedUser = {
            ...authStore.state.currentUser,
            ai_profiling_consent: this.consentState.ai_profiling_consent,
            profiling_opt_out_requested: response.data?.profiling_opt_out_requested ?? true,
          };
          authStore.setCurrentUser(updatedUser);
          this.populateForm(updatedUser);
        }
      } else {
        this.errorMessage = response.error?.message || 'Unable to update consent settings.';
      }

      this.isSubmitting = false;
      this.closeConfirmation();
    },
    async handleAccountDeletionRequest() {
      this.isSubmitting = true;
      this.errorMessage = '';
      this.successMessage = '';

      const response = await privacyService.requestAccountDeletion({
        reason: 'user_requested_deletion',
      });

      if (response.success) {
        this.successMessage = response.data?.message || 'Data deletion request submitted successfully.';
        if (authStore.state.currentUser) {
          const updatedUser = {
            ...authStore.state.currentUser,
            account_deletion_requested: response.data?.account_deletion_requested ?? true,
          };
          authStore.setCurrentUser(updatedUser);
          this.populateForm(updatedUser);
        }
      } else {
        this.errorMessage = response.error?.message || 'Unable to submit the data deletion request.';
      }

      this.isSubmitting = false;
      this.closeConfirmation();
    },
  },
};
</script>
