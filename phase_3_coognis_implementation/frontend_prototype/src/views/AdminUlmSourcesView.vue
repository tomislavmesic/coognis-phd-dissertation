<template>
  <section class="admin-ulm-sources">
    <BasePageHeader
      
      eyebrow="Admin"
      title="ULM sources"
      description="Ingest external knowledge for ULM from pasted text, uploaded files, or URLs, and review indexed source coverage."
    />

    <BaseAlert v-if="successMessage" variant="success" :message="successMessage" />
    <BaseAlert v-if="errorMessage" variant="danger" :message="errorMessage" />

    <BaseCard
      class="admin-ulm-sources__card"
      title="Indexed sources"
      subtitle="Review what ULM can currently retrieve from external-source ingestion."
      card-body-class="p-0"
    >
      <template #actions>
        <input
          v-model.trim="searchQuery"
          class="form-control"
          type="search"
          placeholder="Search by title or source value"
          aria-label="Search ULM sources"
        />
        <div class="d-flex flex-wrap flex-md-nowrap gap-2 justify-content-md-end ms-md-auto">
          <select v-model="typeFilter" class="form-select" aria-label="Filter ULM sources by type">
            <option value="all">All types</option>
            <option value="document">Document</option>
            <option value="url">URL</option>
          </select>
          <select v-model="statusFilter" class="form-select" aria-label="Filter ULM sources by indexing status">
            <option value="all">All statuses</option>
            <option value="indexed">Indexed</option>
            <option value="queued">Queued</option>
            <option value="failed">Failed</option>
          </select>
          <button
            class="btn btn-primary"
            type="button"
            aria-label="Add ULM source"
            title="Add ULM source"
            @click="openIngestModal"
          >
            <ThemeIcon name="create" />
          </button>
        </div>
      </template>

      <BaseLoadingState v-if="isLoading" label="Loading ULM sources..." state-class="py-5" />

      <BaseEmptyState
        v-else-if="!filteredSources.length"
        title="No matching ULM sources"
        :description="sources.length ? 'Try adjusting the filters.' : 'No external sources have been ingested yet.'"
        state-class="py-5"
      />

      <BaseTable
        v-else
        :columns="tableColumns"
        :rows="sortedSources"
        :sort-key="sortState.key"
        :sort-direction="sortState.direction"
        actions-mode="icon-only"
        table-class="admin-ulm-sources__table"
        @sort-change="handleSortChange"
      >
        <template #cell-documents="{ row }">
          <div class="admin-ulm-sources__counts">
            <strong>{{ row.documentCount }}</strong>
            <small class="text-body-secondary">{{ row.indexedChunkCount }} indexed</small>
          </div>
        </template>
        <template #cell-title="{ row }">
          <div class="admin-ulm-sources__title">
            <strong>{{ row.title || fallbackTitle(row) }}</strong>
            <small class="text-body-secondary">{{ row.preview }}</small>
          </div>
        </template>
        <template #cell-type="{ value }">
          <span class="badge text-capitalize text-bg-light">{{ value }}</span>
        </template>
        <template #cell-status="{ value }">
          <span class="badge text-capitalize" :class="statusBadgeClass(value)">
            {{ value }}
          </span>
        </template>
        <template #cell-createdAt="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
        <template #cell-lastUpdatedAt="{ value }">
          <span class="text-nowrap">{{ formatDate(value) }}</span>
        </template>
        <template #actions="{ row }">
          <BaseTableActionsMenu
            :open="openActionMenuId === row.id"
            :disabled="isSubmitting"
            label="Open ULM source actions"
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
                View
              </button>
              <button
                v-if="row.type === 'url'"
                class="base-table__actions-item"
                type="button"
                role="menuitem"
                :disabled="isSubmitting"
                @click="handleRowAction('refresh', row)"
              >
                Refresh
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
      :visible="ingestModal.visible"
      :busy="isSubmitting"
      eyebrow="ULM"
      title="Ingest source"
      modal-id="admin-ulm-source-ingest-modal"
      dialog-class="modal-dialog-centered modal-lg"
      @close="closeIngestModal"
    >
      <BaseAlert
        variant="info"
        message="Text ingestion is available now. File upload supports .txt, .pdf, and .docx when the backend parser dependencies are installed."
      />

      <form id="admin-ulm-source-form" class="row g-3" novalidate @submit.prevent="submitSource">
        <div class="col-12">
          <label class="form-label" for="ulm-source-title">Title</label>
          <input
            id="ulm-source-title"
            v-model.trim="form.title"
            class="form-control"
            type="text"
            :disabled="isSubmitting"
            placeholder="Optional title for this source"
          />
        </div>

        <div class="col-12">
          <label class="form-label d-block">Source type</label>
          <div class="admin-ulm-sources__mode-switch">
            <label class="form-check">
              <input v-model="form.mode" class="form-check-input" type="radio" value="document" :disabled="isSubmitting" />
              <span class="form-check-label">Paste text</span>
            </label>
            <label class="form-check">
              <input v-model="form.mode" class="form-check-input" type="radio" value="file" :disabled="isSubmitting" />
              <span class="form-check-label">Upload file</span>
            </label>
            <label class="form-check">
              <input v-model="form.mode" class="form-check-input" type="radio" value="url" :disabled="isSubmitting" />
              <span class="form-check-label">Import URL</span>
            </label>
          </div>
        </div>

        <div v-if="form.mode === 'document'" class="col-12">
          <label class="form-label" for="ulm-source-document">Document text</label>
          <textarea
            id="ulm-source-document"
            v-model.trim="form.document"
            class="form-control"
            :class="{ 'is-invalid': formErrors.document }"
            rows="10"
            :disabled="isSubmitting"
            placeholder="Paste external text content for ULM ingestion"
          ></textarea>
          <div v-if="formErrors.document" class="invalid-feedback d-block">{{ formErrors.document }}</div>
        </div>

        <div v-else-if="form.mode === 'file'" class="col-12">
          <label class="form-label" for="ulm-source-file">Upload file</label>
          <input
            id="ulm-source-file"
            class="form-control"
            :class="{ 'is-invalid': formErrors.file }"
            type="file"
            accept=".txt,.pdf,.docx,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            :disabled="isSubmitting"
            @change="handleFileChange"
          />
          <div class="form-text">Supported formats: .txt, .pdf, .docx</div>
          <div v-if="selectedFileName" class="admin-ulm-sources__file-meta">
            Selected file: <strong>{{ selectedFileName }}</strong>
          </div>
          <div v-if="formErrors.file" class="invalid-feedback d-block">{{ formErrors.file }}</div>
        </div>

        <div v-else class="col-12">
          <label class="form-label" for="ulm-source-url">Source URL</label>
          <input
            id="ulm-source-url"
            v-model.trim="form.url"
            class="form-control"
            :class="{ 'is-invalid': formErrors.url }"
            type="url"
            :disabled="isSubmitting"
            placeholder="https://example.com/resource"
          />
          <div class="form-text">URL ingestion stores the external source and lets the backend fetch and index it.</div>
          <div v-if="formErrors.url" class="invalid-feedback d-block">{{ formErrors.url }}</div>
        </div>
      </form>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeIngestModal">
          Cancel
        </button>
        <button class="btn btn-primary" type="submit" form="admin-ulm-source-form" :disabled="isSubmitting">
          {{ isSubmitting ? 'Ingesting...' : ingestButtonLabel }}
        </button>
      </template>
    </BaseModal>

    <BaseModal
      :visible="detailModal.visible"
      :busy="isSubmitting"
      eyebrow="ULM"
      title="Source detail"
      modal-id="admin-ulm-source-detail-modal"
      dialog-class="modal-dialog-centered modal-xl"
      @close="closeDetailModal"
    >
      <BaseLoadingState v-if="detailModal.isLoading" label="Loading source detail..." state-class="py-4" />
      <BaseAlert v-else-if="detailModal.errorMessage" variant="danger" :message="detailModal.errorMessage" />

      <div v-else-if="detailModal.source" class="admin-ulm-sources__detail">
        <div class="admin-ulm-sources__detail-meta">
          <div>
            <span class="text-body-secondary">Title</span>
            <strong>{{ detailModal.source.title || fallbackTitle(detailModal.source) }}</strong>
          </div>
          <div>
            <span class="text-body-secondary">Type</span>
            <strong class="text-capitalize">{{ detailModal.source.type }}</strong>
          </div>
          <div>
            <span class="text-body-secondary">Status</span>
            <strong class="text-capitalize">{{ detailModal.source.status }}</strong>
          </div>
          <div>
            <span class="text-body-secondary">Chunks</span>
            <strong>{{ detailModal.source.documentCount }}</strong>
          </div>
          <div>
            <span class="text-body-secondary">Created</span>
            <strong class="text-nowrap">{{ formatDate(detailModal.source.createdAt) }}</strong>
          </div>
          <div>
            <span class="text-body-secondary">Last update</span>
            <strong class="text-nowrap">{{ formatDate(detailModal.source.lastUpdatedAt) }}</strong>
          </div>
        </div>

        <div class="admin-ulm-sources__detail-source">
          <span class="text-body-secondary">Source value</span>
          <a
            v-if="detailModal.source.type === 'url'"
            :href="detailModal.source.sourceValue"
            target="_blank"
            rel="noreferrer"
          >
            {{ detailModal.source.sourceValue }}
          </a>
          <code v-else>{{ detailModal.source.sourceValue }}</code>
        </div>

        <div class="admin-ulm-sources__chunk-list">
          <article v-for="chunk in detailModal.source.documents" :key="chunk.id" class="admin-ulm-sources__chunk">
            <header class="admin-ulm-sources__chunk-header">
              <div>
                <strong>{{ chunk.title || `Chunk ${chunk.chunkIndex + 1}` }}</strong>
                <small class="text-body-secondary">
                  Chunk {{ chunk.chunkIndex + 1 }}/{{ chunk.chunkCount }} • {{ chunk.status }}
                </small>
              </div>
            </header>
            <pre class="admin-ulm-sources__chunk-preview">{{ chunk.content || 'No chunk content stored.' }}</pre>
          </article>
        </div>
      </div>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting || detailModal.isLoading" @click="closeDetailModal">
          Close
        </button>
      </template>
    </BaseModal>

    <BaseModal
      :visible="deleteModal.visible"
      :busy="isSubmitting"
      eyebrow="ULM"
      title="Delete source"
      modal-id="admin-ulm-source-delete-modal"
      @close="closeDeleteModal"
    >
      <p v-if="deleteModal.source" class="mb-0">
        Delete <strong>{{ deleteModal.source.title || fallbackTitle(deleteModal.source) }}</strong>? This removes the source and its indexed chunks from ULM retrieval.
      </p>

      <template #footer>
        <button class="btn btn-outline-secondary" type="button" :disabled="isSubmitting" @click="closeDeleteModal">
          Cancel
        </button>
        <button class="btn btn-danger" type="button" :disabled="isSubmitting" @click="confirmDelete">
          {{ isSubmitting ? 'Deleting...' : 'Delete source' }}
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
  name: 'AdminUlmSourcesView',
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
      typeFilter: 'all',
      statusFilter: 'all',
      sortState: {
        key: 'lastUpdatedAt',
        direction: 'desc',
      },
      sources: [],
      form: {
        title: '',
        mode: 'document',
        document: '',
        url: '',
        file: null,
      },
      formErrors: {},
      deleteModal: {
        visible: false,
        source: null,
      },
      ingestModal: {
        visible: false,
      },
      detailModal: {
        visible: false,
        isLoading: false,
        errorMessage: '',
        source: null,
      },
      openActionMenuId: null,
    };
  },
  computed: {
    tableColumns() {
      return [
        { key: 'title', label: 'Source' },
        { key: 'type', label: 'Type', sortable: true },
        { key: 'status', label: 'Status', sortable: true },
        { key: 'documents', label: 'Chunks', sortable: true },
        { key: 'createdAt', label: 'Created at', sortable: true },
        { key: 'lastUpdatedAt', label: 'Last update', sortable: true },
      ];
    },
    filteredSources() {
      const query = this.searchQuery.toLowerCase();
      return this.sources.filter((source) => {
        const matchesType = this.typeFilter === 'all' || source.type === this.typeFilter;
        const matchesStatus = this.statusFilter === 'all' || source.status === this.statusFilter;
        const matchesQuery =
          !query ||
          (source.title || '').toLowerCase().includes(query) ||
          (source.preview || '').toLowerCase().includes(query) ||
          (source.sourceValue || '').toLowerCase().includes(query);

        return matchesType && matchesStatus && matchesQuery;
      });
    },
    sortedSources() {
      const direction = this.sortState.direction === 'desc' ? -1 : 1;
      return [...this.filteredSources].sort((left, right) => {
        const leftValue = this.sortableValue(left, this.sortState.key);
        const rightValue = this.sortableValue(right, this.sortState.key);

        if (leftValue === rightValue) {
          return left.id - right.id;
        }

        return leftValue > rightValue ? direction : -direction;
      });
    },
    selectedFileName() {
      return this.form.file?.name || '';
    },
    ingestButtonLabel() {
      if (this.form.mode === 'file') {
        return 'Upload and index';
      }
      if (this.form.mode === 'url') {
        return 'Import URL';
      }
      return 'Ingest document';
    },
  },
  created() {
    this.loadSources();
  },
  methods: {
    async loadSources() {
      this.isLoading = true;
      this.errorMessage = '';

      const response = await adminService.fetchUlmSources();

      if (response.success) {
        const items = Array.isArray(response.data) ? response.data : response.data?.items || [];
        this.sources = items.map(this.normalizeSource);
      } else {
        this.errorMessage = response.error?.message || 'Unable to load ULM sources.';
      }

      this.isLoading = false;
    },
    normalizeSource(item) {
      return {
        id: item.id,
        title: item.title || '',
        type: item.source_type,
        sourceValue: item.source_value,
        preview: this.buildPreview(item.source_value),
        status: item.indexing_status,
        documentCount: Number(item.document_count || 0),
        indexedChunkCount: Number(item.indexed_chunk_count || 0),
        createdAt: item.created_at,
        lastUpdatedAt: item.last_updated_at || item.created_at,
        documents: Array.isArray(item.documents)
          ? item.documents.map((document) => ({
              id: document.id,
              title: document.title || '',
              content: document.content || '',
              url: document.url || null,
              chunkIndex: Number(document.chunk_index || 0),
              chunkCount: Number(document.chunk_count || 1),
              status: document.indexing_status,
              createdAt: document.created_at,
            }))
          : [],
      };
    },
    buildPreview(value) {
      if (!value) {
        return 'No source value available.';
      }

      return value.length > 180 ? `${value.slice(0, 177)}...` : value;
    },
    fallbackTitle(source) {
      return source.type === 'url' ? 'Imported URL source' : 'Document source';
    },
    statusBadgeClass(status) {
      if (status === 'indexed') {
        return 'text-bg-success';
      }
      if (status === 'queued') {
        return 'text-bg-warning';
      }
      if (status === 'failed') {
        return 'text-bg-danger';
      }
      return 'text-bg-secondary';
    },
    toggleActionMenu(sourceId) {
      this.openActionMenuId = this.openActionMenuId === sourceId ? null : sourceId;
    },
    closeActionMenu() {
      this.openActionMenuId = null;
    },
    handleRowAction(action, source) {
      this.closeActionMenu();

      if (action === 'view') {
        this.openDetailModal(source);
        return;
      }

      if (action === 'refresh') {
        this.handleRefreshSource(source);
        return;
      }

      if (action === 'delete') {
        this.openDeleteModal(source);
      }
    },
    handleFileChange(event) {
      const [file] = event.target.files || [];
      this.form.file = file || null;
    },
    openIngestModal() {
      this.successMessage = '';
      this.errorMessage = '';
      this.resetForm();
      this.ingestModal.visible = true;
    },
    closeIngestModal() {
      if (this.isSubmitting) {
        return;
      }
      this.ingestModal.visible = false;
      this.resetForm();
    },
    validateForm() {
      const errors = {};

      if (this.form.mode === 'document' && !this.form.document.trim()) {
        errors.document = 'Document text is required.';
      }

      if (this.form.mode === 'url' && !this.form.url.trim()) {
        errors.url = 'A URL is required.';
      }

      if (this.form.mode === 'file') {
        if (!this.form.file) {
          errors.file = 'Choose a .txt, .pdf, or .docx file to upload.';
        } else {
          const lowerName = this.form.file.name.toLowerCase();
          const supportedExtensions = ['.txt', '.pdf', '.docx'];
          if (!supportedExtensions.some((extension) => lowerName.endsWith(extension))) {
            errors.file = 'Only .txt, .pdf, and .docx files are supported.';
          }
        }
      }

      this.formErrors = errors;
      return Object.keys(errors).length === 0;
    },
    resetForm() {
      this.form = {
        title: '',
        mode: 'document',
        document: '',
        url: '',
        file: null,
      };
      this.formErrors = {};
    },
    async submitSource() {
      this.successMessage = '';
      this.errorMessage = '';

      if (!this.validateForm()) {
        return;
      }

      this.isSubmitting = true;

      let response;

      if (this.form.mode === 'file') {
        response = await adminService.uploadUlmSource({
          title: this.form.title.trim() || null,
          file: this.form.file,
        });
      } else {
        response = await adminService.createUlmSource({
          title: this.form.title.trim() || null,
          document: this.form.mode === 'document' ? this.form.document.trim() : null,
          url: this.form.mode === 'url' ? this.form.url.trim() : null,
        });
      }

      if (!response.success) {
        this.errorMessage = response.error?.message || 'Unable to ingest the ULM source.';
        this.isSubmitting = false;
        return;
      }

      this.successMessage =
        this.form.mode === 'file'
          ? 'File uploaded and indexed for ULM.'
          : this.form.mode === 'url'
            ? 'URL source queued or indexed for ULM.'
            : 'Document ingested and indexed for ULM.';
      this.isSubmitting = false;
      this.closeIngestModal();
      await this.loadSources();
    },
    async openDetailModal(source) {
      this.detailModal.visible = true;
      this.detailModal.isLoading = true;
      this.detailModal.errorMessage = '';
      this.detailModal.source = null;

      const response = await adminService.fetchUlmSourceDetail(source.id);

      if (!response.success) {
        this.detailModal.errorMessage = response.error?.message || 'Unable to load the ULM source detail.';
        this.detailModal.isLoading = false;
        return;
      }

      this.detailModal.source = this.normalizeSource(response.data);
      this.detailModal.isLoading = false;
    },
    closeDetailModal() {
      if (this.isSubmitting) {
        return;
      }
      this.detailModal.visible = false;
      this.detailModal.isLoading = false;
      this.detailModal.errorMessage = '';
      this.detailModal.source = null;
    },
    async handleRefreshSource(source) {
      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.refreshUlmSource(source.id);

      if (!response.success) {
        this.errorMessage = response.error?.message || 'Unable to refresh the URL source.';
        this.isSubmitting = false;
        return;
      }

      this.successMessage = 'URL source refreshed and re-indexed.';
      await this.loadSources();
      if (this.detailModal.visible && this.detailModal.source?.id === source.id) {
        this.detailModal.source = this.normalizeSource(response.data);
      }
      this.isSubmitting = false;
    },
    openDeleteModal(source) {
      this.deleteModal.visible = true;
      this.deleteModal.source = source;
    },
    closeDeleteModal() {
      if (this.isSubmitting) {
        return;
      }
      this.deleteModal.visible = false;
      this.deleteModal.source = null;
    },
    async confirmDelete() {
      if (!this.deleteModal.source) {
        return;
      }

      this.isSubmitting = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await adminService.deleteUlmSource(this.deleteModal.source.id);

      if (!response.success) {
        this.errorMessage = response.error?.message || 'Unable to delete the ULM source.';
        this.isSubmitting = false;
        return;
      }

      this.successMessage = 'ULM source deleted.';
      this.closeDeleteModal();
      await this.loadSources();
      this.isSubmitting = false;
    },
    formatDate(value) {
      return formatDateTime(value);
    },
    sortableValue(source, key) {
      if (key === 'documents') {
        return source.documentCount;
      }

      if (key === 'createdAt' || key === 'lastUpdatedAt') {
        const time = new Date(source[key]).getTime();
        return Number.isNaN(time) ? 0 : time;
      }

      return String(source[key] || '').toLowerCase();
    },
    handleSortChange(nextSort) {
      this.sortState = nextSort;
    },
  },
};
</script>
