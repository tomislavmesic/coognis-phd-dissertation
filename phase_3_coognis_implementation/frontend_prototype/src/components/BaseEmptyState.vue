<template>
  <div class="base-empty-state text-center" :class="stateClass">
    <div v-if="$slots.icon" class="base-empty-state__icon">
      <slot name="icon"></slot>
    </div>
    <h2 class="h4 mb-2">{{ title }}</h2>
    <p class="text-body-secondary mb-0">{{ description }}</p>
    <div v-if="$slots.actions" class="base-empty-state__actions">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BaseEmptyState',
  props: {
    title: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      default: '',
    },
    stateClass: {
      type: [String, Array, Object],
      default: '',
    },
  },
};
</script>
