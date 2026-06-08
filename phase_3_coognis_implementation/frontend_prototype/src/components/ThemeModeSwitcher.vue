<template>
  <div ref="root" class="theme-switcher">
    <button
      class="theme-switcher__button"
      type="button"
      :aria-expanded="isOpen ? 'true' : 'false'"
      aria-label="Toggle theme"
      @click.stop="toggleOpen"
    >
      <ThemeIcon :name="activeIconName" />
      <span class="theme-switcher__label">{{ activeLabel }}</span>
    </button>
    <ul v-show="isOpen" class="theme-switcher__menu" role="menu">
      <li v-for="option in options" :key="option.value">
        <button
          type="button"
          class="theme-switcher__option"
          :class="{ 'is-active': selectedTheme === option.value }"
          :aria-pressed="selectedTheme === option.value ? 'true' : 'false'"
          @click="selectTheme(option.value)"
        >
          <ThemeIcon :name="option.icon" />
          <span>{{ option.label }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<script>
import ThemeIcon from '@/components/ThemeIcon.vue';
import { getStoredTheme, setTheme } from '@/services/themeService';

export default {
  name: 'ThemeModeSwitcher',
  emits: ['open-change'],
  components: {
    ThemeIcon,
  },
  data() {
    return {
      selectedTheme: 'light',
      isOpen: false,
      options: [
        { value: 'light', label: 'Light', icon: 'sun' },
        { value: 'dark', label: 'Dark', icon: 'moon' },
        { value: 'auto', label: 'Auto', icon: 'auto' },
      ],
    };
  },
  computed: {
    activeIconName() {
      if (this.selectedTheme === 'dark') {
        return 'moon';
      }
      if (this.selectedTheme === 'auto') {
        return 'auto';
      }
      return 'sun';
    },
    activeLabel() {
      const currentOption = this.options.find((option) => option.value === this.selectedTheme);
      return currentOption ? currentOption.label : 'Theme';
    },
  },
  created() {
    this.selectedTheme = getStoredTheme() || 'auto';
  },
  mounted() {
    document.addEventListener('click', this.handleDocumentClick);
    document.addEventListener('keydown', this.handleEscape);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleDocumentClick);
    document.removeEventListener('keydown', this.handleEscape);
  },
  methods: {
    toggleOpen() {
      this.setOpen(!this.isOpen);
    },
    selectTheme(theme) {
      this.selectedTheme = theme;
      setTheme(theme);
      this.setOpen(false);
    },
    closeMenu() {
      this.setOpen(false);
    },
    setOpen(value) {
      const nextValue = Boolean(value);
      if (this.isOpen === nextValue) {
        return;
      }

      this.isOpen = nextValue;
      this.$emit('open-change', this.isOpen);
    },
    handleDocumentClick(event) {
      if (!this.isOpen) {
        return;
      }

      if (this.$refs.root?.contains(event.target)) {
        return;
      }

      this.setOpen(false);
    },
    handleEscape(event) {
      if (event.key !== 'Escape') {
        return;
      }

      this.setOpen(false);
    },
  },
};
</script>
