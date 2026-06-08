<template>
  <section class="form-section" aria-labelledby="login-title">
    <BaseAlert v-if="isMockAuthEnabled" class="app-alert app-alert--info" variant="info">
      Mock auth is enabled. Use an email containing <code>user</code>, <code>expert</code>, or
      <code>admin</code> to select a role.
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

    <div class="form-card">
      <form novalidate @submit.prevent="handleSubmit">
        <div class="mb-3">
          <label class="form-label" for="login-email">Email</label>
          <input
            id="login-email"
            v-model.trim="form.email"
            class="form-control"
            :class="fieldClass('email')"
            type="email"
            placeholder="name@example.com"
            autocomplete="email"
            :disabled="isLoading"
            @blur="validateFieldState('email')"
          />
          <div v-if="hasValidationError('email')" class="invalid-feedback d-block">
            {{ fieldError('email') }}
          </div>
        </div>
        <div class="mb-4">
          <div class="d-flex justify-content-between align-items-center mb-2 gap-3">
            <label class="form-label mb-0" for="login-password">Password</label>
            <button class="btn btn-link px-0 py-0 text-decoration-none" type="button" @click="openResetModal">
              Forgot password?
            </button>
          </div>
          <input
            id="login-password"
            v-model="form.password"
            class="form-control"
            :class="fieldClass('password')"
            type="password"
            placeholder="Enter your password"
            autocomplete="current-password"
            :disabled="isLoading"
            @blur="validateFieldState('password')"
          />
          <div v-if="hasValidationError('password')" class="invalid-feedback d-block">
            {{ fieldError('password') }}
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="isLoading">
            {{ isLoading ? 'Signing in...' : 'Continue' }}
          </button>
          <RouterLink class="btn btn-outline-secondary" to="/register">Sign up</RouterLink>
        </div>
      </form>
    </div>

    <BaseModal
      :visible="isResetModalVisible"
      title="Reset password"
      eyebrow="Account recovery"
      modal-id="forgot-password-modal"
      :busy="isResetLoading"
      @close="closeResetModal"
    >
      <BaseAlert
        v-if="resetSuccessMessage"
        class="app-alert app-alert--success mb-4"
        variant="success"
        :message="resetSuccessMessage"
      />

      <BaseAlert
        v-if="resetErrorMessage"
        class="app-alert app-alert--server mb-4"
        variant="danger"
        role="alert"
        :message="resetErrorMessage"
      />

      <form novalidate @submit.prevent="handlePasswordResetRequest">
        <div class="mb-0">
          <label class="form-label" for="password-reset-email">Email</label>
          <input
            id="password-reset-email"
            v-model.trim="resetForm.email"
            class="form-control"
            :class="resetFieldClass('email')"
            type="email"
            placeholder="name@example.com"
            autocomplete="email"
            :disabled="isResetLoading"
            @blur="validateResetFieldState('email')"
          />
          <div v-if="hasResetValidationError('email')" class="invalid-feedback d-block">
            {{ resetFieldError('email') }}
          </div>
        </div>
      </form>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isResetLoading" @click="closeResetModal">
          Cancel
        </button>
        <button class="btn btn-primary" type="button" :disabled="isResetLoading" @click="handlePasswordResetRequest">
          {{ isResetLoading ? 'Sending...' : 'Send reset link' }}
        </button>
      </template>
    </BaseModal>
  </section>
</template>

<script>
import { RouterLink } from 'vue-router';
import BaseAlert from '@/components/BaseAlert.vue';
import BaseModal from '@/components/BaseModal.vue';
import authService from '@/services/authService';
import authStore from '@/store/authStore';
import { email, getServerErrorMessage, hasFieldError, required, validateField, validateFields } from '@/utils/formValidation';
import { MOCK_AUTH_ENABLED } from '@/utils/mockAuth';

export default {
  name: 'LoginView',
  components: {
    BaseAlert,
    BaseModal,
    RouterLink,
  },
  data() {
    return {
      isMockAuthEnabled: MOCK_AUTH_ENABLED,
      isLoading: false,
      isResetLoading: false,
      isResetModalVisible: false,
      successMessage: '',
      errorMessage: '',
      resetSuccessMessage: '',
      resetErrorMessage: '',
      form: {
        email: '',
        password: '',
      },
      resetForm: {
        email: '',
      },
      errors: {
        email: '',
        password: '',
      },
      resetErrors: {
        email: '',
      },
    };
  },
  methods: {
    validationRules() {
      return {
        email: [required('Email is required.'), email('Enter a valid email address.')],
        password: [required('Password is required.')],
      };
    },
    resetValidationRules() {
      return {
        email: [required('Email is required.'), email('Enter a valid email address.')],
      };
    },
    hasValidationError(fieldName) {
      return hasFieldError(this.errors, fieldName);
    },
    hasResetValidationError(fieldName) {
      return hasFieldError(this.resetErrors, fieldName);
    },
    fieldError(fieldName) {
      return this.errors[fieldName] || '';
    },
    resetFieldError(fieldName) {
      return this.resetErrors[fieldName] || '';
    },
    fieldClass(fieldName) {
      return {
        'is-invalid': this.hasValidationError(fieldName),
      };
    },
    resetFieldClass(fieldName) {
      return {
        'is-invalid': this.hasResetValidationError(fieldName),
      };
    },
    validateFieldState(fieldName) {
      this.errors = validateField(fieldName, this.form, this.errors, this.validationRules());
      return !this.errors[fieldName];
    },
    validateResetFieldState(fieldName) {
      this.resetErrors = validateField(
        fieldName,
        this.resetForm,
        this.resetErrors,
        this.resetValidationRules()
      );
      return !this.resetErrors[fieldName];
    },
    validateForm() {
      this.errors = validateFields(['email', 'password'], this.form, this.validationRules());
      return !this.errors.email && !this.errors.password;
    },
    validateResetForm() {
      this.resetErrors = validateFields(['email'], this.resetForm, this.resetValidationRules());
      return !this.resetErrors.email;
    },
    getResponseRole(payload) {
      return authStore.resolveRoleFromPayload(payload);
    },
    openResetModal() {
      this.isResetModalVisible = true;
      this.resetForm.email = this.form.email || '';
      this.resetErrors = {
        email: '',
      };
      this.resetErrorMessage = '';
      this.resetSuccessMessage = '';
    },
    closeResetModal() {
      if (this.isResetLoading) {
        return;
      }

      this.isResetModalVisible = false;
    },
    async handlePasswordResetRequest() {
      if (!this.validateResetForm()) {
        return;
      }

      this.isResetLoading = true;
      this.resetErrorMessage = '';
      this.resetSuccessMessage = '';

      const response = await authService.requestPasswordReset(this.resetForm);

      if (!response.success) {
        this.resetErrorMessage = getServerErrorMessage(
          response.error,
          'Unable to request a password reset.'
        );
        this.isResetLoading = false;
        return;
      }

      this.resetSuccessMessage =
        response.data?.message ||
        'If an account exists for that email, a password reset message will be sent.';
      this.resetErrors = {
        email: '',
      };
      this.isResetLoading = false;
    },
    async handleSubmit() {
      if (!this.validateForm()) {
        return;
      }

      this.isLoading = true;
      this.errorMessage = '';
      this.successMessage = '';
      authStore.clearAuth();

      const response = await authService.login(this.form);

      if (!response.success) {
        this.errorMessage = getServerErrorMessage(response.error, 'Login failed.');
        this.isLoading = false;
        return;
      }

      const payload = response.data || {};
      const requiresTwoFactor = Boolean(
        payload.requires_2fa || payload.requiresTwoFactor || payload.two_factor_required
      );

      if (requiresTwoFactor) {
        authStore.setPendingTwoFactor({
          ...payload,
          email: this.form.email,
        });
        this.successMessage = Boolean(payload.setup_required || payload.setupRequired)
          ? 'Two-factor setup is required before the session can continue.'
          : 'Verification required. Continue with your two-factor code.';
        this.isLoading = false;
        this.$router.push('/two-factor');
        return;
      }

      const user = payload.user || payload.account || payload;
      authStore.setCurrentUser(user);
      this.successMessage = 'Login successful.';
      this.isLoading = false;
      this.$router.push(authStore.resolveDashboardPath(this.getResponseRole(payload)));
    },
  },
};
</script>
