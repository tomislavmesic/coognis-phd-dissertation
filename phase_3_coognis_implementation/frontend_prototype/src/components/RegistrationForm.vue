<template>
  <section class="form-section" aria-labelledby="registration-title">
    <BaseAlert
      v-if="errorMessage"
      class="app-alert app-alert--server"
      variant="danger"
      role="alert"
      :message="errorMessage"
    />

    <div class="form-card">
      <form novalidate @submit.prevent="handleSubmit">
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label" for="register-first-name">First name</label>
            <input
              id="register-first-name"
              v-model.trim="form.first_name"
              class="form-control"
              :class="fieldClass('first_name')"
              type="text"
              autocomplete="given-name"
              :disabled="loading"
              @blur="validateFieldState('first_name')"
            />
            <div v-if="hasValidationError('first_name')" class="invalid-feedback d-block">
              {{ fieldError('first_name') }}
            </div>
          </div>

          <div class="col-md-6">
            <label class="form-label" for="register-last-name">Last name</label>
            <input
              id="register-last-name"
              v-model.trim="form.last_name"
              class="form-control"
              :class="fieldClass('last_name')"
              type="text"
              autocomplete="family-name"
              :disabled="loading"
              @blur="validateFieldState('last_name')"
            />
            <div v-if="hasValidationError('last_name')" class="invalid-feedback d-block">
              {{ fieldError('last_name') }}
            </div>
          </div>

          <div class="col-12">
            <label class="form-label" for="register-email">Email</label>
            <input
              id="register-email"
              v-model.trim="form.email"
              class="form-control"
              :class="fieldClass('email')"
              type="email"
              autocomplete="email"
              :disabled="loading"
              @blur="validateFieldState('email')"
            />
            <div v-if="hasValidationError('email')" class="invalid-feedback d-block">
              {{ fieldError('email') }}
            </div>
          </div>

          <div class="col-md-6">
            <label class="form-label" for="register-password">Password</label>
            <input
              id="register-password"
              v-model="form.password"
              class="form-control"
              :class="fieldClass('password')"
              type="password"
              autocomplete="new-password"
              :disabled="loading"
              @blur="validateFieldState('password')"
            />
            <div class="form-hint mt-2">Use at least 8 characters.</div>
            <div v-if="hasValidationError('password')" class="invalid-feedback d-block">
              {{ fieldError('password') }}
            </div>
          </div>

          <div class="col-md-6">
            <label class="form-label" for="register-password-confirmation">Confirm password</label>
            <input
              id="register-password-confirmation"
              v-model="form.password_confirmation"
              class="form-control"
              :class="fieldClass('password_confirmation')"
              type="password"
              autocomplete="new-password"
              :disabled="loading"
              @blur="validateFieldState('password_confirmation')"
            />
            <div v-if="hasValidationError('password_confirmation')" class="invalid-feedback d-block">
              {{ fieldError('password_confirmation') }}
            </div>
          </div>

          <div class="col-12 d-flex pt-2 align-items-center">
            <p class="text-body-secondary mb-0">Registration requires consent for AI profiling and GDPR data processing.</p>
            <button
              class="btn btn-link registration-link d-inline-flex align-items-center"
              type="button"
              aria-label="View privacy details"
              title="View privacy details"
              @click="emitConsentDetails('privacy')"
            >
              <ThemeIcon name="info" />
            </button>
          </div>

          <div class="col-12">
            <div class="card base-card">
              <div class="card-body">
                <div class="d-flex align-items-center gap-2 justify-content-between">
                  <div>
                    <div class="form-check form-switch">
                      <input
                        id="expert-settings-ai-consent"
                        v-model="form.ai_profiling_consent"
                        class="form-check-input"
                        type="checkbox"
                        role="switch"
                        :disabled="loading"
                        @change="validateFieldState('ai_profiling_consent')"
                      />
                      <label class="form-check-label form-label" for="expert-settings-ai-consent">
                        AI profiling consent
                      </label>
                    </div>
                    <p class="text-body-secondary mb-0">
                      I consent to AI profiling for adaptive personalization.
                    </p>
                    <div v-if="hasValidationError('ai_profiling_consent')" class="invalid-feedback d-block">
                      {{ fieldError('ai_profiling_consent') }}
                    </div>
                  </div>
                  <div>
                    <button
                      class="btn btn-link registration-link d-inline-flex align-items-center p-0"
                      type="button"
                      aria-label="View AI profiling consent details"
                      title="View AI profiling consent details"
                      @click="emitConsentDetails('ai_profiling')"
                    >
                      <ThemeIcon name="info" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-12 pb-4">
            <div class="card base-card">
              <div class="card-body">
                <div class="d-flex align-items-center gap-2 justify-content-between">
                  <div>
                    <div class="form-check form-switch">
                      <input
                        id="gdpr-consent"
                        v-model="form.gdpr_consent"
                        class="form-check-input"
                        type="checkbox"
                        :disabled="loading"
                        @change="validateFieldState('gdpr_consent')"
                      />
                      <label class="form-check-label form-label" for="gdpr-consent">
                        GDPR consent
                      </label>
                    </div>
                    <p class="text-body-secondary mb-0">
                      I consent to GDPR-compliant processing of my account data.
                    </p>
                    <div v-if="hasValidationError('gdpr_consent')" class="invalid-feedback d-block">
                      {{ fieldError('gdpr_consent') }}
                    </div>
                  </div>
                  <div>
                    <div class="form-hint">
                      <button
                        class="btn btn-link registration-link d-inline-flex align-items-center p-0"
                        type="button"
                        aria-label="View GDPR consent details"
                        title="View GDPR consent details"
                        @click="emitConsentDetails('gdpr')"
                      >
                        <ThemeIcon name="info" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="form-actions mt-4">
          <button class="btn btn-primary" type="submit" :disabled="loading">
            {{ loading ? 'Submitting...' : 'Submit registration' }}
          </button>
          <RouterLink class="btn btn-outline-secondary" to="/login">Go to login</RouterLink>
        </div>
      </form>
    </div>
  </section>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import ThemeIcon from '@/components/ThemeIcon.vue';
import {
  email,
  hasFieldError,
  matchesField,
  minLength,
  required,
  validateField,
  validateFields,
} from '@/utils/formValidation';

export default {
  name: 'RegistrationForm',
  components: {
    BaseAlert,
    ThemeIcon,
  },
  props: {
    loading: {
      type: Boolean,
      default: false,
    },
    errorMessage: {
      type: String,
      default: '',
    },
    resetOnSuccess: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['submit', 'show-consent-details'],
  data() {
    return {
      form: this.createInitialForm(),
      errors: this.createInitialErrors(),
    };
  },
  watch: {
    resetOnSuccess(value) {
      if (value) {
        this.resetForm();
      }
    },
  },
  methods: {
    createInitialForm() {
      return {
        first_name: '',
        last_name: '',
        email: '',
        password: '',
        password_confirmation: '',
        ai_profiling_consent: false,
        gdpr_consent: false,
      };
    },
    createInitialErrors() {
      return {
        first_name: '',
        last_name: '',
        email: '',
        password: '',
        password_confirmation: '',
        ai_profiling_consent: '',
        gdpr_consent: '',
      };
    },
    validationRules() {
      return {
        first_name: [required('First name is required.')],
        last_name: [required('Last name is required.')],
        email: [required('Email is required.'), email('Enter a valid email address.')],
        password: [
          required('Password is required.'),
          minLength(8, 'Password must be at least 8 characters.'),
        ],
        password_confirmation: [
          required('Please confirm your password.'),
          matchesField('password', 'Password confirmation must match the password.'),
        ],
        ai_profiling_consent: [required('AI profiling consent is required for registration.')],
        gdpr_consent: [required('GDPR consent is required for registration.')],
      };
    },
    resetForm() {
      this.form = this.createInitialForm();
      this.errors = this.createInitialErrors();
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
    emitConsentDetails(type) {
      this.$emit('show-consent-details', type);
    },
    validateFieldState(fieldName) {
      this.errors = validateField(fieldName, this.form, this.errors, this.validationRules());
      return !this.errors[fieldName];
    },
    validateForm() {
      const fields = [
        'first_name',
        'last_name',
        'email',
        'password',
        'password_confirmation',
        'ai_profiling_consent',
        'gdpr_consent',
      ];

      this.errors = validateFields(fields, this.form, this.validationRules());

      return fields.every((fieldName) => !this.errors[fieldName]);
    },
    handleSubmit() {
      if (!this.validateForm()) {
        return;
      }

      this.$emit('submit', { ...this.form });
    },
  },
};
</script>
