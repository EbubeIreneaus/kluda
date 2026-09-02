<script setup lang="ts">
import { computed } from 'vue'

const colorMode = useColorMode()
const themeColor = computed(() => (colorMode.value === 'dark' ? '#09090b' : '#f8fafc'))

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover' },
    { name: 'theme-color', content: themeColor },
    { name: 'apple-mobile-web-app-capable', content: 'yes' },
    { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
    { name: 'apple-mobile-web-app-title', content: 'Kluda Dashboard' },
    { name: 'mobile-web-app-capable', content: 'yes' }
  ],
  link: [
    { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})

const title = 'Kluda — Sell Faster, Track Everything | Modern Retail Platform'
const description = 'Turn any phone, tablet, or laptop into a fast, offline-ready retail POS with instant camera barcode scanning, customer ledgers, and real-time multi-register mesh.'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description,
  twitterCard: 'summary_large_image'
})
</script>

<template>
  <UApp>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
