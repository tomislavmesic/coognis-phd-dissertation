<template>
  <section class="admin-chat-sessions">
    <BasePageHeader
      eyebrow="Admin"
      title="Chat session cleanup"
      description="Review and delete empty chat sessions that match the configured retention rules."
    />

    <BaseAlert
      variant="info"
      message="Only closed empty chats, or still-open empty chats older than the configured age threshold, can be deleted."
    />
    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" role="alert" :message="errorMessage" />

    <BaseCard
      class="admin-chat-sessions__card"
      title="Eligible chat sessions"
      subtitle="This list only shows sessions that the backend currently allows an admin to delete."
      card-body-class="p-0"
    >
      <template #actions>
        <input
          v-model.trim="searchQuery"
          class="form-control"
          type="search"
          placeholder="Search by session, user, or expert"
          aria-label="Search deletable chat sessions"
        />
        <div class="d-flex flex-wrap gap-2 justify-content-md-end">
          <select v-model="statusFilter" class="form-select" aria-label="Filter by session status">
            <option value="all">All statuses</option>
            <option value="closed">Closed</option>
            <option value="active">Active</option>
            <option value="awaiting_expert">Awaiting expert</option>
            <option value="awaiting_user">Awaiting user</option>
          </select>
        </div>
      </template>

      <BaseLoadingState v-if="isLoading" label="Loading eligible chat sessions..." state-class="py-5" />

      <BaseEmptyState
        v-else-if="!filteredSessions.length"
        title="No deletable chat sessions"
        :description="sessions.length ? 'Try adjusting the search or status filter.' : 'The backend has no eligible empty chat sessions right now.'"
        state-class="py-5"
      />

      <BaseTable
        v-else
        :columns="tableColumns"
        :rows="sortedSessions"
        :sort-key="sortState.key"
        :sort-direction="sortState.direction"
        table-class="admin-chat-sessions__table"
        @sort-change="handleSortChange"
      >
        <template #cell-session="{ row }">
          <div class="admin-chat-sessions__session">
            <strong>#{{ row.id }}</strong>
            <span>{{ row.title || 'Untitled session' }}</span>
          </div>
        </template>
        <template #cell-status="{ row }">
          <span class="badge text-capitalize" :class="statusBadgeClass(row.rawStatus)">
            {{ row.status }}
          </span>
        </template>
        <template #cell-mode="{ value }">
          <span class="text-capitalize">{{ value }}</span>
        </template>
        <template #cell-user="{ row }">
          <div class="admin-chat-sessions__entity">
            <span>{{ row.userName || 'Unknown user' }}</span>
            <small class="text-body-secondary">ID: {{ row.userId || 'N/A' }}</small>
          </div>
        </template>
        <template #cell-expert="{ row }">
          <div class="admin-chat-sessions__entity">
            <span>{{ row.expertName || 'Not assigned' }}</span>
            <small class="text-body-secondary">ID: {{ row.assignedExpertId || 'N/A' }}</small>
          </div>
        </template>
        <template #cell-createdAt="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
        <template #cell-eligibleReason="{ value }">
          {{ value }}
        </template>
        <template #actions="{ row }">
          <button
            class="btn btn-sm btn-outline-danger"
            type="button"
            :disabled="isSubmitting"
            @click="openDeleteModal(row)"
          >
            Delete
          </button>
        </template>
      </BaseTable>
    </BaseCard>

    <BaseModal
      :visible="deleteModal.visible"
      :busy="isSubmitting"
      eyebrow="Chat session"
      title="Delete empty chat session"
      modal-id="admin-chat-session-delete-modal"
      @close="closeDeleteModal"
    >
      <p class="mb-3">
        Delete session <strong v-if="deleteModal.session">#{{ deleteModal.session.id }}</strong>
        <span v-if="deleteModal.session">({{ deleteModal.session.title || 'Untitled session' }})</span>?
      </p>
      <p v-if="deleteModal.session" class="text-body-secondary mb-0">
        Eligible because: {{ deleteModal.session.eligibleReason }}.
      </p>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeDeleteModal">
          Cancel
        </button>
        <button class="btn btn-danger" type="button" :disabled="isSubmitting" @click="confirmDelete">
          {{ isSubmitting ? 'Deleting...' : 'Delete session' }}
        </button>
      </template>
    </BaseModal>
  </section>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BaseEmptyState from '@/components/BaseEmptyState.vue';
import BaseLoadingState from '@/components/BaseLoadingState.vue';
import BaseModal from '@/components/BaseModal.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import BaseTable from '@/components/BaseTable.vue';
import adminService from '@/services/adminService';
import { formatDateTime } from '@/utils/dateTime';

export default {
  name: 'AdminChatSessionsView',
  components: {
    BaseAlert,
    BaseCard,
    BaseEmptyState,
    BaseLoadingState,
    BaseModal,
    BasePageHeader,
    BaseTable,
  },
  data() {
    return {
      isLoading: false,
      isSubmitting: false,
      successMessage: '',
      errorMessage: '',
      searchQuery: '',
      statusFilter: 'all',
      sortState: {
        key: 'createdAt',
        direction: 'desc',
      },
      sessions: [],
      deleteModal: {
        visible: false,
        session: null,
      },
    };
  },
  computed: {
    tableColumns() {
      return [
        { key: 'session', label: 'Session', sortable: true },
        { key: 'status', label: 'Status', sortable: true },
        { key: 'mode', label: 'Mode', sortable: true },
        { key: 'user', label: 'User', sortable: true },
        { key: 'expert', label: 'Assigned expert', sortable: true },
        { key: 'createdAt', label: 'Created at', sortable: true },
        { key: 'eligibleReason', label: 'Eligible because', sortable: true },
      ];
    },
    filteredSessions() {
      const query = this.searchQuery.toLowerCase();

      return this.sessions.filter((session) => {
        const matchesStatus = this.statusFilter === 'all' || session.rawStatus === this.statusFilter;
        const matchesQuery =
          !query ||
          String(session.id).includes(query) ||
          (session.title || '').toLowerCase().includes(query) ||
          (session.userName || '').toLowerCase().includes(query) ||
          (session.expertName || '').toLowerCase().includes(query);

        return matchesStatus && matchesQuery;
      });
    },
    sortedSessions() {
      const direction = this.sortState.direction === 'desc' ? -1 : 1;
      return [...this.filteredSessions].sort((left, right) => {
        const leftValue = this.sortableValue(left, this.sortState.key);
        const rightValue = this.sortableValue(right, this.sortState.key);

        if (leftValue === rightValue) {
          return left.id - right.id;
        }

        return leftValue > rightValue ? direction : -direction;
      });
    },
  },
  created() {
    this.loadSessions();
  },
  methods: {
    normalizeSession(item) {
      return {
        id: item.id,
        title: item.title,
        rawStatus: item.status,
        status: this.formatStatusLabel(item.status),
        mode: item.mode,
        userId: item.user_id,
        userName: item.user_name,
        assignedExpertId: item.assigned_expert_id,
        expertName: item.assigned_expert_name,
        createdAt: item.created_at,
        closedAt: item.closed_at,
        eligibleReason: item.eligible_reason,
      };
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    formatStatusLabel(value) {
      return String(value || 'unknown').replace(/_/g, ' ');
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
    async loadSessions() {
      this.isLoading = true;
      this.errorMessage = '';

      const response = await adminService.fetchDeletableChatSessions();

      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : response.data?.items || [];
        this.sessions = items.map((item) => this.normalizeSession(item));
      } else {
        this.errorMessage = response.error?.message || 'Unable to load deletable chat sessions.';
      }

      this.isLoading = false;
    },
    openDeleteModal(session) {
      this.successMessage = '';
      this.errorMessage = '';
      this.deleteModal.visible = true;
      this.deleteModal.session = session;
    },
    closeDeleteModal() {
      if (this.isSubmitting) {
        return;
      }

      this.deleteModal.visible = false;
      this.deleteModal.session = null;
    },
    async confirmDelete() {
      if (!this.deleteModal.session) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.deleteChatSession(this.deleteModal.session.id);

      if (response.success) {
        const deletedSession = this.deleteModal.session;
        this.sessions = this.sessions.filter((item) => item.id !== deletedSession.id);
        this.successMessage = response.data?.message || `Session #${deletedSession.id} deleted successfully.`;
        this.isSubmitting = false;
        this.closeDeleteModal();
      } else {
        this.errorMessage = response.error?.message || 'Unable to delete the selected chat session.';
        this.isSubmitting = false;
      }
    },
    sortableValue(session, key) {
      if (key === 'session') {
        return session.id;
      }

      if (key === 'status') {
        return String(session.rawStatus || '').toLowerCase();
      }

      if (key === 'user') {
        return String(session.userName || '').toLowerCase();
      }

      if (key === 'expert') {
        return String(session.expertName || '').toLowerCase();
      }

      if (key === 'createdAt') {
        const time = new Date(session.createdAt).getTime();
        return Number.isNaN(time) ? 0 : time;
      }

      return String(session[key] || '').toLowerCase();
    },
    handleSortChange(nextSort) {
      this.sortState = nextSort;
    },
  },
};
</script>
