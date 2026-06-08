<template>
  <section class="admin-data-requests">
    <BasePageHeader
      
      eyebrow="Admin"
      title="Data requests"
      description="Review privacy-related requests including account deletion, data removal, and profiling opt-out."
    />

    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" role="alert" :message="errorMessage" />

    <BaseCard 
      class="admin-data-requests__card" 
      title="Request queue" 
      subtitle="Pending and processed data-related requests across the platform."
      card-body-class="p-0"
    >
      <BaseTable :columns="tableColumns" :rows="requests" actions-mode="icon-only" table-class="admin-data-requests__table">
        <template #cell-type="{ row }">
          {{ formatRequestType(row.type) }}
        </template>
        <template #cell-status="{ row }">
          <span class="badge" :class="statusBadgeClass(row.status)">
            {{ row.status }}
          </span>
        </template>
        <template #actions="{ row }">
          <BaseTableActionsMenu
            :open="openActionMenuId === row.id"
            :disabled="isSubmitting"
            label="Open data request actions"
            @toggle="toggleActionMenu(row.id)"
            @close="closeActionMenu"
          >
              <button
                class="base-table__actions-item"
                type="button"
                role="menuitem"
                :disabled="isSubmitting"
                @click="handleRowAction('view', row)"
              >
                View details
              </button>
              <button
                class="base-table__actions-item"
                type="button"
                role="menuitem"
                :disabled="isSubmitting || row.status !== 'pending'"
                @click="handleRowAction('complete', row)"
              >
                Mark completed
              </button>
              <button
                class="base-table__actions-item base-table__actions-item--danger"
                type="button"
                role="menuitem"
                :disabled="isSubmitting || row.status !== 'pending'"
                @click="handleRowAction('reject', row)"
              >
                Reject
              </button>
          </BaseTableActionsMenu>
        </template>
      </BaseTable>
    </BaseCard>
  </section>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import BaseTableActionsMenu from '@/components/BaseTableActionsMenu.vue';
import BaseTable from '@/components/BaseTable.vue';
import adminService from '@/services/adminService';
import { formatDateTime } from '@/utils/dateTime';

export default {
  name: 'AdminDataRequestsView',
  components: {
    BaseAlert,
    BaseCard,
    BasePageHeader,
    BaseTableActionsMenu,
    BaseTable,
  },
  data() {
    return {
      isSubmitting: false,
      successMessage: '',
      errorMessage: '',
      openActionMenuId: null,
      requests: [],
    };
  },
  computed: {
    tableColumns() {
      return [
        { key: 'type', label: 'Request type' },
        { key: 'userName', label: 'User' },
        { key: 'email', label: 'Email' },
        { key: 'status', label: 'Status' },
        { key: 'requestedAt', label: 'Requested at' },
        { key: 'updatedAt', label: 'Updated at' },
      ];
    },
  },
  created() {
    this.loadRequests();
  },
  methods: {
    normalizeRequest(item) {
      return {
        id: item.id,
        type: item.request_type || item.type,
        userName: item.full_name || item.userName,
        email: item.email,
        status: item.status,
        requestedAt: this.formatDate(item.created_at || item.requestedAt),
        updatedAt: this.formatDate(item.updated_at || item.updatedAt),
        reason: item.reason || '',
      };
    },
    async loadRequests() {
      this.errorMessage = '';
      const response = await adminService.fetchDataRequests();

      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : response.data?.items || [];
        this.requests = items.map((item) => this.normalizeRequest(item));
      } else {
        this.errorMessage = response.error?.message || 'Unable to load data requests.';
      }
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    formatRequestType(value) {
      return String(value || '')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (char) => char.toUpperCase());
    },
    statusBadgeClass(status) {
      if (status === 'completed') {
        return 'text-bg-success';
      }

      if (status === 'rejected') {
        return 'text-bg-danger';
      }

      return 'text-bg-warning';
    },
    toggleActionMenu(requestId) {
      this.openActionMenuId = this.openActionMenuId === requestId ? null : requestId;
    },
    closeActionMenu() {
      this.openActionMenuId = null;
    },
    handleRowAction(action, request) {
      this.closeActionMenu();

      if (action === 'view') {
        this.viewDetails(request);
        return;
      }

      if (action === 'complete') {
        this.markCompleted(request);
        return;
      }

      if (action === 'reject') {
        this.rejectRequest(request);
      }
    },
    async runAction(action, request) {
      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await action(request.id);

      if (response.success) {
        return response;
      }

      this.errorMessage = response.error?.message || 'Unable to complete the requested action.';
      this.isSubmitting = false;
      return null;
    },
    async viewDetails(request) {
      const response = await this.runAction(adminService.viewDataRequest, request);

      if (!response) {
        return;
      }

      const details = this.normalizeRequest(response.data);
      this.successMessage = `${this.formatRequestType(details.type)} for ${details.userName}: ${details.reason || 'No extra reason provided.'}`;
      this.isSubmitting = false;
    },
    async markCompleted(request) {
      const response = await this.runAction(adminService.markDataRequestCompleted, request);

      if (!response) {
        return;
      }

      this.requests = this.requests.map((item) =>
        item.id === request.id ? { ...item, status: 'completed', updatedAt: this.formatDate(new Date()) } : item
      );
      this.successMessage = `${this.formatRequestType(request.type)} marked as completed.`;
      this.isSubmitting = false;
    },
    async rejectRequest(request) {
      const response = await this.runAction(adminService.rejectDataRequest, request);

      if (!response) {
        return;
      }

      this.requests = this.requests.map((item) =>
        item.id === request.id ? { ...item, status: 'rejected', updatedAt: this.formatDate(new Date()) } : item
      );
      this.successMessage = `${this.formatRequestType(request.type)} request rejected.`;
      this.isSubmitting = false;
    },
  },
};
</script>
