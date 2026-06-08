<template>
  <div
    class="modal fade base-modal"
    :class="{ show: visible, 'base-modal--visible': visible }"
    tabindex="-1"
    role="dialog"
    :aria-hidden="visible ? 'false' : 'true'"
    :aria-labelledby="titleId"
    @click.self="handleClose"
  >
    <div class="modal-dialog" :class="dialogClass">
      <div class="modal-content base-modal__content">
        <div class="modal-header border-0 base-modal__header">
          <div>
            <p v-if="eyebrow" class="placeholder-eyebrow mb-2">{{ eyebrow }}</p>
            <h2 :id="titleId" class="modal-title h4 mb-0">{{ title }}</h2>
          </div>
          <button class="btn-close" type="button" aria-label="Close" :disabled="busy" @click="handleClose"></button>
        </div>

        <div class="modal-body base-modal__body">
          <slot></slot>
        </div>

        <div v-if="$slots.footer" class="modal-footer border-0 base-modal__footer">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>
  </div>

  <div v-if="visible" class="modal-backdrop fade show"></div>
</template>

<script>
export default {
  name: 'BaseModal',
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    title: {
      type: String,
      required: true,
    },
    eyebrow: {
      type: String,
      default: '',
    },
    modalId: {
      type: String,
      default: 'base-modal',
    },
    dialogClass: {
      type: [String, Array, Object],
      default: 'modal-dialog-centered',
    },
    busy: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['close'],
  computed: {
    titleId() {
      return `${this.modalId}-title`;
    },
  },
  watch: {
    visible(value) {
      if (typeof document === 'undefined') {
        return;
      }

      if (value) {
        document.addEventListener('keydown', this.handleKeydown);
        document.body.classList.add('modal-open');
      } else {
        document.removeEventListener('keydown', this.handleKeydown);
        document.body.classList.remove('modal-open');
      }
    },
  },
  mounted() {
    if (this.visible && typeof document !== 'undefined') {
      document.addEventListener('keydown', this.handleKeydown);
      document.body.classList.add('modal-open');
    }
  },
  beforeUnmount() {
    if (typeof document !== 'undefined') {
      document.removeEventListener('keydown', this.handleKeydown);
      document.body.classList.remove('modal-open');
    }
  },
  methods: {
    handleKeydown(event) {
      if (event.key !== 'Escape') {
        return;
      }

      this.handleClose();
    },
    handleClose() {
      if (this.busy) {
        return;
      }

      this.$emit('close');
    },
  },
};
</script>
