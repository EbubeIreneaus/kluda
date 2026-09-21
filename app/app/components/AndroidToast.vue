<script setup lang="ts">
import { useAndroidToast } from '~/composables/useAndroidToast'

const { toastState } = useAndroidToast()
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-250 ease-out"
      enter-from-class="opacity-0 translate-y-4 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-4 scale-95"
    >
      <div
        v-if="toastState.show"
        class="fixed bottom-24 sm:bottom-12 left-1/2 -translate-x-1/2 z-[999999] pointer-events-none select-none max-w-[92vw]"
      >
        <div class="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-zinc-900/95 dark:bg-zinc-800/95 text-zinc-100 text-xs font-medium shadow-2xl backdrop-blur-md border border-white/10 ring-1 ring-black/20">
          <UIcon
            v-if="toastState.icon"
            :name="toastState.icon"
            class="size-4 text-emerald-400 shrink-0"
          />
          <span class="tracking-wide whitespace-nowrap">{{ toastState.message }}</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
