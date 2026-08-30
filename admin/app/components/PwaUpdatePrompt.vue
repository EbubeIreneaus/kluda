<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const { $pwa } = useNuxtApp()
const isUpdating = ref(false)
let checkInterval: any = null

async function checkForUpdates() {
  if (import.meta.client && 'serviceWorker' in navigator) {
    try {
      const reg = await navigator.serviceWorker.getRegistration()
      if (reg) {
        await reg.update()
      }
    } catch {
      // ignore
    }
  }
}

async function handleUpdate() {
  if (!$pwa) return
  isUpdating.value = true
  try {
    await $pwa.updateServiceWorker(true)
    setTimeout(() => {
      window.location.reload()
    }, 800)
  } catch {
    window.location.reload()
  } finally {
    isUpdating.value = false
  }
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible') {
    checkForUpdates()
  }
}

onMounted(() => {
  if (import.meta.client) {
    checkForUpdates()
    checkInterval = setInterval(checkForUpdates, 30000)
    window.addEventListener('focus', checkForUpdates)
    document.addEventListener('visibilitychange', onVisibilityChange)
  }
})

onUnmounted(() => {
  if (import.meta.client) {
    if (checkInterval) clearInterval(checkInterval)
    window.removeEventListener('focus', checkForUpdates)
    document.removeEventListener('visibilitychange', onVisibilityChange)
  }
})
</script>

<template>
  <ClientOnly>
    <div
      v-if="$pwa?.needRefresh"
      class="fixed top-4 right-4 z-[999999] bg-zinc-900/95 border border-emerald-500/40 shadow-2xl p-4 rounded-2xl flex items-center gap-3 text-xs max-w-sm backdrop-blur-xl animate-in fade-in slide-in-from-top-4 duration-300 ring-1 ring-emerald-500/20"
    >
      <div class="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
        <UIcon name="i-lucide-download-cloud" class="w-5 h-5 animate-bounce" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="font-bold text-zinc-100 truncate">New Version Ready</div>
        <div class="text-[11px] text-zinc-400 truncate">Click to reload with latest features.</div>
      </div>
      <UButton
        label="Update Now"
        size="xs"
        color="primary"
        :loading="isUpdating"
        icon="i-lucide-refresh-cw"
        class="font-semibold shadow-md shadow-emerald-500/20"
        @click="handleUpdate"
      />
    </div>
  </ClientOnly>
</template>
