<template>
  <div class="theme-shell">
    <aside class="theme-sidebar" :class="{ 'is-open': isSidebarOpen, 'is-collapsed': isSidebarCollapsed }" aria-label="Admin navigation">
      <div class="theme-sidebar__brand">
        <RouterLink class="theme-sidebar__brand-link" to="/admin">
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
        </RouterLink>

        <div class="theme-sidebar__section-label">Accounts</div>
        <RouterLink
          v-for="item in usersNavigationItems"
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
            <ThemeIcon :name="item.icon" cl/>
          </span>
          <span>{{ item.label }}</span>
          <span v-if="item.badgeCount" class="badge rounded-pill text-bg-danger">{{ item.badgeCount }}</span>
        </RouterLink>

        <div class="theme-sidebar__section-label">Knowledge</div>
        <RouterLink
          v-for="item in knowledgeNavigationItems"
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
        </RouterLink>

        <div class="theme-sidebar__section-label">Conversation</div>
        <RouterLink
          v-for="item in chatNavigationItems"
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
              <RouterLink class="theme-profile-menu__link" to="/admin" @click="closeProfileMenu">
                <ThemeIcon name="dashboard" />
                <span>Home</span>
              </RouterLink>
              <RouterLink class="theme-profile-menu__link" to="/admin/settings" @click="closeProfileMenu">
                <ThemeIcon name="settings" />
                <span>Admin settings</span>
              </RouterLink>
              <button class="theme-profile-menu__link" type="button" :disabled="isLoggingOut" @click="handleProfileLogout">
                <ThemeIcon name="logout" />
                <span>{{ isLoggingOut ? 'Signing out...' : 'Logout' }}</span>
              </button>
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
import adminService from '@/services/adminService';
import authService from '@/services/authService';
import authStore from '@/store/authStore';

const avatarPlaceholderUrl = new URL(
  '../assets/images/avatar/avatar-placeholder.svg',
  import.meta.url,
).href;

export default {
  name: 'AdminLayout',
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
      isSidebarOpen: false,
      isSidebarCollapsed: false,
      isProfileMenuOpen: false,
      isMobileViewport: false,
      sidebarTooltipInstances: [],
      avatarPlaceholderUrl,
      adminRequestCounts: {
        approvals: 0,
        privacyRequests: 0,
      },
    };
  },
  computed: {
    currentUser() {
      return authStore.state.currentUser || {};
    },
    currentUserDisplayName() {
      const firstName = String(this.currentUser.first_name || '').trim();
      const lastName = String(this.currentUser.last_name || '').trim();
      const combined = `${firstName} ${lastName}`.trim();
      return combined || this.currentUser.name || this.currentUser.email || 'COOGNIS admin';
    },
    currentUserEmail() {
      return this.currentUser.email || 'No email available';
    },
    primaryNavigationItems() {
      return [
        { to: '/admin', label: 'Overview', icon: 'dashboard' },
        { to: '/admin/module-settings', label: 'AI modules', icon: 'modules' },
        { to: '/admin/general-settings', label: 'General settings', icon: 'settings' },
      ];
    },
    usersNavigationItems() {
      return [
        { to: '/admin/users', label: 'Manage users', icon: 'users' },
        { to: '/admin/users/create', label: 'New account', icon: 'create' },
        {
          to: '/admin/registrations',
          label: 'Approvals',
          icon: 'approvals',
          badgeCount: this.adminRequestCounts.approvals,
        },
        {
          to: '/admin/data-requests',
          label: 'Privacy requests',
          icon: 'requests',
          badgeCount: this.adminRequestCounts.privacyRequests,
        },
      ];
    },
    knowledgeNavigationItems() {
      return [
        { to: '/admin/experts/domains', label: 'Experts', icon: 'expert' },
        { to: '/admin/knowledge', label: 'Knowledge', icon: 'knowledge' },
        { to: '/admin/ulm-sources', label: 'ULM sources', icon: 'ulm' },
      ];
    },
    chatNavigationItems() {
      return [
        { to: '/admin/conversations', label: 'Conversations', icon: 'chat' },
        { to: '/admin/chat-sessions', label: 'Chat cleanup', icon: 'cleanup' },
      ];
    },
    currentViewTitle() {
      const titles = {
        'admin-dashboard': 'Operations overview',
        'admin-registrations': 'Registration approvals',
        'admin-user-create': 'New account creation',
        'admin-user-management': 'User management',
        'admin-conversations': 'Conversations',
        'admin-chat-sessions': 'Chat cleanup',
        'admin-expert-domains': 'Expert domains',
        'admin-knowledge': 'Knowledge management',
        'admin-ulm-sources': 'ULM sources',
        'admin-module-settings': 'AI module settings',
        'admin-general-settings': 'General settings',
        'admin-settings': 'Admin settings',
        'admin-data-requests': 'Data requests',
      };
      return titles[this.$route.name] || 'Administration';
    },
    showSidebarTooltips() {
      return !this.isMobileViewport && this.isSidebarCollapsed;
    },
  },
  watch: {
    $route() {
      this.closeSidebar();
      this.closeProfileMenu();
      this.loadAdminRequestCounts();
      this.refreshSidebarTooltips();
    },
    isSidebarCollapsed() {
      this.refreshSidebarTooltips();
    },
    isMobileViewport() {
      this.refreshSidebarTooltips();
    },
  },
  mounted() {
    this.updateViewportFlags();
    this.loadAdminRequestCounts();
    document.addEventListener('click', this.handleDocumentClick);
    window.addEventListener('resize', this.updateViewportFlags);
    window.addEventListener('admin-request-counts:refresh', this.loadAdminRequestCounts);
    this.refreshSidebarTooltips();
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleDocumentClick);
    window.removeEventListener('resize', this.updateViewportFlags);
    window.removeEventListener('admin-request-counts:refresh', this.loadAdminRequestCounts);
    this.disposeSidebarTooltips();
  },
  methods: {
    async loadAdminRequestCounts() {
      const [dashboardResponse, dataRequestsResponse] = await Promise.all([
        adminService.fetchDashboardSummary(),
        adminService.fetchDataRequests(),
      ]);

      const nextCounts = {
        approvals: this.adminRequestCounts.approvals,
        privacyRequests: this.adminRequestCounts.privacyRequests,
      };

      if (dashboardResponse.success) {
        const registrations = Array.isArray(dashboardResponse.data?.pending_registrations)
          ? dashboardResponse.data.pending_registrations
          : [];
        nextCounts.approvals = registrations.length;
      }

      if (dataRequestsResponse.success) {
        const requests = Array.isArray(dataRequestsResponse.data)
          ? dataRequestsResponse.data
          : dataRequestsResponse.data?.items || [];
        nextCounts.privacyRequests = requests.filter((item) => item?.status === 'pending').length;
      }

      this.adminRequestCounts = nextCounts;
    },
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
