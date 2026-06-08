<template>
  <section class="form-section" aria-labelledby="register-panel-title">
    <div v-if="registrationSuccess" class="registration-success">
      <div class="p-4 p-md-5">
        <div class="registration-success__icon auth-theme-shell__brand-mark" aria-hidden="true">
          <BrandLogo variant="compact" />
        </div>
        <p class="auth-theme-shell__panel-eyebrow mb-2">Registration submitted</p>
        <h3 class="registration-success__title mb-3">Account request created and pending approval.</h3>
        <p class="registration-success__lede mb-3">
          Your COOGNIS registration has been received. Access remains locked until an administrator reviews and approves the account.
        </p>
        <p v-if="registrationSuccess.notificationEmailSent" class="registration-success__lede mb-4">
          A confirmation email has been sent to <strong>{{ registrationSuccess.email }}</strong>.
        </p>
        <p v-else class="registration-success__lede mb-4">
          Keep an eye on <strong>{{ registrationSuccess.email }}</strong> for the approval update.
        </p>
        <div class="form-actions d-flex flex-column align-items-center">
          <RouterLink class="btn btn-primary" to="/login">Go to login</RouterLink>
        </div>
      </div>
    </div>

    <template v-else>
      <BaseAlert
        v-if="errorMessage"
        class="app-alert app-alert--server"
        variant="danger"
        role="alert"
        :message="errorMessage"
      />

      <RegistrationForm
        :loading="isSubmitting"
        :error-message="errorMessage"
        :reset-on-success="resetFormFlag"
        @submit="handleRegistration"
        @show-consent-details="showConsentDetails"
      />
    </template>
  </section>

  <BaseModal
    :visible="consentModal.visible"
    eyebrow="Privacy"
    :title="consentModal.title"
    modal-id="register-consent-details-modal"
    dialog-class="modal-dialog-centered modal-lg"
    @close="closeConsentModal"
  >
    <p class="mb-0">{{ consentModal.message }}</p>
  </BaseModal>
</template>

<script>
import { RouterLink } from 'vue-router';
import BaseAlert from '@/components/BaseAlert.vue';
import BrandLogo from '@/components/BrandLogo.vue';
import BaseModal from '@/components/BaseModal.vue';
import RegistrationForm from '@/components/RegistrationForm.vue';
import authService from '@/services/authService';

const DEV_AUTH_PREVIEWS_ENABLED = import.meta.env.DEV;

export default {
  name: 'RegisterView',
  inject: ['authPanelState'],
  components: {
    BaseAlert,
    BrandLogo,
    BaseModal,
    RegistrationForm,
    RouterLink,
  },
  data() {
    return {
      isSubmitting: false,
      errorMessage: '',
      resetFormFlag: false,
      registrationSuccess: null,
      consentModal: {
        visible: false,
        title: '',
        message: '',
      },
    };
  },
  created() {
    this.initializePreviewMode();
  },
  methods: {
    initializePreviewMode() {
      if (!DEV_AUTH_PREVIEWS_ENABLED) {
        return;
      }

      if (this.$route.query.preview !== 'success') {
        return;
      }

      this.registrationSuccess = {
        email: typeof this.$route.query.email === 'string' && this.$route.query.email
          ? this.$route.query.email
          : 'preview@coognis.app',
        notificationEmailSent: this.$route.query.email_sent !== 'false',
      };
    },
    async handleRegistration(formData) {
      this.isSubmitting = true;
      this.errorMessage = '';
      this.resetFormFlag = false;
      this.registrationSuccess = null;

      const response = await authService.registerUser(formData);

      if (response.success) {
        this.registrationSuccess = {
          email: formData.email,
          notificationEmailSent: Boolean(response.data?.notification_email_sent),
        };
        this.resetFormFlag = true;
      } else {
        this.errorMessage = response.error?.message || 'Registration could not be completed.';
      }

      this.isSubmitting = false;
    },
    startAnotherRegistration() {
      this.registrationSuccess = null;
      this.errorMessage = '';
      this.resetFormFlag = true;
    },
    showConsentDetails(type) {
      if (type === 'ai_profiling') {
        this.consentModal = {
          visible: true,
          title: 'AI profiling consent details',
          message: 'AI profiling consent allows COOGNIS to analyze your interaction patterns and profile signals so the system can adapt communication style, improve routing, and personalize responses. This processing is used to support adaptive assistance within the platform and is not required for basic account storage alone. You may withdraw this consent later through the privacy settings or by submitting a privacy-related request.',
        };
        return;
      }

      if (type === 'gdpr') {
        this.consentModal = {
          visible: true,
          title: 'GDPR consent details',
          message: 'GDPR consent covers the collection, storage, and use of the personal data required to register and operate your COOGNIS account, including identity details, contact information, security events, and other account-related records. This processing is used for authentication, service delivery, security, support, and compliance. You may request access, correction, deletion, or restriction of your data through the platform privacy workflow, subject to applicable legal and operational obligations.',
        };
        return;
      }

      this.consentModal = {
        visible: true,
        title: 'Privacy details',
        message: 'COOGNIS processes personal data to register your account, secure access, operate conversations, route support, and maintain required audit and privacy controls. Some processing is necessary to provide the service, while adaptive profiling features require separate consent. You can review and manage privacy-related choices after registration, including consent status and supported data requests, through the platform privacy settings.',
      };
    },
    closeConsentModal() {
      this.consentModal.visible = false;
    },
  },
  watch: {
    registrationSuccess: {
      immediate: true,
      handler(value) {
        if (this.authPanelState) {
          this.authPanelState.hideHeader = Boolean(value);
        }
      },
    },
    resetFormFlag(value) {
      if (value) {
        this.$nextTick(() => {
          this.resetFormFlag = false;
        });
      }
    },
  },
  beforeUnmount() {
    if (this.authPanelState) {
      this.authPanelState.hideHeader = false;
    }
  },
};
</script>
