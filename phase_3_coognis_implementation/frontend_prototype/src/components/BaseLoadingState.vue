<template>
  <div class="base-loading-state text-center" :class="stateClass" role="status" aria-live="polite">
    <div class="spinner-border text-primary" aria-hidden="true"></div>
    <p class="base-loading-state__label mb-0">{{ label }}</p>
  </div>
</template>

<script>
export default {
  name: 'BaseLoadingState',
  props: {
    label: {
      type: String,
      default: 'Loading...',
    },
    stateClass: {
      type: [String, Array, Object],
      default: '',
    },
  },
};
</script>
