<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const emit = defineEmits<{
  (e: 'scanned', code: string): void
  (e: 'close'): void
}>()

const toast = useToast()
const videoRef = ref<HTMLVideoElement | null>(null)

const {
  isCameraActive,
  isCameraLoading,
  hasTorch,
  isTorchActive,
  isNativeEngine,
  hasMultipleCameras,
  startScanner,
  stopScanner,
  toggleTorch,
  switchCamera,
  triggerAutofocus
} = useBarcodeScanner({
  cooldownMs: 1200,
  throttleMs: 100,
  playBeep: true,
  vibrate: true
})

onMounted(async () => {
  await nextTick()
  if (videoRef.value) {
    const success = await startScanner(videoRef.value, (code: string) => {
      emit('scanned', code)
    })
    if (!success) {
      toast.add({
        title: 'Camera Error',
        description: 'Could not access camera device',
        color: 'error'
      })
      emit('close')
    }
  }
})

onUnmounted(() => {
  stopScanner()
  if (videoRef.value) {
    videoRef.value.srcObject = null
  }
})

function handleClose() {
  stopScanner()
  emit('close')
}
</script>

<template>
  <div class="relative overflow-hidden rounded-xl border border-(--ui-border) bg-black aspect-video max-h-56 flex items-center justify-center">
    <!-- Camera Loading State -->
    <div
      v-if="isCameraLoading"
      class="absolute inset-0 bg-black/85 flex flex-col items-center justify-center gap-2 z-10 text-zinc-300"
    >
      <UIcon name="i-lucide-loader-2" class="size-6 animate-spin text-primary-400" />
      <span class="text-xs font-medium">Opening camera...</span>
    </div>

    <!-- Camera Controls Overlay -->
    <div class="absolute top-2.5 right-2.5 flex items-center gap-1.5 z-20">
      <span
        v-if="isNativeEngine"
        class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/80 backdrop-blur-md text-white border border-emerald-400/40 shadow-sm tracking-wider uppercase font-mono"
      >
        Fast ML
      </span>
      <button
        v-if="hasMultipleCameras"
        type="button"
        class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
        title="Switch Camera"
        @click="switchCamera"
      >
        <UIcon name="i-lucide-refresh-cw" class="size-4" />
      </button>
      <button
        v-if="hasTorch"
        type="button"
        class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
        :class="{ 'bg-amber-500! text-black! border-amber-400! shadow-amber-500/50': isTorchActive }"
        title="Toggle Flashlight"
        @click="toggleTorch"
      >
        <UIcon :name="isTorchActive ? 'i-lucide-zap' : 'i-lucide-zap-off'" class="size-4" />
      </button>
      <button
        type="button"
        class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
        title="Close Camera"
        @click="handleClose"
      >
        <UIcon name="i-lucide-x" class="size-4" />
      </button>
    </div>

    <!-- Video Feed -->
    <video
      ref="videoRef"
      class="w-full h-full object-cover cursor-pointer"
      autoplay
      playsinline
      muted
      title="Tap to focus"
      @click="triggerAutofocus"
    />

    <!-- Reticle Box with Focus Guide -->
    <div
      class="absolute inset-0 flex items-center justify-center pointer-events-auto cursor-pointer"
      title="Tap to focus"
      @click="triggerAutofocus"
    >
      <div class="w-3/4 h-1/2 border-2 border-dashed border-emerald-500 rounded-lg opacity-65 relative transition hover:opacity-100">
        <div
          class="absolute inset-x-0 h-0.5 bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]"
          style="top: 50%"
        />
        <span class="absolute -bottom-5 inset-x-0 text-center text-[10px] text-emerald-400 font-medium tracking-wide drop-shadow">
          Tap to Focus
        </span>
      </div>
    </div>
  </div>
</template>
