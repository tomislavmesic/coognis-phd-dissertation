<template>
  <section class="admin-user-creation">
    <BasePageHeader
      eyebrow="Admin"
      title="Manual user creation"
      description="Create user and expert accounts manually and trigger the backend credential email placeholder."
    />

    <div class="row g-4">
      <div class="col-lg-8">
        <BaseCard class="admin-user-creation__card">
          <form novalidate @submit.prevent="handleSubmit">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label" for="create-first-name">First name</label>
                <input
                  id="create-first-name"
                  v-model.trim="form.first_name"
                  class="form-control"
                  :class="fieldClass('first_name')"
                  type="text"
                  :disabled="isSubmitting"
                  @blur="validateFieldState('first_name')"
                />
                <div v-if="hasValidationError('first_name')" class="invalid-feedback d-block">
                  {{ fieldError('first_name') }}
                </div>
              </div>

              <div class="col-md-6">
                <label class="form-label" for="create-last-name">Last name</label>
                <input
                  id="create-last-name"
                  v-model.trim="form.last_name"
                  class="form-control"
                  :class="fieldClass('last_name')"
                  type="text"
                  :disabled="isSubmitting"
                  @blur="validateFieldState('last_name')"
                />
                <div v-if="hasValidationError('last_name')" class="invalid-feedback d-block">
                  {{ fieldError('last_name') }}
                </div>
              </div>

              <div class="col-md-6">
                <label class="form-label" for="create-email">Email</label>
                <input
                  id="create-email"
                  v-model.trim="form.email"
                  class="form-control"
                  :class="fieldClass('email')"
                  type="email"
                  autocomplete="email"
                  :disabled="isSubmitting"
                  @blur="validateFieldState('email')"
                />
                <div v-if="hasValidationError('email')" class="invalid-feedback d-block">
                  {{ fieldError('email') }}
                </div>
              </div>

              <div class="col-md-6">
                <label class="form-label" for="create-role">Role</label>
                <select
                  id="create-role"
                  v-model="form.role"
                  class="form-select"
                  :class="fieldClass('role')"
                  :disabled="isSubmitting"
                  @blur="validateFieldState('role')"
                >
                  <option value="user">User</option>
                  <option value="expert">Expert</option>
                </select>
                <div v-if="hasValidationError('role')" class="invalid-feedback d-block">
                  {{ fieldError('role') }}
                </div>
              </div>

              <div class="col-12">
                <div class="form-check form-switch mb-2">
                  <input
                    id="auto-generate-password"
                    v-model="form.auto_generate_password"
                    class="form-check-input"
                    type="checkbox"
                    :disabled="isSubmitting"
                    @change="validateFieldState('temporary_password')"
                  />
                  <label class="form-check-label" for="auto-generate-password">
                    Auto-generate temporary password
                  </label>
                </div>
                <p class="form-hint mb-0">
                  When enabled, the backend placeholder is expected to generate the password and send credentials by email.
                </p>
              </div>

              <div class="col-sm-6">
                <label class="form-label" for="temporary-password">Temporary password</label>
                <input
                  id="temporary-password"
                  v-model="form.temporary_password"
                  class="form-control"
                  :class="fieldClass('temporary_password')"
                  type="text"
                  :disabled="form.auto_generate_password || isSubmitting"
                  @blur="validateFieldState('temporary_password')"
                />
                <div v-if="hasValidationError('temporary_password')" class="invalid-feedback d-block">
                  {{ fieldError('temporary_password') }}
                </div>
              </div>
            </div>

              <div class="row g-3 mt-2">
                <label class="form-label" for="temporary-password">Privacy policy consent</label>
                <p class="form-hint mb-0">These fields allow the admin to indicate that consents are already recorded outside the system. They do not trigger any specific flows in the backend placeholder but can be useful for record-keeping.</p>
                <div class="col-md-6">
                  <div class="form-check form-switch admin-user-creation__switch">
                    <input
                      id="profiling-consent-recorded"
                      v-model="form.ai_profiling_consent_recorded"
                      class="form-check-input"
                      type="checkbox"
                      :disabled="isSubmitting"
                    />
                    <label class="form-check-label" for="profiling-consent-recorded">
                      AI profiling consent recorded
                    </label>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="form-check form-switch admin-user-creation__switch">
                    <input
                      id="gdpr-consent-recorded"
                      v-model="form.gdpr_consent_recorded"
                      class="form-check-input"
                      type="checkbox"
                      :disabled="isSubmitting"
                    />
                    <label class="form-check-label" for="gdpr-consent-recorded">
                      GDPR consent recorded
                    </label>
                  </div>
                </div>
              </div>

            <div class="form-actions mt-4">
              <button class="btn btn-primary" type="submit" :disabled="isSubmitting">
                {{ isSubmitting ? 'Creating...' : 'Create account' }}
              </button>
            </div>
          </form>
        </BaseCard>
      </div>

      <div class="col-lg-4">
        <BaseCard class="admin-user-creation__card" title="Creation summary">
          <div class="admin-user-creation__summary">
            <div class="admin-user-creation__summary-item">
              <h3 class="h6 mb-1">Supported roles</h3>
              <p class="text-body-secondary mb-0">User and Expert</p>
            </div>
            <div class="admin-user-creation__summary-item">
              <h3 class="h6 mb-1">Credential delivery</h3>
              <p class="text-body-secondary mb-0">
                Backend placeholder should create the account and trigger credential email sending.
              </p>
            </div>
            <div class="admin-user-creation__summary-item">
              <h3 class="h6 mb-1">Consent capture</h3>
              <p class="text-body-secondary mb-0">
                Admin can record whether AI profiling and GDPR consents are already documented.
              </p>
            </div>
          </div>

          <BaseAlert
            class="app-alert app-alert--info mt-4"
            variant="info"
            message="This form does not create Admin accounts. Admin provisioning remains restricted outside the UI."
          />
        </BaseCard>
      </div>
    </div>
  </section>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import toastFeedbackMixin from '@/mixins/toastFeedbackMixin';
import adminService from '@/services/adminService';
import {
  email,
  getServerErrorMessage,
  hasFieldError,
  minLength,
  oneOf,
  required,
  validateField,
  validateFields,
} from '@/utils/formValidation';

export default {
  name: 'AdminUserCreationView',
  mixins: [toastFeedbackMixin],
  components: {
    BaseAlert,
    BaseCard,
    BasePageHeader,
  },
  data() {
    return {
      isSubmitting: false,
      successMessage: '',
      errorMessage: '',
      form: this.createInitialForm(),
      errors: this.createInitialErrors(),
    };
  },
  methods: {
    createInitialForm() {
      return {
        first_name: '',
        last_name: '',
        email: '',
        role: 'user',
        temporary_password: '',
        auto_generate_password: true,
        ai_profiling_consent_recorded: false,
        gdpr_consent_recorded: false,
      };
    },
    createInitialErrors() {
      return {
        first_name: '',
        last_name: '',
        email: '',
        role: '',
        temporary_password: '',
      };
    },
    validationRules() {
      return {
        first_name: [required('First name is required.')],
        last_name: [required('Last name is required.')],
        email: [required('Email is required.'), email('Enter a valid email address.')],
        role: [oneOf(['user', 'expert'], 'Role must be user or expert.')],
        temporary_password: [],
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
      const rules = this.validationRules();

      if (fieldName === 'temporary_password' && !this.form.auto_generate_password) {
        rules.temporary_password = [
          required('Temporary password is required when auto-generate is disabled.'),
          minLength(8, 'Temporary password must be at least 8 characters.'),
        ];
      }

      this.errors = validateField(fieldName, this.form, this.errors, rules);
      return !this.errors[fieldName];
    },
    validateForm() {
      const rules = this.validationRules();

      if (!this.form.auto_generate_password) {
        rules.temporary_password = [
          required('Temporary password is required when auto-generate is disabled.'),
          minLength(8, 'Temporary password must be at least 8 characters.'),
        ];
      }

      const fields = ['first_name', 'last_name', 'email', 'role', 'temporary_password'];
      this.errors = validateFields(fields, this.form, rules);

      return fields.every((fieldName) => !this.errors[fieldName]);
    },
    resetForm() {
      this.form = this.createInitialForm();
      this.errors = this.createInitialErrors();
    },
    async handleSubmit() {
      if (!this.validateForm()) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.createUser({
        ...this.form,
        send_credentials_email: true,
      });

      if (response.success) {
        const generatedPassword = response.data?.generated_temporary_password;
        const emailSent = Boolean(response.data?.credentials_email_triggered);

        if (emailSent) {
          this.pushSuccessToast('Account created successfully. Credentials were sent by email.');
        } else if (generatedPassword) {
          this.pushWarningToast(
            `Account created successfully. Email delivery was not confirmed, so use this temporary password manually: ${generatedPassword}.`,
            { autohide: false }
          );
        } else {
          this.pushSuccessToast('Account created successfully.');
        }
        this.resetForm();
      } else {
        this.errorMessage = getServerErrorMessage(response.error, 'Unable to create the account.');
      }

      this.isSubmitting = false;
    },
  },
};
</script>
