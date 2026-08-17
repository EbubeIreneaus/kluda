<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
const isOnline = ref(true)
const showRestoredBanner = ref(false)
let restoredTimer: any = null

function updateOnlineStatus() {
  if (!import.meta.client) return

  const currentlyOnline = window.navigator.onLine

  if (!currentlyOnline) {
    isOnline.value = false
    showRestoredBanner.value = false
    if (restoredTimer) clearTimeout(restoredTimer)
  } else if (!isOnline.value && currentlyOnline) {
    // Transitioned from offline to online
    isOnline.value = true
    showRestoredBanner.value = true
    if (restoredTimer) clearTimeout(restoredTimer)
    restoredTimer = setTimeout(() => {
      showRestoredBanner.value = false
    }, 3500)
  } else {
    isOnline.value = true
  }
}

onMounted(() => {
  if (import.meta.client) {
    isOnline.value = window.navigator.onLine
    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)
  }
})

onUnmounted(() => {
  if (import.meta.client) {
    window.removeEventListener('online', updateOnlineStatus)
    window.removeEventListener('offline', updateOnlineStatus)
    if (restoredTimer) clearTimeout(restoredTimer)
  }
})
</script>

<template>
  <ClientOnly>
    <Transition name="slide-up">
      <div
        v-if="!isOnline"
        class="fixed bottom-0 inset-x-0 z-[99999] h-[22px] bg-zinc-900 border-t border-zinc-800 text-zinc-300 text-[11px] font-medium flex items-center justify-center gap-1.5 select-none shadow-lg"
      >
        <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
        <span>You are offline &bull; Sales will save locally and sync when reconnected</span>
      </div>
    </Transition>

    <Transition name="slide-up">
      <div
        v-if="showRestoredBanner && isOnline"
        class="fixed bottom-0 inset-x-0 z-[99999] h-[22px] bg-emerald-600 text-white text-[11px] font-medium flex items-center justify-center gap-1.5 select-none shadow-lg"
      >
        <UIcon name="i-lucide-check-circle" class="w-3.5 h-3.5 text-white" />
        <span>Back online &bull; Syncing data...</span>
      </div>
    </Transition>
  </ClientOnly>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
