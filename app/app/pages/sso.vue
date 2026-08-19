<script setup lang="ts">
const route = useRoute()
navigateTo({ path: '/auth/sso', query: route.query })
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-(--ui-bg)">
    <p class="text-sm text-(--ui-text-muted)">Redirecting to SSO verification...</p>
  </div>
</template>
