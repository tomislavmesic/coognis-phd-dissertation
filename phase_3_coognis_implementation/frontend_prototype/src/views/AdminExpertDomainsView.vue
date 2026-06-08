<template>
  <section class="admin-expert-domains">
    <BasePageHeader
      
      eyebrow="Admin"
      title="Expert domain assignment"
      description="Review active experts, their specialization coverage, and maintain domain assignments used by UEX."
    />

    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" />

    <BaseCard
      class="admin-expert-domains__card"
      title="Experts"
      subtitle="Domain assignments should reflect the areas where each expert can provide real guidance."
      card-body-class="p-0"
    >
      <template #actions>
        <input
          v-model.trim="searchQuery"
          class="form-control"
          type="search"
          placeholder="Search experts by name or email"
          aria-label="Search experts"
        />
        <div class="d-flex flex-wrap flex-md-nowrap gap-2 justify-content-md-end ms-md-auto">
          <select v-model="domainFilter" class="form-select" aria-label="Filter experts by domain">
            <option value="all">All domains</option>
            <option v-for="domain in domains" :key="domain" :value="domain">{{ domain }}</option>
          </select>
          <select v-model="activityFilter" class="form-select" aria-label="Filter experts by activity">
            <option value="all">All experts</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <button
            class="btn btn-primary"
            type="button"
            aria-label="Add expert"
            title="Add expert"
            @click="$router.push('/admin/users/create')"
          >
            <ThemeIcon name="create" />
          </button>
        </div>
      </template>

      <BaseLoadingState v-if="isLoading" label="Loading experts..." state-class="py-5" />

      <BaseEmptyState
        v-else-if="!filteredExperts.length"
        title="No matching experts"
        :description="experts.length ? 'Try adjusting the filters.' : 'No experts are available yet.'"
        state-class="py-5"
      />

      <BaseTable
        v-else
        :columns="tableColumns"
        :rows="sortedExperts"
        :sort-key="sortState.key"
        :sort-direction="sortState.direction"
        actions-mode="icon-only"
        table-class="admin-expert-domains__table"
        @sort-change="handleSortChange"
      >
        <template #cell-name="{ row }">
          <div class="admin-expert-domains__identity">
            <strong>{{ row.name }}</strong>
            <small class="text-body-secondary">{{ row.email || 'No email' }}</small>
          </div>
        </template>
        <template #cell-status="{ row }">
          <span class="badge" :class="row.isActive ? 'text-bg-success' : 'text-bg-secondary'">
            {{ row.isActive ? 'Active' : 'Inactive' }}
          </span>
        </template>
        <template #cell-domains="{ row }">
          <div class="admin-expert-domains__chips">
            <span v-for="domain in row.domainCodes" :key="domain" class="badge text-bg-light">{{ domain }}</span>
            <span v-if="!row.domainCodes.length" class="text-body-secondary">No domains</span>
          </div>
        </template>
        <template #cell-account="{ row }">
          <div class="admin-expert-domains__accoun">
            <span class="badge" :class="row.hasPlatformAccount ? 'text-bg-success' : 'text-bg-warning'">
              {{ row.hasPlatformAccount ? 'Provisioned' : 'UEX only' }}
            </span>
            <small class="text-body-secondary d-block mt-1">
              {{ accountStatusLabel(row) }}
            </small>
          </div>
        </template>
        <template #cell-createdAt="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
        <template #actions="{ row }">
          <BaseTableActionsMenu
            :open="openActionMenuId === row.id"
            :disabled="isSubmitting"
            label="Open expert actions"
            @toggle="toggleActionMenu(row.id)"
            @close="closeActionMenu"
          >
              <button
                class="base-table__actions-item"
                type="button"
                role="menuitem"
                :disabled="isSubmitting"
                @click="handleRowAction('assign', row)"
              >
                Assign domains
              </button>
              <button
                v-if="!row.hasPlatformAccount && row.email"
                class="base-table__actions-item"
                type="button"
                role="menuitem"
                :disabled="isSubmitting"
                @click="handleRowAction('provision', row)"
              >
                Provision account
              </button>
          </BaseTableActionsMenu>
        </template>
      </BaseTable>
    </BaseCard>

    <BaseModal
      :visible="domainModal.visible"
      :busy="isSubmitting"
      eyebrow="Expert"
      title="Assign expert domains"
      modal-id="admin-expert-domain-modal"
      dialog-class="modal-dialog-centered modal-lg"
      @close="closeDomainModal"
    >
      <BaseAlert v-if="domainModal.errorMessage" variant="danger" :message="domainModal.errorMessage" />

      <div v-if="domainModal.expert" class="admin-expert-domains__modal-content">
        <p class="mb-3">
          Update domains for <strong>{{ domainModal.expert.name }}</strong>.
        </p>
        <div class="admin-expert-domains__domain-grid">
          <label v-for="domain in domains" :key="domain" class="form-check admin-expert-domains__domain-option">
            <input
              :checked="selectedDomains.includes(domain)"
              class="form-check-input"
              type="checkbox"
              :value="domain"
              :disabled="isSubmitting"
              @change="toggleDomain(domain)"
            />
            <span class="form-check-label">{{ domain }}</span>
          </label>
        </div>
      </div>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeDomainModal">
          Cancel
        </button>
        <button class="btn btn-primary" type="button" :disabled="isSubmitting || !domainModal.expert" @click="submitDomains">
          {{ isSubmitting ? 'Saving...' : 'Save domains' }}
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
import BaseTableActionsMenu from '@/components/BaseTableActionsMenu.vue';
import BaseTable from '@/components/BaseTable.vue';
import ThemeIcon from '@/components/ThemeIcon.vue';
import adminService from '@/services/adminService';
import { formatDateTime } from '@/utils/dateTime';

export default {
  name: 'AdminExpertDomainsView',
  components: {
    BaseAlert,
    BaseCard,
    BaseEmptyState,
    BaseLoadingState,
    BaseModal,
    BasePageHeader,
    BaseTableActionsMenu,
    BaseTable,
    ThemeIcon,
  },
  data() {
    return {
      isLoading: false,
      isSubmitting: false,
      successMessage: '',
      errorMessage: '',
      searchQuery: '',
      domainFilter: 'all',
      activityFilter: 'all',
      sortState: {
        key: 'createdAt',
        direction: 'desc',
      },
      experts: [],
      domains: [],
      selectedDomains: [],
      domainModal: {
        visible: false,
        expert: null,
        errorMessage: '',
      },
      openActionMenuId: null,
    };
  },
  computed: {
    tableColumns() {
      return [
        { key: 'name', label: 'Expert', sortable: true },
        { key: 'status', label: 'Status', sortable: true },
        { key: 'domains', label: 'Assigned domains' },
        { key: 'account', label: 'Platform account' },
        { key: 'createdAt', label: 'Created at', sortable: true },
      ];
    },
    filteredExperts() {
      const query = this.searchQuery.toLowerCase();
      return this.experts.filter((expert) => {
        const matchesActivity =
          this.activityFilter === 'all' ||
          (this.activityFilter === 'active' && expert.isActive) ||
          (this.activityFilter === 'inactive' && !expert.isActive);
        const matchesDomain =
          this.domainFilter === 'all' || expert.domainCodes.includes(this.domainFilter);
        const matchesQuery =
          !query ||
          expert.name.toLowerCase().includes(query) ||
          (expert.email || '').toLowerCase().includes(query);

        return matchesActivity && matchesDomain && matchesQuery;
      });
    },
    sortedExperts() {
      const direction = this.sortState.direction === 'desc' ? -1 : 1;
      return [...this.filteredExperts].sort((left, right) => {
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
      this.isLoading = true;
      this.errorMessage = '';

      const [expertResponse, domainResponse] = await Promise.all([
        adminService.fetchExperts(),
        adminService.fetchDomains(),
      ]);

      if (expertResponse.success) {
        const experts = Array.isArray(expertResponse.data) ? expertResponse.data : expertResponse.data?.items || [];
        this.experts = experts.map((item) => ({
          id: item.id,
          name: item.name,
          email: item.email,
          isActive: Boolean(item.is_active),
          domainCodes: item.domain_codes || [],
          hasPlatformAccount: Boolean(item.has_platform_account),
          platformUserId: item.platform_user_id || null,
          platformAccountActive: Boolean(item.platform_account_active),
          platformAccountRegistrationStatus: item.platform_account_registration_status || null,
          createdAt: item.created_at,
        }));
      } else {
        this.errorMessage = expertResponse.error?.message || 'Unable to load experts.';
      }

      if (domainResponse.success) {
        const domains = Array.isArray(domainResponse.data) ? domainResponse.data : domainResponse.data?.items || [];
        this.domains = domains.map((item) => item.code);
      }

      this.isLoading = false;
    },
    openDomainModal(expert) {
      this.domainModal.visible = true;
      this.domainModal.expert = expert;
      this.domainModal.errorMessage = '';
      this.selectedDomains = [...expert.domainCodes];
    },
    toggleActionMenu(expertId) {
      this.openActionMenuId = this.openActionMenuId === expertId ? null : expertId;
    },
    closeActionMenu() {
      this.openActionMenuId = null;
    },
    handleRowAction(action, expert) {
      this.closeActionMenu();

      if (action === 'assign') {
        this.openDomainModal(expert);
        return;
      }

      if (action === 'provision') {
        this.handleProvisionAccount(expert);
      }
    },
    closeDomainModal() {
      if (this.isSubmitting) {
        return;
      }
      this.domainModal.visible = false;
      this.domainModal.expert = null;
      this.selectedDomains = [];
    },
    toggleDomain(domain) {
      if (this.selectedDomains.includes(domain)) {
        this.selectedDomains = this.selectedDomains.filter((item) => item !== domain);
        return;
      }
      this.selectedDomains = [...this.selectedDomains, domain];
    },
    async submitDomains() {
      if (!this.domainModal.expert || this.isSubmitting) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';
      this.domainModal.errorMessage = '';

      const response = await adminService.updateExpert(this.domainModal.expert.id, {
        domain_codes: this.selectedDomains,
      });

      if (response.success) {
        this.successMessage = 'Expert domains updated.';
        this.closeDomainModal();
        await this.loadData();
      } else {
        this.domainModal.errorMessage = response.error?.message || 'Unable to update expert domains.';
      }

      this.isSubmitting = false;
    },
    accountStatusLabel(expert) {
      if (!expert.email) {
        return 'Missing email';
      }

      if (!expert.hasPlatformAccount) {
        return 'Can be recommended, but cannot be contacted in chat yet.';
      }

      if (!expert.platformAccountActive) {
        return 'Platform account is inactive.';
      }

      return expert.platformAccountRegistrationStatus
        ? `Status: ${expert.platformAccountRegistrationStatus}`
        : 'Ready for expert chat handoff.';
    },
    async handleProvisionAccount(expert) {
      if (this.isSubmitting || expert.hasPlatformAccount) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.provisionExpertAccount(expert.id);

      if (response.success) {
        const emailState = response.data?.credentials_email_triggered
          ? 'Credentials email sent.'
          : `Temporary password: ${response.data?.generated_temporary_password || 'generated'}.`;
        this.successMessage = `COOGNIS expert account provisioned. ${emailState}`;
        await this.loadData();
      } else {
        this.errorMessage = response.error?.message || 'Unable to provision the expert account.';
      }

      this.isSubmitting = false;
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    sortableValue(expert, key) {
      if (key === 'createdAt') {
        const time = new Date(expert.createdAt).getTime();
        return Number.isNaN(time) ? 0 : time;
      }

      if (key === 'status') {
        return expert.isActive ? 'active' : 'inactive';
      }

      return String(expert[key] || '').toLowerCase();
    },
    handleSortChange(nextSort) {
      this.sortState = nextSort;
    },
  },
};
</script>
