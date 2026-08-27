<script setup lang="ts">
import { ref, computed } from 'vue'

const activeStep = ref(0)

const steps = [
  {
    step: '01',
    title: 'Rapid In-Store Barcode Search',
    subtitle: 'Fast Local Product Lookup',
    icon: 'i-lucide-zap',
    description: 'When cashiers scan a product barcode with their phone camera or search by name, results appear instantly on screen. Your entire product catalog is saved right on the device, eliminating checkout delays during peak store hours.',
    specs: ['Fast phone camera scanning', 'Zero waiting time during rush hours', 'Full product catalog ready on device']
  },
  {
    step: '02',
    title: 'Safe Offline Sales Recording',
    subtitle: 'Zero Lost Sales or Double Charges',
    icon: 'i-lucide-shield-check',
    description: 'Every completed sale is securely locked into the device local storage. Even if power cuts, the screen turns off, or the device restarts, your sales and customer records remain intact with zero risk of duplicate entries.',
    specs: ['Protected against duplicate charges', 'Tracks cash, transfers, and customer debts offline', 'Instant thermal receipt generation']
  },
  {
    step: '03',
    title: 'Live Shelf Stock Deduction',
    subtitle: 'Never Oversell Out-of-Stock Items',
    icon: 'i-lucide-boxes',
    description: 'Product quantities decrease immediately on the cashier screen as items are sold, giving staff accurate shelf counts right at the counter even without internet.',
    specs: ['Immediate shelf stock updates', 'Automatic low stock warnings', 'Handles item bundles & packs']
  },
  {
    step: '04',
    title: 'Silent Cloud Backup & Multi-Counter Sync',
    subtitle: 'Zero Effort Automatic Sync',
    icon: 'i-lucide-refresh-cw',
    description: 'The exact moment your internet or Wi-Fi reconnects, all pending offline sales back up to your secure store cloud automatically. All other checkout counters receive updated stock counts in real time.',
    specs: ['Automatic background sync', 'Keeps all your store counters aligned', 'Complete sales reports in your Owner Portal']
  }
]

const currentStep = computed(() => steps[activeStep.value] || steps[0]!)
</script>

<template>
  <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/60 p-6 sm:p-10 shadow-2xl backdrop-blur-xl">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 mb-3">
        <UIcon name="i-lucide-activity" class="w-4 h-4" />
        <span>Built For Uninterrupted Selling</span>
      </div>
      <h3 class="text-2xl sm:text-3xl font-extrabold text-(--ui-text-highlighted) tracking-tight">
        How Offline Selling & Automatic Sync Works
      </h3>
      <p class="text-sm text-(--ui-text-muted) mt-2">
        Designed so your store keeps running at full speed whether you have strong Wi-Fi, weak mobile data, or complete internet outages.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="(item, idx) in steps"
        :key="item.step"
        @click="activeStep = idx"
        class="p-5 rounded-2xl border transition cursor-pointer flex flex-col justify-between group"
        :class="activeStep === idx ? 'bg-emerald-500/10 border-emerald-500/40 shadow-lg shadow-emerald-500/5' : 'bg-(--ui-bg)/60 border-(--ui-border) hover:border-emerald-500/20'"
      >
        <div>
          <div class="flex items-center justify-between mb-3">
            <span class="font-mono text-xs font-bold px-2 py-0.5 rounded-md" :class="activeStep === idx ? 'bg-emerald-500 text-slate-950 font-black' : 'bg-(--ui-bg-elevated) text-(--ui-text-dimmed)'">
              {{ item.step }}
            </span>
            <UIcon :name="item.icon" class="w-5 h-5 transition group-hover:scale-110" :class="activeStep === idx ? 'text-emerald-500' : 'text-(--ui-text-muted)'" />
          </div>
          <h4 class="text-sm font-bold text-(--ui-text-highlighted) mb-1">{{ item.title }}</h4>
          <p class="text-xs text-(--ui-text-muted)">{{ item.subtitle }}</p>
        </div>

        <div class="mt-4 pt-3 border-t border-(--ui-border) flex items-center justify-between">
          <span class="text-[11px] font-bold" :class="activeStep === idx ? 'text-emerald-500' : 'text-(--ui-text-dimmed)'">
            {{ activeStep === idx ? 'Active Step' : 'Click to inspect' }}
          </span>
          <UIcon name="i-lucide-arrow-right" class="w-3.5 h-3.5" :class="activeStep === idx ? 'text-emerald-500' : 'text-(--ui-text-dimmed)'" />
        </div>
      </div>
    </div>

    <div class="mt-8 p-6 rounded-2xl bg-slate-950 text-white border border-emerald-500/30">
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-mono font-bold">
            {{ currentStep.step }}
          </div>
          <div>
            <h4 class="text-lg font-bold text-white">{{ currentStep.title }}</h4>
            <span class="text-xs text-emerald-400">{{ currentStep.subtitle }}</span>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="activeStep = Math.max(0, activeStep - 1)"
            :disabled="activeStep === 0"
            class="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-30 text-slate-300 transition cursor-pointer"
          >
            <UIcon name="i-lucide-chevron-left" class="w-4 h-4" />
          </button>
          <button
            @click="activeStep = Math.min(steps.length - 1, activeStep + 1)"
            :disabled="activeStep === steps.length - 1"
            class="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-30 text-slate-300 transition cursor-pointer"
          >
            <UIcon name="i-lucide-chevron-right" class="w-4 h-4" />
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-6 mt-4 items-center">
        <p class="md:col-span-7 text-xs sm:text-sm text-slate-300 leading-relaxed">
          {{ currentStep.description }}
        </p>

        <div class="md:col-span-5 space-y-2 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span class="text-[11px] font-mono text-emerald-400 uppercase font-semibold">Store Owner Benefits:</span>
          <div v-for="spec in currentStep.specs" :key="spec" class="flex items-center gap-2 text-xs text-slate-200">
            <UIcon name="i-lucide-check-circle" class="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>{{ spec }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
