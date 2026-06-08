<template>
  <section class="card base-card">
    <div class="card-body">
      <p class="placeholder-eyebrow mb-3">Expert suggestion</p>
      <h2 class="h5 mb-3">{{ expert.name }}</h2>

      <dl class="expert-handoff-card__meta mb-4">
        <div>
          <dt>Domain</dt>
          <dd>{{ expert.domain }}</dd>
        </div>
        <div>
          <dt>Reason</dt>
          <dd>{{ expert.reason }}</dd>
        </div>
        <div>
          <dt>Compatibility</dt>
          <dd>{{ expert.compatibility }}</dd>
        </div>
      </dl>

      <div class="alert mb-4" :class="mode === 'expert' ? 'alert-success' : 'alert-info'" role="status">
        {{ mode === 'expert'
          ? 'Expert mode is active. The same chat channel remains open while the expert takes over.'
          : 'System mode can keep the conversation here or hand it off to an expert without changing the chat UI.' }}
      </div>

      <div
        v-if="expert.isContactable === false"
        class="alert alert-warning mb-4"
        role="alert"
      >
        This expert is available in UEX, but does not have a provisioned COOGNIS expert account yet. An admin must provision the account before chat handoff is possible.
      </div>

      <div class="d-flex flex-wrap gap-2">
        <button class="btn btn-primary" type="button" :disabled="disabled || expert.isContactable === false" @click="$emit('contact-expert')">
          {{ expert.isContactable === false ? 'Contact unavailable' : 'Contact expert' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'ExpertHandoffCard',
  props: {
    expert: {
      type: Object,
      required: true,
    },
    mode: {
      type: String,
      default: 'system',
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['continue-system', 'contact-expert'],
};
</script>
