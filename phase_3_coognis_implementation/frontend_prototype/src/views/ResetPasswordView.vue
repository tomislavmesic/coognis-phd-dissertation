<template>
  <section class="form-section" aria-labelledby="reset-password-title">
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
      <div v-if="resetCompleted" class="d-grid gap-4">
        <div>
          <p class="auth-theme-shell__panel-eyebrow mb-2">Password updated</p>
          <h2 id="reset-password-title" class="h5 mb-2">Your password has been reset.</h2>
          <p class="form-hint mb-0">
            You can now sign in with the new password.
          </p>
        </div>

        <div class="form-actions">
          <RouterLink class="btn btn-primary w-100" to="/login">Go to login</RouterLink>
        </div>
      </div>

      <form v-else novalidate @submit.prevent="handleSubmit">
        <div class="mb-3">
          <label class="form-label" for="reset-password-new">New password</label>
          <input
            id="reset-password-new"
            v-model="form.password"
            class="form-control"
            :class="fieldClass('password')"
            type="password"
            placeholder="Enter a new password"
            autocomplete="new-password"
            :disabled="isSubmitting || !hasResetToken"
            @blur="validateFieldState('password')"
          />
          <div v-if="hasValidationError('password')" class="invalid-feedback d-block">
            {{ fieldError('password') }}
          </div>
        </div>

        <div class="mb-4">
          <label class="form-label" for="reset-password-confirmation">Confirm new password</label>
          <input
            id="reset-password-confirmation"
            v-model="form.password_confirmation"
            class="form-control"
            :class="fieldClass('password_confirmation')"
            type="password"
            placeholder="Re-enter the new password"
            autocomplete="new-password"
            :disabled="isSubmitting || !hasResetToken"
            @blur="validateFieldState('password_confirmation')"
          />
          <div v-if="hasValidationError('password_confirmation')" class="invalid-feedback d-block">
            {{ fieldError('password_confirmation') }}
          </div>
        </div>

        <div class="form-actions">
          <button class="btn btn-primary w-100" type="submit" :disabled="isSubmitting || !hasResetToken">
            {{ isSubmitting ? 'Resetting...' : 'Set new password' }}
          </button>
        </div>
      </form>
    </div>
  </section>
</template>

<script>
import { RouterLink } from 'vue-router';
import BaseAlert from '@/components/BaseAlert.vue';
import authService from '@/services/authService';
import {
  getServerErrorMessage,
  hasFieldError,
  matchesField,
  minLength,
  required,
  validateField,
  validateFields,
} from '@/utils/formValidation';

export default {
  name: 'ResetPasswordView',
  components: {
    BaseAlert,
    RouterLink,
  },
  data() {
    return {
      isSubmitting: false,
      resetCompleted: false,
      successMessage: '',
      errorMessage: '',
      form: {
        password: '',
        password_confirmation: '',
      },
      errors: {
        password: '',
        password_confirmation: '',
      },
    };
  },
  computed: {
    resetToken() {
      return typeof this.$route.query.token === 'string' ? this.$route.query.token.trim() : '';
    },
    hasResetToken() {
      return Boolean(this.resetToken);
    },
  },
  created() {
    if (!this.hasResetToken) {
      this.errorMessage = 'Password reset link is missing or invalid.';
    }
  },
  methods: {
    validationRules() {
      return {
        password: [
          required('New password is required.'),
          minLength(8, 'New password must be at least 8 characters long.'),
        ],
        password_confirmation: [
          required('Password confirmation is required.'),
          matchesField('password', 'Password confirmation must match the new password.'),
        ],
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
    validateForm() {
      this.errors = validateFields(['password', 'password_confirmation'], this.form, this.validationRules());
      return !this.errors.password && !this.errors.password_confirmation;
    },
    async handleSubmit() {
      if (!this.hasResetToken) {
        this.errorMessage = 'Password reset link is missing or invalid.';
        return;
      }

      if (!this.validateForm()) {
        return;
      }

      this.isSubmitting = true;
      this.errorMessage = '';
      this.successMessage = '';

      const response = await authService.confirmPasswordReset({
        token: this.resetToken,
        password: this.form.password,
        password_confirmation: this.form.password_confirmation,
      });

      if (!response.success) {
        this.errorMessage = getServerErrorMessage(response.error, 'Unable to reset the password.');
        this.isSubmitting = false;
        return;
      }

      this.resetCompleted = true;
      this.successMessage = response.data?.message || 'Password reset completed successfully.';
      this.form.password = '';
      this.form.password_confirmation = '';
      this.errors = {
        password: '',
        password_confirmation: '',
      };
      this.isSubmitting = false;
    },
  },
};
</script>
