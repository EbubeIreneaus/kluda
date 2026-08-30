<script setup lang="ts">
import { ref } from 'vue'

const { isSettingPinOpen, setPinOnline, closeSetPinModal } = usePinAuth()
const auth = useAuthStore()
const toast = useToast()

const step = ref<'enter' | 'confirm'>('enter')
const firstPin = ref('')
const confirmPin = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)

function handleNumber(n: string) {
  errorMessage.value = ''
  if (step.value === 'enter') {
    if (firstPin.value.length < 4) {
      firstPin.value += n
      if (firstPin.value.length === 4) {
        step.value = 'confirm'
      }
    }
  } else {
    if (confirmPin.value.length < 4) {
      confirmPin.value += n
      if (confirmPin.value.length === 4) {
        submitNewPin()
      }
    }
  }
}

function handleBackspace() {
  errorMessage.value = ''
  if (step.value === 'confirm') {
    if (confirmPin.value.length > 0) {
      confirmPin.value = confirmPin.value.slice(0, -1)
    } else {
      step.value = 'enter'
      firstPin.value = firstPin.value.slice(0, -1)
    }
  } else {
    firstPin.value = firstPin.value.slice(0, -1)
  }
}

function handleClear() {
  firstPin.value = ''
  confirmPin.value = ''
  step.value = 'enter'
  errorMessage.value = ''
}

async function submitNewPin() {
  if (firstPin.value !== confirmPin.value) {
    errorMessage.value = 'PINs do not match. Please try again.'
    confirmPin.value = ''
    step.value = 'enter'
    firstPin.value = ''
    return
  }

  isSubmitting.value = true
  try {
    const res = await setPinOnline(firstPin.value)
    if (res.success) {
      toast.add({
        title: 'PIN Set Successfully',
        description: 'Your 4-digit terminal PIN is ready for offline and quick access.',
        color: 'success',
      })
      handleClear()
      closeSetPinModal()
    } else {
      errorMessage.value = res.message || 'Failed to save PIN'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <ClientOnly>
    <div
      v-if="isSettingPinOpen"
      class="fixed inset-0 z-[999999] bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200"
    >
      <div
        class="w-full max-w-sm bg-zinc-950 border border-zinc-800 rounded-3xl p-6 flex flex-col items-center gap-6 shadow-2xl relative"
        @click.stop
      >
        <div class="flex flex-col items-center text-center gap-1.5 pt-2">
          <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-1">
            <UIcon name="i-lucide-key-round" class="w-6 h-6" />
          </div>
          <h3 class="text-lg font-bold text-white tracking-tight">
            {{ step === 'enter' ? 'Create Quick Terminal PIN' : 'Confirm Your PIN' }}
          </h3>
          <p class="text-xs text-zinc-400 max-w-[260px] leading-relaxed">
            {{ step === 'enter' ? 'Choose a 4-digit numeric PIN for offline access and quick authorization.' : 'Re-enter your 4-digit PIN to confirm.' }}
          </p>
        </div>

        <div class="flex items-center justify-center gap-4 my-1">
          <div
            v-for="i in 4"
            :key="i"
            :class="[
              'w-4 h-4 rounded-full border transition-all duration-200',
              (step === 'enter' ? firstPin.length : confirmPin.length) >= i
                ? 'bg-emerald-500 border-emerald-400 scale-110 shadow-sm shadow-emerald-500/50'
                : 'bg-zinc-900 border-zinc-700'
            ]"
          />
        </div>

        <div
          v-if="errorMessage"
          class="text-xs font-semibold text-red-400 bg-red-500/10 border border-red-500/20 px-3 py-1.5 rounded-xl text-center"
        >
          {{ errorMessage }}
        </div>

        <div class="grid grid-cols-3 gap-3 w-full max-w-[280px]">
          <button
            v-for="n in ['1', '2', '3', '4', '5', '6', '7', '8', '9']"
            :key="n"
            type="button"
            class="h-14 rounded-2xl bg-zinc-900/80 border border-zinc-800 text-lg font-bold text-white hover:bg-zinc-800 active:scale-95 transition-all flex items-center justify-center shadow-xs select-none"
            :disabled="isSubmitting"
            @click="handleNumber(n)"
          >
            {{ n }}
          </button>
          <button
            type="button"
            class="h-14 rounded-2xl bg-zinc-900/40 text-xs font-semibold text-zinc-400 hover:text-white hover:bg-zinc-800/80 active:scale-95 transition-all flex items-center justify-center select-none"
            :disabled="isSubmitting"
            @click="handleClear"
          >
            Reset
          </button>
          <button
            type="button"
            class="h-14 rounded-2xl bg-zinc-900/80 border border-zinc-800 text-lg font-bold text-white hover:bg-zinc-800 active:scale-95 transition-all flex items-center justify-center shadow-xs select-none"
            :disabled="isSubmitting"
            @click="handleNumber('0')"
          >
            0
          </button>
          <button
            type="button"
            class="h-14 rounded-2xl bg-zinc-900/40 text-zinc-400 hover:text-white hover:bg-zinc-800/80 active:scale-95 transition-all flex items-center justify-center select-none"
            :disabled="isSubmitting"
            @click="handleBackspace"
          >
            <UIcon name="i-lucide-delete" class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </ClientOnly>
</template>
