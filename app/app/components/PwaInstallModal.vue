<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
const { $pwa } = useNuxtApp()

const isModalOpen = ref(false)
const isIOS = ref(false)
const isInstalled = ref(false)
const deferredPrompt = ref<any>(null)

function checkInstallState() {
  if (!import.meta.client) return

  // 1. Check if already running in standalone PWA window
  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true ||
    document.referrer.includes('android-app://')

  if (isStandalone || ($pwa && $pwa.isPWAInstalled)) {
    isInstalled.value = true
    isModalOpen.value = false
    return
  }

  // 2. Detect real iOS Safari
  const userAgent = window.navigator.userAgent.toLowerCase()
  const isAppleMobile = /iphone|ipad|ipod/.test(userAgent)
  isIOS.value = isAppleMobile

  // On real iOS devices, show modal since iOS doesn't have beforeinstallprompt
  if (isAppleMobile) {
    setTimeout(() => {
      if (!isInstalled.value) {
        isModalOpen.value = true
      }
    }, 1200)
  }
}

onMounted(() => {
  checkInstallState()

  // Capture native Android / Chromium install prompt (ONLY show when PWA is truly ready)
  window.addEventListener('beforeinstallprompt', (e: any) => {
    e.preventDefault()
    deferredPrompt.value = e
    if (!isInstalled.value) {
      isModalOpen.value = true
    }
  })

  window.addEventListener('appinstalled', () => {
    isInstalled.value = true
    isModalOpen.value = false
    deferredPrompt.value = null
  })
})

async function handleInstall() {
  if (deferredPrompt.value) {
    deferredPrompt.value.prompt()
    const { outcome } = await deferredPrompt.value.userChoice
    if (outcome === 'accepted') {
      isModalOpen.value = false
      deferredPrompt.value = null
    }
  } else if ($pwa && typeof $pwa.install === 'function') {
    $pwa.install()
    isModalOpen.value = false
  }
}

function handleDismiss() {
  isModalOpen.value = false
}
</script>

<template>
  <ClientOnly>
    <UModal
      v-if="!isInstalled"
      v-model:open="isModalOpen"
      :dismissible="false"
      :close="{ color: 'neutral', variant: 'ghost' }"
      title="Install RetailPOS"
    >
      <template #body>
        <div class="p-6 flex flex-col items-center text-center space-y-5">
          <div class="relative flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-tr from-green-600 to-emerald-400 text-white font-extrabold text-3xl shadow-xl shadow-green-500/25 ring-1 ring-white/20">
            RP
            <div class="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-zinc-900 flex items-center justify-center border border-zinc-700">
              <UIcon name="i-lucide-download" class="w-3.5 h-3.5 text-green-400" />
            </div>
          </div>

          <div>
            <h3 class="text-xl font-bold text-highlighted">Install RetailPOS App</h3>
            <p class="text-xs text-muted mt-1 max-w-xs">
              Install our dedicated POS application for lightning-fast offline sales, barcode scanning, and receipt printing.
            </p>
          </div>

          <div
            v-if="isIOS"
            class="w-full text-left bg-accented/40 border border-default rounded-xl p-4 space-y-3"
          >
            <p class="text-xs font-semibold text-highlighted flex items-center gap-1.5">
              <UIcon name="i-lucide-apple" class="w-4 h-4 text-emerald-500" />
              Follow these 2 steps to install on iOS:
            </p>
            <div class="space-y-2 text-xs text-muted">
              <div class="flex items-start gap-2.5">
                <span class="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-500 font-bold text-[10px] shrink-0 mt-0.5">1</span>
                <span>Tap the <strong class="text-highlighted">Share</strong> button <UIcon name="i-lucide-share" class="w-3.5 h-3.5 inline text-emerald-500 mx-0.5" /> in Safari's bottom toolbar.</span>
              </div>
              <div class="flex items-start gap-2.5">
                <span class="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-500 font-bold text-[10px] shrink-0 mt-0.5">2</span>
                <span>Scroll down and tap <strong class="text-highlighted">"Add to Home Screen"</strong> <UIcon name="i-lucide-plus-square" class="w-3.5 h-3.5 inline text-emerald-500 mx-0.5" />.</span>
              </div>
            </div>
          </div>

          <div v-else class="w-full space-y-2">
            <UButton
              block
              size="lg"
              color="primary"
              icon="i-lucide-download"
              class="font-semibold"
              @click="handleInstall"
            >
              Install App Now
            </UButton>
            <UButton
              block
              size="sm"
              variant="ghost"
              color="neutral"
              @click="handleDismiss"
            >
              Not Now
            </UButton>
          </div>

          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[11px] font-medium border border-emerald-500/20">
            <UIcon name="i-lucide-wifi-off" class="w-3 h-3" />
            Works 100% offline once installed
          </div>
        </div>
      </template>
    </UModal>
  </ClientOnly>
</template>
