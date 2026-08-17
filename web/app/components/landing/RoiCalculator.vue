<script setup lang="ts">
import { ref, computed } from 'vue'

const counters = ref(3)
const dailyRevenue = ref(350000) // in Naira
const outageHoursPerWeek = ref(8) // hours

// Hardware cost per traditional POS (Hardware + OS License + Scanner Gun) = ~₦280,000
const traditionalHardwarePerTerminal = 280000

const hardwareSavings = computed(() => {
  return counters.value * traditionalHardwarePerTerminal
})

// Outage revenue loss estimated at ~15% of hourly revenue during down times
const weeklyOutageSavings = computed(() => {
  const hourlyRevenue = dailyRevenue.value / 12
  const lostPerOutageHour = hourlyRevenue * 0.25 // 25% drop without offline POS
  return lostPerOutageHour * outageHoursPerWeek.value
})

const annualOutageSavings = computed(() => {
  return weeklyOutageSavings.value * 52
})

const totalFirstYearSavings = computed(() => {
  return hardwareSavings.value + annualOutageSavings.value
})

function formatNgn(num: number) {
  return '₦' + Math.round(num).toLocaleString('en-NG')
}
</script>

<template>
  <div class="rounded-3xl border border-(--ui-border) glass-panel p-6 sm:p-10 shadow-xl relative overflow-hidden">
    <div class="absolute -right-20 -bottom-20 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
    <div class="absolute -left-20 -top-20 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center relative z-10">
      <!-- Sliders / Inputs (7 cols) -->
      <div class="lg:col-span-7 space-y-6">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
          <UIcon name="i-lucide-calculator" class="w-4 h-4" />
          <span>Interactive Store Cost Simulator</span>
        </div>

        <div>
          <h3 class="text-2xl sm:text-3xl font-extrabold text-(--ui-text-highlighted)">
            Calculate Your First-Year Savings
          </h3>
          <p class="text-sm text-(--ui-text-muted) mt-1">
            See how much your retail business saves by ditching proprietary POS hardware and eliminating network outage downtime.
          </p>
        </div>

        <!-- Slider 1: Counters -->
        <div class="space-y-2 p-4 rounded-2xl bg-(--ui-bg-elevated)/60 border border-(--ui-border)">
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-(--ui-text-highlighted) flex items-center gap-2">
              <UIcon name="i-lucide-monitor" class="w-4 h-4 text-emerald-500" />
              Number of Cashier Counters
            </span>
            <span class="font-mono text-base font-bold text-emerald-500 px-2.5 py-0.5 rounded-lg bg-emerald-500/10">
              {{ counters }} {{ counters === 1 ? 'Terminal' : 'Terminals' }}
            </span>
          </div>
          <input
            v-model.number="counters"
            type="range"
            min="1"
            max="15"
            step="1"
            class="w-full h-2 bg-(--ui-border) rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <div class="flex justify-between text-[11px] text-(--ui-text-dimmed)">
            <span>1 counter</span>
            <span>5 counters</span>
            <span>10 counters</span>
            <span>15 counters</span>
          </div>
        </div>

        <!-- Slider 2: Daily Revenue -->
        <div class="space-y-2 p-4 rounded-2xl bg-(--ui-bg-elevated)/60 border border-(--ui-border)">
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-(--ui-text-highlighted) flex items-center gap-2">
              <UIcon name="i-lucide-banknote" class="w-4 h-4 text-emerald-500" />
              Average Daily Store Sales
            </span>
            <span class="font-mono text-base font-bold text-emerald-500 px-2.5 py-0.5 rounded-lg bg-emerald-500/10">
              {{ formatNgn(dailyRevenue) }}
            </span>
          </div>
          <input
            v-model.number="dailyRevenue"
            type="range"
            min="50000"
            max="2000000"
            step="25000"
            class="w-full h-2 bg-(--ui-border) rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <div class="flex justify-between text-[11px] text-(--ui-text-dimmed)">
            <span>₦50k / day</span>
            <span>₦500k / day</span>
            <span>₦1M / day</span>
            <span>₦2M / day</span>
          </div>
        </div>

        <!-- Slider 3: Network / Power Outage Hours -->
        <div class="space-y-2 p-4 rounded-2xl bg-(--ui-bg-elevated)/60 border border-(--ui-border)">
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-(--ui-text-highlighted) flex items-center gap-2">
              <UIcon name="i-lucide-wifi-off" class="w-4 h-4 text-amber-500" />
              Weekly Internet / Power Glitch Hours
            </span>
            <span class="font-mono text-base font-bold text-amber-500 px-2.5 py-0.5 rounded-lg bg-amber-500/10">
              {{ outageHoursPerWeek }} hrs / week
            </span>
          </div>
          <input
            v-model.number="outageHoursPerWeek"
            type="range"
            min="0"
            max="25"
            step="1"
            class="w-full h-2 bg-(--ui-border) rounded-lg appearance-none cursor-pointer accent-amber-500"
          />
          <div class="flex justify-between text-[11px] text-(--ui-text-dimmed)">
            <span>0 hrs (Fiber)</span>
            <span>5 hrs</span>
            <span>12 hrs (Typical)</span>
            <span>25 hrs</span>
          </div>
        </div>
      </div>

      <!-- Result Scorecard (5 cols) -->
      <div class="lg:col-span-5 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 border border-emerald-500/30 shadow-2xl relative overflow-hidden">
        <div class="absolute top-0 right-0 px-4 py-1.5 rounded-bl-2xl bg-emerald-500 text-slate-950 font-bold text-xs uppercase tracking-wider">
          Total Savings
        </div>

        <div class="mb-6">
          <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Estimated 1st Year ROI</span>
          <div class="text-3xl sm:text-4xl font-extrabold text-emerald-400 font-mono mt-1">
            {{ formatNgn(totalFirstYearSavings) }}
          </div>
          <p class="text-xs text-slate-400 mt-1">
            Saved on upfront hardware purchases + zero sales lost to outages.
          </p>
        </div>

        <div class="space-y-4 pt-4 border-t border-slate-800 text-xs">
          <div class="flex items-center justify-between">
            <span class="text-slate-400 flex items-center gap-1.5">
              <UIcon name="i-lucide-monitor-check" class="w-4 h-4 text-emerald-400" />
              Upfront Hardware Saved:
            </span>
            <span class="font-mono font-bold text-white">{{ formatNgn(hardwareSavings) }}</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-slate-400 flex items-center gap-1.5">
              <UIcon name="i-lucide-shield-check" class="w-4 h-4 text-emerald-400" />
              Outage Revenue Protected / yr:
            </span>
            <span class="font-mono font-bold text-emerald-300">{{ formatNgn(annualOutageSavings) }}</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-slate-400 flex items-center gap-1.5">
              <UIcon name="i-lucide-scan" class="w-4 h-4 text-emerald-400" />
              Scanner Gun Budget:
            </span>
            <span class="font-mono font-bold text-emerald-400">₦0 (Camera Included)</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-slate-400 flex items-center gap-1.5">
              <UIcon name="i-lucide-cloud" class="w-4 h-4 text-emerald-400" />
              Cloud Setup Cost:
            </span>
            <span class="font-mono font-bold text-emerald-400">₦0 (Public Testing)</span>
          </div>
        </div>

        <NuxtLink to="/register" class="block mt-8">
          <button class="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-extrabold text-sm uppercase tracking-wider transition shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 cursor-pointer">
            <UIcon name="i-lucide-sparkles" class="w-4 h-4" />
            Claim These Savings Now
          </button>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
