<template>
  <header class="base-page-header" :class="headerClass">
    <div>
      <p v-if="eyebrow" class="placeholder-eyebrow mb-2">{{ eyebrow }}</p>
      <h1 class="base-page-header__title mb-2">{{ title }}</h1>
      <p v-if="description" class="base-page-header__description mb-0">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="base-page-header__actions">
      <slot name="actions"></slot>
    </div>
  </header>
</template>

<script>
export default {
  name: 'BasePageHeader',
  props: {
    eyebrow: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      default: '',
    },
    headerClass: {
      type: [String, Array, Object],
      default: '',
    },
  },
};
</script>
