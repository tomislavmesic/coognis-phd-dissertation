import toastService from '@/services/toastService';

export default {
  methods: {
    pushToast(variant, message, options = {}) {
      return toastService.show({
        ...options,
        variant,
        message,
      });
    },
    pushSuccessToast(message, options = {}) {
      return toastService.success(message, options);
    },
    pushInfoToast(message, options = {}) {
      return toastService.info(message, options);
    },
    pushWarningToast(message, options = {}) {
      return toastService.warning(message, options);
    },
    pushErrorToast(message, options = {}) {
      return toastService.error(message, {
        autohide: false,
        ...options,
      });
    },
  },
  watch: {
    successMessage(value) {
      if (typeof value === 'string' && value.trim()) {
        this.pushSuccessToast(value);
        this.successMessage = '';
      }
    },
    errorMessage(value) {
      if (typeof value === 'string' && value.trim()) {
        this.pushErrorToast(value);
        this.errorMessage = '';
      }
    },
  },
};
