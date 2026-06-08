<template>
  <div class="theme-shell">
    <aside class="theme-sidebar" :class="{ 'is-open': isSidebarOpen, 'is-collapsed': isSidebarCollapsed }" aria-label="Primary navigation">
      <div class="theme-sidebar__brand">
        <RouterLink class="theme-sidebar__brand-link" :to="navigation.dashboard">
          <span class="theme-sidebar__brand-mark"><BrandLogo variant="sidebar" /></span>
        </RouterLink>
      </div>

      <nav class="theme-sidebar__nav">
        <div class="theme-sidebar__section-label">Workspace</div>
        <RouterLink
          v-for="item in primaryNavigationItems"
          ref="sidebarLinks"
          :key="item.to"
          class="theme-sidebar__link"
          :to="item.to"
          :exact-active-class="'router-link-active'"
          :data-bs-title="showSidebarTooltips ? item.label : null"
          :data-bs-toggle="showSidebarTooltips ? 'tooltip' : null"
          data-bs-placement="right"
          @click="closeSidebar"
        >
          <span class="theme-sidebar__icon" aria-hidden="true">
            <ThemeIcon :name="item.icon" />
          </span>
          <span>{{ item.label }}</span>
          <span v-if="item.badge" class="badge rounded-pill text-bg-danger ms-auto">{{ item.badge }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div v-if="isSidebarOpen" class="theme-shell__backdrop" @click="closeSidebar"></div>

    <div class="theme-main">
      <header class="theme-topbar">
        <div class="theme-topbar__leading">
          <button class="theme-topbar__menu-toggle sidebar-toggle" type="button" @click="toggleSidebar" aria-label="Toggle navigation">
            <template v-if="isMobileViewport">
              <ThemeIcon name="menu-2" />
            </template>
            <ThemeIcon v-else :name="isSidebarCollapsed ? 'sidebar-expand' : 'sidebar-collapse'" />
          </button>

        </div>

        <div class="theme-topbar__actions">
          <ThemeModeSwitcher ref="themeSwitcher" @open-change="handleThemeSwitcherOpenChange" />
          <RouterLink class="theme-topbar__quicklink" :to="navigation.chats" aria-label="Chats">
            <ThemeIcon name="chat" />
            <span v-if="attentionCount > 0" class="badge rounded-pill text-bg-danger">{{ formattedAttentionCount }}</span>
          </RouterLink>
          <div ref="profileMenuRoot" class="theme-profile-menu">
            <button
              class="theme-profile-menu__toggle"
              type="button"
              :aria-expanded="isProfileMenuOpen ? 'true' : 'false'"
              aria-label="Open profile menu"
              @click.stop="toggleProfileMenu"
            >
              <span class="theme-profile-menu__avatar">
                <img :src="avatarPlaceholderUrl" alt="" />
              </span>
            </button>
            <div v-if="isProfileMenuOpen" class="theme-profile-menu__dropdown">
              <div class="theme-profile-menu__header">
                <strong class="theme-profile-menu__name">{{ currentUserDisplayName }}</strong>
                <span class="theme-profile-menu__email">{{ currentUserEmail }}</span>
              </div>
              <RouterLink class="theme-profile-menu__link" :to="navigation.dashboard" @click="closeProfileMenu">
                <ThemeIcon name="dashboard" />
                <span>Home</span>
              </RouterLink>
              <RouterLink class="theme-profile-menu__link" :to="navigation.settings" @click="closeProfileMenu">
                <ThemeIcon name="settings" />
                <span>User settings</span>
              </RouterLink>
              <div class="theme-profile-menu__footer">
                <button class="theme-profile-menu__link" type="button" :disabled="isLoggingOut" @click="handleProfileLogout">
                  <ThemeIcon name="logout" />
                  <span>{{ isLoggingOut ? 'Signing out...' : 'Logout' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main class="theme-content">
        <div class="theme-content__inner">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { nextTick } from 'vue';
import { RouterLink, RouterView } from 'vue-router';
import { Tooltip } from 'bootstrap';
import BrandLogo from '@/components/BrandLogo.vue';
import ThemeIcon from '@/components/ThemeIcon.vue';
import ThemeModeSwitcher from '@/components/ThemeModeSwitcher.vue';
import authService from '@/services/authService';
import chatService from '@/services/chatService';
import authStore from '@/store/authStore';

const avatarPlaceholderUrl = new URL(
  '../assets/images/avatar/avatar-placeholder.svg',
  import.meta.url,
).href;

export default {
  name: 'DashboardLayout',
  components: {
    RouterLink,
    RouterView,
    BrandLogo,
    ThemeIcon,
    ThemeModeSwitcher,
  },
  data() {
    return {
      isLoggingOut: false,
      attentionCount: 0,
      unreadPollingTimerId: null,
      isSidebarOpen: false,
      isSidebarCollapsed: false,
      isProfileMenuOpen: false,
      isMobileViewport: false,
      sidebarTooltipInstances: [],
      avatarPlaceholderUrl,
    };
  },
  computed: {
    currentRole() {
      return authStore.resolveRoleFromPayload(authStore.state.currentUser) || 'user';
    },
    currentUser() {
      return authStore.state.currentUser || {};
    },
    currentUserDisplayName() {
      const firstName = String(this.currentUser.first_name || '').trim();
      const lastName = String(this.currentUser.last_name || '').trim();
      const combined = `${firstName} ${lastName}`.trim();
      return combined || this.currentUser.name || this.currentUser.email || 'COOGNIS account';
    },
    currentUserEmail() {
      return this.currentUser.email || 'No email available';
    },
    navigation() {
      if (this.currentRole === 'expert') {
        return {
          dashboard: '/expert',
          chats: '/expert/chats',
          settings: '/expert/settings',
        };
      }

      return {
        dashboard: '/user',
        chats: '/user/chats',
        settings: '/user/settings',
      };
    },
    primaryNavigationItems() {
      if (this.currentRole === 'expert') {
        return [
          { to: '/expert', label: 'Overview', icon: 'dashboard' },
          { to: '/expert/chats', label: 'Conversations', icon: 'sessions', badge: this.formattedAttentionCountOrEmpty },
          { to: '/expert/chat', label: 'Live chat', icon: 'chat' },
        ];
      }

      return [
        { to: '/user', label: 'Home', icon: 'dashboard' },
        { to: '/user/chats', label: 'Conversations', icon: 'sessions', badge: this.formattedAttentionCountOrEmpty },
        { to: '/user/chat', label: 'Live chat', icon: 'chat' },
      ];
    },
    currentViewTitle() {
      const routeName = this.$route.name;
      const titles = {
        'user-dashboard': 'Overview',
        'user-chat': 'Live chat',
        'user-chat-sessions': 'Chat sessions',
        'user-settings': 'User settings',
        'expert-dashboard': 'Expert dashboard',
        'expert-chat': 'Live expert chat',
        'expert-chat-sessions': 'Assigned conversations',
        'expert-settings': 'Expert settings',
      };
      return titles[routeName] || 'Workspace';
    },
    formattedAttentionCount() {
      if (this.attentionCount > 99) {
        return '99+';
      }
      return String(this.attentionCount);
    },
    formattedAttentionCountOrEmpty() {
      return this.attentionCount > 0 ? this.formattedAttentionCount : '';
    },
    showSidebarTooltips() {
      return !this.isMobileViewport && this.isSidebarCollapsed;
    },
  },
  watch: {
    $route() {
      this.closeSidebar();
      this.closeProfileMenu();
      this.refreshSidebarTooltips();
    },
    isSidebarCollapsed() {
      this.refreshSidebarTooltips();
    },
    isMobileViewport() {
      this.refreshSidebarTooltips();
    },
  },
  created() {
    this.updateViewportFlags();
    this.loadUnreadSummary();
    this.startUnreadSummaryPolling();
  },
  mounted() {
    document.addEventListener('click', this.handleDocumentClick);
    window.addEventListener('resize', this.updateViewportFlags);
    this.refreshSidebarTooltips();
  },
  beforeUnmount() {
    this.stopUnreadSummaryPolling();
    document.removeEventListener('click', this.handleDocumentClick);
    window.removeEventListener('resize', this.updateViewportFlags);
    this.disposeSidebarTooltips();
  },
  methods: {
    updateViewportFlags() {
      this.isMobileViewport = window.matchMedia('(max-width: 991.98px)').matches;
    },
    disposeSidebarTooltips() {
      this.sidebarTooltipInstances.forEach((instance) => instance.dispose());
      this.sidebarTooltipInstances = [];
    },
    async refreshSidebarTooltips() {
      await nextTick();
      this.disposeSidebarTooltips();

      if (!this.showSidebarTooltips) {
        return;
      }

      const refs = this.$refs.sidebarLinks || [];
      const linkElements = (Array.isArray(refs) ? refs : [refs])
        .map((ref) => ref?.$el || ref)
        .filter(Boolean);

      this.sidebarTooltipInstances = linkElements
        .filter((element) => element?.getAttribute?.('data-bs-title'))
        .map((element) => new Tooltip(element, {
          placement: 'right',
          fallbackPlacements: [],
          offset: [0, 8],
          trigger: 'hover focus',
          container: 'body',
        }));
    },
    async loadUnreadSummary() {
      if (!['user', 'expert'].includes(this.currentRole)) {
        this.attentionCount = 0;
        return;
      }

      const response = await chatService.fetchUnreadSummary();
      this.attentionCount = response.success ? Number(response.data?.attention_count || 0) : 0;
    },
    startUnreadSummaryPolling() {
      this.stopUnreadSummaryPolling();
      this.unreadPollingTimerId = window.setInterval(() => {
        this.loadUnreadSummary();
      }, 10000);
    },
    stopUnreadSummaryPolling() {
      if (!this.unreadPollingTimerId) {
        return;
      }

      window.clearInterval(this.unreadPollingTimerId);
      this.unreadPollingTimerId = null;
    },
    toggleSidebar() {
      if (this.isMobileViewport) {
        this.isSidebarOpen = !this.isSidebarOpen;
        return;
      }

      this.isSidebarCollapsed = !this.isSidebarCollapsed;
    },
    closeSidebar() {
      if (!this.isMobileViewport) {
        return;
      }

      this.isSidebarOpen = false;
    },
    toggleProfileMenu() {
      if (!this.isProfileMenuOpen) {
        this.closeThemeMenu();
      }
      this.isProfileMenuOpen = !this.isProfileMenuOpen;
    },
    closeProfileMenu() {
      this.isProfileMenuOpen = false;
    },
    closeThemeMenu() {
      this.$refs.themeSwitcher?.closeMenu?.();
    },
    handleThemeSwitcherOpenChange(isOpen) {
      if (isOpen) {
        this.closeProfileMenu();
      }
    },
    handleDocumentClick(event) {
      if (!this.isProfileMenuOpen) {
        return;
      }

      if (this.$refs.profileMenuRoot?.contains(event.target)) {
        return;
      }

      this.closeProfileMenu();
    },
    async handleProfileLogout() {
      this.closeProfileMenu();
      await this.handleLogout();
    },
    async handleLogout() {
      if (this.isLoggingOut) {
        return;
      }

      this.isLoggingOut = true;

      const response = await authService.logout();

      authStore.clearAuth();
      this.isLoggingOut = false;

      if (!response.success) {
        this.$router.push('/login');
        return;
      }

      this.$router.push('/login');
    },
  },
};
</script>
