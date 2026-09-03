<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isDev = import.meta.dev
const isStandalone = ref(true)
const isIos = ref(false)
const deferredPrompt = ref<any>(null)
const isInstalling = ref(false)
const bypassGate = ref(false)

const route = useRoute()
const isAuthRoute = computed(() => route.path.startsWith('/auth'))

const shouldShowGate = computed(() => {
  if (isAuthRoute.value) return false
  if (isStandalone.value) return false
  if (bypassGate.value) return false
  return true
})

onMounted(() => {
  if (import.meta.client) {
    const standaloneCheck =
      window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as any).standalone === true ||
      window.location.search.includes('standalone=true') ||
      route.query.standalone === 'true'

    isStandalone.value = standaloneCheck
    isIos.value = /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream

    const bypassed = sessionStorage.getItem('bypass_pwa_gate') === 'true' || localStorage.getItem('bypass_pwa_gate') === 'true'
    if (bypassed) {
      bypassGate.value = true
    }

    window.addEventListener('beforeinstallprompt', (e: Event) => {
      e.preventDefault()
      deferredPrompt.value = e
    })
  }
})

async function handleInstall() {
  if (deferredPrompt.value) {
    isInstalling.value = true
    try {
      deferredPrompt.value.prompt()
      const choice = await deferredPrompt.value.userChoice
      if (choice.outcome === 'accepted') {
        isStandalone.value = true
      }
    } finally {
      isInstalling.value = false
    }
  } else if (isIos.value) {
    alert('Tap the Share button at the bottom of Safari, then choose "Add to Home Screen".')
  } else {
    alert('Please install Kluda POS from your browser menu to use the terminal.')
  }
}

function handleBypass() {
  if (!isDev) return
  bypassGate.value = true
  if (import.meta.client) {
    sessionStorage.setItem('bypass_pwa_gate', 'true')
  }
}
</script>

<template>
  <ClientOnly>
    <div
      v-if="shouldShowGate"
      class="fixed inset-0 z-[999999] flex flex-col items-center justify-center bg-zinc-950 text-white p-6 sm:p-10 select-none overflow-y-auto"
    >
      <div class="w-full max-w-sm flex flex-col items-center text-center gap-6">
        <div class="w-20 h-20 rounded-3xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-2xl shadow-emerald-500/20">
          <UIcon name="i-lucide-smartphone" class="w-10 h-10" />
        </div>

        <div class="flex flex-col items-center gap-2">
          <span class="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold uppercase tracking-wider">
            Dedicated Register App
          </span>
          <h2 class="text-2xl font-black text-white tracking-tight">
            Install Kluda POS Terminal
          </h2>
          <p class="text-xs text-zinc-400 leading-relaxed max-w-xs">
            For 100% offline reliability, barcode scanner focus, and thermal receipt printer access, Kluda POS must be installed on this device.
          </p>
        </div>

        <div v-if="isIos" class="w-full p-4 rounded-2xl bg-zinc-900 border border-zinc-800 text-left space-y-2">
          <div class="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
            <UIcon name="i-lucide-share" class="w-4 h-4" />
            iOS Safari Instructions:
          </div>
          <ol class="text-[11px] text-zinc-300 space-y-1 pl-4 list-decimal leading-relaxed">
            <li>Tap the <strong>Share</strong> button at the bottom of Safari.</li>
            <li>Scroll down and tap <strong>Add to Home Screen</strong>.</li>
            <li>Launch <strong>Kluda POS</strong> from your home screen.</li>
          </ol>
        </div>

        <div class="w-full flex flex-col gap-3">
          <button
            type="button"
            class="w-full py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-sm font-bold text-zinc-950 transition-all shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 active:scale-[0.98]"
            :disabled="isInstalling"
            @click="handleInstall"
          >
            <UIcon name="i-lucide-download" class="w-4 h-4" />
            {{ isIos ? 'Show Install Guide' : 'Install Terminal App' }}
          </button>

          <button
            v-if="isDev"
            type="button"
            class="text-[11px] text-zinc-500 hover:text-zinc-300 transition-colors py-2"
            @click="handleBypass"
          >
            Continue in Browser Tab (Testing Mode)
          </button>
        </div>
      </div>
    </div>
  </ClientOnly>
</template>
