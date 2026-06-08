<template>
  <BaseCard
    title="Change password"
    subtitle="Update the account password through a dedicated confirmation flow."
    :card-class="cardClass"
    card-header-class="pb-0"
  >
    <BaseAlert v-if="successMessage" class="mb-3" variant="success" :message="successMessage" />
    <button class="btn btn-outline-primary" type="button" @click="openModal">
      Change password
    </button>
  </BaseCard>

  <BaseModal
    :visible="isModalOpen"
    eyebrow="Security"
    title="Change password"
    modal-id="change-password-modal"
    dialog-class="modal-dialog-centered"
    :busy="isSubmitting"
    @close="closeModal"
  >
    <BaseAlert v-if="errorMessage" class="mb-3" variant="danger" :message="errorMessage" role="alert" />

    <form class="row g-3" novalidate @submit.prevent="handleSubmit">
      <div class="col-12">
        <label class="form-label" for="change-password-current">Current password</label>
        <input
          id="change-password-current"
          v-model="form.current_password"
          class="form-control"
          :class="{ 'is-invalid': errors.current_password }"
          type="password"
          autocomplete="current-password"
          :disabled="isSubmitting"
          @blur="validateFieldState('current_password')"
        />
        <div v-if="errors.current_password" class="invalid-feedback d-block">{{ errors.current_password }}</div>
      </div>

      <div class="col-12">
        <label class="form-label" for="change-password-new">New password</label>
        <input
          id="change-password-new"
          v-model="form.new_password"
          class="form-control"
          :class="{ 'is-invalid': errors.new_password }"
          type="password"
          autocomplete="new-password"
          :disabled="isSubmitting"
          @blur="validateFieldState('new_password')"
        />
        <div v-if="errors.new_password" class="invalid-feedback d-block">{{ errors.new_password }}</div>
      </div>

      <div class="col-12">
        <label class="form-label" for="change-password-confirm">Confirm new password</label>
        <input
          id="change-password-confirm"
          v-model="form.new_password_confirmation"
          class="form-control"
          :class="{ 'is-invalid': errors.new_password_confirmation }"
          type="password"
          autocomplete="new-password"
          :disabled="isSubmitting"
          @blur="validateFieldState('new_password_confirmation')"
        />
        <div v-if="errors.new_password_confirmation" class="invalid-feedback d-block">
          {{ errors.new_password_confirmation }}
        </div>
      </div>
    </form>

    <template #footer>
      <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeModal">
        Cancel
      </button>
      <button class="btn btn-primary" type="button" :disabled="isSubmitting" @click="handleSubmit">
        {{ isSubmitting ? 'Saving...' : 'Save password' }}
      </button>
    </template>
  </BaseModal>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BaseModal from '@/components/BaseModal.vue';
import authService from '@/services/authService';
import { matchesField, minLength, required, validateField, validateFields } from '@/utils/formValidation';

export default {
  name: 'ChangePasswordCard',
  components: {
    BaseAlert,
    BaseCard,
    BaseModal,
  },
  props: {
    cardClass: {
      type: [String, Array, Object],
      default: 'h-auto',
    },
  },
  data() {
    return {
      isModalOpen: false,
      isSubmitting: false,
      successMessage: '',
      errorMessage: '',
      form: {
        current_password: '',
        new_password: '',
        new_password_confirmation: '',
      },
      errors: {
        current_password: '',
        new_password: '',
        new_password_confirmation: '',
      },
    };
  },
  computed: {
    validationRules() {
      return {
        current_password: [required('Current password is required.')],
        new_password: [
          required('New password is required.'),
          minLength(8, 'New password must be at least 8 characters.'),
        ],
        new_password_confirmation: [
          required('Password confirmation is required.'),
          matchesField('new_password', 'Password confirmation must match the new password.'),
        ],
      };
    },
  },
  methods: {
    openModal() {
      this.errorMessage = '';
      this.isModalOpen = true;
    },
    closeModal() {
      if (this.isSubmitting) {
        return;
      }

      this.isModalOpen = false;
      this.errorMessage = '';
      this.resetForm();
    },
    resetForm() {
      this.form = {
        current_password: '',
        new_password: '',
        new_password_confirmation: '',
      };
      this.errors = {
        current_password: '',
        new_password: '',
        new_password_confirmation: '',
      };
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
      this.errorMessage = '';

      const response = await authService.changePassword(this.form);

      if (response.success) {
        this.successMessage = response.data?.message || 'Password changed successfully.';
        this.isModalOpen = false;
        this.resetForm();
      } else {
        this.errorMessage = response.error?.message || 'Unable to change password.';
      }

      this.isSubmitting = false;
    },
  },
};
</script>
