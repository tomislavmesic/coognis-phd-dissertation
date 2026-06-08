<template>
  <div class="alert base-alert d-flex align-items-start gap-3" :class="`alert-${variant}`" :role="role">
    <div v-if="$slots.icon" class="base-alert__icon">
      <slot name="icon"></slot>
    </div>
    <div class="base-alert__content">
      <h2 v-if="title" class="base-alert__title h6 mb-1">{{ title }}</h2>
      <div>
        <slot>{{ message }}</slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BaseAlert',
  props: {
    variant: {
      type: String,
      default: 'info',
    },
    title: {
      type: String,
      default: '',
    },
    message: {
      type: String,
      default: '',
    },
    role: {
      type: String,
      default: 'status',
    },
  },
};
</script>
