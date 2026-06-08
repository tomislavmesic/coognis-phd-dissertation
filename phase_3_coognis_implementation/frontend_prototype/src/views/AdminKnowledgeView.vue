<template>
  <section class="admin-knowledge">
    <BasePageHeader
      
      eyebrow="Admin"
      title="Knowledge management"
      description="Create, edit, filter, and remove UEX knowledge items linked to experts and domains."
    />

    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" />

    <BaseCard
      class="admin-knowledge__card"
      title="Knowledge items"
      subtitle="Manage published and draft UEX knowledge used for expert matching and guidance context."
      card-body-class="p-0"
    >
      <template #actions>
        <input
          v-model.trim="searchQuery"
          class="form-control"
          type="search"
          placeholder="Search by title, content, expert, or domain"
          aria-label="Search knowledge items"
        />
        <div class="d-flex flex-wrap flex-md-nowrap gap-2 justify-content-md-end ms-md-auto">
          <select v-model="domainFilter" class="form-select" aria-label="Filter knowledge by domain">
            <option value="all">All domains</option>
            <option v-for="domain in domains" :key="domain" :value="domain">{{ domain }}</option>
          </select>
          <select v-model="statusFilter" class="form-select" aria-label="Filter knowledge by status">
            <option value="all">All statuses</option>
            <option value="published">Published</option>
            <option value="draft">Draft</option>
          </select>
          <button
            class="btn btn-primary"
            type="button"
            aria-label="Create knowledge item"
            title="Create knowledge item"
            @click="openCreateModal"
          >
            <ThemeIcon name="create" />
          </button>
        </div>
      </template>

      <BaseLoadingState v-if="isLoading" label="Loading knowledge items..." state-class="py-5" />

      <BaseEmptyState
        v-else-if="!filteredItems.length"
        title="No matching knowledge items"
        :description="items.length ? 'Try adjusting the search or filters.' : 'No knowledge items are available yet.'"
        state-class="py-5"
      />

      <BaseTable
        v-else
        :columns="tableColumns"
        :rows="sortedItems"
        :sort-key="sortState.key"
        :sort-direction="sortState.direction"
        actions-mode="icon-only"
        table-class="admin-knowledge__table"
        @sort-change="handleSortChange"
      >
        <template #cell-title="{ row }">
          <div class="admin-knowledge__title">
            <strong>{{ row.title }}</strong>
            <small class="text-body-secondary">{{ row.preview }}</small>
          </div>
        </template>
        <template #cell-domain="{ value }">
          <span class="badge text-bg-light">{{ value }}</span>
        </template>
        <template #cell-status="{ value }">
          <span class="badge text-capitalize" :class="value === 'published' ? 'text-bg-success' : 'text-bg-secondary'">
            {{ value }}
          </span>
        </template>
        <template #cell-expert="{ value }">
          {{ value || 'Unassigned' }}
        </template>
        <template #cell-createdAt="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
        <template #actions="{ row }">
          <BaseTableActionsMenu
            :open="openActionMenuId === row.id"
            :disabled="isSubmitting"
            label="Open knowledge item actions"
            @toggle="toggleActionMenu(row.id)"
            @close="closeActionMenu"
          >
              <button
                class="base-table__actions-item"
                type="button"
                role="menuitem"
                :disabled="isSubmitting"
                @click="handleRowAction('edit', row)"
              >
                Edit
              </button>
              <button
                class="base-table__actions-item base-table__actions-item--danger"
                type="button"
                role="menuitem"
                :disabled="isSubmitting"
                @click="handleRowAction('delete', row)"
              >
                Delete
              </button>
          </BaseTableActionsMenu>
        </template>
      </BaseTable>
    </BaseCard>

    <BaseModal
      :visible="editorModal.visible"
      :busy="isSubmitting"
      eyebrow="Knowledge"
      :title="editorModal.mode === 'create' ? 'Create knowledge item' : 'Edit knowledge item'"
      modal-id="admin-knowledge-editor-modal"
      dialog-class="modal-dialog-centered modal-lg"
      @close="closeEditorModal"
    >
      <BaseAlert v-if="editorModal.errorMessage" variant="danger" :message="editorModal.errorMessage" />

      <form id="admin-knowledge-form" class="row g-3" novalidate @submit.prevent="submitKnowledge">
        <div class="col-12">
          <label class="form-label" for="knowledge-title">Title</label>
          <input
            id="knowledge-title"
            v-model.trim="form.title"
            class="form-control"
            :class="{ 'is-invalid': formErrors.title }"
            type="text"
            :disabled="isSubmitting"
          />
          <div v-if="formErrors.title" class="invalid-feedback d-block">{{ formErrors.title }}</div>
        </div>

        <div class="col-md-6">
          <label class="form-label" for="knowledge-domain">Domain</label>
          <select
            id="knowledge-domain"
            v-model="form.domain_code"
            class="form-select"
            :class="{ 'is-invalid': formErrors.domain_code }"
            :disabled="isSubmitting"
          >
            <option value="">Select domain</option>
            <option v-for="domain in domains" :key="domain" :value="domain">{{ domain }}</option>
          </select>
          <div v-if="formErrors.domain_code" class="invalid-feedback d-block">{{ formErrors.domain_code }}</div>
        </div>

        <div class="col-md-6">
          <label class="form-label" for="knowledge-expert">Source expert</label>
          <select
            id="knowledge-expert"
            v-model="form.source_expert_id"
            class="form-select"
            :class="{ 'is-invalid': formErrors.source_expert_id }"
            :disabled="isSubmitting"
          >
            <option value="">Select expert</option>
            <option v-for="expert in experts" :key="expert.id" :value="String(expert.id)">
              {{ expert.name }}
            </option>
          </select>
          <div v-if="formErrors.source_expert_id" class="invalid-feedback d-block">{{ formErrors.source_expert_id }}</div>
        </div>

        <div class="col-md-6">
          <label class="form-label" for="knowledge-status">Status</label>
          <select id="knowledge-status" v-model="form.status" class="form-select" :disabled="isSubmitting">
            <option value="draft">Draft</option>
            <option value="published">Published</option>
          </select>
        </div>

        <div class="col-12">
          <label class="form-label" for="knowledge-content">Content</label>
          <textarea
            id="knowledge-content"
            v-model.trim="form.content"
            class="form-control"
            :class="{ 'is-invalid': formErrors.content }"
            rows="6"
            :disabled="isSubmitting"
          ></textarea>
          <div v-if="formErrors.content" class="invalid-feedback d-block">{{ formErrors.content }}</div>
        </div>
      </form>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeEditorModal">
          Cancel
        </button>
        <button class="btn btn-primary" type="submit" form="admin-knowledge-form" :disabled="isSubmitting">
          {{ isSubmitting ? 'Saving...' : editorModal.mode === 'create' ? 'Create item' : 'Save changes' }}
        </button>
      </template>
    </BaseModal>

    <BaseModal
      :visible="deleteModal.visible"
      :busy="isSubmitting"
      eyebrow="Knowledge"
      title="Delete knowledge item"
      modal-id="admin-knowledge-delete-modal"
      @close="closeDeleteModal"
    >
      <p v-if="deleteModal.item" class="mb-0">
        Delete <strong>{{ deleteModal.item.title }}</strong>? This removes the knowledge item from UEX matching and PAGE context.
      </p>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeDeleteModal">
          Cancel
        </button>
        <button class="btn btn-danger" type="button" :disabled="isSubmitting" @click="confirmDelete">
          {{ isSubmitting ? 'Deleting...' : 'Delete item' }}
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
  name: 'AdminKnowledgeView',
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
      statusFilter: 'all',
      sortState: {
        key: 'createdAt',
        direction: 'desc',
      },
      items: [],
      experts: [],
      domains: [],
      editorModal: {
        visible: false,
        mode: 'create',
        itemId: null,
        errorMessage: '',
      },
      deleteModal: {
        visible: false,
        item: null,
      },
      openActionMenuId: null,
      form: {
        title: '',
        domain_code: '',
        source_expert_id: '',
        status: 'draft',
        content: '',
      },
      formErrors: {},
    };
  },
  computed: {
    tableColumns() {
      return [
        { key: 'title', label: 'Knowledge item' },
        { key: 'domain', label: 'Domain', sortable: true },
        { key: 'status', label: 'Status', sortable: true },
        { key: 'expert', label: 'Source expert', sortable: true },
        { key: 'createdAt', label: 'Created at', sortable: true },
      ];
    },
    filteredItems() {
      const query = this.searchQuery.toLowerCase();
      return this.items.filter((item) => {
        const matchesDomain = this.domainFilter === 'all' || item.domain === this.domainFilter;
        const matchesStatus = this.statusFilter === 'all' || item.status === this.statusFilter;
        const matchesQuery =
          !query ||
          item.title.toLowerCase().includes(query) ||
          item.preview.toLowerCase().includes(query) ||
          (item.expert || '').toLowerCase().includes(query) ||
          item.domain.toLowerCase().includes(query);

        return matchesDomain && matchesStatus && matchesQuery;
      });
    },
    sortedItems() {
      const direction = this.sortState.direction === 'desc' ? -1 : 1;
      return [...this.filteredItems].sort((left, right) => {
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

      const [knowledgeResponse, expertResponse, domainResponse] = await Promise.all([
        adminService.fetchKnowledgeItems(),
        adminService.fetchExperts(),
        adminService.fetchDomains(),
      ]);

      if (knowledgeResponse.success) {
        const items = Array.isArray(knowledgeResponse.data) ? knowledgeResponse.data : knowledgeResponse.data?.items || [];
        this.items = items.map((item) => this.normalizeItem(item));
      } else {
        this.errorMessage = knowledgeResponse.error?.message || 'Unable to load knowledge items.';
      }

      if (expertResponse.success) {
        const experts = Array.isArray(expertResponse.data) ? expertResponse.data : expertResponse.data?.items || [];
        this.experts = experts.map((item) => ({
          id: item.id,
          name: item.name,
        }));
      }

      if (domainResponse.success) {
        const domains = Array.isArray(domainResponse.data) ? domainResponse.data : domainResponse.data?.items || [];
        this.domains = domains.map((item) => item.code);
      }

      this.isLoading = false;
    },
    normalizeItem(item) {
      return {
        id: item.id,
        title: item.title,
        preview: item.content.slice(0, 120),
        domain: item.domain_code,
        status: item.status,
        expert: item.source_expert_name,
        sourceExpertId: item.source_expert_id,
        content: item.content,
        createdAt: item.created_at,
      };
    },
    toggleActionMenu(itemId) {
      this.openActionMenuId = this.openActionMenuId === itemId ? null : itemId;
    },
    closeActionMenu() {
      this.openActionMenuId = null;
    },
    handleRowAction(action, item) {
      this.closeActionMenu();

      if (action === 'edit') {
        this.openEditModal(item);
        return;
      }

      if (action === 'delete') {
        this.openDeleteModal(item);
      }
    },
    resetForm() {
      this.form = {
        title: '',
        domain_code: '',
        source_expert_id: '',
        status: 'draft',
        content: '',
      };
      this.formErrors = {};
      this.editorModal.errorMessage = '';
    },
    openCreateModal() {
      this.resetForm();
      this.editorModal.visible = true;
      this.editorModal.mode = 'create';
      this.editorModal.itemId = null;
    },
    openEditModal(item) {
      this.resetForm();
      this.editorModal.visible = true;
      this.editorModal.mode = 'edit';
      this.editorModal.itemId = item.id;
      this.form = {
        title: item.title,
        domain_code: item.domain,
        source_expert_id: item.sourceExpertId ? String(item.sourceExpertId) : '',
        status: item.status,
        content: item.content,
      };
    },
    closeEditorModal() {
      if (this.isSubmitting) {
        return;
      }
      this.editorModal.visible = false;
    },
    openDeleteModal(item) {
      this.deleteModal.visible = true;
      this.deleteModal.item = item;
    },
    closeDeleteModal() {
      if (this.isSubmitting) {
        return;
      }
      this.deleteModal.visible = false;
      this.deleteModal.item = null;
    },
    validateForm() {
      const errors = {};

      if (!this.form.title) {
        errors.title = 'Title is required.';
      }
      if (!this.form.domain_code) {
        errors.domain_code = 'Domain is required.';
      }
      if (!this.form.source_expert_id) {
        errors.source_expert_id = 'Source expert is required.';
      }
      if (!this.form.content) {
        errors.content = 'Content is required.';
      }

      this.formErrors = errors;
      return !Object.keys(errors).length;
    },
    async submitKnowledge() {
      if (this.isSubmitting || !this.validateForm()) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';
      this.editorModal.errorMessage = '';

      const payload = {
        title: this.form.title,
        content: this.form.content,
        domain_code: this.form.domain_code,
        source_expert_id: Number(this.form.source_expert_id),
        status: this.form.status,
      };

      const response = this.editorModal.mode === 'create'
        ? await adminService.createKnowledgeItem(payload)
        : await adminService.updateKnowledgeItem(this.editorModal.itemId, payload);

      if (response.success) {
        this.successMessage = this.editorModal.mode === 'create'
          ? 'Knowledge item created.'
          : 'Knowledge item updated.';
        this.closeEditorModal();
        await this.loadData();
      } else {
        this.editorModal.errorMessage = response.error?.message || 'Unable to save knowledge item.';
      }

      this.isSubmitting = false;
    },
    async confirmDelete() {
      if (!this.deleteModal.item || this.isSubmitting) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.deleteKnowledgeItem(this.deleteModal.item.id);

      if (response.success) {
        this.successMessage = 'Knowledge item deleted.';
        this.closeDeleteModal();
        await this.loadData();
      } else {
        this.errorMessage = response.error?.message || 'Unable to delete knowledge item.';
      }

      this.isSubmitting = false;
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    sortableValue(item, key) {
      if (key === 'createdAt') {
        const time = new Date(item.createdAt).getTime();
        return Number.isNaN(time) ? 0 : time;
      }

      return String(item[key] || '').toLowerCase();
    },
    handleSortChange(nextSort) {
      this.sortState = nextSort;
    },
  },
};
</script>
