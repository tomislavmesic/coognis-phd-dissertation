<template>
  <svg
    class="theme-icon"
    xmlns="http://www.w3.org/2000/svg"
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'dashboard'">
      <path d="M4 4h6v6H4z" />
      <path d="M14 4h6v10h-6z" />
      <path d="M4 14h6v6H4z" />
      <path d="M14 18h6v2h-6z" />
    </template>
    <template v-else-if="name === 'chat'">
      <path d="M7 10h10" />
      <path d="M7 14h6" />
      <path d="M5 19l-1 0a2 2 0 0 1 -2 -2v-10a2 2 0 0 1 2 -2h16a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-10l-5 3z" />
    </template>
    <template v-else-if="name === 'sessions'">
      <path d="M4 5h16" />
      <path d="M4 12h16" />
      <path d="M4 19h10" />
    </template>
    <template v-else-if="name === 'settings'">
      <path d="M10.325 4.317c.426 -1.756 2.924 -1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543 -.94 3.31 .826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756 .426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543 -.826 3.31 -2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756 -2.924 1.756 -3.35 0a1.724 1.724 0 0 0 -2.573 -1.066c-1.543 .94 -3.31 -.826 -2.37 -2.37a1.724 1.724 0 0 0 -1.065 -2.572c-1.756 -.426 -1.756 -2.924 0 -3.35a1.724 1.724 0 0 0 1.066 -2.573c-.94 -1.543 .826 -3.31 2.37 -2.37c1 .608 2.296 .07 2.572 -1.065z" />
      <path d="M9 12a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" />
    </template>
    <template v-else-if="name === 'privacy'">
      <path d="M12 3l7 4v5c0 5 -3.5 7.5 -7 9c-3.5 -1.5 -7 -4 -7 -9V7z" />
      <path d="M10 11h4" />
      <path d="M12 9v4" />
    </template>
    <template v-else-if="name === 'approvals'">
      <path d="M9 12l2 2l4 -4" />
      <path d="M12 3l7 4v5c0 5 -3.5 7.5 -7 9c-3.5 -1.5 -7 -4 -7 -9V7z" />
    </template>
    <template v-else-if="name === 'users'">
      <path d="M9 7a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" />
      <path d="M17 21v-2a4 4 0 0 0 -4 -4h-2a4 4 0 0 0 -4 4v2" />
      <path d="M7 8H5a2 2 0 0 0 -2 2v0" />
    </template>
    <template v-else-if="name === 'create'">
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </template>
    <template v-else-if="name === 'expert'">
      <path d="M12 12a4 4 0 1 0 0 -8a4 4 0 0 0 0 8z" />
      <path d="M20 21a8 8 0 1 0 -16 0" />
    </template>
    <template v-else-if="name === 'knowledge'">
      <path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 0 -3 3z" />
      <path d="M8 4v16" />
    </template>
    <template v-else-if="name === 'ulm'">
      <path d="M6 4h9l5 5v11a2 2 0 0 1 -2 2H6a2 2 0 0 1 -2 -2V6a2 2 0 0 1 2 -2z" />
      <path d="M14 4v5h5" />
      <path d="M8 13h8" />
      <path d="M8 17h5" />
    </template>
    <template v-else-if="name === 'modules'">
      <path d="M4 7l8 -4l8 4l-8 4z" />
      <path d="M4 12l8 4l8 -4" />
      <path d="M4 17l8 4l8 -4" />
    </template>
    <template v-else-if="name === 'requests'">
      <path d="M8 6h11" />
      <path d="M8 12h8" />
      <path d="M8 18h6" />
      <path d="M4 6h.01" />
      <path d="M4 12h.01" />
      <path d="M4 18h.01" />
    </template>
    <template v-else-if="name === 'cleanup'">
      <path d="M4 7h16" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
      <path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" />
      <path d="M9 7V4h6v3" />
    </template>
    <template v-else-if="name === 'logout'">
      <path d="M14 8v-3a2 2 0 0 0 -2 -2h-5a2 2 0 0 0 -2 2v14a2 2 0 0 0 2 2h5a2 2 0 0 0 2 -2v-3" />
      <path d="M9 12h12l-3 -3" />
      <path d="M18 15l3 -3" />
    </template>
    <template v-else-if="name === 'sun'">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2.5" />
      <path d="M12 19.5V22" />
      <path d="M4.93 4.93l1.77 1.77" />
      <path d="M17.3 17.3l1.77 1.77" />
      <path d="M2 12h2.5" />
      <path d="M19.5 12H22" />
      <path d="M4.93 19.07l1.77 -1.77" />
      <path d="M17.3 6.7l1.77 -1.77" />
    </template>
    <template v-else-if="name === 'moon'">
      <path d="M12 3a6 6 0 0 0 9 9a9 9 0 1 1 -9 -9" />
      <path d="M19 3v4" />
      <path d="M21 5h-4" />
    </template>
    <template v-else-if="name === 'auto'">
      <path d="M12 3a9 9 0 1 0 0 18a9 9 0 0 0 0 -18" />
      <path d="M12 3v18" />
    </template>
    <template v-else-if="name === 'info'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8h.01" />
      <path d="M11 12h1v4h1" />
    </template>
    <template v-else-if="name === 'menu-2'">
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M4 6l16 0" />
      <path d="M4 12l16 0" />
      <path d="M4 18l16 0" />
    </template>
    <template v-else-if="name === 'dots-vertical'">
      <path d="M12 5m-1.25 0a1.25 1.25 0 1 0 2.5 0a1.25 1.25 0 1 0 -2.5 0" />
      <path d="M12 12m-1.25 0a1.25 1.25 0 1 0 2.5 0a1.25 1.25 0 1 0 -2.5 0" />
      <path d="M12 19m-1.25 0a1.25 1.25 0 1 0 2.5 0a1.25 1.25 0 1 0 -2.5 0" />
    </template>
    <template v-else-if="name === 'sidebar-collapse'">
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M4 12l10 0" />
      <path d="M4 12l4 4" />
      <path d="M4 12l4 -4" />
      <path d="M20 4l0 16" />
    </template>
    <template v-else-if="name === 'sidebar-expand'">
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M20 12l-10 0" />
      <path d="M20 12l-4 4" />
      <path d="M20 12l-4 -4" />
      <path d="M4 4l0 16" />
    </template>
    <template v-else>
      <circle cx="12" cy="12" r="8" />
    </template>
  </svg>
</template>

<script>
export default {
  name: 'ThemeIcon',
  props: {
    name: {
      type: String,
      required: true,
    },
  },
};
</script>
