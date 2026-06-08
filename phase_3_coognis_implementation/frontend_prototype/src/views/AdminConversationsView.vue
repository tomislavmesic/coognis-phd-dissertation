<template>
  <section class="admin-conversations">
    <BasePageHeader
      eyebrow="Admin"
      title="Conversation operations"
      description="Read-only visibility into live conversations, handoffs, and current workflow ownership."
    />

    <BaseAlert
      variant="info"
      message="This page is read-only. Admins can review workflow state, handoff history, and conversation metadata without sending messages."
    />
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" />

    <BaseCard
      class="admin-conversations__card"
      title="Conversation overview"
      subtitle="Track active sessions, current responsibility, unread reply pressure, and the latest visible activity."
      card-body-class="p-0"
    >
      <template #actions>
        <input
          v-model.trim="searchQuery"
          class="form-control"
          type="search"
          placeholder="Search by session, user, expert, or preview"
          aria-label="Search conversations"
        />
        <div class="d-flex flex-wrap flex-md-nowrap gap-2 justify-content-md-end ms-md-auto">
          <select v-model="statusFilter" class="form-select" aria-label="Filter by conversation status">
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="awaiting_expert">Awaiting expert</option>
            <option value="awaiting_user">Awaiting user</option>
            <option value="closed">Closed</option>
          </select>
          <select v-model="waitingOnFilter" class="form-select" aria-label="Filter by responsibility">
            <option value="all">All owners</option>
            <option value="System">System</option>
            <option value="Expert">Expert</option>
            <option value="User">User</option>
            <option value="Closed">Closed</option>
          </select>
        </div>
      </template>

      <BaseLoadingState v-if="isLoading" label="Loading operational conversations..." state-class="py-5" />

      <BaseEmptyState
        v-else-if="!filteredConversations.length"
        title="No conversations found"
        :description="conversations.length ? 'Try adjusting the filters.' : 'No conversation records are available yet.'"
        state-class="py-5"
      />

      <BaseTable
        v-else
        :columns="conversationColumns"
        :rows="sortedConversations"
        :sort-key="sortState.key"
        :sort-direction="sortState.direction"
        table-class="admin-conversations__table"
        @sort-change="handleSortChange"
      >
        <template #cell-session="{ row }">
          <div class="admin-conversations__session">
            <strong>#{{ row.id }}</strong>
            <span>{{ row.title || 'Untitled conversation' }}</span>
          </div>
        </template>
        <template #cell-status="{ row }">
          <div class="d-flex flex-wrap align-items-center gap-2">
            <span class="badge text-capitalize" :class="statusBadgeClass(row.rawStatus)">
              {{ row.status }}
            </span>
            <span v-if="row.needsAttention" class="badge text-bg-danger">
              {{ row.unreadMessageCount }} new
            </span>
            <span v-if="row.typingActorRole" class="badge text-bg-light">
              {{ typingLabel(row.typingActorRole) }}
            </span>
          </div>
        </template>
        <template #cell-participants="{ row }">
          <div class="admin-conversations__participants">
            <span><strong>User:</strong> {{ row.userName || 'Unknown' }}</span>
            <span><strong>Expert:</strong> {{ row.expertName || 'Not assigned' }}</span>
          </div>
        </template>
        <template #cell-waitingOn="{ value }">
          <span class="badge" :class="waitingOnBadgeClass(value)">
            {{ value }}
          </span>
        </template>
        <template #cell-lastActivity="{ row }">
          <div class="admin-conversations__activity">
            <span class="text-nowrap">{{ formatDate(row.lastActivityAt || row.createdAt) }}</span>
            <small class="text-body-secondary">
              {{ row.lastMessageRole ? `${formatRoleLabel(row.lastMessageRole)} · ${row.lastMessagePreview || 'No preview'}` : 'No messages yet' }}
            </small>
          </div>
        </template>
        <template #actions="{ row }">
          <button class="btn btn-sm btn-outline-primary" type="button" :disabled="isLoadingDetail" @click="openDetailModal(row)">
            View
          </button>
        </template>
      </BaseTable>
    </BaseCard>

    <BaseCard
      class="admin-conversations__card"
      title="Recent handoffs"
      subtitle="Latest expert handoff events across all conversations."
      card-body-class="p-0"
    >
      <BaseLoadingState v-if="isLoadingHandoffs" label="Loading handoff history..." state-class="py-4" />

      <BaseEmptyState
        v-else-if="!handoffs.length"
        title="No handoffs yet"
        description="Expert handoff events will appear here after users transition from system mode to expert mode."
        state-class="py-4"
      />

      <BaseTable v-else :columns="handoffColumns" :rows="handoffs" table-class="admin-conversations__table">
        <template #cell-session="{ row }">
          <div class="admin-conversations__session">
            <strong>#{{ row.sessionId }}</strong>
            <span>{{ row.sessionTitle || 'Untitled conversation' }}</span>
          </div>
        </template>
        <template #cell-expert="{ value }">
          {{ value || 'Unknown expert' }}
        </template>
        <template #cell-transition="{ row }">
          <span class="text-capitalize">{{ row.fromMode }}</span>
          <span class="text-body-secondary"> -> </span>
          <span class="text-capitalize">{{ row.toMode }}</span>
        </template>
        <template #cell-createdAt="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
      </BaseTable>
    </BaseCard>

    <BaseModal
      :visible="detailModal.visible"
      :busy="isLoadingDetail"
      eyebrow="Conversation"
      title="Conversation detail"
      modal-id="admin-conversation-detail-modal"
      dialog-class="modal-dialog-centered modal-xl"
      @close="closeDetailModal"
    >
      <BaseLoadingState v-if="isLoadingDetail" label="Loading conversation detail..." state-class="py-5" />

      <template v-else-if="detailModal.conversation">
        <div class="admin-conversations__detail-grid">
          <div class="admin-conversations__detail-item">
            <span class="admin-conversations__detail-label">Session</span>
            <strong>#{{ detailModal.conversation.id }}</strong>
          </div>
          <div class="admin-conversations__detail-item">
            <span class="admin-conversations__detail-label">Mode</span>
            <strong class="text-capitalize">{{ detailModal.conversation.mode }}</strong>
          </div>
          <div class="admin-conversations__detail-item">
            <span class="admin-conversations__detail-label">Status</span>
            <strong>{{ formatStatusLabel(detailModal.conversation.status) }}</strong>
          </div>
          <div class="admin-conversations__detail-item">
            <span class="admin-conversations__detail-label">Waiting on</span>
            <strong>{{ detailModal.conversation.waiting_on }}</strong>
          </div>
          <div class="admin-conversations__detail-item">
            <span class="admin-conversations__detail-label">User</span>
            <strong>{{ detailModal.conversation.user_name || 'Unknown user' }}</strong>
          </div>
          <div class="admin-conversations__detail-item">
            <span class="admin-conversations__detail-label">Expert</span>
            <strong>{{ detailModal.conversation.assigned_expert_name || 'Not assigned' }}</strong>
          </div>
        </div>

        <div class="admin-conversations__detail-section">
          <h3 class="h6 mb-3">Message timeline</h3>
          <div v-if="detailModal.messages.length" class="admin-conversations__message-list">
            <article
              v-for="message in detailModal.messages"
              :key="message.id"
              class="admin-conversations__message"
            >
              <div class="admin-conversations__message-meta">
                <strong>{{ formatRoleLabel(message.role) }}</strong>
                <span class="text-nowrap">{{ formatDate(message.createdAt) }}</span>
              </div>
              <p class="mb-0">{{ message.content }}</p>
            </article>
          </div>
          <BaseEmptyState
            v-else
            title="No messages"
            description="This conversation has no persisted messages yet."
            state-class="py-4"
          />
        </div>

        <div class="admin-conversations__detail-section">
          <h3 class="h6 mb-3">Handoff timeline</h3>
          <div v-if="detailModal.handoffs.length" class="admin-conversations__handoff-list">
            <article
              v-for="handoff in detailModal.handoffs"
              :key="handoff.id"
              class="admin-conversations__handoff"
            >
              <div class="admin-conversations__message-meta">
                <strong class="text-nowrap">{{ handoff.expertName || 'Unknown expert' }}</strong>
                <span class="text-nowrap">{{ formatDate(handoff.createdAt) }}</span>
              </div>
              <p class="mb-1 text-capitalize">{{ handoff.fromMode }} -> {{ handoff.toMode }}</p>
              <p class="mb-0 text-body-secondary">{{ handoff.reason || 'No handoff reason recorded.' }}</p>
            </article>
          </div>
          <BaseEmptyState
            v-else
            title="No handoffs"
            description="This conversation was not handed off to an expert."
            state-class="py-4"
          />
        </div>
      </template>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isLoadingDetail" @click="closeDetailModal">
          Close
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
  name: 'AdminConversationsView',
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
      isLoadingDetail: false,
      isLoadingHandoffs: false,
      errorMessage: '',
      searchQuery: '',
      statusFilter: 'all',
      waitingOnFilter: 'all',
      sortState: {
        key: 'lastActivity',
        direction: 'desc',
      },
      conversations: [],
      handoffs: [],
      detailModal: {
        visible: false,
        conversation: null,
        messages: [],
        handoffs: [],
      },
    };
  },
  computed: {
    conversationColumns() {
      return [
        { key: 'session', label: 'Conversation', sortable: true },
        { key: 'status', label: 'Status', sortable: true },
        { key: 'participants', label: 'Participants' },
        { key: 'waitingOn', label: 'Waiting on', sortable: true },
        { key: 'lastActivity', label: 'Last activity', sortable: true },
      ];
    },
    handoffColumns() {
      return [
        { key: 'session', label: 'Conversation' },
        { key: 'expert', label: 'Expert' },
        { key: 'transition', label: 'Transition' },
        { key: 'createdAt', label: 'Created at' },
      ];
    },
    filteredConversations() {
      const query = this.searchQuery.toLowerCase();

      return this.conversations.filter((conversation) => {
        const matchesStatus = this.statusFilter === 'all' || conversation.rawStatus === this.statusFilter;
        const matchesWaitingOn = this.waitingOnFilter === 'all' || conversation.waitingOn === this.waitingOnFilter;
        const matchesQuery =
          !query ||
          String(conversation.id).includes(query) ||
          (conversation.title || '').toLowerCase().includes(query) ||
          (conversation.userName || '').toLowerCase().includes(query) ||
          (conversation.expertName || '').toLowerCase().includes(query) ||
          (conversation.lastMessagePreview || '').toLowerCase().includes(query);

        return matchesStatus && matchesWaitingOn && matchesQuery;
      });
    },
    sortedConversations() {
      const direction = this.sortState.direction === 'desc' ? -1 : 1;
      return [...this.filteredConversations].sort((left, right) => {
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
    this.loadData();
  },
  methods: {
    async loadData() {
      await Promise.all([
        this.loadConversations(),
        this.loadHandoffs(),
      ]);
    },
    async loadConversations() {
      this.isLoading = true;
      this.errorMessage = '';

      const response = await adminService.fetchConversationOverview();

      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : response.data?.items || [];
        this.conversations = items.map((item) => this.normalizeConversation(item));
      } else {
        this.errorMessage = response.error?.message || 'Unable to load conversations.';
      }

      this.isLoading = false;
    },
    async loadHandoffs() {
      this.isLoadingHandoffs = true;

      const response = await adminService.fetchHandoffs();

      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : response.data?.items || [];
        this.handoffs = items.map((item) => ({
          id: item.id,
          sessionId: item.session_id,
          sessionTitle: item.session_title,
          expertName: item.expert_name,
          fromMode: item.from_mode,
          toMode: item.to_mode,
          createdAt: item.created_at,
        }));
      } else if (!this.errorMessage) {
        this.errorMessage = response.error?.message || 'Unable to load handoff overview.';
      }

      this.isLoadingHandoffs = false;
    },
    normalizeConversation(item) {
      return {
        id: item.id,
        title: item.title,
        rawStatus: item.status,
        status: this.formatStatusLabel(item.status),
        userName: item.user_name,
        expertName: item.assigned_expert_name,
        waitingOn: item.waiting_on,
        typingActorRole: item.typing_actor_role,
        lastMessageAt: item.last_message_at,
        lastActivityAt: item.last_activity_at || item.last_message_at || item.created_at,
        lastMessageRole: item.last_message_role,
        lastMessagePreview: item.last_message_preview,
        unreadMessageCount: Number(item.unread_message_count || 0),
        needsAttention: Boolean(item.needs_attention),
        createdAt: item.created_at,
      };
    },
    async openDetailModal(conversation) {
      this.detailModal.visible = true;
      this.detailModal.conversation = conversation;
      this.detailModal.messages = [];
      this.detailModal.handoffs = [];
      this.isLoadingDetail = true;

      const response = await adminService.fetchConversationDetail(conversation.id);

      if (response.success) {
        const data = response.data || {};
        this.detailModal.conversation = {
          ...conversation,
          ...(data.conversation || {}),
        };
        this.detailModal.messages = (data.messages || []).map((item) => ({
          id: item.id,
          role: item.role,
          mode: item.mode,
          content: item.content,
          createdAt: item.created_at,
        }));
        this.detailModal.handoffs = (data.handoffs || []).map((item) => ({
          id: item.id,
          expertName: item.expert_name,
          fromMode: item.from_mode,
          toMode: item.to_mode,
          reason: item.reason,
          createdAt: item.created_at,
        }));
      } else {
        this.errorMessage = response.error?.message || 'Unable to load conversation detail.';
      }

      this.isLoadingDetail = false;
    },
    closeDetailModal() {
      if (this.isLoadingDetail) {
        return;
      }

      this.detailModal.visible = false;
      this.detailModal.conversation = null;
      this.detailModal.messages = [];
      this.detailModal.handoffs = [];
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    formatStatusLabel(value) {
      return String(value || 'unknown').replace(/_/g, ' ');
    },
    formatRoleLabel(role) {
      if (role === 'assistant') {
        return 'System';
      }

      return String(role || 'unknown').replace(/_/g, ' ');
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
    waitingOnBadgeClass(value) {
      if (value === 'Expert') {
        return 'text-bg-warning';
      }

      if (value === 'User') {
        return 'text-bg-info';
      }

      if (value === 'System') {
        return 'text-bg-primary';
      }

      return 'text-bg-secondary';
    },
    typingLabel(role) {
      return role === 'expert' ? 'Expert typing' : role === 'user' ? 'User typing' : 'Typing';
    },
    sortableValue(conversation, key) {
      if (key === 'session') {
        return conversation.id;
      }

      if (key === 'status') {
        return String(conversation.rawStatus || '').toLowerCase();
      }

      if (key === 'lastActivity') {
        const time = new Date(conversation.lastActivityAt || conversation.createdAt).getTime();
        return Number.isNaN(time) ? 0 : time;
      }

      return String(conversation[key] || '').toLowerCase();
    },
    handleSortChange(nextSort) {
      this.sortState = nextSort;
    },
  },
};
</script>
