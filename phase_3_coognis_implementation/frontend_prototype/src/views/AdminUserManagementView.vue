<template>
  <section class="admin-user-management">
    <BasePageHeader
      
      eyebrow="Admin"
      title="User management"
      description="Search, filter, and review platform accounts across users, experts, and admins."
    />

    <div v-if="!isLoading && accounts.length" class="row g-4">
      <div class="col-md-4" v-for="summary in twoFactorSummaries" :key="summary.role">
        <BaseCard
          class="admin-user-management__summary-card"
          :class="{ 'admin-user-management__summary-card--active': accountFilter === summary.role }"
        >
          <button
            class="admin-user-management__summary-button"
            type="button"
            @click="toggleAccountFilter(summary.role)"
          >
          <div class="admin-user-management__summary">
            <span class="admin-user-management__summary-label">{{ summary.label }}</span>
            <strong class="admin-user-management__summary-value">
              {{ summary.enabled }} / {{ summary.total }}
            </strong>
            <span class="admin-user-management__summary-meta">
              2FA enabled
            </span>
          </div>
          </button>
        </BaseCard>
      </div>
    </div>

    <BaseCard
      class="admin-user-management__card"
      title="Accounts"
      subtitle="Use the search and role filters to narrow the management table."
      card-body-class="p-0"
    >
      <template #actions>
        <input
          v-model.trim="searchQuery"
          class="form-control"
          type="search"
          placeholder="Search by name or email"
          aria-label="Search accounts"
        />
        <div class="d-flex flex-wrap flex-md-nowrap gap-2 justify-content-md-end ms-md-auto">
          <select v-model="accountFilter" class="form-select" aria-label="Filter by account type">
            <option value="all">All roles</option>
            <option value="user">User</option>
            <option value="expert">Expert</option>
            <option value="admin">Admin</option>
            <option value="debug-enabled">Debug enabled</option>
          </select>
          <button
            class="btn btn-primary"
            type="button"
            aria-label="Add user"
            title="Add user"
            @click="$router.push('/admin/users/create')"
          >
            <ThemeIcon name="create" />
          </button>
        </div>
      </template>

      <BaseLoadingState v-if="isLoading" label="Loading accounts..." state-class="py-5" />

      <BaseEmptyState
        v-else-if="!filteredAccounts.length"
        title="No matching accounts"
        description="Try a different search term or role filter."
        state-class="py-5"
      />

      <BaseTable
        v-else
        :columns="tableColumns"
        :rows="sortedAccounts"
        :sort-key="sortState.key"
        :sort-direction="sortState.direction"
        actions-mode="icon-only"
        table-class="admin-user-management__table"
        @sort-change="handleSortChange"
      >
        <template #cell-role="{ value }">
          <span class="text-capitalize">{{ value }}</span>
        </template>
        <template #cell-status="{ row }">
          <div class="admin-user-management__status-stack">
            <div class="admin-user-management__status-row">
              <span class="admin-user-management__status-label">Registration</span>
              <span class="badge" :class="row.registrationConfirmed ? 'text-bg-success' : 'text-bg-secondary'">
                {{ row.registrationConfirmed ? 'Confirmed' : 'Pending' }}
              </span>
            </div>
            <div class="admin-user-management__status-row">
              <span class="admin-user-management__status-label">2FA</span>
              <span class="badge" :class="row.twoFactorEnabled ? 'text-bg-success' : 'text-bg-secondary'">
                {{ row.twoFactorEnabled ? 'Enabled' : 'Disabled' }}
              </span>
            </div>
            <div class="admin-user-management__status-row">
              <span class="admin-user-management__status-label">Profiling</span>
              <span class="badge" :class="row.profilingConsent ? 'text-bg-success' : 'text-bg-warning'">
                {{ row.profilingConsent ? 'Recorded' : 'Missing' }}
              </span>
            </div>
            <div class="admin-user-management__status-row">
              <span class="admin-user-management__status-label">GDPR</span>
              <span class="badge" :class="row.gdprConsent ? 'text-bg-success' : 'text-bg-warning'">
                {{ row.gdprConsent ? 'Recorded' : 'Missing' }}
              </span>
            </div>
            <div class="admin-user-management__status-row">
              <span class="admin-user-management__status-label">Deletion</span>
              <span class="badge" :class="row.deletionRequested ? 'text-bg-danger' : 'text-bg-secondary'">
                {{ row.deletionRequested ? 'Requested' : 'No request' }}
              </span>
            </div>
            <div class="admin-user-management__status-row">
              <span class="admin-user-management__status-label">Access</span>
              <span class="badge" :class="row.isActive ? 'text-bg-success' : 'text-bg-secondary'">
                {{ row.isActive ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <div class="admin-user-management__status-row">
              <span class="admin-user-management__status-label">Debug</span>
              <span class="badge" :class="row.canAccessChatDebugPanels ? 'text-bg-info' : 'text-bg-secondary'">
                {{ row.canAccessChatDebugPanels ? 'Allowed' : 'Blocked' }}
              </span>
            </div>
          </div>
        </template>
        <template #actions="{ row }">
          <BaseTableActionsMenu
            :open="openActionMenuId === row.id"
            :disabled="isSubmitting"
            label="Open account actions"
            @toggle="toggleActionMenu(row.id)"
            @close="closeActionMenu"
          >
              <button class="base-table__actions-item" type="button" role="menuitem" @click="handleRowAction('view', row)">
                View
              </button>
              <button class="base-table__actions-item" type="button" role="menuitem" @click="handleRowAction('edit', row)">
                Edit
              </button>
              <button class="base-table__actions-item" type="button" role="menuitem" @click="handleRowAction('reset-password', row)">
                Reset password
              </button>
              <button class="base-table__actions-item" type="button" role="menuitem" @click="handleRowAction('resend-credentials', row)">
                Resend credentials
              </button>
              <button class="base-table__actions-item" type="button" role="menuitem" @click="handleRowAction('reset-2fa', row)">
                Reset 2FA
              </button>
              <button
                class="base-table__actions-item base-table__actions-item--danger"
                type="button"
                role="menuitem"
                :disabled="!row.isActive"
                @click="handleRowAction('deactivate', row)"
              >
                Deactivate
              </button>
          </BaseTableActionsMenu>
        </template>
      </BaseTable>
    </BaseCard>

    <BaseModal
      :visible="detailModal.visible"
      eyebrow="Account"
      title="User details"
      modal-id="admin-user-details-modal"
      @close="closeDetailModal"
    >
      <dl v-if="detailModal.account" class="admin-user-management__detail-grid mb-0">
        <div>
          <dt>Full name</dt>
          <dd>{{ detailModal.account.fullName }}</dd>
        </div>
        <div>
          <dt>Email</dt>
          <dd>{{ detailModal.account.email }}</dd>
        </div>
        <div>
          <dt>Role</dt>
          <dd class="text-capitalize">{{ detailModal.account.role }}</dd>
        </div>
        <div>
          <dt>Registration</dt>
          <dd>{{ detailModal.account.registrationStatus }}</dd>
        </div>
        <div>
          <dt>2FA enabled</dt>
          <dd>{{ detailModal.account.twoFactorEnabled ? 'Yes' : 'No' }}</dd>
        </div>
        <div>
          <dt>Account active</dt>
          <dd>{{ detailModal.account.isActive ? 'Yes' : 'No' }}</dd>
        </div>
        <div>
          <dt>AI profiling consent</dt>
          <dd>{{ detailModal.account.profilingConsent ? 'Recorded' : 'Missing' }}</dd>
        </div>
        <div>
          <dt>GDPR consent</dt>
          <dd>{{ detailModal.account.gdprConsent ? 'Recorded' : 'Missing' }}</dd>
        </div>
        <div>
          <dt>Chat debug access</dt>
          <dd>{{ detailModal.account.canAccessChatDebugPanels ? 'Allowed' : 'Blocked' }}</dd>
        </div>
        <div>
          <dt>Deletion requested</dt>
          <dd>{{ detailModal.account.deletionRequested ? 'Yes' : 'No' }}</dd>
        </div>
        <div>
          <dt>Manual MBTI</dt>
          <dd>{{ detailModal.account.manualMbti || 'Not set' }}</dd>
        </div>
        <div>
          <dt>Inferred MBTI</dt>
          <dd>{{ detailModal.account.inferredMbti || 'Not inferred' }}</dd>
        </div>
        <div>
          <dt>Effective MBTI</dt>
          <dd>{{ detailModal.account.effectiveMbti || 'Unavailable' }}</dd>
        </div>
        <div>
          <dt>Profile confidence</dt>
          <dd>{{ detailModal.account.profileConfidenceLabel }}</dd>
        </div>
        <div>
          <dt>Profile interactions</dt>
          <dd>{{ detailModal.account.profileInteractionCount }}</dd>
        </div>
      </dl>

      <div v-if="detailModal.account" class="mt-4">
        <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
          <h3 class="h6 mb-0">Remembered devices</h3>
          <button
            v-if="detailModal.trustedDevices.length"
            class="btn btn-sm btn-outline-danger"
            type="button"
            :disabled="isSubmitting"
            @click="handleRevokeAllTrustedDevices"
          >
            Revoke all
          </button>
        </div>

        <BaseAlert
          v-if="detailModal.devicesError"
          class="mb-3"
          variant="danger"
          :message="detailModal.devicesError"
        />

        <BaseLoadingState
          v-if="detailModal.loadingDevices"
          label="Loading remembered devices..."
          state-class="py-4"
        />

        <BaseEmptyState
          v-else-if="!detailModal.trustedDevices.length"
          title="No remembered devices"
          description="This account does not currently have any trusted-device exemptions."
          state-class="py-4"
        />

        <div v-else class="d-grid gap-2">
          <div
            v-for="device in detailModal.trustedDevices"
            :key="device.id"
            class="border rounded-2 p-3 d-flex flex-wrap align-items-start justify-content-between gap-3"
          >
            <dl class="mb-0 admin-user-management__device-grid">
              <div>
                <dt>Created</dt>
                <dd>{{ formatDateTime(device.createdAt) }}</dd>
              </div>
              <div>
                <dt>Last used</dt>
                <dd>{{ device.lastUsedAt ? formatDateTime(device.lastUsedAt) : 'Never used' }}</dd>
              </div>
              <div>
                <dt>Expires</dt>
                <dd>{{ formatDateTime(device.expiresAt) }}</dd>
              </div>
            </dl>
            <button
              class="btn btn-sm btn-outline-danger"
              type="button"
              :disabled="isSubmitting"
              @click="handleRevokeTrustedDevice(device.id)"
            >
              Revoke
            </button>
          </div>
        </div>
      </div>
    </BaseModal>

    <BaseModal
      :visible="editModal.visible"
      :busy="isSubmitting"
      eyebrow="Account"
      title="Edit user"
      modal-id="admin-user-edit-modal"
      dialog-class="modal-dialog-centered modal-lg"
      @close="closeEditModal"
    >
      <BaseAlert v-if="editModal.errorMessage" variant="danger" :message="editModal.errorMessage" />

      <form id="admin-user-edit-form" class="row g-3" novalidate @submit.prevent="submitEdit">
        <div class="col-md-6">
          <label class="form-label" for="edit-first-name">First name</label>
          <input
            id="edit-first-name"
            v-model.trim="editForm.first_name"
            class="form-control"
            :class="{ 'is-invalid': editErrors.first_name }"
            type="text"
            :disabled="isSubmitting"
            @blur="validateEditField('first_name')"
          />
          <div v-if="editErrors.first_name" class="invalid-feedback d-block">{{ editErrors.first_name }}</div>
        </div>

        <div class="col-md-6">
          <label class="form-label" for="edit-last-name">Last name</label>
          <input
            id="edit-last-name"
            v-model.trim="editForm.last_name"
            class="form-control"
            :class="{ 'is-invalid': editErrors.last_name }"
            type="text"
            :disabled="isSubmitting"
            @blur="validateEditField('last_name')"
          />
          <div v-if="editErrors.last_name" class="invalid-feedback d-block">{{ editErrors.last_name }}</div>
        </div>

        <div class="col-md-6">
          <label class="form-label" for="edit-email">Email</label>
          <input
            id="edit-email"
            v-model.trim="editForm.email"
            class="form-control"
            :class="{ 'is-invalid': editErrors.email }"
            type="email"
            :disabled="isSubmitting"
            @blur="validateEditField('email')"
          />
          <div v-if="editErrors.email" class="invalid-feedback d-block">{{ editErrors.email }}</div>
        </div>

        <div class="col-md-6">
          <label class="form-label" for="edit-role">Role</label>
          <select
            id="edit-role"
            v-model="editForm.role"
            class="form-select"
            :class="{ 'is-invalid': editErrors.role }"
            :disabled="isSubmitting"
            @change="validateEditField('role')"
          >
            <option value="user">User</option>
            <option value="expert">Expert</option>
            <option value="admin">Admin</option>
          </select>
          <div v-if="editErrors.role" class="invalid-feedback d-block">{{ editErrors.role }}</div>
        </div>

        <div class="col-md-6">
          <div class="form-check form-switch">
            <input
              id="edit-active"
              v-model="editForm.is_active"
              class="form-check-input"
              type="checkbox"
              :disabled="isSubmitting"
            />
            <label class="form-check-label" for="edit-active">Account active</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-check form-switch">
            <input
              id="edit-two-factor"
              v-model="editForm.two_factor_enabled"
              class="form-check-input"
              type="checkbox"
              :disabled="isSubmitting"
            />
            <label class="form-check-label" for="edit-two-factor">2FA enabled</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-check form-switch">
            <input
              id="edit-ai-consent"
              v-model="editForm.ai_profiling_consent"
              class="form-check-input"
              type="checkbox"
              :disabled="isSubmitting"
            />
            <label class="form-check-label" for="edit-ai-consent">AI profiling consent recorded</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-check form-switch">
            <input
              id="edit-gdpr-consent"
              v-model="editForm.gdpr_consent"
              class="form-check-input"
              type="checkbox"
              :disabled="isSubmitting"
            />
            <label class="form-check-label" for="edit-gdpr-consent">GDPR consent recorded</label>
          </div>
        </div>

        <div class="col-md-6">
          <label class="form-label" for="edit-manual-mbti">Manual MBTI override</label>
          <select
            id="edit-manual-mbti"
            v-model="editForm.manual_mbti"
            class="form-select"
            :disabled="isSubmitting"
          >
            <option value="">Use inferred profile</option>
            <option v-for="type in mbtiOptions" :key="type" :value="type">{{ type }}</option>
          </select>
          <div class="form-text">
            Setting a manual MBTI override takes precedence over the inferred profile for future matching.
          </div>
        </div>

        <div class="col-md-6">
          <label class="form-label" for="edit-inferred-mbti">Current inferred MBTI</label>
          <input
            id="edit-inferred-mbti"
            :value="editForm.inferred_mbti || 'Not inferred yet'"
            class="form-control"
            type="text"
            disabled
            readonly
          />
        </div>

        <div class="col-md-12">
          <div class="form-check form-switch">
            <input
              id="edit-chat-debug-access"
              v-model="editForm.can_access_chat_debug_panels"
              class="form-check-input"
              type="checkbox"
              :disabled="isSubmitting"
            />
            <label class="form-check-label" for="edit-chat-debug-access">Allow chat debug panels</label>
          </div>
          <div class="form-text">
            Works only when the global Chat debug panels setting is enabled and the backend is running in debug mode.
          </div>
        </div>
      </form>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeEditModal">
          Cancel
        </button>
        <button class="btn btn-primary" type="submit" form="admin-user-edit-form" :disabled="isSubmitting">
          {{ isSubmitting ? 'Saving...' : 'Save changes' }}
        </button>
      </template>
    </BaseModal>

    <BaseModal
      :visible="deactivateModal.visible"
      :busy="isSubmitting"
      eyebrow="Access"
      title="Confirm deactivation"
      modal-id="admin-user-deactivate-modal"
      @close="closeDeactivateModal"
    >
      <p class="mb-3">
        Deactivate <strong>{{ deactivateModal.account?.fullName }}</strong>? This keeps the account record but blocks
        active access until an admin re-enables it.
      </p>
      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeDeactivateModal">
          Cancel
        </button>
        <button class="btn btn-danger" type="button" :disabled="isSubmitting" @click="confirmDeactivate">
          {{ isSubmitting ? 'Deactivating...' : 'Deactivate account' }}
        </button>
      </template>
    </BaseModal>

    <BaseModal
      :visible="passwordResetModal.visible"
      :busy="isSubmitting"
      eyebrow="Access"
      title="Reset password"
      modal-id="admin-user-password-reset-modal"
      @close="closePasswordResetModal"
    >
      <p class="mb-3">
        Reset the password for <strong>{{ passwordResetModal.account?.fullName }}</strong>? A new temporary password
        will be generated.
      </p>
      <BaseAlert
        variant="warning"
        message="If email delivery is unavailable, the backend will return the generated temporary password so the admin can share it manually."
      />
      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closePasswordResetModal">
          Cancel
        </button>
        <button class="btn btn-warning" type="button" :disabled="isSubmitting" @click="confirmPasswordReset">
          {{ isSubmitting ? 'Resetting...' : 'Reset password' }}
        </button>
      </template>
    </BaseModal>

    <BaseModal
      :visible="resendCredentialsModal.visible"
      :busy="isSubmitting"
      eyebrow="Credentials"
      title="Resend credentials"
      modal-id="admin-user-resend-credentials-modal"
      @close="closeResendCredentialsModal"
    >
      <p class="mb-3">
        Reissue credentials for <strong>{{ resendCredentialsModal.account?.fullName }}</strong>? This action generates
        a new temporary password and sends it by email.
      </p>
      <BaseAlert
        variant="info"
        message="For security reasons, existing plaintext passwords are never resent. A new temporary password is issued instead."
      />
      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeResendCredentialsModal">
          Cancel
        </button>
        <button class="btn btn-dark" type="button" :disabled="isSubmitting" @click="confirmResendCredentials">
          {{ isSubmitting ? 'Sending...' : 'Reissue and send' }}
        </button>
      </template>
    </BaseModal>

    <BaseModal
      :visible="twoFactorResetModal.visible"
      :busy="isSubmitting"
      eyebrow="Access"
      title="Reset two-factor authentication"
      modal-id="admin-user-two-factor-reset-modal"
      @close="closeTwoFactorResetModal"
    >
      <p class="mb-3">
        Reset two-factor authentication for <strong>{{ twoFactorResetModal.account?.fullName }}</strong>? The user
        will need to enroll a new authenticator on the next login.
      </p>
      <BaseAlert
        variant="warning"
        message="This clears the current TOTP secret and all recovery codes. Existing authenticated browser sessions are not forcibly terminated."
      />
      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeTwoFactorResetModal">
          Cancel
        </button>
        <button class="btn btn-primary" type="button" :disabled="isSubmitting" @click="confirmTwoFactorReset">
          {{ isSubmitting ? 'Resetting...' : 'Reset 2FA' }}
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
import toastFeedbackMixin from '@/mixins/toastFeedbackMixin';
import ThemeIcon from '@/components/ThemeIcon.vue';
import adminService from '@/services/adminService';
import { email, getServerErrorMessage, oneOf, required, validateField, validateFields } from '@/utils/formValidation';

const EDIT_RULES = {
  first_name: [required('First name is required.')],
  last_name: [required('Last name is required.')],
  email: [required('Email is required.'), email('Enter a valid email address.')],
  role: [required('Role is required.'), oneOf(['user', 'expert', 'admin'], 'Select a valid role.')],
};

function createEmptyEditForm() {
  return {
    id: null,
    first_name: '',
    last_name: '',
    email: '',
    role: 'user',
    is_active: true,
    two_factor_enabled: false,
    ai_profiling_consent: false,
    gdpr_consent: false,
    can_access_chat_debug_panels: false,
    manual_mbti: '',
    inferred_mbti: '',
  };
}

export default {
  name: 'AdminUserManagementView',
  mixins: [toastFeedbackMixin],
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
      accountFilter: 'all',
      sortState: {
        key: 'fullName',
        direction: 'asc',
      },
      openActionMenuId: null,
      accounts: [],
      detailModal: {
        visible: false,
        account: null,
        loadingDevices: false,
        devicesError: '',
        trustedDevices: [],
      },
      editModal: {
        visible: false,
        errorMessage: '',
      },
      deactivateModal: {
        visible: false,
        account: null,
      },
      passwordResetModal: {
        visible: false,
        account: null,
      },
      resendCredentialsModal: {
        visible: false,
        account: null,
      },
      twoFactorResetModal: {
        visible: false,
        account: null,
      },
      editForm: createEmptyEditForm(),
      editErrors: {},
    };
  },
  computed: {
    mbtiOptions() {
      return ['INTJ', 'INTP', 'ENTJ', 'ENTP', 'INFJ', 'INFP', 'ENFJ', 'ENFP', 'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 'ISTP', 'ISFP', 'ESTP', 'ESFP'];
    },
    twoFactorSummaries() {
      return ['user', 'expert', 'admin'].map((role) => {
        const items = this.accounts.filter((account) => account.role === role);
        return {
          role,
          label: `${role.charAt(0).toUpperCase()}${role.slice(1)} accounts`,
          total: items.length,
          enabled: items.filter((account) => account.twoFactorEnabled).length,
        };
      });
    },
    tableColumns() {
      return [
        { key: 'fullName', label: 'Name', sortable: true },
        { key: 'email', label: 'Email', sortable: true },
        { key: 'role', label: 'Role', sortable: true },
        { key: 'status', label: 'Status' },
      ];
    },
    filteredAccounts() {
      return this.accounts.filter((account) => {
        const matchesRole = this.accountFilter === 'all'
          || account.role === this.accountFilter
          || (this.accountFilter === 'debug-enabled' && account.canAccessChatDebugPanels);
        const haystack = `${account.fullName} ${account.email}`.toLowerCase();
        const matchesSearch = !this.searchQuery || haystack.includes(this.searchQuery.toLowerCase());

        return matchesRole && matchesSearch;
      });
    },
    sortedAccounts() {
      const direction = this.sortState.direction === 'desc' ? -1 : 1;
      return [...this.filteredAccounts].sort((left, right) => {
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
    this.loadUsers();
  },
  methods: {
    normalizeAccount(item) {
      const firstName = item.first_name || '';
      const lastName = item.last_name || '';
      const fullName = `${firstName} ${lastName}`.trim() || item.name || item.email;
      const registrationStatus = String(item.registration_status || '').toLowerCase();

      return {
        id: item.id,
        fullName,
        firstName,
        lastName,
        email: item.email,
        role: String(item.role || '').toLowerCase(),
        isActive: Boolean(item.is_active),
        registrationStatus,
        registrationConfirmed: registrationStatus === 'approved',
        twoFactorEnabled: Boolean(item.two_factor_enabled),
        profilingConsent: Boolean(item.ai_profiling_consent),
        gdprConsent: Boolean(item.gdpr_consent),
        canAccessChatDebugPanels: Boolean(item.can_access_chat_debug_panels),
        deletionRequested: Boolean(item.account_deletion_requested),
        profilingOptOutRequested: Boolean(item.profiling_opt_out_requested),
        manualMbti: item.manual_mbti || '',
        inferredMbti: item.inferred_mbti || '',
        effectiveMbti: item.effective_mbti || '',
        profileConfidence: item.profile_confidence,
        profileConfidenceLabel: typeof item.profile_confidence === 'number' ? `${Math.round(item.profile_confidence * 100)}%` : 'N/A',
        profileInteractionCount: Number(item.profile_interaction_count || 0),
      };
    },
    normalizeTrustedDevice(item) {
      return {
        id: item.id,
        createdAt: item.created_at,
        lastUsedAt: item.last_used_at,
        expiresAt: item.expires_at,
      };
    },
    applyAccountUpdate(item) {
      const normalized = this.normalizeAccount(item);
      const index = this.accounts.findIndex((account) => account.id === normalized.id);

      if (index === -1) {
        this.accounts = [normalized, ...this.accounts];
        return normalized;
      }

      this.accounts = this.accounts.map((account) => (account.id === normalized.id ? normalized : account));
      return normalized;
    },
    async loadUsers() {
      this.isLoading = true;
      this.errorMessage = '';

      const response = await adminService.fetchUsers();

      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : response.data?.items || [];
        this.accounts = items.map((item) => this.normalizeAccount(item));
      } else {
        this.errorMessage = response.error?.message || 'Unable to load user accounts.';
      }

      this.isLoading = false;
    },
    async fetchUserDetails(userId) {
      const response = await adminService.viewUser(userId);

      if (!response.success) {
        this.errorMessage = response.error?.message || 'Unable to load user details.';
        return null;
      }

      return this.normalizeAccount(response.data);
    },
    async handleView(account) {
      this.successMessage = '';
      this.errorMessage = '';
      this.isSubmitting = true;

      const detailedAccount = await this.fetchUserDetails(account.id);
      this.isSubmitting = false;

      if (!detailedAccount) {
        return;
      }

      this.applyAccountUpdate({
        id: detailedAccount.id,
        first_name: detailedAccount.firstName,
        last_name: detailedAccount.lastName,
        email: detailedAccount.email,
        role: detailedAccount.role,
        is_active: detailedAccount.isActive,
        registration_status: detailedAccount.registrationStatus,
        two_factor_enabled: detailedAccount.twoFactorEnabled,
        ai_profiling_consent: detailedAccount.profilingConsent,
        gdpr_consent: detailedAccount.gdprConsent,
        can_access_chat_debug_panels: detailedAccount.canAccessChatDebugPanels,
        account_deletion_requested: detailedAccount.deletionRequested,
        profiling_opt_out_requested: detailedAccount.profilingOptOutRequested,
        manual_mbti: detailedAccount.manualMbti || null,
        inferred_mbti: detailedAccount.inferredMbti || null,
        effective_mbti: detailedAccount.effectiveMbti || null,
        profile_confidence: detailedAccount.profileConfidence,
        profile_interaction_count: detailedAccount.profileInteractionCount,
      });
      this.detailModal.account = detailedAccount;
      this.detailModal.visible = true;
      await this.loadTrustedDevices(detailedAccount.id);
    },
    closeDetailModal() {
      this.detailModal.visible = false;
      this.detailModal.account = null;
      this.detailModal.loadingDevices = false;
      this.detailModal.devicesError = '';
      this.detailModal.trustedDevices = [];
    },
    async loadTrustedDevices(userId) {
      this.detailModal.loadingDevices = true;
      this.detailModal.devicesError = '';
      this.detailModal.trustedDevices = [];

      const response = await adminService.fetchUserTrustedDevices(userId);
      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : [];
        this.detailModal.trustedDevices = items.map((item) => this.normalizeTrustedDevice(item));
      } else {
        this.detailModal.devicesError =
          response.error?.message || 'Unable to load remembered devices.';
      }

      this.detailModal.loadingDevices = false;
    },
    formatDateTime(value) {
      if (!value) {
        return 'N/A';
      }

      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return 'N/A';
      }

      return new Intl.DateTimeFormat(undefined, {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date);
    },
    async handleEdit(account) {
      this.successMessage = '';
      this.errorMessage = '';
      this.editModal.errorMessage = '';
      this.editErrors = {};
      this.isSubmitting = true;

      const detailedAccount = await this.fetchUserDetails(account.id);
      this.isSubmitting = false;

      if (!detailedAccount) {
        return;
      }

      this.editForm = {
        id: detailedAccount.id,
        first_name: detailedAccount.firstName,
        last_name: detailedAccount.lastName,
        email: detailedAccount.email,
        role: detailedAccount.role,
        is_active: detailedAccount.isActive,
        two_factor_enabled: detailedAccount.twoFactorEnabled,
        ai_profiling_consent: detailedAccount.profilingConsent,
        gdpr_consent: detailedAccount.gdprConsent,
        can_access_chat_debug_panels: detailedAccount.canAccessChatDebugPanels,
        manual_mbti: detailedAccount.manualMbti,
        inferred_mbti: detailedAccount.inferredMbti,
      };
      this.editModal.visible = true;
    },
    closeEditModal() {
      this.editModal.visible = false;
      this.editModal.errorMessage = '';
      this.editForm = createEmptyEditForm();
      this.editErrors = {};
    },
    validateEditField(fieldName) {
      this.editErrors = validateField(fieldName, this.editForm, this.editErrors, EDIT_RULES);
    },
    validateEditForm() {
      this.editErrors = validateFields(Object.keys(EDIT_RULES), this.editForm, EDIT_RULES);
      return !Object.values(this.editErrors).some(Boolean);
    },
    toggleAccountFilter(filterValue) {
      this.accountFilter = this.accountFilter === filterValue ? 'all' : filterValue;
    },
    toggleActionMenu(accountId) {
      this.openActionMenuId = this.openActionMenuId === accountId ? null : accountId;
    },
    closeActionMenu() {
      this.openActionMenuId = null;
    },
    handleRowAction(action, account) {
      this.closeActionMenu();

      if (action === 'view') {
        this.handleView(account);
        return;
      }

      if (action === 'edit') {
        this.handleEdit(account);
        return;
      }

      if (action === 'reset-password') {
        this.openPasswordResetModal(account);
        return;
      }

      if (action === 'resend-credentials') {
        this.openResendCredentialsModal(account);
        return;
      }

      if (action === 'reset-2fa') {
        this.openTwoFactorResetModal(account);
        return;
      }

      if (action === 'deactivate') {
        this.openDeactivateModal(account);
      }
    },
    sortableValue(account, key) {
      if (key === 'role') {
        return String(account.role || '').toLowerCase();
      }

      return String(account[key] || '').toLowerCase();
    },
    handleSortChange(nextSort) {
      this.sortState = nextSort;
    },
    async submitEdit() {
      if (!this.editForm.id || !this.validateEditForm()) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';
      this.editModal.errorMessage = '';

      const response = await adminService.editUser(this.editForm.id, {
        first_name: this.editForm.first_name,
        last_name: this.editForm.last_name,
        email: this.editForm.email,
        role: this.editForm.role,
        is_active: this.editForm.is_active,
        two_factor_enabled: this.editForm.two_factor_enabled,
        ai_profiling_consent: this.editForm.ai_profiling_consent,
        gdpr_consent: this.editForm.gdpr_consent,
        can_access_chat_debug_panels: this.editForm.can_access_chat_debug_panels,
        manual_mbti: this.editForm.manual_mbti || null,
      });

      if (response.success) {
        const updatedAccount = this.applyAccountUpdate(response.data);
        this.successMessage = `${updatedAccount.fullName} was updated successfully.`;
        this.closeEditModal();
      } else {
        this.editModal.errorMessage = getServerErrorMessage(response.error, 'Unable to update the user.');
      }

      this.isSubmitting = false;
    },
    openDeactivateModal(account) {
      this.successMessage = '';
      this.errorMessage = '';
      this.deactivateModal.account = account;
      this.deactivateModal.visible = true;
    },
    closeDeactivateModal() {
      this.deactivateModal.visible = false;
      this.deactivateModal.account = null;
    },
    openPasswordResetModal(account) {
      this.successMessage = '';
      this.errorMessage = '';
      this.passwordResetModal.account = account;
      this.passwordResetModal.visible = true;
    },
    closePasswordResetModal() {
      this.passwordResetModal.visible = false;
      this.passwordResetModal.account = null;
    },
    openResendCredentialsModal(account) {
      this.successMessage = '';
      this.errorMessage = '';
      this.resendCredentialsModal.account = account;
      this.resendCredentialsModal.visible = true;
    },
    closeResendCredentialsModal() {
      this.resendCredentialsModal.visible = false;
      this.resendCredentialsModal.account = null;
    },
    openTwoFactorResetModal(account) {
      this.successMessage = '';
      this.errorMessage = '';
      this.twoFactorResetModal.account = account;
      this.twoFactorResetModal.visible = true;
    },
    closeTwoFactorResetModal() {
      this.twoFactorResetModal.visible = false;
      this.twoFactorResetModal.account = null;
    },
    async confirmDeactivate() {
      if (!this.deactivateModal.account) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.deactivateUser(this.deactivateModal.account.id);

      if (response.success) {
        const updatedAccount = this.applyAccountUpdate(response.data);
        this.pushSuccessToast(`${updatedAccount.fullName} was deactivated.`);
        this.closeDeactivateModal();
      } else {
        this.errorMessage = response.error?.message || 'Unable to deactivate the user.';
      }

      this.isSubmitting = false;
    },
    async confirmPasswordReset() {
      if (!this.passwordResetModal.account) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.resetUserPassword(this.passwordResetModal.account.id);

      if (response.success) {
        const generatedPassword = response.data?.generated_temporary_password;
        if (response.data?.credentials_email_triggered) {
          this.pushSuccessToast(
            `Password reset for ${this.passwordResetModal.account.fullName}. A new temporary password was sent by email.`
          );
        } else {
          this.pushWarningToast(
            `Password reset for ${this.passwordResetModal.account.fullName}. Share this temporary password manually: ${generatedPassword}`,
            { autohide: false }
          );
        }
        this.closePasswordResetModal();
      } else {
        this.errorMessage = response.error?.message || 'Unable to reset the user password.';
      }

      this.isSubmitting = false;
    },
    async confirmResendCredentials() {
      if (!this.resendCredentialsModal.account) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.resendUserCredentials(this.resendCredentialsModal.account.id);

      if (response.success) {
        const generatedPassword = response.data?.generated_temporary_password;
        if (response.data?.credentials_email_triggered) {
          this.pushSuccessToast(
            `Credentials reissued for ${this.resendCredentialsModal.account.fullName}. A new temporary password was sent by email.`
          );
        } else {
          this.pushWarningToast(
            `Credentials reissued for ${this.resendCredentialsModal.account.fullName}. Email delivery was not confirmed, so use this temporary password manually: ${generatedPassword}.`,
            { autohide: false }
          );
        }
        this.closeResendCredentialsModal();
      } else {
        this.errorMessage = response.error?.message || 'Unable to resend credentials.';
      }

      this.isSubmitting = false;
    },
    async confirmTwoFactorReset() {
      if (!this.twoFactorResetModal.account) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.resetUserTwoFactor(this.twoFactorResetModal.account.id);

      if (response.success) {
        await this.loadUsers();
        this.pushSuccessToast(`Two-factor authentication was reset for ${this.twoFactorResetModal.account.fullName}.`);
        this.closeTwoFactorResetModal();
      } else {
        this.errorMessage = response.error?.message || 'Unable to reset two-factor authentication.';
      }

      this.isSubmitting = false;
    },
    async handleRevokeTrustedDevice(deviceId) {
      if (!this.detailModal.account) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';
      this.detailModal.devicesError = '';

      const response = await adminService.revokeUserTrustedDevice(this.detailModal.account.id, deviceId);
      if (response.success) {
        this.detailModal.trustedDevices = this.detailModal.trustedDevices.filter((device) => device.id !== deviceId);
        this.pushInfoToast(`Remembered device revoked for ${this.detailModal.account.fullName}.`);
      } else {
        this.detailModal.devicesError =
          response.error?.message || 'Unable to revoke the remembered device.';
      }

      this.isSubmitting = false;
    },
    async handleRevokeAllTrustedDevices() {
      if (!this.detailModal.account) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';
      this.detailModal.devicesError = '';

      const response = await adminService.revokeAllUserTrustedDevices(this.detailModal.account.id);
      if (response.success) {
        this.detailModal.trustedDevices = [];
        this.pushInfoToast(`All remembered devices were revoked for ${this.detailModal.account.fullName}.`);
      } else {
        this.detailModal.devicesError =
          response.error?.message || 'Unable to revoke remembered devices.';
      }

      this.isSubmitting = false;
    },
  },
};
</script>
