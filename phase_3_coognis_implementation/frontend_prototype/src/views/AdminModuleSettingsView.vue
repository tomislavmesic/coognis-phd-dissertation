<template>
  <section class="admin-module-settings">
    <BasePageHeader
      
      eyebrow="Admin"
      title="AI module settings"
      description="Control which intelligence modules are enabled globally for live MIND conversations."
    />

    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" />

    <BaseLoadingState v-if="isLoading" label="Loading module settings..." state-class="py-5" />

    <BaseCard
      v-else
      class="mb-4"
      title="Conversation intelligence policy"
      subtitle="These settings are applied centrally by the backend."
    >
      <form class="row g-4" @submit.prevent="handleSubmit">
  
        <div class="col-12 col-lg-6" v-for="moduleCard in moduleCards" :key="moduleCard.key">
          <div class="base-settings__module">
            <div class="d-flex justify-content-between align-items-start gap-3">
              <div>
                <h3 class="h5 mb-2">{{ moduleCard.title }}</h3>
                <p class="text-body-secondary mb-0">{{ moduleCard.description }}</p>
              </div>
              <div class="form-check form-switch base-settings__switch">
                <input
                  :id="`module-${moduleCard.key}`"
                  v-model="form[moduleCard.key]"
                  class="form-check-input"
                  type="checkbox"
                  role="switch"
                  :disabled="isSubmitting"
                />
                <label class="form-check-label" :for="`module-${moduleCard.key}`">
                  {{ form[moduleCard.key] ? 'Enabled' : 'Disabled' }}
                </label>
              </div>
            </div>
            <div class="base-settings__note">
              {{ moduleCard.note }}
            </div>
          </div>
        </div>

        <div class="col-12 col-lg-6">
          <div class="base-settings__module">
            <div class="d-flex justify-content-between align-items-start gap-3 flex-wrap">
              <div>
                <h3 class="h5 mb-2">Generation provider</h3>
                <p class="text-body-secondary mb-0">
                  Choose which model provider and runtime model will generate PAGE and ULM responses.
                </p>
              </div>
              <span class="badge text-bg-light border">{{ selectedProviderLabel }}</span>
            </div>
            <div class="row g-3 mt-2">
              <div class="col-12 col-lg-6">
                <label class="form-label" for="llm-provider">Provider</label>
                <select
                  id="llm-provider"
                  v-model="form.llm_provider"
                  class="form-select"
                  :disabled="isSubmitting || !providerOptions.length"
                  @change="handleProviderChange"
                >
                  <option v-for="option in providerOptions" :key="option.provider" :value="option.provider">
                    {{ formatProviderLabel(option.provider) }}
                  </option>
                </select>
              </div>
              <div class="col-12 col-lg-6">
                <label class="form-label" for="llm-model">Model</label>
                <select
                  id="llm-model"
                  v-model="form.llm_model"
                  class="form-select"
                  :disabled="isSubmitting || !selectedProviderOption"
                >
                  <option
                    v-for="model in selectedModelOptions"
                    :key="model"
                    :value="model"
                  >
                    {{ model }}
                  </option>
                </select>
              </div>
            </div>
            <div class="base-settings__note">
              PAGE and ULM use this provider selection. Retrieval, routing, database operations, and expert matching stay
              deterministic in backend code.
            </div>
          </div>
        </div>

        <div class="col-12 d-flex flex-wrap gap-3">
          <button class="btn btn-primary" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Saving...' : 'Save module settings' }}
          </button>
          <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="resetForm">
            Reset
          </button>
        </div>
      </form>
    </BaseCard>
  </section>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BaseLoadingState from '@/components/BaseLoadingState.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import adminService from '@/services/adminService';

export default {
  name: 'AdminModuleSettingsView',
  components: {
    BaseAlert,
    BaseCard,
    BaseLoadingState,
    BasePageHeader,
  },
  data() {
    return {
      isLoading: true,
      isSubmitting: false,
      successMessage: '',
      errorMessage: '',
      initialSettings: {
        synapse_enabled: true,
        uex_enabled: true,
        ulm_enabled: false,
        page_enabled: true,
        llm_provider: 'mock',
        llm_model: 'mock',
      },
      form: {
        synapse_enabled: true,
        uex_enabled: true,
        ulm_enabled: false,
        page_enabled: true,
        llm_provider: 'mock',
        llm_model: 'mock',
      },
      providerOptions: [],
    };
  },
  computed: {
    moduleCards() {
      return [
        {
          key: 'synapse_enabled',
          title: 'SYNAPSE',
          description: 'Controls profiling and adaptive user-style inference for conversation routing and personalization.',
          note: 'Disable this if you want responses without live profiling signals.',
        },
        {
          key: 'uex_enabled',
          title: 'UEX',
          description: 'Controls expert matching, knowledge context injection, and expert recommendation generation.',
          note: 'Disable this if you want to evaluate system responses without expert routing and UEX knowledge.',
        },
        {
          key: 'ulm_enabled',
          title: 'ULM',
          description: 'Controls retrieval-based grounding and extra explanation generation from indexed source context.',
          note: 'ULM is optional and can be enabled globally when you want retrieval support in live conversations.',
        },
        {
          key: 'page_enabled',
          title: 'PAGE',
          description: 'Controls the final response composition layer that packages outputs into the user-facing answer.',
          note: 'Disabling PAGE falls back to a simpler backend-composed response without PAGE formatting.',
        },
      ];
    },
    selectedProviderOption() {
      return this.providerOptions.find((item) => item.provider === this.form.llm_provider) || null;
    },
    selectedModelOptions() {
      return this.selectedProviderOption?.model_options || [];
    },
    selectedProviderLabel() {
      const option = this.selectedProviderOption;
      if (!option) {
        return 'No provider available';
      }
      return `${this.formatProviderLabel(option.provider)} · ${this.form.llm_model}`;
    },
  },
  created() {
    this.loadSettings();
  },
  methods: {
    async loadSettings() {
      this.isLoading = true;
      this.errorMessage = '';

      const response = await adminService.fetchModuleSettings();

      if (response.success) {
        const data = response.data || {};
        this.providerOptions = Array.isArray(data.llm_available_providers) ? data.llm_available_providers : [];
        this.initialSettings = {
          synapse_enabled: Boolean(data.synapse_enabled),
          uex_enabled: Boolean(data.uex_enabled),
          ulm_enabled: Boolean(data.ulm_enabled),
          page_enabled: Boolean(data.page_enabled),
          llm_provider: data.llm_provider || this.providerOptions[0]?.provider || 'mock',
          llm_model: data.llm_model || this.providerOptions[0]?.default_model || 'mock',
        };
        this.resetForm();
      } else {
        this.errorMessage = response.error?.message || 'Unable to load module settings.';
      }

      this.isLoading = false;
    },
    resetForm() {
      this.successMessage = '';
      this.errorMessage = '';
      this.form = {
        synapse_enabled: this.initialSettings.synapse_enabled,
        uex_enabled: this.initialSettings.uex_enabled,
        ulm_enabled: this.initialSettings.ulm_enabled,
        page_enabled: this.initialSettings.page_enabled,
        llm_provider: this.initialSettings.llm_provider,
        llm_model: this.initialSettings.llm_model,
      };
      this.ensureValidModelSelection();
    },
    formatProviderLabel(provider) {
      if (provider === 'llama_cpp') {
        return 'llama.cpp';
      }
      if (provider === 'openai') {
        return 'OpenAI';
      }
      if (provider === 'mock') {
        return 'Mock';
      }
      return provider;
    },
    handleProviderChange() {
      this.ensureValidModelSelection({ resetToDefault: true });
    },
    ensureValidModelSelection({ resetToDefault = false } = {}) {
      const option = this.selectedProviderOption;
      if (!option) {
        this.form.llm_model = '';
        return;
      }

      const currentModel = this.form.llm_model;
      if (resetToDefault || !option.model_options.includes(currentModel)) {
        this.form.llm_model = option.default_model;
      }
    },
    async handleSubmit() {
      if (this.isSubmitting) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.updateModuleSettings(this.form);

      if (response.success) {
        const data = response.data || {};
        this.providerOptions = Array.isArray(data.llm_available_providers) ? data.llm_available_providers : this.providerOptions;
        this.initialSettings = {
          synapse_enabled: Boolean(data.synapse_enabled),
          uex_enabled: Boolean(data.uex_enabled),
          ulm_enabled: Boolean(data.ulm_enabled),
          page_enabled: Boolean(data.page_enabled),
          llm_provider: data.llm_provider || this.form.llm_provider,
          llm_model: data.llm_model || this.form.llm_model,
        };
        this.resetForm();
        this.successMessage = 'Module settings updated.';
      } else {
        this.errorMessage = response.error?.message || 'Unable to update module settings.';
      }

      this.isSubmitting = false;
    },
  },
};
</script>
