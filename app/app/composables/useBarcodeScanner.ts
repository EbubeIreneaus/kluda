import { ref, onUnmounted, nextTick } from 'vue'
import {
  BrowserMultiFormatReader,
  BarcodeFormat,
  DecodeHintType
} from '@zxing/library'

export interface BarcodeScannerOptions {
  cooldownMs?: number // Cooldown before same barcode can trigger again (default: 1200ms)
  throttleMs?: number // Delay between scan attempts (default: 100ms)
  formats?: BarcodeFormat[] // Allowed ZXing formats
  playBeep?: boolean // Web Audio API beep chime on capture (default: true)
  vibrate?: boolean // Device vibration on capture (default: true)
}

export function useBarcodeScanner(options: BarcodeScannerOptions = {}) {
  const {
    cooldownMs = 1200,
    throttleMs = 100,
    playBeep = true,
    vibrate = true,
  } = options

  // State
  const isCameraActive = ref(false)
  const isCameraLoading = ref(false)
  const cameraError = ref<string | null>(null)
  const hasTorch = ref(false)
  const isTorchActive = ref(false)
  const isNativeEngine = ref(false)
  const hasMultipleCameras = ref(false)
  const availableDevices = ref<MediaDeviceInfo[]>([])
  const selectedDeviceId = ref<string | undefined>(undefined)

  // Internal references
  let codeReader: BrowserMultiFormatReader | null = null
  let currentStream: MediaStream | null = null
  let attachedVideoEl: HTMLVideoElement | null = null
  let scanLoopActive = false
  let rafId: number | null = null
  let lastCheckTime = 0
  let lastScannedCode = ''
  let lastScanTime = 0
  let onScanCallback: ((code: string) => void) | null = null
  let audioContext: AudioContext | null = null

  function playAudioBeep() {
    if (!playBeep || typeof window === 'undefined') return
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
      osc.frequency.exponentialRampToValueAtTime(1800, audioContext.currentTime + 0.1)
      gain.gain.setValueAtTime(0.25, audioContext.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1)
      osc.connect(gain)
      gain.connect(audioContext.destination)
      osc.start()
      osc.stop(audioContext.currentTime + 0.1)
    } catch {
      // Ignore audio errors
    }
  }

  function triggerVibrate() {
    if (!vibrate || typeof navigator === 'undefined' || !navigator.vibrate) return
    try {
      navigator.vibrate([80, 40, 80])
    } catch {
      // Ignore vibration errors
    }
  }

  function handleCapturedCode(rawCode: string) {
    const code = rawCode.trim()
    if (!code) return

    const now = Date.now()
    // Cooldown check for the same barcode (prevents multi-firing on continuous frames)
    if (code === lastScannedCode && now - lastScanTime < cooldownMs) {
      return
    }

    lastScannedCode = code
    lastScanTime = now

    playAudioBeep()
    triggerVibrate()

    if (onScanCallback) {
      onScanCallback(code)
    }
  }

  async function listCameras() {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.enumerateDevices) return
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      const videoDevices = devices.filter(d => d.kind === 'videoinput')
      availableDevices.value = videoDevices
      hasMultipleCameras.value = videoDevices.length > 1

      if (!selectedDeviceId.value && videoDevices.length > 0) {
        const backCam = videoDevices.find(d =>
          d.label.toLowerCase().includes('back') ||
          d.label.toLowerCase().includes('rear') ||
          d.label.toLowerCase().includes('environment')
        )
        const first = videoDevices[0]
        selectedDeviceId.value = backCam?.deviceId || first?.deviceId || ''
      }
    } catch {
      // Ignore enumeration errors
    }
  }

  async function startScanner(
    videoEl: HTMLVideoElement,
    callback: (code: string) => void
  ): Promise<boolean> {
    if (!videoEl) {
      cameraError.value = 'Camera video element not available'
      return false
    }

    stopScanner()
    attachedVideoEl = videoEl
    onScanCallback = callback
    isCameraActive.value = true
    isCameraLoading.value = true
    cameraError.value = null
    isTorchActive.value = false
    hasTorch.value = false

    await nextTick()

    try {
      if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
        throw new Error('Camera access not supported on this browser')
      }

      // Resolution capped at 720p: ideal 1280x720 (drastically faster than 1080p/4K)
      // We avoid rigid max constraints so portrait mode (720x1280) never triggers OverconstrainedError
      const constraints: MediaStreamConstraints = {
        video: {
          deviceId: selectedDeviceId.value ? { exact: selectedDeviceId.value } : undefined,
          facingMode: selectedDeviceId.value ? undefined : { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 },
          // @ts-ignore - Supported in Chromium/Android for rapid hardware lens focus
          focusMode: { ideal: 'continuous' }
        },
        audio: false
      }

      let stream: MediaStream
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints)
      } catch {
        // Fallback for devices that fail specific resolution constraints
        stream = await navigator.mediaDevices.getUserMedia({
          video: selectedDeviceId.value
            ? { deviceId: { exact: selectedDeviceId.value } }
            : { facingMode: { ideal: 'environment' } },
          audio: false
        })
      }

      currentStream = stream
      videoEl.srcObject = stream
      await videoEl.play()

      // Inspect hardware capabilities (flashlight/torch & continuous autofocus)
      const track = stream.getVideoTracks()[0]
      if (track) {
        try {
          const capabilities = (track.getCapabilities && track.getCapabilities()) as any
          hasTorch.value = !!(capabilities && capabilities.torch)

          // Engage hardware continuous auto-focus if supported by lens actuator
          if (capabilities?.focusMode && Array.isArray(capabilities.focusMode)) {
            if (capabilities.focusMode.includes('continuous')) {
              await (track as any).applyConstraints({
                advanced: [{ focusMode: 'continuous' }]
              })
            }
          }
        } catch {
          // Ignore constraint application errors on older browsers
        }
      }

      // Enumerate cameras in the background now that permissions are active (non-blocking)
      listCameras().catch(() => {})

      // -------------------------------------------------------------
      // ENGINE 1: Check Native Hardware-Accelerated BarcodeDetector
      // (Built into Android Chrome, Chromium, Edge; 0.02s - 0.05s detection)
      // -------------------------------------------------------------
      let nativeDetector: any = null
      if (typeof window !== 'undefined' && 'BarcodeDetector' in window) {
        try {
          const retailFormats = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128']
          if (typeof (window as any).BarcodeDetector.getSupportedFormats === 'function') {
            const supported: string[] = await (window as any).BarcodeDetector.getSupportedFormats()
            const matched = retailFormats.filter(f => supported.includes(f))
            if (matched.length > 0) {
              nativeDetector = new (window as any).BarcodeDetector({ formats: matched })
            }
          } else {
            nativeDetector = new (window as any).BarcodeDetector({ formats: retailFormats })
          }
        } catch {
          nativeDetector = null
        }
      }

      if (nativeDetector) {
        isNativeEngine.value = true
        scanLoopActive = true
        lastCheckTime = 0

        const nativeScanLoop = async () => {
          if (!scanLoopActive) return
          const now = Date.now()

          if (now - lastCheckTime >= throttleMs && videoEl && videoEl.readyState >= 2) {
            lastCheckTime = now
            try {
              const barcodes = await nativeDetector.detect(videoEl)
              if (barcodes && barcodes.length > 0) {
                const code = barcodes[0].rawValue
                if (code) {
                  handleCapturedCode(code)
                }
              }
            } catch {
              // Frame decoding skip while camera auto-focuses
            }
          }

          if (scanLoopActive) {
            rafId = requestAnimationFrame(nativeScanLoop)
          }
        }

        rafId = requestAnimationFrame(nativeScanLoop)
        isCameraLoading.value = false
        return true
      }

      // -------------------------------------------------------------
      // ENGINE 2: Tuned @zxing/library Fallback
      // (For iOS Safari & Firefox: NO TRY_HARDER, 100ms throttle, retail formats)
      // -------------------------------------------------------------
      isNativeEngine.value = false
      if (!codeReader) {
        const hints = new Map()
        const retailFormats = [
          BarcodeFormat.EAN_13,
          BarcodeFormat.EAN_8,
          BarcodeFormat.UPC_A,
          BarcodeFormat.UPC_E,
          BarcodeFormat.CODE_128,
        ]
        hints.set(DecodeHintType.POSSIBLE_FORMATS, retailFormats)
        // NOTE: Never enable TRY_HARDER for live video streams; it causes 3-5s lag
        hints.delete(DecodeHintType.TRY_HARDER)

        codeReader = new BrowserMultiFormatReader(hints)
        codeReader.timeBetweenDecodingAttempts = throttleMs
      }

      await codeReader.decodeFromStream(stream, videoEl, (result) => {
        if (result) {
          const text = result.getText()
          if (text) {
            handleCapturedCode(text)
          }
        }
      })

      isCameraLoading.value = false
      return true
    } catch (err: any) {
      console.error('useBarcodeScanner start error:', err)
      cameraError.value = err?.message || 'Could not access camera. Please check permissions.'
      stopScanner()
      return false
    }
  }

  function stopScanner() {
    scanLoopActive = false
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
    }

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

    if (attachedVideoEl) {
      attachedVideoEl.srcObject = null
      attachedVideoEl = null
    }

    isCameraActive.value = false
    isCameraLoading.value = false
    isTorchActive.value = false
    hasTorch.value = false
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

  async function switchCamera() {
    if (availableDevices.value.length <= 1 || !attachedVideoEl || !onScanCallback) return

    const currentIndex = availableDevices.value.findIndex(d => d.deviceId === selectedDeviceId.value)
    const nextIndex = (currentIndex + 1) % availableDevices.value.length
    const nextDevice = availableDevices.value[nextIndex]
    if (!nextDevice) return
    selectedDeviceId.value = nextDevice.deviceId

    const videoEl = attachedVideoEl
    const cb = onScanCallback
    stopScanner()
    await startScanner(videoEl, cb)
  }

  async function triggerAutofocus() {
    if (!currentStream) return
    const track = currentStream.getVideoTracks()[0]
    if (!track) return

    try {
      const capabilities = (track.getCapabilities && track.getCapabilities()) as any
      if (capabilities?.focusMode && Array.isArray(capabilities.focusMode)) {
        if (capabilities.focusMode.includes('continuous')) {
          await (track as any).applyConstraints({
            advanced: [{ focusMode: 'continuous' }]
          })
        } else if (capabilities.focusMode.includes('single-shot')) {
          await (track as any).applyConstraints({
            advanced: [{ focusMode: 'single-shot' }]
          })
        }
      }
    } catch (err) {
      console.debug('Autofocus trigger not supported:', err)
    }
  }

  onUnmounted(() => {
    stopScanner()
    if (audioContext && audioContext.state !== 'closed') {
      try {
        audioContext.close()
      } catch {}
      audioContext = null
    }
  })

  return {
    // Reactive State
    isCameraActive,
    isCameraLoading,
    cameraError,
    hasTorch,
    isTorchActive,
    isNativeEngine,
    hasMultipleCameras,
    availableDevices,
    selectedDeviceId,

    // Methods
    startScanner,
    stopScanner,
    toggleTorch,
    switchCamera,
    triggerAutofocus
  }
}
