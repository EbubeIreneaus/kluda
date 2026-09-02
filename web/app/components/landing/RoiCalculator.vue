<script setup lang="ts">
import { ref, computed } from 'vue'

const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'

const counters = ref(3)
const dailyRevenue = ref(350000)
const outageHoursPerWeek = ref(8)

const traditionalHardwarePerTerminal = 250000

const hardwareSavings = computed(() => {
  return counters.value * traditionalHardwarePerTerminal
})

const weeklyOutageSavings = computed(() => {
  const hourlyRevenue = dailyRevenue.value / 12
  const lostPerOutageHour = hourlyRevenue * 0.20
  return lostPerOutageHour * outageHoursPerWeek.value
})

const annualOutageSavings = computed(() => {
  return weeklyOutageSavings.value * 52
})

const totalAnnualSavings = computed(() => {
  return hardwareSavings.value + annualOutageSavings.value
})

function formatNgn(num: number) {
  return '₦' + Math.round(num).toLocaleString('en-NG')
}
</script>

<template>
  <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/60 p-6 sm:p-10 shadow-2xl relative overflow-hidden backdrop-blur-xl">
    <div class="absolute -right-20 -bottom-20 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
    <div class="absolute -left-20 -top-20 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center relative z-10">
      <div class="lg:col-span-7 space-y-6">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
          <UIcon name="i-lucide-calculator" class="w-4 h-4" />
          <span>Interactive Savings Estimator</span>
        </div>

        <div>
          <h3 class="text-2xl sm:text-3xl font-extrabold text-(--ui-text-highlighted) tracking-tight">
            How much could Kluda save your store?
          </h3>
          <p class="text-sm text-(--ui-text-muted) mt-1">
            See how much your store protects by avoiding dedicated POS hardware and preventing downtime sales loss.
          </p>
        </div>

        <div class="space-y-2 p-4 rounded-2xl bg-(--ui-bg)/60 border border-(--ui-border)">
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-(--ui-text-highlighted) flex items-center gap-2">
              <UIcon name="i-lucide-monitor" class="w-4 h-4 text-emerald-500" />
              Number of Checkout Counters
            </span>
            <span class="font-mono text-base font-bold text-emerald-500 px-2.5 py-0.5 rounded-lg bg-emerald-500/10">
              {{ counters }} {{ counters === 1 ? 'Counter' : 'Counters' }}
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

        <div class="space-y-2 p-4 rounded-2xl bg-(--ui-bg)/60 border border-(--ui-border)">
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

        <div class="space-y-2 p-4 rounded-2xl bg-(--ui-bg)/60 border border-(--ui-border)">
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-(--ui-text-highlighted) flex items-center gap-2">
              <UIcon name="i-lucide-wifi-off" class="w-4 h-4 text-amber-500" />
              Estimated Weekly Internet Glitch Hours
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
            <span>0 hrs</span>
            <span>5 hrs</span>
            <span>12 hrs (Typical)</span>
            <span>25 hrs</span>
          </div>
        </div>
      </div>

      <div class="lg:col-span-5 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 border border-emerald-500/30 shadow-2xl relative overflow-hidden">
        <div class="absolute top-0 right-0 px-4 py-1.5 rounded-bl-2xl bg-emerald-500 text-slate-950 font-bold text-xs uppercase tracking-wider">
          Savings Projection
        </div>

        <div class="mb-6">
          <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Estimated Annual Savings</span>
          <div class="text-3xl sm:text-4xl font-extrabold text-emerald-400 font-mono mt-1">
            {{ formatNgn(totalAnnualSavings) }}
          </div>
          <p class="text-xs text-slate-400 mt-1">
            Hardware avoided upfront + potential sales protected during outages.
          </p>
        </div>

        <div class="space-y-4 pt-4 border-t border-slate-800 text-xs">
          <div class="flex items-center justify-between">
            <span class="text-slate-400 flex items-center gap-1.5">
              <UIcon name="i-lucide-monitor-check" class="w-4 h-4 text-emerald-400" />
              Hardware Purchase Avoided:
            </span>
            <span class="font-mono font-bold text-white">{{ formatNgn(hardwareSavings) }}</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-slate-400 flex items-center gap-1.5">
              <UIcon name="i-lucide-shield-check" class="w-4 h-4 text-emerald-400" />
              Sales Protected / Year:
            </span>
            <span class="font-mono font-bold text-emerald-300">{{ formatNgn(annualOutageSavings) }}</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-slate-400 flex items-center gap-1.5">
              <UIcon name="i-lucide-scan" class="w-4 h-4 text-emerald-400" />
              Barcode Scanner Expense:
            </span>
            <span class="font-mono font-bold text-emerald-400">₦0 (Camera Included)</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-slate-400 flex items-center gap-1.5">
              <UIcon name="i-lucide-sparkles" class="w-4 h-4 text-emerald-400" />
              Public Beta Access:
            </span>
            <span class="font-mono font-bold text-emerald-400">100% Free</span>
          </div>
        </div>

        <a :href="`${posUrl}/auth/register`" class="block mt-8">
          <button class="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-extrabold text-xs uppercase tracking-wider transition shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 cursor-pointer active:scale-95">
            <span>Start Selling Free</span>
            <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
          </button>
        </a>

        <p class="text-[10px] text-slate-400 text-center mt-3 italic">
          * Estimates are based on the parameters provided and are illustrative.
        </p>
      </div>
    </div>
  </div>
</template>
