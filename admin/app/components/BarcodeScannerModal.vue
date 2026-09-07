<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import {
  BrowserMultiFormatReader,
  BarcodeFormat,
  DecodeHintType
} from '@zxing/library'

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
const isCameraLoading = ref(false)
const cameraError = ref<string | null>(null)
const hasMultipleCameras = ref(false)
const availableDevices = ref<MediaDeviceInfo[]>([])
const selectedDeviceId = ref<string | undefined>(undefined)
const isTorchActive = ref(false)
const hasTorch = ref(false)
const manualCode = ref('')
const scannedSuccess = ref(false)

let codeReader: BrowserMultiFormatReader | null = null
let currentStream: MediaStream | null = null
let audioContext: AudioContext | null = null

// Web Audio API beep sound for feedback
function playBeep() {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
    if (!AudioCtx) return

    if (!audioContext || audioContext.state === 'closed') {
      audioContext = new AudioCtx()
    }
    if (audioContext.state === 'suspended') {
      audioContext.resume()
    }

    const osc = audioContext.createOscillator()
    const gain = audioContext.createGain()

    osc.type = 'sine'
    osc.frequency.setValueAtTime(1200, audioContext.currentTime)
    osc.frequency.exponentialRampToValueAtTime(1800, audioContext.currentTime + 0.12)

    gain.gain.setValueAtTime(0.3, audioContext.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.12)

    osc.connect(gain)
    gain.connect(audioContext.destination)

    osc.start()
    osc.stop(audioContext.currentTime + 0.12)
  } catch {
    // Ignore audio errors if blocked
  }
}

function vibrateDevice() {
  try {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate([100, 50, 100])
    }
  } catch {
    // Ignore
  }
}

async function listVideoInputDevices() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    const videoDevices = devices.filter(d => d.kind === 'videoinput')
    availableDevices.value = videoDevices
    hasMultipleCameras.value = videoDevices.length > 1

    // Prefer back/environment facing camera if available
    if (!selectedDeviceId.value && videoDevices.length > 0) {
      const backCam = videoDevices.find(d =>
        d.label.toLowerCase().includes('back') ||
        d.label.toLowerCase().includes('rear') ||
        d.label.toLowerCase().includes('environment')
      )
      selectedDeviceId.value = backCam ? backCam.deviceId : videoDevices[0].deviceId
    }
  } catch {
    // Ignore enumeration errors
  }
}

async function startScanner() {
  isCameraLoading.value = true
  cameraError.value = null
  scannedSuccess.value = false
  manualCode.value = ''

  await nextTick()

  try {
    if (!navigator?.mediaDevices?.getUserMedia) {
      throw new Error('Camera access is not supported on this device/browser.')
    }

    // List devices
    await listVideoInputDevices()

    // Initialize ZXing Reader with common retail barcode formats
    if (!codeReader) {
      const hints = new Map()
      const formats = [
        BarcodeFormat.EAN_13,
        BarcodeFormat.EAN_8,
        BarcodeFormat.UPC_A,
        BarcodeFormat.UPC_E,
        BarcodeFormat.CODE_128,
        BarcodeFormat.CODE_39,
        BarcodeFormat.ITF,
        BarcodeFormat.QR_CODE
      ]
      hints.set(DecodeHintType.POSSIBLE_FORMATS, formats)
      hints.set(DecodeHintType.TRY_HARDER, true)
      codeReader = new BrowserMultiFormatReader(hints)
    }

    const videoEl = videoRef.value
    if (!videoEl) {
      throw new Error('Video element not found')
    }

    const constraints: MediaStreamConstraints = {
      video: selectedDeviceId.value
        ? { deviceId: { exact: selectedDeviceId.value } }
        : {
            facingMode: { ideal: 'environment' },
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
      audio: false
    }

    // Request stream explicitly to check torch support & attach to reader
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia(constraints)
    } catch {
      stream = await navigator.mediaDevices.getUserMedia({
        video: selectedDeviceId.value
          ? { deviceId: { exact: selectedDeviceId.value } }
          : { facingMode: { ideal: 'environment' } },
        audio: false
      })
    }

    currentStream = stream

    // Check torch capabilities
    const track = stream.getVideoTracks()[0]
    if (track) {
      const capabilities = (track.getCapabilities && track.getCapabilities()) as any
      hasTorch.value = !!(capabilities && capabilities.torch)
    }

    // Start ZXing continuous decoding loop
    await codeReader.decodeFromStream(stream, videoEl, (result, err) => {
      if (result && !scannedSuccess.value) {
        const text = result.getText()
        if (text && text.trim()) {
          onCodeCaptured(text.trim())
        }
      }
    })

    isCameraLoading.value = false
  } catch (err: any) {
    console.error('Barcode scanner start error:', err)
    isCameraLoading.value = false
    cameraError.value = err?.message || 'Could not access camera. Please check permissions.'
  }
}

function stopScanner() {
  if (codeReader) {
    try {
      codeReader.reset()
    } catch {}
  }

  if (currentStream) {
    currentStream.getTracks().forEach(track => {
      try {
        track.stop()
      } catch {}
    })
    currentStream = null
  }

  if (videoRef.value) {
    videoRef.value.srcObject = null
  }

  isTorchActive.value = false
  hasTorch.value = false
}

function onCodeCaptured(code: string) {
  if (scannedSuccess.value) return
  scannedSuccess.value = true
  playBeep()
  vibrateDevice()

  // Small delay so user sees green flash reticle before closing
  setTimeout(() => {
    emit('scan', code)
    isOpen.value = false
  }, 400)
}

function submitManualCode() {
  const code = manualCode.value.trim()
  if (!code) return
  onCodeCaptured(code)
}

async function switchCamera() {
  if (availableDevices.value.length <= 1) return

  const currentIndex = availableDevices.value.findIndex(d => d.deviceId === selectedDeviceId.value)
  const nextIndex = (currentIndex + 1) % availableDevices.value.length
  selectedDeviceId.value = availableDevices.value[nextIndex].deviceId

  stopScanner()
  await startScanner()
}

async function toggleTorch() {
  if (!currentStream) return
  const track = currentStream.getVideoTracks()[0]
  if (!track) return

  try {
    const nextState = !isTorchActive.value
    await (track as any).applyConstraints({
      advanced: [{ torch: nextState }]
    })
    isTorchActive.value = nextState
  } catch (err) {
    console.warn('Torch toggle failed:', err)
  }
}

function handleClose() {
  stopScanner()
  isOpen.value = false
}

watch(isOpen, (newVal) => {
  if (newVal) {
    startScanner()
  } else {
    stopScanner()
  }
})

onMounted(() => {
  if (isOpen.value) {
    startScanner()
  }
})

onUnmounted(() => {
  stopScanner()
  if (audioContext && audioContext.state !== 'closed') {
    try {
      audioContext.close()
    } catch {}
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
              @click="startScanner"
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
