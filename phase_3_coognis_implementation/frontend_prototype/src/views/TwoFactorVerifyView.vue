<template>
  <section class="form-section" aria-labelledby="two-factor-title">
    <BaseAlert v-if="isMockAuthEnabled" class="app-alert app-alert--info" variant="info">
      Mock auth is enabled. Use verification code <code>123456</code>.
    </BaseAlert>

    <BaseAlert
      v-if="successMessage"
      class="app-alert app-alert--success"
      variant="success"
      :message="successMessage"
    />

    <BaseAlert
      v-if="errorMessage"
      class="app-alert app-alert--server"
      variant="danger"
      role="alert"
      :message="errorMessage"
    />

    <BaseAlert
      v-if="isPreviewMode"
      class="app-alert app-alert--info"
      variant="info"
      :message="previewBannerMessage"
    />

    <div class="form-card">
      <div v-if="recoveryCodes.length" class="d-grid gap-3">
        <div>
          <h2 id="two-factor-title" class="h5 mb-2">Save recovery codes</h2>
          <p class="form-hint mb-0">
            These one-time recovery codes will not be shown again. Store them before continuing.
          </p>
        </div>

        <div class="border rounded-1 p-3 bg-body-tertiary">
          <ul class="mb-0 list-unstyled m-0 p-0">
            <li v-for="code in recoveryCodes" :key="code">
              <code>{{ code }}</code>
            </li>
          </ul>
        </div>

        <div class="form-check">
          <input
            id="acknowledge-recovery-codes"
            v-model="hasAcknowledgedRecoveryCodes"
            class="form-check-input"
            type="checkbox"
          />
          <label class="form-check-label" for="acknowledge-recovery-codes">
            Recovery codes have been stored safely.
          </label>
        </div>

        <div class="form-actions">
          <button class="btn btn-outline-secondary" type="button" @click="downloadRecoveryCodes">
            Download codes
          </button>
          <button
            class="btn btn-primary"
            type="button"
            :disabled="!hasAcknowledgedRecoveryCodes"
            @click="continueAfterSetup"
          >
            Continue
          </button>
        </div>
      </div>

      <form v-else novalidate @submit.prevent="handleSubmit">
        <div v-if="isSetupRequired" class="mb-4 d-grid gap-3">
          <div>
            <h2 id="two-factor-title" class="h5 mb-2">Set up an authenticator app</h2>
            <p class="form-hint mb-0">
              Add this account to a TOTP-compatible authenticator app, then enter the current 6-digit code below.
            </p>
          </div>

          <div v-if="setupDetails" class="border rounded-1 p-3 bg-body-tertiary d-grid gap-2">
            <div v-if="qrCodeDataUrl" class="text-center mb-2">
              <img
                :src="qrCodeDataUrl"
                alt="Authenticator setup QR code"
                class="img-fluid border rounded-2 bg-white p-2"
                style="max-width: 160px;"
              />
            </div>
            <div>
              <div class="small text-body-secondary mb-1">Issuer</div>
              <code>{{ setupDetails.issuer }}</code>
            </div>
            <div>
              <div class="small text-body-secondary mb-1">Account</div>
              <code>{{ setupDetails.account_name }}</code>
            </div>
            <div>
              <div class="small text-body-secondary mb-1">Secret</div>
              <code class="d-block text-break">{{ setupDetails.secret }}</code>
            </div>
          </div>

          <BaseAlert
            v-if="isSetupLoading"
            variant="info"
            message="Loading authenticator setup details..."
          />
        </div>

        <div class="mb-3">
          <label class="form-label" for="verification-code">
            {{ isSetupRequired ? 'Authenticator code' : 'Verification or recovery code' }}
          </label>
          <input
            id="verification-code"
            v-model.trim="form.verification_code"
            class="form-control"
            :class="fieldClass('verification_code')"
            type="text"
            inputmode="numeric"
            autocomplete="one-time-code"
            :placeholder="isSetupRequired ? 'Enter the 6-digit authenticator code' : 'Enter verification or recovery code'"
            :disabled="isLoading || isSetupLoading"
            @blur="validateFieldState('verification_code')"
          />
          <div v-if="hasValidationError('verification_code')" class="invalid-feedback d-block">
            {{ fieldError('verification_code') }}
          </div>
          <p class="form-hint mt-2 mb-0">
            {{
              isSetupRequired
                ? 'Use the code currently shown by the authenticator app.'
                : 'Either the current authenticator code or one unused recovery code is accepted.'
            }}
          </p>
        </div>

        <div v-if="canRememberDevice" class="form-check mb-4">
          <input
            id="remember-device"
            v-model="form.remember_device"
            class="form-check-input"
            type="checkbox"
            :disabled="isLoading || isSetupLoading"
          />
          <label class="form-check-label" for="remember-device">
            {{ rememberDeviceLabel }}
          </label>
        </div>

        <div class="form-actions">
          <button class="btn btn-primary w-100" type="submit" :disabled="isLoading || isSetupLoading">
            {{ isLoading ? (isSetupRequired ? 'Confirming...' : 'Verifying...') : (isSetupRequired ? 'Complete setup' : 'Verify') }}
          </button>
        </div>
      </form>
    </div>
  </section>
</template>

<script>
import QRCode from 'qrcode';
import BaseAlert from '@/components/BaseAlert.vue';
import authService from '@/services/authService';
import { getPreferredTheme, resolveTheme } from '@/services/themeService';
import authStore from '@/store/authStore';
import { getServerErrorMessage, hasFieldError, required, validateField, validateFields } from '@/utils/formValidation';
import { MOCK_AUTH_ENABLED } from '@/utils/mockAuth';

const DEV_AUTH_PREVIEWS_ENABLED = import.meta.env.DEV;

export default {
  name: 'TwoFactorVerifyView',
  components: {
    BaseAlert,
  },
  data() {
    return {
      isMockAuthEnabled: MOCK_AUTH_ENABLED,
      isLoading: false,
      isSetupLoading: false,
      successMessage: '',
      errorMessage: '',
      setupDetails: null,
      qrCodeDataUrl: '',
      completedPayload: null,
      recoveryCodes: [],
      hasAcknowledgedRecoveryCodes: false,
      previewMode: null,
      previewChallenge: null,
      form: {
        verification_code: '',
        remember_device: true,
      },
      errors: {
        verification_code: '',
      },
    };
  },
  computed: {
    pendingChallenge() {
      return this.previewChallenge || authStore.state.pendingTwoFactor;
    },
    isSetupRequired() {
      return this.previewMode === 'setup' || Boolean(this.pendingChallenge?.setupRequired);
    },
    isPreviewMode() {
      return Boolean(this.previewMode);
    },
    rememberDeviceDays() {
      return Number(this.pendingChallenge?.rememberDeviceDays || 0) || 0;
    },
    canRememberDevice() {
      return this.rememberDeviceDays > 0 && !this.recoveryCodes.length;
    },
    rememberDeviceLabel() {
      const days = this.rememberDeviceDays;
      return `Remember this device for ${days} day${days === 1 ? '' : 's'}.`;
    },
    previewBannerMessage() {
      if (this.previewMode === 'setup') {
        return 'Preview mode: authenticator setup screen.';
      }

      if (this.previewMode === 'recovery') {
        return 'Preview mode: recovery-code confirmation screen.';
      }

      if (this.previewMode === 'verify') {
        return 'Preview mode: verification screen.';
      }

      return '';
    },
  },
  async created() {
    if (await this.initializePreviewMode()) {
      return;
    }

    if (!this.pendingChallenge) {
      this.$router.replace('/login');
      return;
    }

    if (this.isSetupRequired) {
      await this.initializeSetup();
    }
  },
  methods: {
    async initializePreviewMode() {
      if (!DEV_AUTH_PREVIEWS_ENABLED) {
        return false;
      }

      const preview = this.normalizePreviewMode(this.$route.query.preview);

      if (!preview) {
        return false;
      }

      this.previewMode = preview;
      this.previewChallenge = {
        challengeId: 'preview-challenge',
        redirectTo: '/admin',
        email: 'preview@coognis.app',
        role: 'admin',
        setupRequired: preview === 'setup',
        rememberDeviceDays: 14,
        user: {
          id: 'preview-user',
          email: 'preview@coognis.app',
          role: 'admin',
          first_name: 'Preview',
          last_name: 'Admin',
        },
      };

      if (preview === 'setup') {
        this.setupDetails = {
          issuer: 'COOGNIS',
          account_name: 'preview@coognis.app',
          secret: 'JBSWY3DPEHPK3PXP',
          provisioning_uri:
            'otpauth://totp/COOGNIS:preview%40coognis.app?secret=JBSWY3DPEHPK3PXP&issuer=COOGNIS',
        };
        await this.generateQrCode();
        return true;
      }

      if (preview === 'recovery') {
        this.completedPayload = {
          user: this.previewChallenge.user,
          redirect_to: '/admin',
        };
        this.recoveryCodes = [
          'COOGNIS-RCVR-1048',
          'COOGNIS-RCVR-2081',
          'COOGNIS-RCVR-3194',
          'COOGNIS-RCVR-4472',
          'COOGNIS-RCVR-5520',
          'COOGNIS-RCVR-6891',
          'COOGNIS-RCVR-7345',
          'COOGNIS-RCVR-8803',
        ];
        return true;
      }

      return true;
    },
    normalizePreviewMode(value) {
      if (typeof value !== 'string') {
        return null;
      }

      const normalized = value.trim().toLowerCase();
      return ['setup', 'verify', 'recovery'].includes(normalized) ? normalized : null;
    },
    validationRules() {
      return {
        verification_code: [required('Verification code is required.')],
      };
    },
    hasValidationError(fieldName) {
      return hasFieldError(this.errors, fieldName);
    },
    fieldError(fieldName) {
      return this.errors[fieldName] || '';
    },
    fieldClass(fieldName) {
      return {
        'is-invalid': this.hasValidationError(fieldName),
      };
    },
    validateFieldState(fieldName) {
      this.errors = validateField(fieldName, this.form, this.errors, this.validationRules());
      return !this.errors[fieldName];
    },
    async initializeSetup() {
      if (!this.pendingChallenge?.challengeId) {
        this.errorMessage = 'Two-factor setup challenge is missing or has expired.';
        return;
      }

      this.isSetupLoading = true;
      this.errorMessage = '';
      const response = await authService.setupTwoFactor(this.pendingChallenge.challengeId);

      if (!response.success) {
        this.errorMessage = getServerErrorMessage(response.error, 'Unable to start two-factor setup.');
        this.isSetupLoading = false;
        return;
      }

      this.setupDetails = response.data || null;
      await this.generateQrCode();
      this.isSetupLoading = false;
    },
    async generateQrCode() {
      if (!this.setupDetails?.provisioning_uri) {
        this.qrCodeDataUrl = '';
        return;
      }

      const activeTheme =
        typeof document !== 'undefined'
          ? document.documentElement.getAttribute('data-bs-theme') || resolveTheme(getPreferredTheme())
          : 'light';
      const isDarkTheme = activeTheme === 'dark';

      try {
        this.qrCodeDataUrl = await QRCode.toDataURL(this.setupDetails.provisioning_uri, {
          width: 220,
          margin: 1,
          color: isDarkTheme
            ? { dark: '#ffffff', light: '#111827' }
            : { dark: '#111827', light: '#ffffff' },
        });
      } catch {
        this.qrCodeDataUrl = '';
      }
    },
    finalizeAuthentication(payload = {}) {
      const redirectTo = this.pendingChallenge?.redirectTo || payload.redirect_to;
      const user = payload.user || payload.account || this.pendingChallenge?.user || payload;
      const role = authStore.resolveRoleFromPayload(payload) || authStore.resolveRoleFromPayload(user);

      authStore.setCurrentUser(user);
      authStore.clearPendingTwoFactor();
      this.isLoading = false;
      this.$router.push(redirectTo || authStore.resolveDashboardPath(role));
    },
    continueAfterSetup() {
      if (!this.completedPayload || !this.hasAcknowledgedRecoveryCodes) {
        return;
      }

      if (this.isPreviewMode) {
        this.successMessage = 'Preview only. Recovery codes step completed.';
        return;
      }

      this.successMessage = 'Two-factor setup completed successfully.';
      this.finalizeAuthentication(this.completedPayload);
    },
    downloadRecoveryCodes() {
      if (!this.recoveryCodes.length || typeof window === 'undefined') {
        return;
      }

      const lines = [
        'COOGNIS recovery codes',
        '',
        ...this.recoveryCodes,
      ];

      const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = 'coognis-recovery-codes.txt';
      window.document.body.appendChild(link);
      link.click();
      window.document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
    async handleSubmit() {
      this.errors = validateFields(['verification_code'], this.form, this.validationRules());

      if (this.errors.verification_code) {
        return;
      }

      if (this.isPreviewMode) {
        this.handlePreviewSubmit();
        return;
      }

      this.isLoading = true;
      this.errorMessage = '';
      this.successMessage = '';

      const response = this.isSetupRequired
        ? await authService.confirmTwoFactor({
            verification_code: this.form.verification_code,
            challenge_id: this.pendingChallenge?.challengeId,
            remember_device: this.form.remember_device,
          })
        : await authService.verifyTwoFactor({
            verification_code: this.form.verification_code,
            challenge_id: this.pendingChallenge?.challengeId,
            remember_device: this.form.remember_device,
          });

      if (!response.success) {
        this.errorMessage = getServerErrorMessage(
          response.error,
          this.isSetupRequired ? 'Two-factor setup failed.' : 'Verification failed.'
        );
        this.isLoading = false;
        return;
      }

      const payload = response.data || {};
      if (this.isSetupRequired) {
        this.completedPayload = payload;
        this.recoveryCodes = Array.isArray(payload.recovery_codes) ? payload.recovery_codes : [];
        this.hasAcknowledgedRecoveryCodes = false;
        this.form.verification_code = '';
        this.successMessage = 'Two-factor setup completed. Save the recovery codes before continuing.';
        this.isLoading = false;
        if (!this.recoveryCodes.length) {
          this.finalizeAuthentication(payload);
        }
        return;
      }

      this.successMessage = 'Two-factor verification successful.';
      this.finalizeAuthentication(payload);
    },
    handlePreviewSubmit() {
      this.isLoading = true;
      this.errorMessage = '';
      this.successMessage = '';

      if (this.previewMode === 'setup') {
        this.completedPayload = {
          user: this.previewChallenge?.user,
          redirect_to: this.previewChallenge?.redirectTo || '/admin',
        };
        this.recoveryCodes = [
          'COOGNIS-RCVR-1048',
          'COOGNIS-RCVR-2081',
          'COOGNIS-RCVR-3194',
          'COOGNIS-RCVR-4472',
          'COOGNIS-RCVR-5520',
          'COOGNIS-RCVR-6891',
          'COOGNIS-RCVR-7345',
          'COOGNIS-RCVR-8803',
        ];
        this.hasAcknowledgedRecoveryCodes = false;
        this.form.verification_code = '';
        this.successMessage = 'Preview only. Setup confirmed and recovery codes revealed.';
        this.isLoading = false;
        return;
      }

      this.successMessage = 'Preview only. Verification accepted.';
      this.isLoading = false;
    },
  },
};
</script>
