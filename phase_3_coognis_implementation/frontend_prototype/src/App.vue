<template>
  <div class="app-shell">
    <router-view />
    <CookieConsentManager />
    <AppToastViewport />
  </div>
</template>

<script>
import AppToastViewport from '@/components/AppToastViewport.vue';
import CookieConsentManager from '@/components/CookieConsentManager.vue';

export default {
  name: 'AppRoot',
  components: {
    AppToastViewport,
    CookieConsentManager,
  },
};
</script>
