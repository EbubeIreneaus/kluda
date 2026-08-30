<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'complete', mode: 'staff' | 'merchant'): void
}>()

const currentSlide = ref(0)

const slides = [
  {
    badge: 'High-Speed POS',
    title: 'Instant Barcode Scanning & Checkout',
    description: 'Ring up sales in seconds with lightning-fast barcode lookup, flexible discounts, and thermal receipt printing.',
    icon: 'i-lucide-scan-barcode',
    color: 'from-emerald-500 to-teal-600',
    highlight: 'Designed for high-traffic retail counters',
  },
  {
    badge: '100% Offline Ready',
    title: 'Sell Continuously Without Internet',
    description: 'Network down? No problem. The terminal records sales locally in IndexedDB and automatically syncs when reconnected.',
    icon: 'i-lucide-wifi-off',
    color: 'from-blue-500 to-indigo-600',
    highlight: 'Zero downtime during network outages',
  },
  {
    badge: 'Multi-Register',
    title: 'Multi-Counter Synchronization',
    description: 'Operate multiple cashiers, mobile devices, and desktop registers simultaneously with shared store inventory.',
    icon: 'i-lucide-layers',
    color: 'from-purple-500 to-pink-600',
    highlight: 'Real-time multi-counter deduction',
  },
  {
    badge: 'Smart Management',
    title: 'Inventory Alerts & Debt Tracking',
    description: 'Keep track of out-of-stock items, manage customer balances, and review daily cashier shift reconciliations.',
    icon: 'i-lucide-trending-up',
    color: 'from-amber-500 to-orange-600',
    highlight: 'Automated ledger & credit tracking',
  },
  {
    badge: 'Welcome to Kluda',
    title: 'How would you like to begin?',
    description: 'Select your role to start using Kluda POS or register a brand-new retail store.',
    icon: 'i-lucide-sparkles',
    color: 'from-emerald-500 to-emerald-700',
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
</script>

<template>
  <div class="fixed inset-0 z-[99999] flex flex-col items-center justify-between bg-zinc-950 text-white p-6 sm:p-10 select-none overflow-y-auto">
    <div class="w-full max-w-md flex items-center justify-between pt-2">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold font-mono">
          K
        </div>
        <span class="font-bold text-sm tracking-wider uppercase text-zinc-300">Kluda POS</span>
      </div>

      <button
        v-if="currentSlide < slides.length - 1"
        type="button"
        class="text-xs font-semibold text-zinc-400 hover:text-white px-3 py-1 rounded-full hover:bg-zinc-900 transition-colors"
        @click="currentSlide = slides.length - 1"
      >
        Skip
      </button>
    </div>

    <div class="w-full max-w-md my-auto flex flex-col items-center text-center gap-6 py-6">
      <div
        :class="[
          'w-28 h-28 rounded-3xl bg-gradient-to-tr flex items-center justify-center text-white shadow-2xl shadow-emerald-500/10 border border-white/10 transition-all duration-500',
          slides[currentSlide].color
        ]"
      >
        <UIcon :name="slides[currentSlide].icon" class="w-14 h-14" />
      </div>

      <div class="flex flex-col items-center gap-2">
        <span class="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold uppercase tracking-wider">
          {{ slides[currentSlide].badge }}
        </span>
        <h2 class="text-2xl sm:text-3xl font-black text-white tracking-tight mt-1">
          {{ slides[currentSlide].title }}
        </h2>
        <p class="text-xs sm:text-sm text-zinc-400 max-w-xs sm:max-w-sm leading-relaxed mt-1">
          {{ slides[currentSlide].description }}
        </p>
      </div>

      <div class="px-4 py-2 rounded-xl bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-300 font-medium">
        ✨ {{ slides[currentSlide].highlight }}
      </div>
    </div>

    <div class="w-full max-w-md flex flex-col items-center gap-5 pb-4">
      <div class="flex items-center gap-2">
        <button
          v-for="(_, idx) in slides"
          :key="idx"
          type="button"
          :class="[
            'h-2 rounded-full transition-all duration-300',
            currentSlide === idx ? 'w-8 bg-emerald-500' : 'w-2 bg-zinc-800 hover:bg-zinc-700'
          ]"
          @click="currentSlide = idx"
        />
      </div>

      <div v-if="currentSlide < slides.length - 1" class="w-full flex items-center gap-3">
        <button
          v-if="currentSlide > 0"
          type="button"
          class="flex-1 py-3.5 rounded-2xl bg-zinc-900 border border-zinc-800 text-xs font-bold text-zinc-300 hover:text-white hover:bg-zinc-850 transition-colors"
          @click="handlePrev"
        >
          Previous
        </button>
        <button
          type="button"
          class="flex-1 py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-zinc-950 transition-all shadow-lg shadow-emerald-500/20 active:scale-[0.98]"
          @click="handleNext"
        >
          Continue
        </button>
      </div>

      <div v-else class="w-full flex flex-col gap-3">
        <button
          type="button"
          class="w-full py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-sm font-bold text-zinc-950 transition-all shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 active:scale-[0.98]"
          @click="handleComplete('staff')"
        >
          <UIcon name="i-lucide-log-in" class="w-4 h-4" />
          Sign In to Register Terminal
        </button>

        <button
          type="button"
          class="w-full py-3.5 rounded-2xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-bold text-zinc-200 transition-colors flex items-center justify-center gap-2"
          @click="handleComplete('merchant')"
        >
          <UIcon name="i-lucide-store" class="w-4 h-4 text-emerald-400" />
          New Merchant? Create Store
        </button>
      </div>
    </div>
  </div>
</template>
