<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue?: boolean
  title?: string
  description?: string
  persistent?: boolean
  maxWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  title: '',
  description: '',
  persistent: true,
  maxWidth: 'max-w-lg'
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'close'): void
}>()

const isMobile = useMediaQuery('(max-width: 767px)')

const isOpen = computed({
  get: () => props.modelValue,
  set: (val: boolean) => {
    emit('update:modelValue', val)
    if (!val) emit('close')
  }
})

function handleBackdropClick() {
  if (!props.persistent) {
    isOpen.value = false
  }
}

function handleClose() {
  isOpen.value = false
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex"
      :class="isMobile ? 'items-end justify-center' : 'items-stretch justify-end'"
    >
      <Transition
        appear
        enter-active-class="transition-opacity duration-300 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          class="fixed inset-0 bg-black/70 backdrop-blur-xs"
          @click="handleBackdropClick"
        />
      </Transition>

      <Transition
        appear
        :enter-active-class="isMobile ? 'transition-transform duration-300 ease-out' : 'transition-transform duration-300 ease-out'"
        :enter-from-class="isMobile ? 'translate-y-full' : 'translate-x-full'"
        :enter-to-class="isMobile ? 'translate-y-0' : 'translate-x-0'"
        :leave-active-class="isMobile ? 'transition-transform duration-200 ease-in' : 'transition-transform duration-200 ease-in'"
        :leave-from-class="isMobile ? 'translate-y-0' : 'translate-x-0'"
        :leave-to-class="isMobile ? 'translate-y-full' : 'translate-x-full'"
      >
        <div
          class="relative z-10 bg-zinc-900 text-zinc-100 flex flex-col shadow-2xl transition-all"
          :class="[
            isMobile
              ? 'w-full max-w-full rounded-t-3xl border-t border-x border-zinc-800 max-h-[85vh] pb-safe'
              : `w-full ${maxWidth} h-screen max-h-screen rounded-l-3xl border-l border-zinc-800`
          ]"
        >
          <div v-if="isMobile" class="flex justify-center pt-2.5 pb-1 shrink-0">
            <div class="w-12 h-1.5 rounded-full bg-zinc-700 opacity-80" />
          </div>

          <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800/80 shrink-0">
            <div class="min-w-0 pr-3">
              <slot name="header">
                <h3 v-if="title" class="text-base font-bold text-white truncate">
                  {{ title }}
                </h3>
                <p v-if="description" class="text-xs text-zinc-400 truncate mt-0.5">
                  {{ description }}
                </p>
              </slot>
            </div>

            <button
              type="button"
              class="p-1.5 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition shrink-0 cursor-pointer"
              aria-label="Close dialog"
              @click="handleClose"
            >
              <UIcon name="i-lucide-x" class="size-5" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-5">
            <slot />
          </div>

          <div v-if="$slots.footer" class="px-6 py-4 border-t border-zinc-800/80 bg-zinc-950/40 shrink-0">
            <slot name="footer" />
          </div>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>
