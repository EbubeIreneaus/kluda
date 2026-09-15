<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const { modalState, verifyPin } = usePinAuth()
const auth = useAuthStore()

const enteredPin = ref('')
const isShaking = ref(false)
const errorMessage = ref('')
const maxPinLength = 4
const isChecking = ref(false)

watch(() => modalState.value.isOpen, (open) => {
  if (open) {
    enteredPin.value = ''
    errorMessage.value = ''
  }
})

function handleNumber(num: string) {
  if (enteredPin.value.length < maxPinLength && !isChecking.value) {
    enteredPin.value += num
    errorMessage.value = ''
    if (enteredPin.value.length === maxPinLength) {
      setTimeout(() => {
        submitPin()
      }, 180)
    }
  }
}

function handleBackspace() {
  if (enteredPin.value.length > 0 && !isChecking.value) {
    enteredPin.value = enteredPin.value.slice(0, -1)
    errorMessage.value = ''
  }
}

function handleClear() {
  enteredPin.value = ''
  errorMessage.value = ''
}

async function submitPin() {
  if (enteredPin.value.length !== maxPinLength) return
  isChecking.value = true

  try {
    if (!auth.user?.pin_hash || !auth.user?.pin_salt) {
      triggerError('No PIN configured for this account')
      return
    }

    const isValid = await verifyPin(enteredPin.value)
    if (isValid) {
      if (modalState.value.resolve) {
        modalState.value.resolve(true)
      }
      modalState.value.isOpen = false
      enteredPin.value = ''
    } else {
      triggerError('Incorrect PIN. Please try again.')
    }
  } finally {
    isChecking.value = false
  }
}

function triggerError(msg: string) {
  errorMessage.value = msg
  isShaking.value = true
  setTimeout(() => {
    isShaking.value = false
    enteredPin.value = ''
  }, 400)
}

function handleCancel() {
  if (modalState.value.resolve) {
    modalState.value.resolve(false)
  }
  modalState.value.isOpen = false
  enteredPin.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (!modalState.value.isOpen) return
  if (e.key >= '0' && e.key <= '9') {
    handleNumber(e.key)
  } else if (e.key === 'Backspace') {
    handleBackspace()
  } else if (e.key === 'Escape') {
    handleCancel()
  }
}

onMounted(() => {
  if (import.meta.client) {
    window.addEventListener('keydown', handleKeydown)
  }
})

onUnmounted(() => {
  if (import.meta.client) {
    window.removeEventListener('keydown', handleKeydown)
  }
})
</script>

<template>
 <Teleport to="body">
   <ClientOnly>
    <div
      v-if="modalState.isOpen"
      class="fixed inset-0 z-[99999]! bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200"
      @click="handleCancel"
    >
      <div
        class="w-full max-w-sm bg-zinc-950 border border-zinc-800 rounded-3xl p-6 flex flex-col items-center gap-6 shadow-2xl relative"
        @click.stop
      >
        <button
          type="button"
          class="absolute top-4 right-4 text-zinc-500 hover:text-white p-1 rounded-full hover:bg-zinc-900 transition-colors"
          @click="handleCancel"
        >
          <UIcon name="i-lucide-x" class="w-5 h-5" />
        </button>

        <div class="flex flex-col items-center text-center gap-1.5 pt-2">
          <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-1">
            <UIcon name="i-lucide-shield-check" class="w-6 h-6" />
          </div>
          <h3 class="text-lg font-bold text-white tracking-tight">{{ modalState.title }}</h3>
          <p class="text-xs text-zinc-400 max-w-[240px] leading-relaxed">{{ modalState.description }}</p>
        </div>

        <div
          :class="[
            'flex items-center justify-center gap-4 my-1 transition-transform',
            isShaking ? 'animate-shake' : ''
          ]"
        >
          <div
            v-for="i in maxPinLength"
            :key="i"
            :class="[
              'w-4 h-4 rounded-full border transition-all duration-200',
              enteredPin.length >= i
                ? 'bg-emerald-500 border-emerald-400 scale-110 shadow-sm shadow-emerald-500/50'
                : 'bg-zinc-900 border-zinc-700'
            ]"
          />
        </div>

        <div
          v-if="errorMessage"
          class="text-xs font-semibold text-red-400 bg-red-500/10 border border-red-500/20 px-3 py-1.5 rounded-xl animate-in fade-in duration-200"
        >
          {{ errorMessage }}
        </div>

        <div class="grid grid-cols-3 gap-3 w-full max-w-[280px]">
          <button
            v-for="n in ['1', '2', '3', '4', '5', '6', '7', '8', '9']"
            :key="n"
            type="button"
            class="h-14 rounded-2xl bg-zinc-900/80 border border-zinc-800 text-lg font-bold text-white hover:bg-zinc-800 active:scale-95 transition-all flex items-center justify-center shadow-xs select-none"
            @click="handleNumber(n)"
          >
            {{ n }}
          </button>
          <button
            type="button"
            class="h-14 rounded-2xl bg-zinc-900/40 text-xs font-semibold text-zinc-400 hover:text-white hover:bg-zinc-800/80 active:scale-95 transition-all flex items-center justify-center select-none"
            @click="handleClear"
          >
            Clear
          </button>
          <button
            type="button"
            class="h-14 rounded-2xl bg-zinc-900/80 border border-zinc-800 text-lg font-bold text-white hover:bg-zinc-800 active:scale-95 transition-all flex items-center justify-center shadow-xs select-none"
            @click="handleNumber('0')"
          >
            0
          </button>
          <button
            type="button"
            class="h-14 rounded-2xl bg-zinc-900/40 text-zinc-400 hover:text-white hover:bg-zinc-800/80 active:scale-95 transition-all flex items-center justify-center select-none"
            @click="handleBackspace"
          >
            <UIcon name="i-lucide-delete" class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </ClientOnly>
 </Teleport>
</template>

<style scoped>
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-8px); }
  40%, 80% { transform: translateX(8px); }
}
.animate-shake {
  animation: shake 0.35s ease-in-out;
}
</style>
