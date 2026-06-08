<template>
  <section class="base-dashboard">
    <BasePageHeader
      class="base-dashboard__hero"
      eyebrow="Admin workspace"
      title="Operations overview"
      description="Oversee approvals, monitor active accounts, and review privacy-related requests from one control surface."
    >
      <template #actions>
        <div class="base-dashboard__hero-actions">
          <RouterLink class="btn" to="/admin/registrations">
            Open approvals
          </RouterLink>
          <RouterLink class="btn btn-outline" to="/admin/module-settings">
            AI modules
          </RouterLink>
        </div>
      </template>
    </BasePageHeader>

    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" />
    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />

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
      <div class="col-sm-12">
        <BaseCard 
          class="base-card" 
          card-body-class="p-0"
        >
          <template #header>
            <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 w-100">
              <div class="base-card__heading">
                <h2 class="h5 mb-1">Pending registrations</h2>
                <p class="text-body-secondary mb-0">Registration requests waiting for manual review and approval.</p>
              </div>
              <RouterLink class="btn btn-outline-secondary btn-sm" to="/admin/registrations">
                Open approvals
              </RouterLink>
            </div>
          </template>
          <BaseTable :columns="pendingRegistrationColumns" :rows="pendingRegistrations">
            <template #actions="{ row }">
              <div class="d-flex flex-wrap gap-2">
                <RouterLink class="btn btn-sm btn-primary" :to="`/admin/registrations`">
                  Approve
                </RouterLink>
                <RouterLink class="btn btn-sm btn-outline-secondary" :to="`/admin/registrations`">
                  Review
                </RouterLink>
              </div>
            </template>
          </BaseTable>
        </BaseCard>
      </div>
    </div>

    <div class="row g-4">
      <div class="col-lg-6">
        <BaseCard 
          class="base-card"
          card-body-class="p-0"
        >
          <template #header>
            <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 w-100">
              <div class="base-card__heading">
                <h2 class="h5 mb-1">Active users</h2>
                <p class="text-body-secondary mb-0">Snapshot of active user accounts and current status.</p>
              </div>
              <RouterLink class="btn btn-outline-primary btn-sm" to="/admin/users/create">Create user</RouterLink>
            </div>
          </template>
          <BaseTable :columns="activeUserColumns" :rows="activeUsers">
            <template #cell-status="{ value }">
              <span class="badge text-bg-success">{{ value }}</span>
            </template>
          </BaseTable>
        </BaseCard>
      </div>

      <div class="col-lg-6">
        <BaseCard 
          class="base-card" 
          card-body-class="p-0"
        >
          <template #header>
            <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 w-100">
              <div class="base-card__heading">
                <h2 class="h5 mb-1">Active experts</h2>
                <p class="text-body-secondary mb-0">Expert roster overview with availability and security status.</p>
              </div>
              <RouterLink class="btn btn-outline-primary btn-sm" to="/admin/users/create">Create expert</RouterLink>
            </div>
          </template>
          <BaseTable :columns="activeExpertColumns" :rows="activeExperts" />
        </BaseCard>
      </div>
    </div>

    <div class="row g-4">
      <div class="col-lg-12">
        <BaseCard 
          class="base-card" 
          card-body-class="p-0"
        >
          <template #header>
            <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 w-100">
              <div class="base-card__heading">
                <h2 class="h5 mb-1">Consent and deletion requests</h2>
                <p class="text-body-secondary mb-0">Review privacy-related actions that may require follow-up or audit handling.</p>
              </div>
              <RouterLink class="btn btn-outline-secondary btn-sm" to="/admin/data-requests">
                Open queue
              </RouterLink>
            </div>
          </template>
          <BaseTable :columns="consentRequestColumns" :rows="consentRequests">
            <template #actions>
              <RouterLink class="btn btn-sm btn-outline-primary" to="/admin/data-requests">Open</RouterLink>
            </template>
          </BaseTable>
        </BaseCard>
      </div>
    </div>
  </section>
</template>

<script>
import { RouterLink } from 'vue-router';
import BaseAlert from '@/components/BaseAlert.vue';
import BaseCard from '@/components/BaseCard.vue';
import BasePageHeader from '@/components/BasePageHeader.vue';
import BaseTable from '@/components/BaseTable.vue';
import adminService from '@/services/adminService';
import { formatDateTime } from '@/utils/dateTime';

export default {
  name: 'AdminDashboardView',
  components: {
    BaseAlert,
    BaseCard,
    BasePageHeader,
    BaseTable,
    RouterLink,
  },
  data() {
    return {
      successMessage: '',
      errorMessage: '',
      pendingRegistrations: [],
      systemStats: [],
      activeUsers: [],
      activeExperts: [],
      consentRequests: [],
    };
  },
  computed: {
    pendingRegistrationColumns() {
      return [
        { key: 'name', label: 'Name' },
        { key: 'role', label: 'Role' },
        { key: 'submittedAt', label: 'Submitted' },
        { key: 'consents', label: 'Consents' },
      ];
    },
    activeUserColumns() {
      return [
        { key: 'name', label: 'User' },
        { key: 'status', label: 'Status' },
        { key: 'twoFactor', label: '2FA', headerClass: 'text-end', cellClass: 'text-end' },
      ];
    },
    activeExpertColumns() {
      return [
        { key: 'name', label: 'Expert' },
        { key: 'availability', label: 'Availability' },
        { key: 'twoFactor', label: '2FA', headerClass: 'text-end', cellClass: 'text-end' },
      ];
    },
    consentRequestColumns() {
      return [
        { key: 'type', label: 'Request' },
        { key: 'submittedBy', label: 'Submitted by' },
        { key: 'status', label: 'Status' },
      ];
    },
    overviewStats() {
      const statsMap = Object.fromEntries((this.systemStats || []).map((item) => [item.label, item.value]));
      return [
        {
          label: 'Pending approvals',
          value: String(this.pendingRegistrations.length),
          note: 'Registration requests currently waiting for manual review.',
        },
        {
          label: 'Active users',
          value: String(statsMap['Active users'] ?? this.activeUsers.length),
          note: 'Current snapshot of active user accounts.',
        },
        {
          label: 'Active experts',
          value: String(statsMap['Active experts'] ?? this.activeExperts.length),
          note: 'Current expert roster available in the platform.',
        },
        {
          label: 'Privacy requests',
          value: String(this.consentRequests.length),
          note: 'Consent, deletion, and privacy-related actions awaiting follow-up.',
        },
      ];
    },
  },
  created() {
    this.loadDashboard();
  },
  methods: {
    formatDate(value) {
      return formatDateTime(value);
    },
    async loadDashboard() {
      this.errorMessage = '';

      const response = await adminService.fetchDashboardSummary();

      if (!response.success) {
        this.errorMessage = response.error?.message || 'Unable to load dashboard data.';
        return;
      }

      const data = response.data || {};
      this.pendingRegistrations = (data.pending_registrations || []).map((item) => ({
        id: item.id,
        name: item.name,
        role: item.role,
        submittedAt: this.formatDate(item.submitted_at),
        consents: item.consents,
      }));
      this.systemStats = data.system_stats || [];
      this.activeUsers = (data.active_users || []).map((item) => ({
        id: item.id,
        name: item.name,
        status: item.status,
        twoFactor: item.two_factor,
      }));
      this.activeExperts = (data.active_experts || []).map((item) => ({
        id: item.id,
        name: item.name,
        availability: item.availability,
        twoFactor: item.two_factor,
      }));
      this.consentRequests = (data.consent_requests || []).map((item) => ({
        id: item.id,
        type: item.type,
        submittedBy: item.submitted_by,
        status: item.status,
      }));
    },
  },
};
</script>
