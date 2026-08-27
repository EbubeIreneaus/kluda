<script setup lang="ts">
import LandingNavbar from '~/components/landing/LandingNavbar.vue'
import LandingFooter from '~/components/landing/LandingFooter.vue'
</script>

<template>
  <div class="min-h-screen bg-(--ui-bg) text-(--ui-text) flex flex-col selection:bg-emerald-500 selection:text-black">
    <LandingNavbar />
    <main class="flex-1">
      <slot />
    </main>
    <LandingFooter />
  </div>
</template>
