<template>
  <div class="toast-container position-fixed top-0 end-0 p-3 app-toast-container">
    <div
      v-for="item in items"
      :key="item.id"
      :ref="(element) => setToastRef(item.id, element)"
      class="toast app-toast"
      :class="`app-toast--${item.variant}`"
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div class="toast-header app-toast__header">
        <strong class="me-auto">{{ item.title }}</strong>
        <button
          type="button"
          class="btn-close"
          data-bs-dismiss="toast"
          aria-label="Close"
        ></button>
      </div>
      <div class="toast-body app-toast__body">
        {{ item.message }}
      </div>
    </div>
  </div>
</template>

<script>
import { Toast } from 'bootstrap';
import toastService from '@/services/toastService';

export default {
  name: 'AppToastViewport',
  data() {
    return {
      toastRefs: new Map(),
      toastInstances: new Map(),
    };
  },
  computed: {
    items() {
      return toastService.state.items;
    },
  },
  watch: {
    items: {
      deep: true,
      handler() {
        this.$nextTick(() => {
          this.items.forEach((item) => {
            this.ensureToast(item);
          });
        });
      },
    },
  },
  beforeUnmount() {
    this.toastInstances.forEach(({ instance, element, onHidden }) => {
      if (element && onHidden) {
        element.removeEventListener('hidden.bs.toast', onHidden);
      }
      instance.dispose();
    });
    this.toastInstances.clear();
    this.toastRefs.clear();
  },
  methods: {
    setToastRef(id, element) {
      if (element) {
        this.toastRefs.set(id, element);
        return;
      }
      this.toastRefs.delete(id);
    },
    ensureToast(item) {
      if (this.toastInstances.has(item.id)) {
        return;
      }

      const element = this.toastRefs.get(item.id);
      if (!element) {
        return;
      }

      const instance = Toast.getOrCreateInstance(element, {
        autohide: item.autohide,
        delay: item.delay,
      });

      const onHidden = () => {
        element.removeEventListener('hidden.bs.toast', onHidden);
        this.toastInstances.delete(item.id);
        toastService.remove(item.id);
      };

      element.addEventListener('hidden.bs.toast', onHidden);
      this.toastInstances.set(item.id, {
        instance,
        element,
        onHidden,
      });
      instance.show();
    },
  },
};
</script>
