<script setup lang="ts">
import { ref, onMounted } from 'vue'

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' },
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
    { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap' }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})

useSeoMeta({
  title: 'Kluda — Sell Faster, Track Everything',
  description: 'Mobile-first retail POS & inventory management. Scan barcodes, record sales, and manage your store from any device.'
})

const isAppReady = ref(true)
</script>

<template>
  <UApp>
    <VitePwaManifest />
    <PwaUpdateBanner />
    <PwaInstallModal />
    <NetworkStatusBar />
    <NuxtLoadingIndicator color="#10b981" :height="3" />

    <Transition name="splash-fade">
      <div
        v-if="!isAppReady"
        class="fixed inset-0 z-[99999] flex flex-col items-center justify-center bg-zinc-950 text-white select-none pointer-events-auto"
      >
        <div class="relative flex flex-col items-center">
          <div class="absolute -inset-4 rounded-full bg-emerald-500/20 blur-2xl animate-pulse" />

          <div class="relative flex items-center justify-center w-20 h-20 rounded-2xl bg-[#090d16] border border-emerald-500/40 text-white font-extrabold text-3xl shadow-xl shadow-emerald-500/30 ring-1 ring-white/20 mb-5 overflow-hidden">
            <img src="/kluda_icon.jpg" alt="Kluda" class="w-full h-full object-cover" />
          </div>

          <h1 class="text-2xl font-bold tracking-tight text-white">Kluda</h1>
          <p class="text-xs text-zinc-400 font-medium mt-1 tracking-wider uppercase">Sell Faster, Track Everything</p>

          <div class="w-40 h-1 bg-zinc-800 rounded-full overflow-hidden mt-8 relative">
            <div class="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full animate-splash-progress" />
          </div>
        </div>
      </div>
    </Transition>

    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>

<style>
.splash-fade-leave-active {
  transition: opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.splash-fade-leave-to {
  opacity: 0;
  transform: scale(1.02);
}

@keyframes splash-progress {
  0% {
    width: 0%;
    transform: translateX(-100%);
  }
  50% {
    width: 70%;
    transform: translateX(20%);
  }
  100% {
    width: 100%;
    transform: translateX(100%);
  }
}

.animate-splash-progress {
  animation: splash-progress 1.2s infinite ease-in-out;
}
</style>
