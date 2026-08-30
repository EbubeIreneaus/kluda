<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const emit = defineEmits<{
  (e: 'complete', mode: 'staff' | 'merchant'): void
}>()

const currentSlide = ref(0)
let touchStartX = 0
let touchEndX = 0

const slides = [
  {
    badge: 'Lightning Fast POS',
    title: 'Instant Barcode Scanning & Checkout',
    description: 'Ring up sales in milliseconds with fast barcode lookup, instant discounts, multi-currency support, and thermal receipt printing.',
    icon: 'i-lucide-scan-barcode',
    color: 'from-emerald-500 to-teal-600',
    bgGradient: 'radial-gradient(circle at 50% 30%, rgba(16, 185, 129, 0.25) 0%, rgba(13, 148, 136, 0.1) 45%, transparent 70%)',
    ambientGlow: 'bg-emerald-500/20',
    highlight: 'Designed for high-traffic retail counters',
  },
  {
    badge: '100% Offline Durability',
    title: 'Sell Continuously Without Internet',
    description: 'Wi-Fi drops? Cell towers down? No problem. The terminal records sales in IndexedDB and silently syncs when reconnected.',
    icon: 'i-lucide-wifi-off',
    color: 'from-cyan-500 to-blue-600',
    bgGradient: 'radial-gradient(circle at 50% 30%, rgba(6, 182, 212, 0.25) 0%, rgba(37, 99, 235, 0.1) 45%, transparent 70%)',
    ambientGlow: 'bg-cyan-500/20',
    highlight: 'Zero interrupted sales or queue delays',
  },
  {
    badge: 'Multi-Terminal Sync',
    title: 'Multi-Counter Synchronization',
    description: 'Operate multiple cashiers, mobile phones, and desktop registers simultaneously with shared store inventory.',
    icon: 'i-lucide-layers',
    color: 'from-purple-500 to-indigo-600',
    bgGradient: 'radial-gradient(circle at 50% 30%, rgba(168, 85, 247, 0.25) 0%, rgba(79, 70, 229, 0.1) 45%, transparent 70%)',
    ambientGlow: 'bg-purple-500/20',
    highlight: 'Real-time multi-counter deduction',
  },
  {
    badge: 'Intelligent Inventory',
    title: 'Inventory Alerts & Debt Tracking',
    description: 'Keep track of low stock thresholds, manage customer credit balances, and review daily cashier reconciliations.',
    icon: 'i-lucide-trending-up',
    color: 'from-amber-500 to-orange-600',
    bgGradient: 'radial-gradient(circle at 50% 30%, rgba(245, 158, 11, 0.25) 0%, rgba(234, 88, 12, 0.1) 45%, transparent 70%)',
    ambientGlow: 'bg-amber-500/20',
    highlight: 'Automated ledger & credit tracking',
  },
  {
    badge: 'Welcome to Kluda',
    title: 'How would you like to begin?',
    description: 'Select your role to start using Kluda POS or register a brand-new retail store.',
    icon: 'i-lucide-sparkles',
    color: 'from-emerald-400 to-emerald-600',
    bgGradient: 'radial-gradient(circle at 50% 30%, rgba(16, 185, 129, 0.3) 0%, rgba(5, 150, 105, 0.12) 50%, transparent 75%)',
    ambientGlow: 'bg-emerald-500/25',
    highlight: 'Fast setup in less than 2 minutes',
  },
]

function handleNext() {
  if (currentSlide.value < slides.length - 1) {
    currentSlide.value++
  }
}

function handlePrev() {
  if (currentSlide.value > 0) {
    currentSlide.value--
  }
}

function handleComplete(mode: 'staff' | 'merchant') {
  if (import.meta.client) {
    localStorage.setItem('has_completed_onboarding', 'true')
  }
  emit('complete', mode)
}

function onTouchStart(e: TouchEvent) {
  touchStartX = e.changedTouches[0].screenX
}

function onTouchEnd(e: TouchEvent) {
  touchEndX = e.changedTouches[0].screenX
  handleSwipe()
}

function handleSwipe() {
  const diff = touchStartX - touchEndX
  if (Math.abs(diff) > 45) {
    if (diff > 0) {
      handleNext()
    } else {
      handlePrev()
    }
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowRight' || e.key === 'Enter') {
    handleNext()
  } else if (e.key === 'ArrowLeft') {
    handlePrev()
  }
}

onMounted(() => {
  if (import.meta.client) {
    window.addEventListener('keydown', onKeydown)
  }
})

onUnmounted(() => {
  if (import.meta.client) {
    window.removeEventListener('keydown', onKeydown)
  }
})
</script>

<template>
  <div
    class="fixed inset-0 z-[99999] flex flex-col justify-between bg-zinc-950 text-white p-5 sm:p-8 select-none overflow-hidden touch-manipulation"
    @touchstart="onTouchStart"
    @touchend="onTouchEnd"
  >
    <div
      class="absolute inset-0 pointer-events-none transition-all duration-700 ease-out"
      :style="{ background: slides[currentSlide].bgGradient }"
    />

    <div class="absolute inset-0 bg-[radial-gradient(#ffffff0a_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none opacity-60" />

    <div
      :class="[
        'absolute -top-32 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full blur-3xl pointer-events-none transition-all duration-700 opacity-60',
        slides[currentSlide].ambientGlow
      ]"
    />

    <div class="relative z-10 w-full max-w-md mx-auto flex items-center justify-between pt-2">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold font-mono shadow-sm">
          K
        </div>
        <span class="font-bold text-xs tracking-wider uppercase text-zinc-300">Kluda POS</span>
      </div>

      <button
        v-if="currentSlide < slides.length - 1"
        type="button"
        class="text-xs font-semibold text-zinc-400 hover:text-white px-3 py-1.5 rounded-full hover:bg-zinc-900/80 transition-colors touch-manipulation cursor-pointer"
        @click="currentSlide = slides.length - 1"
      >
        Skip
      </button>
    </div>

    <div class="relative z-10 w-full max-w-md mx-auto my-auto py-4">
      <div class="overflow-hidden w-full">
        <div
          class="flex transition-transform duration-350 ease-[cubic-bezier(0.16,1,0.3,1)] will-change-transform"
          :style="{ transform: `translate3d(-${currentSlide * 100}%, 0, 0)` }"
        >
          <div
            v-for="(s, idx) in slides"
            :key="idx"
            class="w-full shrink-0 flex flex-col items-center text-center px-2 gap-5"
          >
            <div
              :class="[
                'w-24 h-24 sm:w-28 sm:h-28 rounded-3xl bg-gradient-to-tr flex items-center justify-center text-white shadow-2xl border border-white/15 transition-transform duration-300',
                s.color
              ]"
            >
              <UIcon :name="s.icon" class="w-12 h-12 sm:w-14 sm:h-14" />
            </div>

            <div class="flex flex-col items-center gap-2 max-w-sm">
              <span class="px-3 py-1 rounded-full bg-white/5 border border-white/10 backdrop-blur-md text-emerald-400 text-[11px] font-bold uppercase tracking-wider">
                {{ s.badge }}
              </span>
              <h2 class="text-2xl sm:text-3xl font-black text-white tracking-tight leading-tight">
                {{ s.title }}
              </h2>
              <p class="text-xs sm:text-sm text-zinc-300/90 leading-relaxed max-w-xs sm:max-w-sm">
                {{ s.description }}
              </p>
            </div>

            <div class="px-3.5 py-1.5 rounded-xl bg-zinc-900/70 border border-zinc-800/80 backdrop-blur-md text-[11px] text-zinc-300 font-medium">
              ✨ {{ s.highlight }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="relative z-10 w-full max-w-md mx-auto flex flex-col items-center gap-4 pb-2">
      <div class="flex items-center gap-2 py-1">
        <button
          v-for="(_, idx) in slides"
          :key="idx"
          type="button"
          :class="[
            'h-1.5 rounded-full transition-all duration-300 cursor-pointer touch-manipulation',
            currentSlide === idx ? 'w-8 bg-emerald-400' : 'w-2 bg-zinc-800 hover:bg-zinc-700'
          ]"
          @click="currentSlide = idx"
        />
      </div>

      <div v-if="currentSlide < slides.length - 1" class="w-full flex items-center gap-3">
        <button
          v-if="currentSlide > 0"
          type="button"
          class="flex-1 py-3.5 rounded-2xl bg-zinc-900/90 border border-zinc-800 text-xs font-bold text-zinc-300 hover:text-white active:scale-95 transition-all touch-manipulation cursor-pointer"
          @click="handlePrev"
        >
          Previous
        </button>
        <button
          type="button"
          class="flex-1 py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-300 text-xs font-bold text-zinc-950 transition-all shadow-lg shadow-emerald-500/25 active:scale-95 touch-manipulation cursor-pointer flex items-center justify-center gap-1.5"
          @click="handleNext"
        >
          Continue
          <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
        </button>
      </div>

      <div v-else class="w-full flex flex-col gap-2.5">
        <button
          type="button"
          class="w-full py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-300 text-sm font-bold text-zinc-950 transition-all shadow-lg shadow-emerald-500/30 flex items-center justify-center gap-2 active:scale-95 touch-manipulation cursor-pointer"
          @click="handleComplete('staff')"
        >
          <UIcon name="i-lucide-log-in" class="w-4 h-4" />
          Sign In to Register Terminal
        </button>

        <button
          type="button"
          class="w-full py-3.5 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-zinc-700 active:bg-zinc-800 text-xs font-bold text-zinc-200 transition-all flex items-center justify-center gap-2 active:scale-95 touch-manipulation cursor-pointer"
          @click="handleComplete('merchant')"
        >
          <UIcon name="i-lucide-store" class="w-4 h-4 text-emerald-400" />
          New Merchant? Create Store
        </button>
      </div>
    </div>
  </div>
</template>
