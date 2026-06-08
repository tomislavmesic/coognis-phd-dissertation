<template>
  <section class="user-settings" aria-labelledby="admin-settings-title">
    <BasePageHeader
      eyebrow="Admin"
      title="Admin settings"
      description="Manage personal account details, cookie preferences, and consent settings for the authenticated admin account."
      header-class="user-settings__header"
    />

    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" role="alert" />

    <div class="row g-4">
      <div class="col-xl-7">
        <BaseCard
          title="Account details"
          card-class="h-auto"
          card-header-class="pb-0"
        >
          <form class="row g-3" novalidate @submit.prevent="handleSubmit">
            <div class="col-md-6">
              <label class="form-label" for="admin-settings-first-name">First name</label>
              <input
                id="admin-settings-first-name"
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
              <label class="form-label" for="admin-settings-last-name">Last name</label>
              <input
                id="admin-settings-last-name"
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
              <label class="form-label" for="admin-settings-email">Email</label>
              <input
                id="admin-settings-email"
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
                      id="admin-settings-gdpr-consent"
                      v-model="form.gdpr_consent"
                      class="form-check-input"
                      type="checkbox"
                      role="switch"
                      :disabled="isSubmitting"
                    />
                    <label class="form-check-label" for="admin-settings-gdpr-consent">
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
      </div>

      <div class="col-xl-5">
        <ChangePasswordCard card-class="mb-4 h-auto" />

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
      modal-id="admin-cookie-settings-modal"
      dialog-class="modal-dialog-centered"
      @close="closeCookieSettingsModal"
    >
      <CookieConsentSettingsSection id-prefix="admin-cookie-settings-modal" :show-card="false" />
    </BaseModal>
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
import authStore from '@/store/authStore';
import { email, required, validateField, validateFields } from '@/utils/formValidation';

export default {
  name: 'AdminSettingsView',
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
      isCookieSettingsModalOpen: false,
      successMessage: '',
      errorMessage: '',
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
    };
  },
  computed: {
    currentUser() {
      return authStore.state.currentUser || {};
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
    openCookieSettingsModal() {
      this.isCookieSettingsModalOpen = true;
    },
    closeCookieSettingsModal() {
      this.isCookieSettingsModalOpen = false;
    },
    validateFieldState(fieldName) {
      this.errors = validateField(fieldName, this.form, this.errors, this.validationRules);
      return !this.errors[fieldName];
    },
    validateForm() {
      this.errors = validateFields(Object.keys(this.validationRules), this.form, this.validationRules);
      return Object.values(this.errors).every((value) => !value);
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
        this.successMessage = 'Admin account settings updated successfully.';
      } else {
        this.errorMessage = response.error?.message || 'Unable to update admin settings.';
      }

      this.isSubmitting = false;
    },
  },
};
</script>
