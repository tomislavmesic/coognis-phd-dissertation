<template>
  <section class="base-dashboard">
    <div class="row g-4">
      <div class="col-md-6 col-xl-9">
        <BasePageHeader
          class="base-dashboard__hero h-100"
          eyebrow="Expert workspace"
          title="Work overview"
          description="Review assigned conversations, monitor knowledge contributions, and track communication quality from one operational workspace."
        >
          <template #actions>
            <div class="base-dashboard__hero-actions">
              <RouterLink class="btn" :to="expertWorkspaceLink">Open chat</RouterLink>
              <RouterLink class="btn btn-outline" to="/expert/settings">Settings</RouterLink>
            </div>
          </template>
        </BasePageHeader>
      </div>
      <div class="col-md-6 col-xl-3">
        <BaseCard 
          class="base-card base-stat-card"
          card-body-class="p-0"
        >
          <ul class="list-unstyled mb-0 d-flex flex-column gap-3">
            <li>
              <strong>Domains</strong>
              <div class="d-flex flex-wrap gap-2 mt-1">
                <span
                  v-for="specialization in specializationBadges"
                  :key="specialization"
                  class="badge text-bg-light border"
                >
                  {{ specialization }}
                </span>
              </div>
            </li>
            <li>
              <strong>Availability</strong>
              <div><span class="badge" :class="availabilityBadgeClass">{{ profileSummary.availability }}</span></div>
            </li>
            <li>
              <strong>Registration status</strong>
              <div><span class="badge" :class="registrationStatusBadgeClass">{{ profileSummary.registration_status }}</span></div>
            </li>
          </ul>
        </BaseCard>
      </div>
    </div>
    
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" role="alert" />

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
      <div class="col-lg-12">
        <BaseCard
          title="Knowledge contributions"
          subtitle="Current backend counts for published expert knowledge assets tied to your expert record."
          card-header-class="pb-0"
          card-body-class="pt-0"
        >
          <div class="row">
            <div class="col-sm-4 g-4" v-for="item in knowledgeContributions" :key="item.label">
              <div class="base-card base-stat-card">
                <strong class="base-stat-value">{{ item.value }}</strong>
                <p class="base-stat-note mb-0">{{ item.label }}</p>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>
    </div>

    <BaseLoadingState
      v-if="isLoading"
      state-class="base-dashboard__loading"
      label="Loading expert dashboard..."
    />

    <template v-else>
      <div class="row g-4">
        <div class="col-lg-12">
          <BaseCard
            class=""
            title="Assigned conversations"
            subtitle="Active and recently updated conversations currently assigned to this expert."
            header-content-class="d-flex flex-wrap justify-content-between align-items-start gap-3"
            card-body-class="p-0"
          >
            <template #actions>
              <span class="badge text-bg-light">
                {{ assignedConversations.length }} assigned
              </span>
            </template>

            <BaseEmptyState
              v-if="!assignedConversations.length"
              title="No assigned conversations yet"
              description="Expert handoffs will appear here once a user conversation is assigned to your account."
              state-class="base-dashboard__empty-state"
            >
              <template #actions>
                <RouterLink class="btn btn-outline-primary btn-sm" to="/expert/chats">
                  View all chat sessions
                </RouterLink>
              </template>
            </BaseEmptyState>

            <BaseTable
              v-else
              :columns="assignedConversationColumns"
              :rows="assignedConversations"
            >
              <template #cell-status="{ row }">
                <div class="d-flex flex-wrap align-items-center gap-2">
                  <span class="badge" :class="row.badgeClass">
                    {{ row.status }}
                  </span>
                  <span v-if="row.needsAttention" class="badge text-bg-danger">
                    {{ row.unreadMessageCount }} new
                  </span>
                </div>
              </template>
              <template #actions="{ row }">
                <RouterLink class="btn btn-sm btn-outline-primary" :to="`/expert/chat?session=${row.id}`">
                  Open chat
                </RouterLink>
              </template>
            </BaseTable>
          </BaseCard>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-lg-12">
          <BaseCard
            title="Communication feedback summary"
            subtitle="Averages from feedback submitted on sessions assigned to this expert."
            header-content-class="d-flex flex-wrap justify-content-between align-items-start gap-3"
            card-body-class="p-0"
          >
            <template #actions>
              <span class="badge" :class="feedbackHealthBadgeClass">
                {{ feedbackHealthLabel }}
              </span>
            </template>
            <BaseTable :columns="feedbackColumns" :rows="feedbackRows"/>
          </BaseCard>
        </div>
      </div>
    </template>
  </section>
</template>

<script>
import { RouterLink } from 'vue-router';
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BaseEmptyState from '@/components/BaseEmptyState.vue';
import BaseLoadingState from '@/components/BaseLoadingState.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import BaseTable from '@/components/BaseTable.vue';
import authStore from '@/store/authStore';
import expertService from '@/services/expertService';
import { formatDateTime } from '@/utils/dateTime';

export default {
  name: 'ExpertDashboardView',
  components: {
    BaseAlert,
    BaseCard,
    BaseEmptyState,
    BaseLoadingState,
    BasePageHeader,
    BaseTable,
    RouterLink,
  },
  data() {
    return {
      isLoading: true,
      errorMessage: '',
      refreshTimerId: null,
      assignedConversations: [],
    profileSummary: {
        name: '',
        email: '',
        specialization: '',
        availability: '',
        registration_status: 'approved',
        two_factor_enabled: false,
      },
      knowledgeSummary: {
        published_guidance_notes: 0,
        reusable_annotations: 0,
        review_templates: 0,
      },
      feedbackSummary: {
        clarity_score: null,
        usefulness_score: null,
        satisfaction_score: null,
        communication_quality_score: null,
        total_feedback_entries: 0,
      },
    };
  },
  computed: {
    specializationBadges() {
      const raw = String(this.profileSummary?.specialization || '').trim();
      if (!raw) {
        return ['Not specified'];
      }

      return raw
        .split(/[;,]/)
        .map((item) => item.trim())
        .filter(Boolean);
    },
    assignedConversationColumns() {
      return [
        { key: 'title', label: 'Conversation' },
        { key: 'user', label: 'User' },
        { key: 'status', label: 'Status' },
        { key: 'updatedAt', label: 'Updated' },
      ];
    },
    currentUser() {
      return authStore.state.currentUser || null;
    },
    fallbackExpertName() {
      const currentUser = this.currentUser;
      if (!currentUser) {
        return 'Expert account';
      }

      const fullName = [currentUser.first_name, currentUser.last_name].filter(Boolean).join(' ').trim();
      return fullName || currentUser.name || currentUser.email || 'Expert account';
    },
    fallbackExpertEmail() {
      return this.currentUser?.email || 'No email available';
    },
    expertWorkspaceLink() {
      const firstAssignedConversation = this.assignedConversations[0];
      if (firstAssignedConversation?.id) {
        return `/expert/chat?session=${firstAssignedConversation.id}`;
      }

      return '/expert/chats';
    },
    knowledgeContributions() {
      return [
        {
          label: 'Published guidance notes',
          value: this.knowledgeSummary.published_guidance_notes,
        },
        {
          label: 'Reusable annotations',
          value: this.knowledgeSummary.reusable_annotations,
        },
        {
          label: 'Expert review templates',
          value: this.knowledgeSummary.review_templates,
        },
      ];
    },
    feedbackColumns() {
      return [
        { key: 'metric', label: 'Metric' },
        {
          key: 'current',
          label: 'Current',
          headerClass: 'text-end',
          cellClass: 'text-end',
        },
        {
          key: 'trend',
          label: 'Coverage',
          headerClass: 'text-end',
          cellClass: 'text-end',
        },
      ];
    },
    feedbackRows() {
      return [
        {
          metric: 'Clarity score',
          current: this.formatScore(this.feedbackSummary.clarity_score),
          trend: this.feedbackCoverageLabel,
        },
        {
          metric: 'Usefulness score',
          current: this.formatScore(this.feedbackSummary.usefulness_score),
          trend: this.feedbackCoverageLabel,
        },
        {
          metric: 'Satisfaction score',
          current: this.formatScore(this.feedbackSummary.satisfaction_score),
          trend: this.feedbackCoverageLabel,
        },
        {
          metric: 'Communication quality',
          current: this.formatScore(this.feedbackSummary.communication_quality_score),
          trend: this.feedbackCoverageLabel,
        },
      ];
    },
    feedbackCoverageLabel() {
      if (!this.feedbackSummary.total_feedback_entries) {
        return 'No feedback yet';
      }

      const count = this.feedbackSummary.total_feedback_entries;
      return `${count} entr${count === 1 ? 'y' : 'ies'}`;
    },
    feedbackHealthLabel() {
      const score = this.feedbackSummary.communication_quality_score;

      if (score === null || score === undefined) {
        return 'No data';
      }

      if (score >= 4) {
        return 'Healthy';
      }

      if (score >= 3) {
        return 'Stable';
      }

      return 'Needs review';
    },
    feedbackHealthBadgeClass() {
      const score = this.feedbackSummary.communication_quality_score;

      if (score === null || score === undefined) {
        return 'text-bg-secondary';
      }

      if (score >= 4) {
        return 'text-bg-success';
      }

      if (score >= 3) {
        return 'text-bg-warning';
      }

      return 'text-bg-danger';
    },
    availabilityBadgeClass() {
      const availability = this.profileSummary.availability?.toLowerCase() || '';

      if (availability === 'available') {
        return 'text-bg-success';
      }

      if (availability === 'busy') {
        return 'text-bg-danger';
      }

      if (availability === 'away') {
        return 'text-bg-warning';
      }

      return 'text-bg-secondary';
    },
    registrationStatusBadgeClass() {
      const status = this.profileSummary.registration_status?.toLowerCase() || '';

      if (status === 'approved') {
        return 'text-bg-success';
      }

      if (status === 'pending') {
        return 'text-bg-warning';
      }

      if (status === 'rejected') {
        return 'text-bg-danger';
      }

      return 'text-bg-secondary';
    },  
    overviewStats() {
      const attentionCount = this.assignedConversations.filter((item) => item.needsAttention).length;
      const knowledgeTotal = this.knowledgeContributions.reduce((sum, item) => sum + Number(item.value || 0), 0);
      return [
        {
          label: 'Assigned conversations',
          value: String(this.assignedConversations.length),
          note: 'Current sessions assigned to this expert account.',
        },
        {
          label: 'Needs attention',
          value: String(attentionCount),
          note: 'Assigned sessions with unread or outstanding follow-up.',
        },
        {
          label: 'Knowledge assets',
          value: String(knowledgeTotal),
          note: 'Current published guidance, annotations, and review templates.',
        },
        {
          label: 'Communication health',
          value: this.feedbackHealthLabel,
          note: this.feedbackCoverageLabel,
        },
      ];
    },
  },
  created() {
    this.loadDashboard();
    this.startRefreshPolling();
  },
  beforeUnmount() {
    this.stopRefreshPolling();
  },
  methods: {
    startRefreshPolling() {
      this.stopRefreshPolling();
      this.refreshTimerId = window.setInterval(() => {
        this.loadDashboard({ silent: true });
      }, 10000);
    },
    stopRefreshPolling() {
      if (!this.refreshTimerId) {
        return;
      }

      window.clearInterval(this.refreshTimerId);
      this.refreshTimerId = null;
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    formatScore(value) {
      if (value === null || value === undefined) {
        return 'No feedback';
      }

      return `${value.toFixed(1)} / 5`;
    },
    formatStatusLabel(value) {
      return String(value || 'unknown').replace(/_/g, ' ');
    },
    buildConversationStatusClass(status) {
      if (status === 'active') {
        return 'text-bg-primary';
      }

      if (status === 'awaiting_expert') {
        return 'text-bg-warning';
      }

      if (status === 'awaiting_user') {
        return 'text-bg-info';
      }

      if (status === 'closed') {
        return 'text-bg-secondary';
      }

      return 'text-bg-secondary';
    },
    async loadDashboard(options = {}) {
      const { silent = false } = options;

      if (!silent) {
        this.isLoading = true;
      }

      this.errorMessage = '';

      const response = await expertService.fetchDashboardSummary();

      if (!response.success) {
        this.errorMessage = response.error?.message || 'Unable to load expert dashboard data.';
        if (!silent) {
          this.isLoading = false;
        }
        return;
      }

      const data = response.data || {};

      this.assignedConversations = (data.assigned_conversations || []).map((item) => ({
        id: item.id,
        title: item.title || `Conversation #${item.id}`,
        user: item.user_name || 'Unknown user',
        status: this.formatStatusLabel(item.status),
        badgeClass: this.buildConversationStatusClass(item.status),
        unreadMessageCount: Number(item.unread_message_count || 0),
        needsAttention: Boolean(item.needs_attention),
        updatedAt: this.formatDate(item.updated_at),
      }));

      this.profileSummary = {
        name: this.fallbackExpertName,
        email: this.fallbackExpertEmail,
        specialization: 'Not linked to a UEX expert profile',
        availability: 'Unknown',
        registration_status: this.currentUser?.registration_status || this.profileSummary.registration_status,
        two_factor_enabled: Boolean(this.currentUser?.two_factor_enabled ?? this.profileSummary.two_factor_enabled),
        ...(data.profile_summary || {}),
      };
      this.knowledgeSummary = {
        ...this.knowledgeSummary,
        ...(data.knowledge_contributions || {}),
      };
      this.feedbackSummary = {
        ...this.feedbackSummary,
        ...(data.feedback_summary || {}),
      };

      if (!silent) {
        this.isLoading = false;
      }
    },
  },
};
</script>
