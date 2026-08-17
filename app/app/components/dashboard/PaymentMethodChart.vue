<script setup lang="ts">
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const colorMode = useColorMode()
const salesStore = useSalesStore()

const methodConfigs = [
  { key: 'cash', label: 'Cash', color: '#10B981' },
  { key: 'pos', label: 'POS', color: '#3B82F6' },
  { key: 'transfer', label: 'Transfer', color: '#F59E0B' },
  { key: 'online', label: 'Online', color: '#8B5CF6' },
  { key: 'debt', label: 'Debt', color: '#EF4444' }
]

const methods = computed(() => {
  const totalSales = salesStore.sales.length
  if (totalSales === 0) {
    return methodConfigs.map(m => ({ ...m, value: 0 }))
  }

  const counts: Record<string, number> = { cash: 0, pos: 0, transfer: 0, online: 0, debt: 0 }
  salesStore.sales.forEach(s => {
    const m = (s.method || 'cash').toLowerCase()
    if (counts[m] !== undefined) {
      counts[m]++
    }
  })

  return methodConfigs.map(m => ({
    ...m,
    value: Math.round(((counts[m.key] || 0) / totalSales) * 100)
  }))
})

const chartData = computed(() => {
  const totalSales = salesStore.sales.length
  const data = totalSales === 0 ? [100] : methods.value.map(m => m.value)
  const bgColors = totalSales === 0 ? ['rgba(148, 163, 184, 0.2)'] : methods.value.map(m => m.color)

  return {
    labels: totalSales === 0 ? ['No Data'] : methods.value.map(m => m.label),
    datasets: [{
      data,
      backgroundColor: bgColors,
      borderWidth: 0,
      hoverOffset: 6,
      spacing: 2
    }]
  }
})

const chartOptions = computed(() => {
  const isDark = colorMode.value === 'dark'
  return {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '72%',
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: isDark ? '#1e293b' : '#ffffff',
        titleColor: isDark ? '#e2e8f0' : '#0f172a',
        bodyColor: isDark ? '#94a3b8' : '#64748b',
        borderColor: isDark ? '#334155' : '#e2e8f0',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: (ctx: any) => `${ctx.label}: ${ctx.raw}%`
        }
      }
    }
  }
})
</script>

<template>
  <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
    <div class="mb-4">
      <h3 class="text-sm font-medium text-(--ui-text-muted)">Payment Methods</h3>
      <p class="text-xs text-(--ui-text-dimmed) mt-0.5">Distribution across sales</p>
    </div>
    <div class="flex items-center gap-6">
      <div class="relative w-[160px] h-[160px] shrink-0">
        <Doughnut :data="chartData" :options="chartOptions" />
        <div class="absolute inset-0 flex flex-col items-center justify-center">
          <span class="text-2xl font-bold text-(--ui-text-highlighted)">{{ salesStore.sales.length }}</span>
          <span class="text-xs text-(--ui-text-dimmed)">Sales</span>
        </div>
      </div>
      <div class="flex-1 space-y-2.5">
        <div
          v-for="method in methods"
          :key="method.label"
          class="flex items-center justify-between text-sm"
        >
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ backgroundColor: method.color }" />
            <span class="text-(--ui-text-muted)">{{ method.label }}</span>
          </div>
          <span class="font-medium text-(--ui-text-highlighted)">{{ method.value }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>
