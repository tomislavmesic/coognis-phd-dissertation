<template>
  <section class="base-dashboard">
    <div class="row g-4">
      <div class="col-md-9">
        <BasePageHeader
          class="base-dashboard__hero h-100"
          eyebrow="User workspace"
          :title="`👋 Hello, ${displayName}`"
          description="Continue your activity, review privacy settings, and prepare for new expert interactions from one place."
        >
          <template #actions>
            <div class="base-dashboard__hero-actions">
              <RouterLink class="btn" to="/user/chat">Start chat</RouterLink>
              <RouterLink class="btn btn-outline" to="/user/settings">Settings</RouterLink>
            </div>
          </template>
        </BasePageHeader>
      </div>
      <div class="col-md-3">
        <BaseCard 
          class="base-card base-stat-card"
          card-body-class="p-0"
        >
          <ul class="list-unstyled mb-0 d-flex flex-column gap-3">
            <li>
              <span class="badge align-self-start mb-1" :class="recommendation.profiling_used ? 'text-bg-warning' : 'text-bg-secondary'" >
                {{ profileIndicatorLabel }}
              </span>
              <div class="base-stat-note mb-0">Profiling signals used for expert matching.</div>
            </li>
            <li>
              <strong>AI profiling consent</strong>
              <p class="base-stat-note mb-0">
                <span class="badge" :class="consentBadgeClass(consentStatus.ai_profiling_consent)">
                  {{ consentLabel(consentStatus.ai_profiling_consent) }}
                </span>
              </p>
            </li>
            <li>
              <strong>GDPR consent</strong>
              <p class="base-stat-note mb-0">
                <span class="badge" :class="consentBadgeClass(consentStatus.gdpr_consent)">
                  {{ consentLabel(consentStatus.gdpr_consent) }}
                </span>
              </p>
            </li>

          </ul>
        </BaseCard>
      </div>
    </div>

    <div class="row g-4">
      <div class="col-md-6 col-xl-3" v-for="item in overviewStats" :key="item.label">
        <div class="base-card base-stat-card">
          <span class="base-stat-label">{{ item.label }}</span>
          <strong class="base-stat-value">{{ item.value }}</strong>
          <p class="base-stat-note mb-0">{{ item.note }}</p>
        </div>
      </div>
    </div>

    <div class="row g-4">
      <div class="col-md-6 col-xl-4" v-for="action in quickActions" :key="action.title">
        <BaseCard>
          <div class="d-grid gap-3">
            <div class="d-flex align-items-center justify-content-between">
              <div
                class="d-inline-flex align-items-center justify-content-center rounded-4 text-primary fw-semibold"
                style="width: 3rem; height: 3rem; background-color: var(--bs-light-bg-subtle);"
                aria-hidden="true"
              >
                <ThemeIcon :name="action.icon" />   
              </div>
              <div>
                <RouterLink class="btn btn-outline-primary btn-sm" :to="action.to">
                  {{ action.buttonLabel }}
                </RouterLink>
              </div>
            </div>
            <div>
              <h2 class="h5 mb-2">{{ action.title }}</h2>
              <p class="text-body-secondary mb-0">{{ action.description }}</p>
            </div>
          </div>
        </BaseCard>
      </div>
    </div>

    <BaseCard>
      <template #header>
        <div class="d-flex flex-wrap justify-content-between align-items-start gap-3">
          <div>
            <p class="placeholder-eyebrow mb-2">Recommended expert</p>
            <h2 class="h3 mb-2">Current best match</h2>
            <p class="text-body-secondary mb-0" style="max-width: 34rem;">
              This recommendation is generated from your current consent state and any available profile signal.
            </p>
          </div>
          <div class="d-flex flex-column flex-wrap align-items-center gap-4">
            <div><span class="badge align-self-start" :class="recommendation.profiling_used ? 'text-bg-warning' : 'text-bg-secondary'">{{ profileIndicatorLabel }}</span></div>
            
            <button
              class="btn btn-outline-primary btn-sm"
              type="button"
              :disabled="isStartingMatchedChat || !recommendedExpert || recommendedExpert.is_contactable === false"
              @click="startMatchedExpertChat"
            >
              {{ isStartingMatchedChat ? 'Starting...' : 'Start matched chat' }}
            </button>
          </div>
        </div>
      </template>

      <BaseAlert v-if="recommendationError" variant="danger" :message="recommendationError" role="alert" />

      <BaseLoadingState
        v-else-if="isLoadingRecommendation"
        state-class="base-dashboard__loading"
        label="Finding the best expert match..."
      />

      <BaseEmptyState
        v-else-if="!recommendedExpert"
        title="No expert recommendation available"
        :description="recommendationMessage || 'No expert records are available for matching yet.'"
        state-class="base-dashboard__empty-state"
      >
        <template #actions>
          <RouterLink class="btn btn-outline-primary btn-sm" to="/user/chat">
            Continue with system chat
          </RouterLink>
        </template>
      </BaseEmptyState>

      <div v-else class="row g-4 align-items-start">
        <div class="col-lg-7">
          <div class="d-grid gap-3">
            <div class="p-3 rounded-1 border-0 bg-light-subtle">
              <strong class="text-body-secondary small d-block mb-1">Expert</strong>
              <h3 class="h4 mb-2">{{ recommendedExpert.name }}</h3>
              <p class="text-body-secondary mb-0">
                {{ recommendedExpert.email || 'No public email available' }}
              </p>
            </div>

            <div class="p-3 rounded-1 border-0 bg-light-subtle">
              <strong class="text-body-secondary small d-block mb-2">Domains</strong>
              <div class="d-flex flex-wrap gap-2">
                <span
                  v-for="domainCode in recommendedExpert.domain_codes"
                  :key="domainCode"
                  class="badge text-bg-light border"
                >
                  {{ formatDomain(domainCode) }}
                </span>
              </div>
            </div>

            <div class="p-3 rounded-1 border-0 bg-light-subtle">
              <strong class="text-body-secondary small d-block mb-1">Reason</strong>
              <p class="mb-0 text-body-secondary">{{ recommendedExpert.reason }}</p>
            </div>

            <div class="p-3 rounded-1 border-0 bg-light-subtle">
              <strong class="text-body-secondary small d-block mb-1">Compatibility</strong>
              <p class="mb-0 text-body-secondary">{{ recommendedExpert.compatibility_note }}</p>
            </div>

            <div class="p-3 rounded-1 border-0 bg-light-subtle">
              <strong class="text-body-secondary small d-block mb-1">Contact availability</strong>
              <p class="mb-0 text-body-secondary">
                {{ recommendedExpert.is_contactable
                  ? 'This expert can be contacted through COOGNIS expert handoff.'
                  : 'This expert is currently available as a UEX knowledge match only. An admin must provision a COOGNIS expert account before direct handoff is possible.' }}
              </p>
            </div>
          </div>
        </div>

        <div class="col-lg-5">
          <div class="d-grid gap-3">
            <div class="p-4 text-center rounded-2 border-0" style="background: linear-gradient(var(--bs-success-bg-subtle), rgba(255, 255, 255, 0));">
              <span class="small fw-semibold d-block mb-1">Match score</span>
              <span class="d-block fw-semibold" style="font-size: 2rem; color: var(--bs-primary);">
                {{ formatMatchScore(recommendedExpert.total_score) }}
              </span>
            </div>

            <BaseAlert
              :variant="recommendation.profiling_used ? 'success' : 'info'"
              :message="profilingStatusMessage"
            />

            <BaseAlert
              :variant="recommendedExpert.is_contactable ? 'success' : 'warning'"
              :message="recommendedExpert.is_contactable
                ? 'This expert is contactable through the live expert handoff flow.'
                : 'This expert is not contactable yet. You can still continue with system chat until an admin provisions the expert account.'"
            />

            <p class="text-body-secondary small mb-0">
              {{ profileCaption }}
            </p>

            <div class="d-grid gap-2">
              <button
                class="btn btn-primary"
                type="button"
                :disabled="isStartingMatchedChat || recommendedExpert.is_contactable === false"
                @click="startMatchedExpertChat"
              >
                {{ isStartingMatchedChat ? 'Starting...' : 'Start chat with this expert' }}
              </button>
              <RouterLink class="btn btn-outline-secondary" to="/user/settings">
                Review privacy settings
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </BaseCard>
  </section>
</template>

<script>
import { RouterLink } from 'vue-router';
import ThemeIcon from '@/components/ThemeIcon.vue'
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BaseEmptyState from '@/components/BaseEmptyState.vue';
import BaseLoadingState from '@/components/BaseLoadingState.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import authStore from '@/store/authStore';
import chatService from '@/services/chatService';
import userService from '@/services/userService';

export default {
  name: 'UserDashboardView',
  components: {
    ThemeIcon,
    BaseAlert,
    BaseCard,
    BaseEmptyState,
    BaseLoadingState,
    BasePageHeader,
    RouterLink,
  },
  data() {
    return {
      isLoadingRecommendation: true,
      isStartingMatchedChat: false,
      recommendationError: '',
      recommendationMessage: '',
      recommendation: {
        item: null,
        profiling_used: false,
        target_mbti: null,
        profile_source: null,
      },
      quickActions: [
        {
          title: 'Start new chat',
          description: 'Begin a new guided conversation with the platform.',
          buttonLabel: 'Start chat',
          to: '/user/chat',
          icon: 'chat',
        },
        {
          title: 'Converstions',
          description: 'Review earlier sessions and reopen a previous MIND conversation.',
          buttonLabel: 'Chats history',
          to: '/user/chats',
          icon: 'sessions',
        },
        {
          title: 'Privacy',
          description: 'Review consent status and manage privacy-related requests.',
          buttonLabel: 'User settings',
          to: '/user/settings',
          icon: 'settings',
        },
      ],
    };
  },
  computed: {
    currentUser() {
      return authStore.state.currentUser || {};
    },
    displayName() {
      return this.currentUser.first_name || 'User';
    },
    fullName() {
      const fullName = `${this.currentUser.first_name || ''} ${this.currentUser.last_name || ''}`.trim();

      return fullName || 'Pending profile details';
    },
    userEmail() {
      return this.currentUser.email || 'No email available';
    },
    userRole() {
      return this.currentUser.role || 'user';
    },
    consentStatus() {
      return {
        ai_profiling_consent:
          typeof this.currentUser.ai_profiling_consent === 'boolean'
            ? this.currentUser.ai_profiling_consent
            : true,
        gdpr_consent:
          typeof this.currentUser.gdpr_consent === 'boolean'
            ? this.currentUser.gdpr_consent
            : true,
      };
    },
    recommendedExpert() {
      return this.recommendation.item;
    },
    overviewStats() {
      const grantedConsents = [this.consentStatus.ai_profiling_consent, this.consentStatus.gdpr_consent].filter(Boolean).length;
      return [
        {
          label: 'Consents granted',
          value: `${grantedConsents}/2`,
          note: 'Current privacy and profiling permissions on your account.',
        },
        {
          label: 'Profile signal',
          value: this.recommendation.target_mbti || 'Fallback',
          note: this.recommendation.profiling_used ? 'Matching is using a profile-informed route.' : 'Matching is currently running without stored profiling.',
        },
        {
          label: 'Expert availability',
          value: this.recommendedExpert ? (this.recommendedExpert.is_contactable ? 'Live handoff' : 'Knowledge-only') : 'Pending',
          note: this.recommendedExpert ? 'Current recommendation contact status.' : 'No recommendation loaded yet.',
        },
        {
          label: 'Match score',
          value: this.recommendedExpert ? this.formatMatchScore(this.recommendedExpert.total_score) : 'N/A',
          note: 'Strength of the current recommended expert match.',
        },
      ];
    },
    profileIndicatorLabel() {
      if (this.recommendation.profile_source === 'manual_override') {
        return 'Manual profile override used';
      }

      if (this.recommendation.profile_source === 'synapse_inferred') {
        return 'SYNAPSE profile used';
      }

      return 'Fallback matching';
    },
    profileCaption() {
      if (this.recommendation.profile_source === 'manual_override') {
        return 'This recommendation uses a manually defined effective MBTI profile.';
      }

      if (this.recommendation.profile_source === 'synapse_inferred') {
        return 'This recommendation includes the latest stored SYNAPSE user profile.';
      }

      return 'This recommendation does not currently use a stored SYNAPSE user profile.';
    },
    profilingStatusMessage() {
      if (this.recommendation.profile_source === 'manual_override' && this.recommendation.target_mbti) {
        return `A manual effective profile is active for matching. The current MBTI type is ${this.recommendation.target_mbti}.`;
      }

      if (this.recommendation.profiling_used && this.recommendation.target_mbti) {
        return `Profiling-informed matching is active. Your latest inferred profile signal is ${this.recommendation.target_mbti}.`;
      }

      if (!this.consentStatus.ai_profiling_consent) {
        return 'Profiling consent is withdrawn, so this recommendation uses non-profiling signals only.';
      }

      return 'No stored user profile was available, so this recommendation currently relies on expert availability and coverage.';
    },
  },
  created() {
    this.loadRecommendedExpert();
  },
  methods: {
    consentLabel(value) {
      return value ? 'Granted' : 'Withdrawn';
    },
    consentBadgeClass(value) {
      return value ? 'text-bg-success' : 'text-bg-secondary';
    },
    formatDomain(value) {
      return String(value || '')
        .split('-')
        .filter(Boolean)
        .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
        .join(' ');
    },
    formatMatchScore(value) {
      if (typeof value !== 'number') {
        return 'N/A';
      }

      return `${Math.round(value * 100)}%`;
    },
    async loadRecommendedExpert() {
      this.isLoadingRecommendation = true;
      this.recommendationError = '';
      this.recommendationMessage = '';

      const response = await userService.fetchRecommendedExpert();

      if (response.success) {
        this.recommendation = {
          item: response.data?.item || null,
          profiling_used: Boolean(response.data?.profiling_used),
          target_mbti: response.data?.target_mbti || null,
          profile_source: response.data?.profile_source || null,
        };
        this.recommendationMessage = response.data?.message || '';
      } else {
        this.recommendation = {
          item: null,
          profiling_used: false,
          target_mbti: null,
          profile_source: null,
        };
        this.recommendationError = response.error?.message || 'Unable to load the recommended expert.';
      }

      this.isLoadingRecommendation = false;
    },
    async startMatchedExpertChat() {
      if (
        this.isStartingMatchedChat
        || !this.recommendedExpert
        || this.recommendedExpert.is_contactable === false
        || !this.recommendedExpert.expert_id
      ) {
        return;
      }

      this.isStartingMatchedChat = true;
      this.recommendationError = '';

      const response = await chatService.startConversation({
        title: `Expert chat: ${this.recommendedExpert.name}`,
        mode: 'system',
        expert_id: this.recommendedExpert.expert_id,
        handoff_reason: this.recommendedExpert.reason || 'Started from dashboard expert recommendation.',
      });

      if (response.success && response.data?.id) {
        await this.$router.push({ path: '/user/chat', query: { session: String(response.data.id) } });
        this.isStartingMatchedChat = false;
        return;
      }

      this.recommendationError = response.error?.message || 'Unable to start the expert chat.';
      this.isStartingMatchedChat = false;
    },
  },
};
</script>
