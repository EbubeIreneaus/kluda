<script setup lang="ts">

import type { AnalyticsPeriod } from '@/stores/analytics'

const { format, formatCompact } = useFormatCurrency()
const analyticsStore = useAnalyticsStore()
const { data, isLoading, error } = storeToRefs(analyticsStore)

type PeriodOption = { label: string; value: AnalyticsPeriod }
const periods: PeriodOption[] = [
  { label: 'Today', value: 'today' },
  { label: 'This Week', value: 'week' },
  { label: 'This Month', value: 'month' },
  { label: '3 Months', value: '3month' },
  { label: '6 Months', value: '6month' },
  { label: '12 Months', value: '12month' },
  { label: 'Custom', value: 'custom' },
]
const activePeriod = ref<AnalyticsPeriod>('month')
const customFrom = ref('')
const customTo = ref('')
const showCustomPicker = computed(() => activePeriod.value === 'custom')

function selectPeriod(p: AnalyticsPeriod) {
  activePeriod.value = p
  if (p !== 'custom') loadData()
}

function loadData() {
  if (activePeriod.value === 'custom') {
    if (!customFrom.value || !customTo.value) return
    analyticsStore.fetchAnalytics('custom', customFrom.value, customTo.value)
  } else {
    analyticsStore.fetchAnalytics(activePeriod.value)
  }
}

loadData()

const totalRevenue = computed(() => data.value?.total_revenue ?? 0)
const totalTx = computed(() => data.value?.total_transactions ?? 0)
const avgRevPerTx = computed(() =>
  totalTx.value > 0 ? Math.round(totalRevenue.value / totalTx.value) : 0
)

const paymentBreakdown = computed(() => {
  const bd = data.value?.payment_breakdown ?? {}
  return Object.entries(bd).map(([method, count]) => ({ method, count }))
})

const totalPaymentCount = computed(() =>
  paymentBreakdown.value.reduce((s, b) => s + b.count, 0)
)

const topProducts = computed(() => data.value?.top_products ?? [])
const maxQty = computed(() => Math.max(...topProducts.value.map(p => p.qty), 1))

const revenuePoints = computed(() => data.value?.revenue_series ?? [])
const maxRevenue = computed(() => Math.max(...revenuePoints.value.map(p => p.revenue), 1))

const dailyPoints = computed(() => data.value?.daily_series ?? [])
const maxCount = computed(() => Math.max(...dailyPoints.value.map(p => p.count), 1))

// mini sparkline: last 14 datapoints → bar heights as %
const sparkbarRevenue = computed(() => {
  const pts = revenuePoints.value.slice(-14)
  const mx = Math.max(...pts.map(p => p.revenue), 1)
  return pts.map(p => ({ ...p, pct: Math.round((p.revenue / mx) * 100) }))
})

const methodColors: Record<string, string> = {
  cash: 'bg-emerald-500',
  pos: 'bg-sky-500',
  transfer: 'bg-violet-500',
  debt: 'bg-rose-500',
  online: 'bg-amber-500',
}

const methodLabel: Record<string, string> = {
  cash: 'Cash',
  pos: 'POS Terminal',
  transfer: 'Bank Transfer',
  debt: 'Credit / Debt',
  online: 'Online',
}

function pctOf(n: number, total: number) {
  if (!total) return 0
  return Math.round((n / total) * 100)
}

const kpis = computed(() => [
  {
    label: 'Total Revenue',
    value: formatCompact(totalRevenue.value),
    sub: `${totalTx.value} transactions`,
    icon: 'i-lucide-banknote',
    color: 'emerald',
  },
  {
    label: 'Avg. Per Sale',
    value: formatCompact(avgRevPerTx.value),
    sub: 'average ticket size',
    icon: 'i-lucide-trending-up',
    color: 'sky',
  },
  {
    label: 'Transactions',
    value: String(totalTx.value),
    sub: 'completed sales',
    icon: 'i-lucide-shopping-cart',
    color: 'violet',
  },
  {
    label: 'Top Product',
    value: topProducts.value[0]?.name ?? '—',
    sub: topProducts.value[0] ? `${topProducts.value[0].qty} units sold` : 'no data',
    icon: 'i-lucide-award',
    color: 'amber',
  },
])

const colorMap: Record<string, string> = {
  emerald: 'text-emerald-500 bg-emerald-500/10',
  sky: 'text-sky-500 bg-sky-500/10',
  violet: 'text-violet-500 bg-violet-500/10',
  amber: 'text-amber-500 bg-amber-500/10',
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Analytics</h2>
        <p class="text-sm text-(--ui-text-muted)">
          <template v-if="data">
            {{ data.date_from }} → {{ data.date_to }}
          </template>
          <template v-else>Select a period to load data</template>
        </p>
      </div>
      <UButton
        icon="i-lucide-refresh-cw"
        variant="outline"
        color="neutral"
        :loading="isLoading"
        @click="loadData"
      >
        Refresh
      </UButton>
    </div>

    <div class="flex flex-wrap gap-2">
      <button
        v-for="p in periods"
        :key="p.value"
        :class="[
          'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
          activePeriod === p.value
            ? 'bg-green-500/10 text-green-600 dark:text-green-400 ring-1 ring-green-500/20'
            : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented)',
        ]"
        @click="selectPeriod(p.value)"
      >
        {{ p.label }}
      </button>
    </div>

    <transition name="slide-down">
      <div v-if="showCustomPicker" class="flex flex-wrap items-end gap-3 p-4 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)">
        <UFormField label="From">
          <UInput v-model="customFrom" type="date" />
        </UFormField>
        <UFormField label="To">
          <UInput v-model="customTo" type="date" />
        </UFormField>
        <UButton icon="i-lucide-search" :disabled="!customFrom || !customTo" @click="loadData">
          Load
        </UButton>
      </div>
    </transition>

    <div v-if="error" class="rounded-xl border border-rose-500/30 bg-rose-500/5 p-4 text-sm text-rose-500">
      <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 inline mr-2" />
      {{ error }}
    </div>

    <div v-if="isLoading && !data" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <div
        v-for="i in 4"
        :key="i"
        class="h-28 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) animate-pulse"
      />
    </div>

    <template v-if="data">
      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div
          v-for="kpi in kpis"
          :key="kpi.label"
          class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5 flex items-start gap-4 transition-all hover:shadow-sm"
        >
          <div :class="['w-10 h-10 rounded-lg flex items-center justify-center shrink-0', colorMap[kpi.color]]">
            <UIcon :name="kpi.icon" class="w-5 h-5" />
          </div>
          <div class="min-w-0">
            <p class="text-xs text-(--ui-text-dimmed) uppercase tracking-wide">{{ kpi.label }}</p>
            <p class="text-xl font-bold text-(--ui-text-highlighted) mt-0.5 truncate">{{ kpi.value }}</p>
            <p class="text-xs text-(--ui-text-muted) mt-0.5">{{ kpi.sub }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="font-semibold text-(--ui-text-highlighted)">Revenue Over Time</p>
            <p class="text-xs text-(--ui-text-muted)">Daily revenue in ₦</p>
          </div>
          <p class="text-sm font-medium text-green-500">{{ formatCompact(totalRevenue) }}</p>
        </div>

        <div v-if="revenuePoints.length === 0" class="flex items-center justify-center h-32 text-(--ui-text-dimmed) text-sm">
          No revenue data for this period
        </div>

        <div v-else class="space-y-3">
          <div class="flex items-end gap-1 h-40">
            <div
              v-for="pt in revenuePoints"
              :key="pt.date"
              class="flex-1 h-full group relative flex flex-col items-center justify-end"
              :title="`${pt.date}: ${format(pt.revenue)}`"
            >
              <div
                class="w-full rounded-t-sm bg-green-500/70 hover:bg-green-500 transition-all cursor-pointer min-h-[4px]"
                :style="{ height: `${Math.max(4, Math.round((pt.revenue / maxRevenue) * 100))}%` }"
              />
              <div class="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 rounded bg-(--ui-bg) border border-(--ui-border) text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition z-10 pointer-events-none shadow-md">
                {{ pt.date }}<br />{{ format(pt.revenue) }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1 text-xs text-(--ui-text-dimmed)">
            <div
              v-for="(pt, idx) in revenuePoints"
              :key="pt.date"
              class="flex-1 text-center truncate"
            >
              <span v-if="idx % Math.max(1, Math.floor(revenuePoints.length / 7)) === 0">
                {{ pt.date.slice(5) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
          <p class="font-semibold text-(--ui-text-highlighted) mb-1">Payment Methods</p>
          <p class="text-xs text-(--ui-text-muted) mb-4">Transaction share by method</p>
          <div v-if="paymentBreakdown.length === 0" class="text-center py-8 text-(--ui-text-dimmed) text-sm">
            No data
          </div>
          <div v-else class="space-y-3">
            <div v-for="item in paymentBreakdown" :key="item.method" class="space-y-1">
              <div class="flex items-center justify-between text-sm">
                <span class="font-medium text-(--ui-text-highlighted)">{{ methodLabel[item.method] ?? item.method }}</span>
                <span class="text-(--ui-text-muted)">{{ item.count }} ({{ pctOf(item.count, totalPaymentCount) }}%)</span>
              </div>
              <div class="h-2 rounded-full bg-(--ui-bg-accented) overflow-hidden">
                <div
                  :class="['h-full rounded-full transition-all', methodColors[item.method] ?? 'bg-green-500']"
                  :style="{ width: `${pctOf(item.count, totalPaymentCount)}%` }"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
          <p class="font-semibold text-(--ui-text-highlighted) mb-1">Daily Transactions</p>
          <p class="text-xs text-(--ui-text-muted) mb-4">Number of completed sales per day</p>
          <div v-if="dailyPoints.length === 0" class="text-center py-8 text-(--ui-text-dimmed) text-sm">No data</div>
          <div v-else class="space-y-3">
            <div class="flex items-end gap-1 h-32">
              <div
                v-for="pt in dailyPoints"
                :key="pt.date"
                class="flex-1 h-full group relative flex flex-col items-center justify-end"
                :title="`${pt.date}: ${pt.count} sales`"
              >
                <div
                  class="w-full rounded-t-sm bg-sky-500/70 hover:bg-sky-500 transition-all min-h-[4px]"
                  :style="{ height: `${Math.max(4, Math.round((pt.count / maxCount) * 100))}%` }"
                />
                <div class="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 rounded bg-(--ui-bg) border border-(--ui-border) text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition z-10 pointer-events-none shadow-md">
                  {{ pt.date }}<br />{{ pt.count }} sales
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1 text-xs text-(--ui-text-dimmed)">
              <div
                v-for="(pt, idx) in dailyPoints"
                :key="pt.date"
                class="flex-1 text-center truncate"
              >
                <span v-if="idx % Math.max(1, Math.floor(dailyPoints.length / 7)) === 0">
                  {{ pt.date.slice(5) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="font-semibold text-(--ui-text-highlighted)">Top Products</p>
            <p class="text-xs text-(--ui-text-muted)">By units sold in this period</p>
          </div>
        </div>
        <div v-if="topProducts.length === 0" class="text-center py-8 text-(--ui-text-dimmed) text-sm">
          No product data
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(prod, idx) in topProducts"
            :key="prod.name"
            class="flex items-center gap-4 group"
          >
            <div
              :class="[
                'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0',
                idx === 0 ? 'bg-amber-500/20 text-amber-500' :
                idx === 1 ? 'bg-neutral-400/20 text-neutral-400' :
                idx === 2 ? 'bg-orange-700/20 text-orange-700' :
                'bg-(--ui-bg-accented) text-(--ui-text-dimmed)'
              ]"
            >
              {{ idx + 1 }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <p class="text-sm font-medium text-(--ui-text-highlighted) truncate">{{ prod.name }}</p>
                <div class="flex items-center gap-3 text-xs shrink-0">
                  <span class="text-(--ui-text-muted)">{{ prod.qty }} units</span>
                  <span class="font-medium text-green-500">{{ formatCompact(prod.revenue) }}</span>
                </div>
              </div>
              <div class="h-2 rounded-full bg-(--ui-bg-accented) overflow-hidden">
                <div
                  class="h-full rounded-full bg-violet-500/70 group-hover:bg-violet-500 transition-all"
                  :style="{ width: `${Math.round((prod.qty / maxQty) * 100)}%` }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
        <div class="flex items-start justify-between mb-3">
          <div>
            <p class="font-semibold text-(--ui-text-highlighted)">Revenue Spark</p>
            <p class="text-xs text-(--ui-text-muted)">Last {{ sparkbarRevenue.length }} data points</p>
          </div>
          <div class="text-right">
            <p class="text-2xl font-bold text-green-500">{{ formatCompact(totalRevenue) }}</p>
            <p class="text-xs text-(--ui-text-muted)">total this period</p>
          </div>
        </div>
        <div class="flex items-end gap-0.5 h-16">
          <div
            v-for="pt in sparkbarRevenue"
            :key="pt.date"
            class="flex-1 rounded-t-sm transition-all hover:opacity-80 cursor-default"
            :class="pt.pct > 60 ? 'bg-green-500' : pt.pct > 30 ? 'bg-green-400' : 'bg-green-300/70'"
            :style="{ height: `${Math.max(8, pt.pct)}%` }"
            :title="`${pt.date}: ${format(pt.revenue)}`"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.slide-down-enter-from,
.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-4px);
}
.slide-down-enter-to,
.slide-down-leave-from {
  max-height: 200px;
  opacity: 1;
  transform: translateY(0);
}
</style>
