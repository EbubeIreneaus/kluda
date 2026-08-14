<script setup lang="ts">
const { $pwa } = useNuxtApp()
const isUpdating = ref(false)

async function handleUpdate() {
  if (!$pwa) return
  isUpdating.value = true
  try {
    await $pwa.updateServiceWorker(true)
  } catch (err) {
    console.error('Failed to update service worker:', err)
  } finally {
    isUpdating.value = false
  }
}
</script>

<template>
  <ClientOnly>
    <Transition name="banner-slide">
      <div
        v-if="$pwa?.needRefresh"
        class="fixed top-3 left-1/2 -translate-x-1/2 z-[999999] w-[92%] max-w-lg shadow-2xl rounded-2xl border border-emerald-500/30 bg-zinc-900/95 backdrop-blur-md p-4 text-white ring-1 ring-emerald-500/20"
      >
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-green-500 to-emerald-400 flex items-center justify-center text-white shrink-0 shadow-md shadow-green-500/20 animate-pulse">
              <UIcon name="i-lucide-sparkles" class="w-5 h-5" />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-semibold text-white truncate">Update Available</p>
              <p class="text-xs text-zinc-400 truncate">A new version of RetailPOS is ready.</p>
            </div>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <UButton
              size="sm"
              color="primary"
              :loading="isUpdating"
              icon="i-lucide-refresh-cw"
              class="font-semibold shadow-md shadow-green-500/20"
              @click="handleUpdate"
            >
              Update Now
            </UButton>
          </div>
        </div>
      </div>
    </Transition>
  </ClientOnly>
</template>

<style scoped>
.banner-slide-enter-active,
.banner-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.banner-slide-enter-from,
.banner-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px) scale(0.95);
}
</style>
