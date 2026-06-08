<template>
  <section class="chat-sessions-page">
    <BasePageHeader
      :eyebrow="pageEyebrow"
      title="Previous chats"
      :description="pageDescription"
    />

    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" />

    <BaseCard 
      title="Chat sessions" 
      subtitle="Sessions are ordered from newest to oldest."
      card-body-class="p-0"
    >
      <BaseLoadingState v-if="isLoading" label="Loading previous chat sessions..." state-class="py-5" />

      <BaseEmptyState
        v-else-if="!sessions.length"
        title="No previous chats yet"
        description="Start a new conversation and it will appear here."
        state-class="py-5"
      >
        <template #actions>
          <RouterLink class="btn btn-primary" :to="chatRoute">
            Start new chat
          </RouterLink>
        </template>
      </BaseEmptyState>

      <BaseTable
        v-else
        :columns="tableColumns"
        :rows="sortedSessions"
        :sort-key="sortState.key"
        :sort-direction="sortState.direction"
        table-class="chat-sessions-page__table"
        @sort-change="handleSortChange"
      >
        <template #cell-session="{ row }">
          <div class="chat-sessions-page__session-cell">
            <strong>{{ row.sessionLabel }}</strong>
            <p v-if="row.lastMessagePreview" class="chat-sessions-page__session-preview mb-0">
              {{ row.lastMessagePreview }}
            </p>
          </div>
        </template>
        <template #cell-mode="{ value }">
          <span class="badge text-capitalize" :class="value === 'expert' ? 'text-bg-success' : 'text-bg-primary'">
            {{ value }}
          </span>
        </template>
        <template #cell-status="{ row }">
          <div class="d-flex flex-wrap align-items-center gap-2">
            <span class="badge text-capitalize" :class="statusBadgeClass(row.rawStatus)">
              {{ row.status }}
            </span>
            <span v-if="row.needsAttention" class="badge text-bg-danger">
              {{ row.unreadMessageCount }} new
            </span>
          </div>
        </template>
        <template #cell-createdAt="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
        <template #cell-lastActivity="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
        <template #actions="{ row }">
          <RouterLink class="btn btn-sm btn-outline-primary" :to="`${chatRoute}?session=${row.id}`">
            Open chat
          </RouterLink>
        </template>
      </BaseTable>
    </BaseCard>
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
import chatService from '@/services/chatService';
import expertService from '@/services/expertService';
import authStore from '@/store/authStore';
import { formatDateTime } from '@/utils/dateTime';

export default {
  name: 'UserChatSessionsView',
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
      isLoading: false,
      errorMessage: '',
      sessions: [],
      refreshTimerId: null,
      sortState: {
        key: 'lastActivity',
        direction: 'desc',
      },
    };
  },
  computed: {
    currentRole() {
      return authStore.resolveRoleFromPayload(authStore.state.currentUser) || 'user';
    },
    pageEyebrow() {
      return this.currentRole === 'expert' ? 'Expert workspace' : 'User workspace';
    },
    pageDescription() {
      return this.currentRole === 'expert'
        ? 'Review past MIND conversations assigned to your expert account and reopen a session in the shared chat interface.'
        : 'Review your past MIND conversations and reopen a session in the shared chat interface.';
    },
    chatRoute() {
      return this.currentRole === 'expert' ? '/expert/chat' : '/user/chat';
    },
    tableColumns() {
      return [
        { key: 'session', label: 'Session', sortable: true },
        { key: 'mode', label: 'Mode' },
        { key: 'status', label: 'Status', sortable: true },
        { key: 'createdAt', label: 'Created at', sortable: true },
        { key: 'lastActivity', label: 'Last activity', sortable: true },
      ];
    },
    sortedSessions() {
      const items = [...this.sessions];
      const { key, direction } = this.sortState;
      const multiplier = direction === 'asc' ? 1 : -1;

      return items.sort((left, right) => {
        const leftValue = this.sortableValue(left, key);
        const rightValue = this.sortableValue(right, key);

        if (leftValue < rightValue) {
          return -1 * multiplier;
        }
        if (leftValue > rightValue) {
          return 1 * multiplier;
        }
        return 0;
      });
    },
  },
  created() {
    this.loadSessions();
    this.startRefreshPolling();
  },
  beforeUnmount() {
    this.stopRefreshPolling();
  },
  methods: {
    startRefreshPolling() {
      this.stopRefreshPolling();
      this.refreshTimerId = window.setInterval(() => {
        this.loadSessions({ silent: true });
      }, 10000);
    },
    stopRefreshPolling() {
      if (!this.refreshTimerId) {
        return;
      }

      window.clearInterval(this.refreshTimerId);
      this.refreshTimerId = null;
    },
    async loadSessions(options = {}) {
      const { silent = false } = options;

      if (!silent) {
        this.isLoading = true;
      }

      this.errorMessage = '';

      const response = this.currentRole === 'expert'
        ? await expertService.fetchAssignedSessions()
        : await chatService.fetchConversations(authStore.state.currentUser?.id || null);

      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : response.data?.items || [];
        this.sessions = items.map((item) => ({
          id: item.id,
          session: item.id,
          sessionLabel: item.title || `Session #${item.id}`,
          mode: item.mode,
          rawStatus: item.status,
          status: this.formatStatusLabel(item.status),
          unreadMessageCount: Number(item.unread_message_count || 0),
          needsAttention: Boolean(item.needs_attention),
          lastMessagePreview: this.buildPreview(item.last_message_preview),
          createdAt: item.created_at || item.createdAt || item.updated_at,
          lastActivity: item.last_activity_at || item.last_message_at || item.updated_at || item.created_at,
        }));
      } else {
        this.errorMessage = response.error?.message || 'Unable to load previous chat sessions.';
      }

      if (!silent) {
        this.isLoading = false;
      }
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    sortableValue(row, key) {
      if (key === 'session') {
        return Number(row.session || row.id || 0);
      }

      if (key === 'status') {
        return String(row.rawStatus || row.status || '').toLowerCase();
      }

      if (key === 'createdAt' || key === 'lastActivity') {
        return row[key] ? new Date(row[key]).getTime() : 0;
      }

      return String(row[key] || '').toLowerCase();
    },
    handleSortChange(nextSort) {
      this.sortState = nextSort;
    },
    formatStatusLabel(value) {
      return String(value || 'unknown').replace(/_/g, ' ');
    },
    buildPreview(value) {
      const normalized = String(value || '').trim();
      if (!normalized) {
        return '';
      }

      return normalized.length > 140
        ? `${normalized.slice(0, 137).trimEnd()}...`
        : normalized;
    },
    statusBadgeClass(status) {
      if (status === 'closed') {
        return 'text-bg-secondary';
      }

      if (status === 'awaiting_expert') {
        return 'text-bg-warning';
      }

      if (status === 'awaiting_user') {
        return 'text-bg-info';
      }

      return 'text-bg-success';
    },
  },
};
</script>

<style scoped>
.chat-sessions-page__session-cell {
  display: grid;
  gap: 0.3rem;
}

.chat-sessions-page__session-preview {
  color: var(--bs-secondary-color);
  font-size: 0.9rem;
  line-height: 1.45;
}
</style>
