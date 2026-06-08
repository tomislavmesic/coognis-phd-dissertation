<template>
  <div class="default-layout">
    <header class="app-topbar">
      <div class="container py-3 d-flex align-items-center justify-content-between gap-3">
        <span class="app-brand">COOGNIS</span>
        <nav aria-label="Public navigation">
          <ul class="nav">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/login">Login</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/register">Register</RouterLink>
            </li>
          </ul>
        </nav>
      </div>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>

<script>
import { RouterLink, RouterView } from 'vue-router';

export default {
  name: 'PublicLayout',
  components: {
    RouterLink,
    RouterView,
  },
};
</script>
