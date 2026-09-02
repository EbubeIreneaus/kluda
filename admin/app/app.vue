<script setup lang="ts">
import { computed } from 'vue'

const colorMode = useColorMode()
const themeColor = computed(() => (colorMode.value === 'dark' ? '#09090b' : '#f8fafc'))

useHead({
  title: 'Kluda Admin',
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover' },
    { name: 'theme-color', content: themeColor },
    { name: 'apple-mobile-web-app-capable', content: 'yes' },
    { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
    { name: 'apple-mobile-web-app-title', content: 'Kluda Admin' },
    { name: 'mobile-web-app-capable', content: 'yes' }
  ],
  link: [
    { rel: 'icon', type: 'image/x-icon', href: '/kluda-icons/favicon.ico' },
    { rel: 'apple-touch-icon', href: '/kluda-icons/apple-touch-icon.png' }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})
</script>

<template>
  <UApp>
    <NuxtLayout>
      <VitePwaManifest />
      <NuxtPage />
    </NuxtLayout>
    <PwaInstallModal />
    <PwaUpdatePrompt />
  </UApp>
</template>
