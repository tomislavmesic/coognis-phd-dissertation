<template>
  <div ref="wrapRef" class="base-table__actions-menu-wrap">
    <button
      ref="triggerRef"
      class="base-table__actions-trigger"
      type="button"
      :disabled="disabled"
      :aria-expanded="open ? 'true' : 'false'"
      aria-haspopup="menu"
      :aria-label="label"
      @click.stop="$emit('toggle')"
    >
      <ThemeIcon name="dots-vertical" />
    </button>

    <Teleport to="body">
      <div
        v-if="open"
        ref="menuRef"
        class="base-table__actions-menu"
        :style="menuStyle"
        role="menu"
        @click.stop
      >
        <slot />
      </div>
    </Teleport>
  </div>
</template>

<script>
import { nextTick } from 'vue';
import ThemeIcon from '@/components/ThemeIcon.vue';

export default {
  name: 'BaseTableActionsMenu',
  components: {
    ThemeIcon,
  },
  props: {
    open: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    label: {
      type: String,
      default: 'Open row actions',
    },
    minWidth: {
      type: Number,
      default: 160,
    },
  },
  emits: ['toggle', 'close'],
  data() {
    return {
      menuStyle: {
        top: '0px',
        left: '0px',
        minWidth: `${this.minWidth}px`,
      },
    };
  },
  watch: {
    open(nextValue) {
      if (nextValue) {
        this.bindListeners();
        this.$nextTick(() => {
          this.updatePosition();
        });
        return;
      }

      this.unbindListeners();
    },
  },
  beforeUnmount() {
    this.unbindListeners();
  },
  methods: {
    bindListeners() {
      window.addEventListener('resize', this.updatePosition);
      window.addEventListener('scroll', this.updatePosition, true);
      document.addEventListener('mousedown', this.handleDocumentPointer, true);
      document.addEventListener('keydown', this.handleKeydown);
    },
    unbindListeners() {
      window.removeEventListener('resize', this.updatePosition);
      window.removeEventListener('scroll', this.updatePosition, true);
      document.removeEventListener('mousedown', this.handleDocumentPointer, true);
      document.removeEventListener('keydown', this.handleKeydown);
    },
    handleDocumentPointer(event) {
      if (!this.open) {
        return;
      }

      const wrap = this.$refs.wrapRef;
      const menu = this.$refs.menuRef;

      if (wrap?.contains(event.target) || menu?.contains(event.target)) {
        return;
      }

      this.$emit('close');
    },
    handleKeydown(event) {
      if (event.key === 'Escape') {
        this.$emit('close');
      }
    },
    async updatePosition() {
      if (!this.open) {
        return;
      }

      await nextTick();

      const trigger = this.$refs.triggerRef;
      const menu = this.$refs.menuRef;
      if (!trigger || !menu) {
        return;
      }

      const triggerRect = trigger.getBoundingClientRect();
      const menuRect = menu.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const padding = 12;
      const gap = 6;

      const left = Math.max(
        padding,
        Math.min(triggerRect.right - Math.max(menuRect.width, this.minWidth), viewportWidth - menuRect.width - padding)
      );

      const fitsBelow = triggerRect.bottom + gap + menuRect.height <= viewportHeight - padding;
      const top = fitsBelow
        ? triggerRect.bottom + gap
        : Math.max(padding, triggerRect.top - menuRect.height - gap);

      this.menuStyle = {
        top: `${Math.round(top)}px`,
        left: `${Math.round(left)}px`,
        minWidth: `${this.minWidth}px`,
      };
    },
  },
};
</script>
