<script setup lang="ts">
const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'

if (import.meta.client) {
  window.location.href = `${posUrl}/auth/register`
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-(--ui-bg)">
    <UIcon name="i-lucide-loader" class="w-8 h-8 animate-spin text-emerald-500" />
  </div>
</template>
