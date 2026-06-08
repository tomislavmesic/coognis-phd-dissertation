import { createRouter, createWebHistory } from 'vue-router';
import AdminLayout from '@/layouts/AdminLayout.vue';
import AuthLayout from '@/layouts/AuthLayout.vue';
import DashboardLayout from '@/layouts/DashboardLayout.vue';
import PublicLayout from '@/layouts/PublicLayout.vue';
import authStore from '@/store/authStore';
import AdminDashboardView from '@/views/AdminDashboardView.vue';
import AdminChatSessionsView from '@/views/AdminChatSessionsView.vue';
import AdminConversationsView from '@/views/AdminConversationsView.vue';
import AdminDataRequestsView from '@/views/AdminDataRequestsView.vue';
import AdminExpertDomainsView from '@/views/AdminExpertDomainsView.vue';
import AdminGeneralSettingsView from '@/views/AdminGeneralSettingsView.vue';
import AdminKnowledgeView from '@/views/AdminKnowledgeView.vue';
import AdminModuleSettingsView from '@/views/AdminModuleSettingsView.vue';
import AdminRegistrationApprovalView from '@/views/AdminRegistrationApprovalView.vue';
import AdminSettingsView from '@/views/AdminSettingsView.vue';
import AdminUlmSourcesView from '@/views/AdminUlmSourcesView.vue';
import AdminUserCreationView from '@/views/AdminUserCreationView.vue';
import AdminUserManagementView from '@/views/AdminUserManagementView.vue';
import ChatInterfaceView from '@/views/ChatInterfaceView.vue';
import ExpertDashboardView from '@/views/ExpertDashboardView.vue';
import ExpertSettingsView from '@/views/ExpertSettingsView.vue';
import LoginView from '@/views/LoginView.vue';
import RegisterView from '@/views/RegisterView.vue';
import ResetPasswordView from '@/views/ResetPasswordView.vue';
import TwoFactorVerifyView from '@/views/TwoFactorVerifyView.vue';
import UserDashboardView from '@/views/UserDashboardView.vue';
import UserChatSessionsView from '@/views/UserChatSessionsView.vue';
import UserSettingsView from '@/views/UserSettingsView.vue';

const routes = [
  {
    path: '/',
    component: PublicLayout,
    meta: {
      requiresAuth: false,
      role: null,
      requires2FA: false,
      group: 'public',
    },
    children: [
      {
        path: '',
        redirect: '/user',
      },
    ],
  },
  {
    path: '/',
    component: AuthLayout,
    meta: {
      requiresAuth: false,
      role: null,
      requires2FA: false,
      group: 'public',
    },
    children: [
      {
        path: 'login',
        name: 'login',
        component: LoginView,
        meta: {
          requiresAuth: false,
          role: null,
          requires2FA: false,
          group: 'public',
        },
      },
      {
        path: 'register',
        name: 'register',
        component: RegisterView,
        meta: {
          requiresAuth: false,
          role: null,
          requires2FA: false,
          group: 'public',
        },
      },
      {
        path: 'two-factor',
        name: 'two-factor-verify',
        component: TwoFactorVerifyView,
        meta: {
          requiresAuth: true,
          role: null,
          requires2FA: true,
          group: 'public',
        },
      },
      {
        path: 'reset-password',
        name: 'reset-password',
        component: ResetPasswordView,
        meta: {
          requiresAuth: false,
          role: null,
          requires2FA: false,
          group: 'public',
        },
      },
    ],
  },
  {
    path: '/user',
    component: DashboardLayout,
    meta: {
      requiresAuth: true,
      role: 'user',
      requires2FA: true,
      group: 'user',
    },
    children: [
      {
        path: '',
        name: 'user-dashboard',
        component: UserDashboardView,
        meta: {
          requiresAuth: true,
          role: 'user',
          requires2FA: true,
          group: 'user',
        },
      },
      {
        path: 'settings',
        name: 'user-settings',
        component: UserSettingsView,
        meta: {
          requiresAuth: true,
          role: 'user',
          requires2FA: true,
          group: 'user',
        },
      },
      {
        path: 'privacy',
        redirect: { name: 'user-settings' },
        meta: {
          requiresAuth: true,
          role: 'user',
          requires2FA: true,
          group: 'user',
        },
      },
      {
        path: 'chat',
        name: 'user-chat',
        component: ChatInterfaceView,
        meta: {
          requiresAuth: true,
          role: 'user',
          requires2FA: true,
          group: 'user',
        },
      },
      {
        path: 'chats',
        name: 'user-chat-sessions',
        component: UserChatSessionsView,
        meta: {
          requiresAuth: true,
          role: 'user',
          requires2FA: true,
          group: 'user',
        },
      },
    ],
  },
  {
    path: '/expert',
    component: DashboardLayout,
    meta: {
      requiresAuth: true,
      role: 'expert',
      requires2FA: true,
      group: 'expert',
    },
    children: [
      {
        path: '',
        name: 'expert-dashboard',
        component: ExpertDashboardView,
        meta: {
          requiresAuth: true,
          role: 'expert',
          requires2FA: true,
          group: 'expert',
        },
      },
      {
        path: 'chat',
        name: 'expert-chat',
        component: ChatInterfaceView,
        meta: {
          requiresAuth: true,
          role: 'expert',
          requires2FA: true,
          group: 'expert',
        },
      },
      {
        path: 'chats',
        name: 'expert-chat-sessions',
        component: UserChatSessionsView,
        meta: {
          requiresAuth: true,
          role: 'expert',
          requires2FA: true,
          group: 'expert',
        },
      },
      {
        path: 'settings',
        name: 'expert-settings',
        component: ExpertSettingsView,
        meta: {
          requiresAuth: true,
          role: 'expert',
          requires2FA: true,
          group: 'expert',
        },
      },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: {
      requiresAuth: true,
      role: 'admin',
      requires2FA: true,
      group: 'admin',
    },
    children: [
      {
        path: '',
        name: 'admin-dashboard',
        component: AdminDashboardView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'registrations',
        name: 'admin-registrations',
        component: AdminRegistrationApprovalView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'users/create',
        name: 'admin-user-create',
        component: AdminUserCreationView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'users',
        name: 'admin-user-management',
        component: AdminUserManagementView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'settings',
        name: 'admin-settings',
        component: AdminSettingsView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'conversations',
        name: 'admin-conversations',
        component: AdminConversationsView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'chat-sessions',
        name: 'admin-chat-sessions',
        component: AdminChatSessionsView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'experts/domains',
        name: 'admin-expert-domains',
        component: AdminExpertDomainsView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'knowledge',
        name: 'admin-knowledge',
        component: AdminKnowledgeView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'ulm-sources',
        name: 'admin-ulm-sources',
        component: AdminUlmSourcesView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'module-settings',
        name: 'admin-module-settings',
        component: AdminModuleSettingsView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'general-settings',
        name: 'admin-general-settings',
        component: AdminGeneralSettingsView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
      {
        path: 'data-requests',
        name: 'admin-data-requests',
        component: AdminDataRequestsView,
        meta: {
          requiresAuth: true,
          role: 'admin',
          requires2FA: true,
          group: 'admin',
        },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/user',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

const DEV_AUTH_PREVIEWS_ENABLED = import.meta.env.DEV;

function getMetaValue(to, key, fallback = null) {
  const matchedRecord = [...to.matched].reverse().find((record) => record.meta && key in record.meta);

  if (matchedRecord) {
    return matchedRecord.meta[key];
  }

  return fallback;
}

router.beforeEach(async (to, from, next) => {
  void from;

  await authStore.initializeSession();

  const requiresAuth = Boolean(getMetaValue(to, 'requiresAuth', false));
  const requiredRole = getMetaValue(to, 'role', null);
  const isAuthenticated = authStore.state.isAuthenticated;
  const isAwaitingTwoFactor = Boolean(authStore.state.pendingTwoFactor);
  const currentRole = authStore.resolveRoleFromPayload(authStore.state.currentUser);
  const isAuthEntryRoute = ['login', 'register', 'two-factor-verify'].includes(to.name);
  const isRegisterPreview =
    DEV_AUTH_PREVIEWS_ENABLED && to.name === 'register' && to.query.preview === 'success';
  const isTwoFactorPreview =
    DEV_AUTH_PREVIEWS_ENABLED &&
    to.name === 'two-factor-verify' &&
    typeof to.query.preview === 'string';
  const isPreviewAuthRoute = isRegisterPreview || isTwoFactorPreview;

  if (to.name === 'two-factor-verify' && !isAwaitingTwoFactor && !isTwoFactorPreview) {
    next('/login');
    return;
  }

  if (isAwaitingTwoFactor && to.name !== 'two-factor-verify') {
    next('/two-factor');
    return;
  }

  if (!isAuthenticated && requiresAuth) {
    if (to.name === 'two-factor-verify' && isAwaitingTwoFactor) {
      next();
      return;
    }

    next('/login');
    return;
  }

  if (isAuthenticated && isAuthEntryRoute && !isAwaitingTwoFactor && !isPreviewAuthRoute) {
    next(authStore.resolveDashboardPath(currentRole));
    return;
  }

  if (requiredRole && !authStore.hasRequiredRole(requiredRole)) {
    next(authStore.resolveDashboardPath(currentRole));
    return;
  }

  next();
});

export default router;
