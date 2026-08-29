<script setup lang="ts">
const { $pwa } = useNuxtApp()
</script>

<template>
  <ClientOnly>
    <div
      v-if="$pwa?.needRefresh"
      class="fixed bottom-4 right-4 z-50 bg-zinc-900 border border-emerald-500/30 shadow-2xl p-4 rounded-2xl flex items-center gap-3 text-xs max-w-sm backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-300"
    >
      <div class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
        <UIcon name="i-lucide-download-cloud" class="w-4 h-4" />
      </div>
      <div class="flex-1">
        <div class="font-semibold text-zinc-100">Update Available</div>
        <div class="text-[11px] text-zinc-400">A new version of Kluda Admin is ready.</div>
      </div>
      <UButton
        label="Reload"
        size="xs"
        color="primary"
        @click="$pwa?.updateServiceWorker()"
      />
    </div>
  </ClientOnly>
</template>
