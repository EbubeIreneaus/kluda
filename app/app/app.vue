<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

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
const auth = useAuthStore()
const { syncStaffCredentials, openSetPinModal } = usePinAuth()

onMounted(async () => {
  if (auth.isLoggedIn) {
    await syncStaffCredentials()
    checkPinStatus()
  }
})

watch(() => auth.isLoggedIn, async (loggedIn) => {
  if (loggedIn) {
    await syncStaffCredentials()
    checkPinStatus()
  }
})

function checkPinStatus() {
  if (
    auth.isLoggedIn &&
    auth.staff &&
    auth.staff.role !== 'owner' &&
    auth.staff.staff_id !== 'OWNER' &&
    !auth.staff.has_pin &&
    !(auth.staff as any).pin_hash &&
    import.meta.client &&
    localStorage.getItem('has_set_pin') !== 'true'
  ) {
    openSetPinModal()
  }
}
</script>

<template>
  <UApp>
    <VitePwaManifest />
    <PwaUpdateBanner />
    <PwaInstallModal />
    <PwaStandaloneGatekeeper />
    <PinAuthModal />
    <SetPinModal />
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
            <img src="/kluda-icons/192x192.png" alt="Kluda" class="w-full h-full object-cover" />
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
@keyframes splashProgress {
  0% { width: 0%; }
  50% { width: 70%; }
  100% { width: 100%; }
}
.animate-splash-progress {
  animation: splashProgress 1.2s ease-in-out infinite;
}
.splash-fade-enter-active,
.splash-fade-leave-active {
  transition: opacity 0.4s ease;
}
.splash-fade-enter-from,
.splash-fade-leave-to {
  opacity: 0;
}
</style>
