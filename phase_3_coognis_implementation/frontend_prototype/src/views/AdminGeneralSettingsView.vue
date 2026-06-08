<template>
  <section class="admin-general-settings">
    <BasePageHeader
      eyebrow="Admin"
      title="General settings"
      description="Control runtime-safe conversation flags without touching infrastructure-only environment settings."
    />

    <BaseLoadingState v-if="isLoading" label="Loading general settings..." state-class="py-5" />

    <BaseCard
      v-if="!isLoading"
      title="Security controls"
      subtitle="High-impact authentication policy changes for platform roles."
      class="mb-4"
      card-header-class="pb-0"
      card-body-class="pt-0"
    >
      <div class="row">
        <div class="col-sm-4 g-4">
          <div class="base-settings__module d-flex align-items-center justify-content-between gap-3">
            <div>
              <h3 class="h6 mb-1">Users</h3>
              <p class="text-body-secondary mb-0">Bulk enable or disable 2FA for user accounts.</p>
            </div>
            <div class="form-check form-switch base-settings__switch mb-0">
              <input
                id="general-2fa-user"
                v-model="roleTwoFactorState.user"
                class="form-check-input"
                type="checkbox"
                role="switch"
                :disabled="isUpdatingTwoFactor"
                @change="onRoleTwoFactorToggle('user')"
              />
              <label class="form-check-label" for="general-2fa-user">
                {{ roleTwoFactorLabel('user') }}
              </label>
            </div>
          </div>
        </div>

        <div class="col-sm-4 g-4">
          <div class="base-settings__module d-flex align-items-center justify-content-between gap-3">
            <div>
              <h3 class="h6 mb-1">Experts</h3>
              <p class="text-body-secondary mb-0">Bulk enable or disable 2FA for expert accounts.</p>
            </div>
            <div class="form-check form-switch base-settings__switch mb-0">
              <input
                id="general-2fa-expert"
                v-model="roleTwoFactorState.expert"
                class="form-check-input"
                type="checkbox"
                role="switch"
                :disabled="isUpdatingTwoFactor"
                @change="onRoleTwoFactorToggle('expert')"
              />
              <label class="form-check-label" for="general-2fa-expert">
                {{ roleTwoFactorLabel('expert') }}
              </label>
            </div>
          </div>
        </div>

        <div class="col-sm-4 g-4">
          <div class="base-settings__module d-flex align-items-center justify-content-between gap-3">
            <div>
              <h3 class="h6 mb-1">Admins</h3>
              <p class="text-body-secondary mb-0">Admin 2FA remains enforced and cannot be disabled.</p>
            </div>
            <span class="badge text-bg-dark">Always enabled</span>
          </div>
        </div>
      </div>
    </BaseCard>

    <BaseCard
      v-if="!isLoading" 
      title="Platform conversation controls"
      subtitle="These flags affect live chat behavior and operator visibility."
      card-header-class="pb-0"
    >
      <form class="row g-4" @submit.prevent="handleSubmit">
        <div class="col-12 col-lg-6" v-for="settingCard in settingCards" :key="settingCard.key">
          <div class="base-settings__module">
            <div class="d-flex justify-content-between align-items-start gap-3">
              <div>
                <h3 class="h5 mb-2">{{ settingCard.title }}</h3>
                <p class="text-body-secondary mb-0">{{ settingCard.description }}</p>
              </div>
              <div class="form-check form-switch base-settings__switch">
                <input
                  :id="`general-${settingCard.key}`"
                  v-model="form[settingCard.key]"
                  class="form-check-input"
                  type="checkbox"
                  role="switch"
                  :disabled="isSubmitting"
                />
                <label class="form-check-label" :for="`general-${settingCard.key}`">
                  {{ form[settingCard.key] ? 'Enabled' : 'Disabled' }}
                </label>
              </div>
            </div>
            <div class="base-settings__note">
              {{ settingCard.note }}
            </div>
          </div>
        </div>

        <div class="col-12 d-flex flex-wrap gap-3">
          <button class="btn btn-primary" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Saving...' : 'Save conversation settings' }}
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
import BaseCard from '@/components/BaseCard.vue';
import BaseLoadingState from '@/components/BaseLoadingState.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import toastFeedbackMixin from '@/mixins/toastFeedbackMixin';
import adminService from '@/services/adminService';

export default {
  name: 'AdminGeneralSettingsView',
  mixins: [toastFeedbackMixin],
  components: {
    BaseCard,
    BaseLoadingState,
    BasePageHeader,
  },
  data() {
    return {
      isLoading: true,
      isSubmitting: false,
      isUpdatingTwoFactor: false,
      successMessage: '',
      errorMessage: '',
      initialSettings: {
        show_chat_debug_panels: false,
        verbose_routing_logs: true,
        allow_expert_handoff: true,
        allow_ulm_in_chat: true,
      },
      form: {
        show_chat_debug_panels: false,
        verbose_routing_logs: true,
        allow_expert_handoff: true,
        allow_ulm_in_chat: true,
      },
      roleTwoFactorState: {
        user: false,
        expert: false,
      },
    };
  },
  computed: {
    settingCards() {
      return [
        {
          key: 'show_chat_debug_panels',
          title: 'Chat debug panels',
          description: 'Controls whether live MIND responses include the debug payload that powers chat-side debug panels.',
          note: 'Disable this when you want cleaner production-style conversations without PAGE, UEX, and SYNAPSE trace details.',
        },
        {
          key: 'verbose_routing_logs',
          title: 'Verbose routing logs',
          description: 'Controls whether MIND emits detailed routing-decision events into structured application logs.',
          note: 'Disable this to reduce conversation-orchestration noise in logs while leaving normal request logging untouched.',
        },
        {
          key: 'allow_expert_handoff',
          title: 'Expert handoff',
          description: 'Controls whether user conversations can be handed off into expert mode and whether expert suggestions are surfaced.',
          note: 'Disable this to keep UEX knowledge active without allowing direct human handoff in live chats.',
        },
        {
          key: 'allow_ulm_in_chat',
          title: 'ULM in chat',
          description: 'Controls whether live MIND chat flows can invoke ULM grounding when the request asks for retrieval support.',
          note: 'Disable this to keep indexed sources available in admin while removing retrieval-grounded augmentation from chats.',
        },
      ];
    },
  },
  created() {
    this.loadSettings();
  },
  methods: {
    normalizeTwoFactorValue(value) {
      if (typeof value === 'boolean') {
        return value;
      }

      return String(value || '').toLowerCase() === 'enabled';
    },
    deriveRoleTwoFactorState(role, dashboardData = {}) {
      const activeExperts = (dashboardData.active_experts || []).map((item) => ({
        twoFactor: item.two_factor,
      }));
      const activeUsers = (dashboardData.active_users || []).map((item) => ({
        twoFactor: item.two_factor,
      }));

      if (role === 'expert') {
        const expertAccounts = activeExperts.filter((item) => item.twoFactor !== 'No platform account');

        if (!expertAccounts.length) {
          return false;
        }

        return expertAccounts.every((item) => this.normalizeTwoFactorValue(item.twoFactor));
      }

      if (!activeUsers.length) {
        return false;
      }

      return activeUsers.every((item) => this.normalizeTwoFactorValue(item.twoFactor));
    },
    roleTwoFactorLabel(role) {
      return this.roleTwoFactorState[role] ? 'Enabled' : 'Disabled';
    },
    onRoleTwoFactorToggle(role) {
      this.handleBulkTwoFactorUpdate(role, this.roleTwoFactorState[role]);
    },
    async loadSettings() {
      this.isLoading = true;
      this.errorMessage = '';

      const [settingsResponse, dashboardResponse] = await Promise.all([
        adminService.fetchGeneralSettings(),
        adminService.fetchDashboardSummary(),
      ]);

      if (settingsResponse.success) {
        const data = settingsResponse.data || {};
        this.initialSettings = {
          show_chat_debug_panels: Boolean(data.show_chat_debug_panels),
          verbose_routing_logs: Boolean(data.verbose_routing_logs),
          allow_expert_handoff: Boolean(data.allow_expert_handoff),
          allow_ulm_in_chat: Boolean(data.allow_ulm_in_chat),
        };
        this.resetForm();
      } else {
        this.errorMessage = settingsResponse.error?.message || 'Unable to load general settings.';
      }

      if (dashboardResponse.success) {
        const dashboardData = dashboardResponse.data || {};
        this.roleTwoFactorState = {
          user: this.deriveRoleTwoFactorState('user', dashboardData),
          expert: this.deriveRoleTwoFactorState('expert', dashboardData),
        };
      } else if (!this.errorMessage) {
        this.errorMessage = dashboardResponse.error?.message || 'Unable to load security controls.';
      }

      this.isLoading = false;
    },
    resetForm() {
      this.successMessage = '';
      this.errorMessage = '';
      this.form = {
        show_chat_debug_panels: this.initialSettings.show_chat_debug_panels,
        verbose_routing_logs: this.initialSettings.verbose_routing_logs,
        allow_expert_handoff: this.initialSettings.allow_expert_handoff,
        allow_ulm_in_chat: this.initialSettings.allow_ulm_in_chat,
      };
    },
    async handleSubmit() {
      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.updateGeneralSettings(this.form);

      if (response.success) {
        const data = response.data || {};
        this.initialSettings = {
          show_chat_debug_panels: Boolean(data.show_chat_debug_panels),
          verbose_routing_logs: Boolean(data.verbose_routing_logs),
          allow_expert_handoff: Boolean(data.allow_expert_handoff),
          allow_ulm_in_chat: Boolean(data.allow_ulm_in_chat),
        };
        this.resetForm();
        this.successMessage = 'General settings saved.';
      } else {
        this.errorMessage = response.error?.message || 'Unable to save general settings.';
      }

      this.isSubmitting = false;
    },
    async handleBulkTwoFactorUpdate(role, enabled) {
      const previousValue = this.roleTwoFactorState[role];
      this.isUpdatingTwoFactor = true;
      this.errorMessage = '';
      this.successMessage = '';
      this.roleTwoFactorState = {
        ...this.roleTwoFactorState,
        [role]: enabled,
      };

      const response = await adminService.bulkUpdateTwoFactor({
        role,
        enabled,
      });

      if (!response.success) {
        this.errorMessage = response.error?.message || 'Unable to update 2FA settings.';
        this.roleTwoFactorState = {
          ...this.roleTwoFactorState,
          [role]: previousValue,
        };
        this.isUpdatingTwoFactor = false;
        return;
      }

      this.successMessage = response.data?.message || 'Two-factor settings updated.';
      await this.loadSettings();
      this.isUpdatingTwoFactor = false;
    },
  },
};
</script>
