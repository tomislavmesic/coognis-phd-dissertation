<template>
  <section class="admin-registration-approval">
    <BasePageHeader
      
      eyebrow="Admin"
      title="Registration approvals"
      description="Review pending registrations and confirm approval before credentials are sent by the backend."
    />

    <BaseAlert v-if="isLoading" variant="info" message="Loading pending registrations..." />

    <BaseCard
      title="Pending users"
      subtitle="Pending registrations requiring manual approval or rejection."
      card-body-class="p-0"
    >
      <template #actions>
        <input
          v-model.trim="searchQuery"
          class="form-control"
          type="search"
          placeholder="Search pending users"
          aria-label="Search pending users"
        />
        <div class="d-flex flex-wrap gap-2 justify-content-md-end">
          <select v-model="roleFilter" class="form-select" aria-label="Filter requested role">
            <option value="all">All roles</option>
            <option value="user">User</option>
            <option value="expert">Expert</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </template>

      <BaseTable
        :columns="tableColumns"
        :rows="sortedPendingUsers"
        :sort-key="sortState.key"
        :sort-direction="sortState.direction"
        actions-mode="icon-only"
        table-class="admin-registration-approval__table"
        @sort-change="handleSortChange"
      >
        <template #cell-requestedRole="{ value }">
          <span class="text-capitalize">{{ value }}</span>
        </template>
        <template #cell-aiProfilingConsent="{ value }">
          {{ value ? 'Granted' : 'Declined' }}
        </template>
        <template #cell-gdprConsent="{ value }">
          {{ value ? 'Granted' : 'Declined' }}
        </template>
        <template #cell-createdAt="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
        <template #actions="{ row }">
          <BaseTableActionsMenu
            :open="openActionMenuId === row.id"
            :disabled="isSubmitting"
            label="Open registration actions"
            @toggle="toggleActionMenu(row.id)"
            @close="closeActionMenu"
          >
              <button
                class="base-table__actions-item"
                type="button"
                role="menuitem"
                :disabled="isSubmitting"
                @click="handleRowAction('approve', row)"
              >
                Approve
              </button>
              <button
                class="base-table__actions-item base-table__actions-item--danger"
                type="button"
                role="menuitem"
                :disabled="isSubmitting"
                @click="handleRowAction('reject', row)"
              >
                Reject
              </button>
          </BaseTableActionsMenu>
        </template>
        <template #empty>
          <div class="text-center text-body-secondary py-4">
            No pending registrations match the current filters.
          </div>
        </template>
      </BaseTable>
    </BaseCard>

    <BaseModal
      :visible="approvalModal.visible"
      :busy="isSubmitting"
      eyebrow="Approval"
      title="Confirm approval"
      modal-id="approval-modal"
      @close="closeApprovalModal"
    >
      <p class="mb-3">
        Approve <strong>{{ approvalModal.registration?.fullName }}</strong> as
        <strong class="text-capitalize">{{ approvalModal.registration?.requestedRole }}</strong>?
      </p>
      <BaseAlert
        variant="info"
        message="Backend approval marks the registration approved and reserves credential email sending for the next backend step."
      />
      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeApprovalModal">
          Cancel
        </button>
        <button class="btn btn-primary" type="button" :disabled="isSubmitting" @click="confirmApproval">
          {{ isSubmitting ? 'Approving...' : 'Confirm approval' }}
        </button>
      </template>
    </BaseModal>
  </section>
</template>

<script>
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BaseModal from '@/components/BaseModal.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import BaseTableActionsMenu from '@/components/BaseTableActionsMenu.vue';
import BaseTable from '@/components/BaseTable.vue';
import toastFeedbackMixin from '@/mixins/toastFeedbackMixin';
import adminService from '@/services/adminService';
import { formatDateTime } from '@/utils/dateTime';

export default {
  name: 'AdminRegistrationApprovalView',
  mixins: [toastFeedbackMixin],
  components: {
    BaseAlert,
    BaseCard,
    BaseModal,
    BasePageHeader,
    BaseTableActionsMenu,
    BaseTable,
  },
  data() {
    return {
      isLoading: false,
      isSubmitting: false,
      successMessage: '',
      errorMessage: '',
      searchQuery: '',
      roleFilter: 'all',
      sortState: {
        key: 'createdAt',
        direction: 'desc',
      },
      approvalModal: {
        visible: false,
        registration: null,
      },
      openActionMenuId: null,
      pendingUsers: [],
    };
  },
  computed: {
    tableColumns() {
      return [
        { key: 'fullName', label: 'Full name', sortable: true },
        { key: 'email', label: 'Email', sortable: true },
        { key: 'requestedRole', label: 'Requested role' },
        { key: 'aiProfilingConsent', label: 'AI profiling consent' },
        { key: 'gdprConsent', label: 'GDPR consent' },
        { key: 'createdAt', label: 'Created at', sortable: true },
      ];
    },
    filteredPendingUsers() {
      return this.pendingUsers.filter((registration) => {
        const matchesRole = this.roleFilter === 'all' || registration.requestedRole === this.roleFilter;
        const haystack = `${registration.fullName} ${registration.email}`.toLowerCase();
        const matchesSearch = !this.searchQuery || haystack.includes(this.searchQuery.toLowerCase());

        return matchesRole && matchesSearch;
      });
    },
    sortedPendingUsers() {
      const direction = this.sortState.direction === 'desc' ? -1 : 1;
      return [...this.filteredPendingUsers].sort((left, right) => {
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
    this.loadPendingRegistrations();
  },
  methods: {
    normalizeRegistration(item) {
      return {
        id: item.id,
        fullName: item.full_name || item.fullName,
        email: item.email,
        requestedRole: String(item.requested_role || item.requestedRole || '').toLowerCase(),
        aiProfilingConsent: Boolean(item.ai_profiling_consent ?? item.aiProfilingConsent),
        gdprConsent: Boolean(item.gdpr_consent ?? item.gdprConsent),
        createdAt: item.created_at || item.createdAt,
      };
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    sortableValue(registration, key) {
      if (key === 'createdAt') {
        const time = new Date(registration.createdAt).getTime();
        return Number.isNaN(time) ? 0 : time;
      }

      return String(registration[key] || '').toLowerCase();
    },
    handleSortChange(nextSort) {
      this.sortState = nextSort;
    },
    toggleActionMenu(registrationId) {
      this.openActionMenuId = this.openActionMenuId === registrationId ? null : registrationId;
    },
    closeActionMenu() {
      this.openActionMenuId = null;
    },
    handleRowAction(action, registration) {
      this.closeActionMenu();

      if (action === 'approve') {
        this.openApprovalModal(registration);
        return;
      }

      if (action === 'reject') {
        this.rejectRegistration(registration);
      }
    },
    async loadPendingRegistrations() {
      this.isLoading = true;
      this.errorMessage = '';

      const response = await adminService.fetchPendingRegistrations();

      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : response.data?.items || [];
        this.pendingUsers = items.map((item) => this.normalizeRegistration(item));
      } else {
        this.errorMessage = response.error?.message || 'Unable to load pending registrations.';
      }

      this.isLoading = false;
    },
    openApprovalModal(registration) {
      this.successMessage = '';
      this.errorMessage = '';
      this.approvalModal.visible = true;
      this.approvalModal.registration = registration;
    },
    closeApprovalModal() {
      this.approvalModal.visible = false;
      this.approvalModal.registration = null;
    },
    async confirmApproval() {
      if (!this.approvalModal.registration) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.approveRegistration(this.approvalModal.registration.id);

      if (response.success) {
        if (response.data?.credentials_email_triggered) {
          this.pushSuccessToast('Registration approved. Credential email sending is marked in the backend response.');
        } else {
          this.pushSuccessToast('Registration approved.');
        }
        this.pendingUsers = this.pendingUsers.filter(
          (registration) => registration.id !== this.approvalModal.registration.id
        );
        this.closeApprovalModal();
        window.dispatchEvent(new CustomEvent('admin-request-counts:refresh'));
      } else {
        this.errorMessage = response.error?.message || 'Unable to approve the registration.';
      }

      this.isSubmitting = false;
    },
    async rejectRegistration(registration) {
      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.rejectRegistration(registration.id);

      if (response.success) {
        this.pushInfoToast(`Registration for ${registration.fullName} rejected.`);
        this.pendingUsers = this.pendingUsers.filter((item) => item.id !== registration.id);
        window.dispatchEvent(new CustomEvent('admin-request-counts:refresh'));
      } else {
        this.errorMessage = response.error?.message || 'Unable to reject the registration.';
      }

      this.isSubmitting = false;
    },
  },
};
</script>
