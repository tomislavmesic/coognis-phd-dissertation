<template>
  <div
    class="modal fade feedback-modal"
    :class="{ show: visible, 'feedback-modal--visible': visible }"
    tabindex="-1"
    role="dialog"
    :aria-hidden="visible ? 'false' : 'true'"
    :aria-labelledby="titleId"
    @click.self="handleClose"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content feedback-modal__content">
        <div class="modal-header border-0">
          <div>
            <p class="placeholder-eyebrow mb-2">{{ modeLabel }}</p>
            <h2 :id="titleId" class="modal-title h4 mb-0">Share feedback</h2>
          </div>
          <button class="btn-close" type="button" aria-label="Close" :disabled="submitting" @click="handleClose"></button>
        </div>

        <form @submit.prevent="handleSubmit">
          <div class="modal-body">
            <p class="text-body-secondary mb-4">
              {{ description }}
            </p>

            <div v-if="errorMessage" class="alert alert-danger" role="alert">
              {{ errorMessage }}
            </div>

            <div class="row g-3">
              <div class="col-md-4">
                <label class="form-label" for="feedback-clarity">Clarity</label>
                <select id="feedback-clarity" v-model="form.clarity" class="form-select" :disabled="submitting">
                  <option value="">Select</option>
                  <option v-for="option in scoreOptions" :key="`clarity-${option.value}`" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <div v-if="validation.clarity" class="invalid-feedback d-block">
                  {{ validation.clarity }}
                </div>
              </div>

              <div class="col-md-4">
                <label class="form-label" for="feedback-usefulness">Usefulness</label>
                <select id="feedback-usefulness" v-model="form.usefulness" class="form-select" :disabled="submitting">
                  <option value="">Select</option>
                  <option v-for="option in scoreOptions" :key="`usefulness-${option.value}`" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <div v-if="validation.usefulness" class="invalid-feedback d-block">
                  {{ validation.usefulness }}
                </div>
              </div>

              <div class="col-md-4">
                <label class="form-label" for="feedback-satisfaction">Satisfaction</label>
                <select id="feedback-satisfaction" v-model="form.satisfaction" class="form-select" :disabled="submitting">
                  <option value="">Select</option>
                  <option v-for="option in scoreOptions" :key="`satisfaction-${option.value}`" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <div v-if="validation.satisfaction" class="invalid-feedback d-block">
                  {{ validation.satisfaction }}
                </div>
              </div>

              <div v-if="isExpertMode" class="col-md-6">
                <label class="form-label" for="feedback-communication-quality">Communication quality</label>
                <select
                  id="feedback-communication-quality"
                  v-model="form.communication_quality"
                  class="form-select"
                  :disabled="submitting"
                >
                  <option value="">Select</option>
                  <option
                    v-for="option in scoreOptions"
                    :key="`communication-${option.value}`"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
                <div v-if="validation.communication_quality" class="invalid-feedback d-block">
                  {{ validation.communication_quality }}
                </div>
              </div>

              <div class="col-12">
                <label class="form-label" for="feedback-comment">Comment</label>
                <textarea
                  id="feedback-comment"
                  v-model.trim="form.comment"
                  class="form-control"
                  rows="4"
                  :disabled="submitting"
                  placeholder="Optional additional feedback"
                ></textarea>
              </div>
            </div>
          </div>

          <div class="modal-footer border-0">
            <button class="btn btn-outline-secondary" type="button" :disabled="submitting" @click="handleClose">
              Cancel
            </button>
            <button class="btn btn-primary" type="submit" :disabled="submitting">
              {{ submitting ? 'Submitting...' : 'Submit feedback' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div v-if="visible" class="modal-backdrop fade show"></div>
</template>

<script>
const MODE_SYSTEM = 'system';
const MODE_EXPERT = 'expert';

function buildInitialForm() {
  return {
    clarity: '',
    usefulness: '',
    satisfaction: '',
    communication_quality: '',
    comment: '',
  };
}

export default {
  name: 'FeedbackModal',
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    mode: {
      type: String,
      default: MODE_SYSTEM,
      validator(value) {
        return [MODE_SYSTEM, MODE_EXPERT].includes(value);
      },
    },
    submitting: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['close', 'submit'],
  data() {
    return {
      form: buildInitialForm(),
      validation: {},
      scoreOptions: [
        { value: '1', label: '1 - Low' },
        { value: '2', label: '2 - Fair' },
        { value: '3', label: '3 - Good' },
        { value: '4', label: '4 - Very good' },
        { value: '5', label: '5 - Excellent' },
      ],
    };
  },
  computed: {
    isExpertMode() {
      return this.mode === MODE_EXPERT;
    },
    modeLabel() {
      return this.isExpertMode ? 'Expert interaction feedback' : 'System response feedback';
    },
    description() {
      return this.isExpertMode
        ? 'Rate the quality of the expert interaction and leave any useful context for follow-up review.'
        : 'Rate the system response quality and leave optional context to improve future interactions.';
    },
    titleId() {
      return `feedback-modal-title-${this.mode}`;
    },
    errorMessage() {
      const firstError = Object.values(this.validation)[0];
      return firstError || '';
    },
  },
  watch: {
    visible(isVisible) {
      if (isVisible) {
        this.resetForm();
      }
    },
    mode() {
      this.resetForm();
    },
  },
  methods: {
    resetForm() {
      this.form = buildInitialForm();
      this.validation = {};
    },
    validateForm() {
      const validation = {};

      if (!this.form.clarity) {
        validation.clarity = 'Clarity rating is required.';
      }

      if (!this.form.usefulness) {
        validation.usefulness = 'Usefulness rating is required.';
      }

      if (!this.form.satisfaction) {
        validation.satisfaction = 'Satisfaction rating is required.';
      }

      if (this.isExpertMode && !this.form.communication_quality) {
        validation.communication_quality = 'Communication quality rating is required for expert feedback.';
      }

      this.validation = validation;

      return Object.keys(validation).length === 0;
    },
    handleClose() {
      if (this.submitting) {
        return;
      }

      this.$emit('close');
    },
    handleSubmit() {
      if (!this.validateForm()) {
        return;
      }

      this.$emit('submit', {
        mode: this.mode,
        clarity: Number(this.form.clarity),
        usefulness: Number(this.form.usefulness),
        satisfaction: Number(this.form.satisfaction),
        communication_quality: this.isExpertMode ? Number(this.form.communication_quality) : null,
        comment: this.form.comment || null,
      });
    },
  },
};
</script>
