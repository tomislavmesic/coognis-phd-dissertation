<template>
  <section class="card base-card h-100" :class="cardClass">
    <div v-if="title || $slots.header" class="card-header base-card__header" :class="cardHeaderClass">
      <slot name="header">
        <div class="base-card__header-content" :class="headerContentClass">
          <div class="base-card__heading">
            <h2 v-if="title" class="h5 mb-1">{{ title }}</h2>
            <p v-if="subtitle" class="text-body-secondary mb-0">{{ subtitle }}</p>
          </div>
          <div v-if="$slots.actions" class="base-card__actions">
            <slot name="actions"></slot>
          </div>
        </div>
      </slot>
    </div>
    <div class="card-body base-card__body" :class="cardBodyClass">
      <slot></slot>
    </div>
    <div v-if="$slots.footer" class="card-footer base-card__footer" :class="cardFooterClass">
      <slot name="footer"></slot>
    </div>
  </section>
</template>

<script>
export default {
  name: 'BaseCard',
  props: {
    title: {
      type: String,
      default: '',
    },
    subtitle: {
      type: String,
      default: '',
    },
    cardClass: {
      type: [String, Array, Object],
      default: '',
    },
    cardHeaderClass: {
      type: [String, Array, Object],
      default: '',
    },
    headerContentClass: {
      type: [String, Array, Object],
      default: '',
    },
    cardBodyClass: {
      type: [String, Array, Object],
      default: '',
    },
  },
};
</script>
