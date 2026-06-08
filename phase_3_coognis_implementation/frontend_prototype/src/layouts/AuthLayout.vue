<template>
  <div class="auth-theme-shell">
    <section class="auth-theme-shell__hero">
      <div class="auth-theme-shell__hero-top">
        <RouterLink class="auth-theme-shell__brand" to="/login">
          <span class="auth-theme-shell__brand-mark"><BrandLogo variant="sidebar" /></span>
          <span class="auth-theme-shell__brand-caption">Adaptive expert system</span>
        </RouterLink>
        <ThemeModeSwitcher />
      </div>

      <div class="auth-theme-shell__hero-copy">
        <p class="auth-theme-shell__eyebrow">Secure access</p>
        <h1 class="auth-theme-shell__headline">{{ headline }}</h1>
        <p class="auth-theme-shell__lede">{{ lede }}</p>
      </div>

      <div class="auth-theme-shell__feature-card">
        <div class="auth-theme-shell__feature-kicker">Why COOGNIS</div>
        <ul class="auth-theme-shell__feature-list">
          <li>Adaptive responses shaped by user psychological profiling signals.</li>
          <li>Expert handoff and routing when deeper support is needed.</li>
          <li>Privacy-aware consent and two-factor protected access paths.</li>
        </ul>
      </div>
    </section>

    <main class="auth-theme-shell__main">
      <div class="auth-theme-shell__panel" :class="panelClass">
        <div v-if="showPanelHeader" class="auth-theme-shell__panel-header">
          <p class="auth-theme-shell__panel-eyebrow">Authentication</p>
          <h2 class="auth-theme-shell__panel-title">{{ panelTitle }}</h2>
          <p class="auth-theme-shell__panel-subtitle">{{ panelSubtitle }}</p>
        </div>
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script>
import { RouterLink, RouterView } from 'vue-router';
import BrandLogo from '@/components/BrandLogo.vue';
import ThemeModeSwitcher from '@/components/ThemeModeSwitcher.vue';

export default {
  name: 'AuthLayout',
  components: {
    RouterLink,
    RouterView,
    BrandLogo,
    ThemeModeSwitcher,
  },
  data() {
    return {
      authPanelState: {
        hideHeader: false,
      },
    };
  },
  provide() {
    return {
      authPanelState: this.authPanelState,
    };
  },
  computed: {
    currentRouteName() {
      return this.$route.name || '';
    },
    showPanelHeader() {
      return !this.authPanelState.hideHeader;
    },
    headline() {
      if (this.currentRouteName === 'register') {
        return 'Request secure COOGNIS access.';
      }
      if (this.currentRouteName === 'reset-password') {
        return 'Choose a new password and restore access securely.';
      }
      if (this.currentRouteName === 'two-factor-verify') {
        return 'Complete verification before entering protected workspaces.';
      }
      return 'Continue into the COOGNIS workspace.';
    },
    lede() {
      if (this.currentRouteName === 'register') {
        return 'Register new users with the required consent signals so access can be approved and provisioned cleanly.';
      }
      if (this.currentRouteName === 'reset-password') {
        return 'Use the secure reset link from your email to replace the current password and return to the platform.';
      }
      if (this.currentRouteName === 'two-factor-verify') {
        return 'Protected routes remain locked until the current verification challenge is completed successfully.';
      }
      return 'Use your account credentials to enter user, expert, or admin areas with the current security requirements applied.';
    },
    panelTitle() {
      if (this.currentRouteName === 'register') {
        return 'Sign up for COOGNIS';
      }
      if (this.currentRouteName === 'reset-password') {
        return 'Reset password';
      }
      if (this.currentRouteName === 'two-factor-verify') {
        return 'Two-factor verification';
      }
      return 'Sign in';
    },
    panelSubtitle() {
      if (this.currentRouteName === 'register') {
        return 'Submit the registration details and required privacy consents for approval.';
      }
      if (this.currentRouteName === 'reset-password') {
        return 'Enter and confirm the new password for this account.';
      }
      if (this.currentRouteName === 'two-factor-verify') {
        return 'Enter the verification code to complete the sign-in sequence.';
      }
      return 'Enter your credentials to continue into COOGNIS.';
    },
    panelClass() {
      if (this.currentRouteName === 'register') {
        return 'auth-theme-shell__panel--register';
      }

      return 'auth-theme-shell__panel--default';
    },
  },
  watch: {
    currentRouteName() {
      this.authPanelState.hideHeader = false;
    },
  },
};
</script>
