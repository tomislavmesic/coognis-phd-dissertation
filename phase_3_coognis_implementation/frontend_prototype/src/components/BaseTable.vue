<template>
  <div class="base-table" :class="wrapperClass">
    <div v-if="caption || $slots.toolbar" class="base-table__toolbar">
      <p v-if="caption" class="text-body-secondary mb-0">{{ caption }}</p>
      <div v-if="$slots.toolbar" class="base-table__toolbar-actions">
        <slot name="toolbar"></slot>
      </div>
    </div>

    <div class="table-responsive">
      <table class="table align-middle mb-0" :class="tableClass">
        <thead v-if="columns.length">
          <tr>
            <th v-for="column in columns" :key="column.key" :class="column.headerClass">
              <button
                v-if="column.sortable"
                class="base-table__sort-button"
                type="button"
                @click="handleSort(column.key)"
              >
                <span>{{ column.label }}</span>
                <span v-if="sortKey === column.key" class="base-table__sort-indicator" aria-hidden="true">
                  <svg
                    v-if="sortDirection === 'asc'"
                    class="base-table__sort-icon"
                    viewBox="0 0 12 12"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M3 7.5L6 4.5L9 7.5"
                      stroke="currentColor"
                      stroke-width="1.75"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  <svg
                    v-else
                    class="base-table__sort-icon"
                    viewBox="0 0 12 12"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M3 4.5L6 7.5L9 4.5"
                      stroke="currentColor"
                      stroke-width="1.75"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </span>
              </button>
              <template v-else>
                {{ column.label }}
              </template>
            </th>
            <th
              v-if="$slots.actions"
              class="base-table__actions-header"
              :class="{ 'base-table__actions-header--icon-only': actionsMode === 'icon-only' }"
            >
              <span v-if="actionsMode !== 'icon-only'">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody v-if="rows.length">
          <tr v-for="(row, rowIndex) in rows" :key="row[rowKey] || rowIndex">
            <td v-for="column in columns" :key="`${rowIndex}-${column.key}`" :class="column.cellClass">
              <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]" :column="column">
                {{ row[column.key] }}
              </slot>
            </td>
            <td
              v-if="$slots.actions"
              class="base-table__actions"
              :class="{ 'base-table__actions--icon-only': actionsMode === 'icon-only' }"
            >
              <slot name="actions" :row="row"></slot>
            </td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr>
            <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="p-0 border-0">
              <slot name="empty">
                <div class="base-table__empty">No records available.</div>
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BaseTable',
  props: {
    columns: {
      type: Array,
      default() {
        return [];
      },
    },
    rows: {
      type: Array,
      default() {
        return [];
      },
    },
    rowKey: {
      type: String,
      default: 'id',
    },
    caption: {
      type: String,
      default: '',
    },
    tableClass: {
      type: [String, Array, Object],
      default: '',
    },
    wrapperClass: {
      type: [String, Array, Object],
      default: '',
    },
    sortKey: {
      type: String,
      default: '',
    },
    sortDirection: {
      type: String,
      default: 'asc',
    },
    actionsMode: {
      type: String,
      default: 'default',
    },
  },
  emits: ['sort-change'],
  methods: {
    handleSort(columnKey) {
      const nextDirection =
        this.sortKey === columnKey && this.sortDirection === 'asc' ? 'desc' : 'asc';
      this.$emit('sort-change', {
        key: columnKey,
        direction: nextDirection,
      });
    },
  },
};
</script>

<style scoped>
.base-table__sort-button {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: inherit;
}

.base-table__sort-button:hover {
  color: var(--bs-primary);
}

.base-table__sort-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.base-table__sort-icon {
  width: 0.9rem;
  height: 0.9rem;
}

.base-table__actions-header--icon-only,
.base-table__actions--icon-only {
  width: 2.5rem;
  min-width: 2.5rem;
  max-width: 2.5rem;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  text-align: right;
}
</style>
