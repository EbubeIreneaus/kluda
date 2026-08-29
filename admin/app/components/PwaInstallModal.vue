<script setup lang="ts">
import { ref, onMounted } from 'vue'

const { $pwa } = useNuxtApp()

const isModalOpen = ref(false)
const isIOS = ref(false)
const isInstalled = ref(false)
const deferredPrompt = ref<any>(null)

function checkInstallState() {
  if (!import.meta.client) return

  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true ||
    document.referrer.includes('android-app://')

  if (isStandalone || ($pwa && $pwa.isPWAInstalled)) {
    isInstalled.value = true
    isModalOpen.value = false
    return
  }

  const userAgent = window.navigator.userAgent.toLowerCase()
  const isAppleMobile = /iphone|ipad|ipod/.test(userAgent)
  isIOS.value = isAppleMobile

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
      title="Install Kluda Admin"
    >
      <template #body>
        <div class="p-6 flex flex-col items-center text-center space-y-5">
          <div class="relative flex items-center justify-center w-20 h-20 rounded-2xl bg-zinc-950 border border-emerald-500/40 overflow-hidden shadow-xl shadow-emerald-500/20">
            <img src="/pwa-192x192.png" alt="Kluda Admin" class="w-full h-full object-cover" />
            <div class="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-zinc-900 flex items-center justify-center border border-zinc-700">
              <UIcon name="i-lucide-shield-check" class="w-3.5 h-3.5 text-emerald-400" />
            </div>
          </div>

          <div>
            <h3 class="text-xl font-bold tracking-tight text-white">Install Kluda Admin</h3>
            <p class="text-xs text-zinc-400 mt-1 max-w-xs leading-relaxed">
              Install the administrative console on your desktop or mobile device for quick dashboard access and operations.
            </p>
          </div>

          <div
            v-if="isIOS"
            class="w-full text-left bg-zinc-950 border border-zinc-800 rounded-xl p-4 space-y-3"
          >
            <p class="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
              <UIcon name="i-lucide-apple" class="w-4 h-4 text-emerald-400" />
              Follow these 2 steps to install on iOS:
            </p>
            <div class="space-y-2 text-xs text-zinc-400">
              <div class="flex items-start gap-2.5">
                <span class="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-[10px] shrink-0 mt-0.5">1</span>
                <span>Tap the <strong class="text-zinc-200">Share</strong> button <UIcon name="i-lucide-share" class="w-3.5 h-3.5 inline text-emerald-400 mx-0.5" /> in Safari's toolbar.</span>
              </div>
              <div class="flex items-start gap-2.5">
                <span class="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-[10px] shrink-0 mt-0.5">2</span>
                <span>Scroll down and select <strong class="text-zinc-200">"Add to Home Screen"</strong> <UIcon name="i-lucide-plus-square" class="w-3.5 h-3.5 inline text-emerald-400 mx-0.5" />.</span>
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
              Install Admin App
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

          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-medium border border-emerald-500/20">
            <UIcon name="i-lucide-shield" class="w-3 h-3" />
            Standalone secure operations console
          </div>
        </div>
      </template>
    </UModal>
  </ClientOnly>
</template>
