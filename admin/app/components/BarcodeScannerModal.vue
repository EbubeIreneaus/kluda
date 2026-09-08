<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

interface Props {
  modelValue?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'scan', code: string): void
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val)
})

const videoRef = ref<HTMLVideoElement | null>(null)
const manualCode = ref('')
const scannedSuccess = ref(false)

const {
  isCameraLoading,
  cameraError,
  hasMultipleCameras,
  hasTorch,
  isTorchActive,
  isNativeEngine,
  startScanner,
  stopScanner,
  toggleTorch,
  switchCamera
} = useBarcodeScanner({
  cooldownMs: 1500,
  throttleMs: 100,
  playBeep: true,
  vibrate: true
})

function onCodeCaptured(code: string) {
  if (scannedSuccess.value) return
  scannedSuccess.value = true

  // Short delay so user sees green flash reticle before modal closes
  setTimeout(() => {
    emit('scan', code)
    isOpen.value = false
    scannedSuccess.value = false
  }, 350)
}

function submitManualCode() {
  const code = manualCode.value.trim()
  if (!code) return
  onCodeCaptured(code)
}

async function initScanner() {
  scannedSuccess.value = false
  manualCode.value = ''
  await nextTick()
  if (videoRef.value) {
    await startScanner(videoRef.value, onCodeCaptured)
  }
}

function handleClose() {
  stopScanner()
  isOpen.value = false
}

watch(isOpen, (newVal) => {
  if (newVal) {
    initScanner()
  } else {
    stopScanner()
  }
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-[80] flex items-center justify-center p-4 sm:p-6"
    >
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
        @click="handleClose"
      />

      <!-- Scanner Dialog -->
      <div
        class="relative z-10 w-full max-w-md bg-zinc-950 border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-zinc-800/80 bg-zinc-900/80">
          <div class="flex items-center gap-2">
            <div class="size-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <UIcon name="i-lucide-scan-barcode" class="size-4" />
            </div>
            <div>
              <h3 class="text-sm font-semibold text-white">Scan Barcode</h3>
              <p class="text-[11px] text-zinc-400">Align barcode inside the camera box</p>
            </div>
          </div>

          <button
            type="button"
            class="size-8 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 flex items-center justify-center transition cursor-pointer"
            aria-label="Close scanner"
            @click="handleClose"
          >
            <UIcon name="i-lucide-x" class="size-4" />
          </button>
        </div>

        <!-- Camera Viewport Box -->
        <div class="relative bg-black aspect-4/3 w-full overflow-hidden flex items-center justify-center">
          <!-- Video feed -->
          <video
            ref="videoRef"
            class="w-full h-full object-cover"
            autoplay
            playsinline
            muted
          />

          <!-- Loading state -->
          <div
            v-if="isCameraLoading"
            class="absolute inset-0 bg-black/90 flex flex-col items-center justify-center gap-3 text-zinc-400 z-20"
          >
            <UIcon name="i-lucide-loader-2" class="size-8 animate-spin text-emerald-400" />
            <span class="text-xs font-medium text-zinc-300">Starting camera feed...</span>
          </div>

          <!-- Camera Error / Permission Denied -->
          <div
            v-if="cameraError"
            class="absolute inset-0 bg-zinc-950/95 p-6 flex flex-col items-center justify-center text-center gap-3 z-20"
          >
            <div class="size-12 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
              <UIcon name="i-lucide-camera-off" class="size-6" />
            </div>
            <div class="space-y-1">
              <h4 class="text-sm font-semibold text-zinc-200">Camera Unavailable</h4>
              <p class="text-xs text-zinc-400 max-w-xs">{{ cameraError }}</p>
            </div>
            <UButton
              label="Try Again"
              icon="i-lucide-refresh-cw"
              size="xs"
              color="primary"
              variant="outline"
              @click="initScanner"
            />
          </div>

          <!-- Reticle / Target Overlay -->
          <div
            v-if="!isCameraLoading && !cameraError"
            class="absolute inset-0 pointer-events-none flex items-center justify-center p-8"
          >
            <div
              class="relative w-full max-w-70 h-42.5 rounded-xl border-2 transition-colors duration-200"
              :class="scannedSuccess ? 'border-emerald-400 bg-emerald-500/20' : 'border-zinc-500/60'"
            >
              <!-- 4 Corner Focus Accents -->
              <span class="absolute -top-1 -left-1 size-4 border-t-3 border-l-3 rounded-tl-sm transition-colors" :class="scannedSuccess ? 'border-emerald-400' : 'border-emerald-500'" />
              <span class="absolute -top-1 -right-1 size-4 border-t-3 border-r-3 rounded-tr-sm transition-colors" :class="scannedSuccess ? 'border-emerald-400' : 'border-emerald-500'" />
              <span class="absolute -bottom-1 -left-1 size-4 border-b-3 border-l-3 rounded-bl-sm transition-colors" :class="scannedSuccess ? 'border-emerald-400' : 'border-emerald-500'" />
              <span class="absolute -bottom-1 -right-1 size-4 border-b-3 border-r-3 rounded-br-sm transition-colors" :class="scannedSuccess ? 'border-emerald-400' : 'border-emerald-500'" />

              <!-- Laser Scanning Line -->
              <div
                v-if="!scannedSuccess"
                class="absolute inset-x-2 h-0.5 bg-linear-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_12px_#10b981] animate-pulse"
                style="top: 50%;"
              />

              <!-- Success Checkmark Banner -->
              <div
                v-if="scannedSuccess"
                class="absolute inset-0 flex items-center justify-center bg-emerald-950/80 backdrop-blur-xs rounded-lg text-emerald-300 font-semibold text-xs gap-1.5 animate-in fade-in zoom-in-95"
              >
                <UIcon name="i-lucide-check-circle-2" class="size-5 text-emerald-400" />
                Barcode Captured!
              </div>
            </div>
          </div>

          <!-- Camera Controls Overlay (Top Right of Preview) -->
          <div class="absolute top-3 right-3 flex items-center gap-1.5 z-10">
            <!-- Flash / Torch Toggle -->
            <button
              v-if="hasTorch"
              type="button"
              class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-xs border border-white/10 text-white flex items-center justify-center transition cursor-pointer"
              :class="{ 'bg-amber-500/80! text-black! border-amber-400!': isTorchActive }"
              title="Toggle flashlight"
              @click="toggleTorch"
            >
              <UIcon :name="isTorchActive ? 'i-lucide-zap' : 'i-lucide-zap-off'" class="size-4" />
            </button>

            <!-- Flip / Switch Camera -->
            <button
              v-if="hasMultipleCameras"
              type="button"
              class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-xs border border-white/10 text-white flex items-center justify-center transition cursor-pointer"
              title="Switch camera"
              @click="switchCamera"
            >
              <UIcon name="i-lucide-switch-camera" class="size-4" />
            </button>
          </div>
        </div>

        <!-- Footer / Manual Input Fallback -->
        <div class="p-3 bg-zinc-900/90 border-t border-zinc-800 flex flex-col gap-2">
          <div class="flex items-center justify-between text-[11px] text-zinc-400">
            <span>Or enter code manually:</span>
            <span class="text-[10px] text-zinc-500 font-mono">USB scanners also supported</span>
          </div>

          <div class="flex items-center gap-2">
            <UInput
              v-model="manualCode"
              placeholder="e.g. 089686120110"
              size="sm"
              class="flex-1"
              autofocus
              @keydown.enter.prevent="submitManualCode"
            />
            <UButton
              label="Apply"
              icon="i-lucide-check"
              color="primary"
              size="sm"
              :disabled="!manualCode.trim()"
              @click="submitManualCode"
            />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
