<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const colorMode = useColorMode()
const salesStore = useSalesStore()
const productStore = useProductsStore()

const products = computed(() => {
  const counts: Record<string, number> = {}

  salesStore.sales.forEach(s => {
    s.items?.forEach((item: any) => {
      const name = item.name || item.stock_slug || 'Unknown Product'
      counts[name] = (counts[name] || 0) + (item.qty || 1)
    })
  })

  const sorted = Object.entries(counts)
    .map(([name, sold]) => ({ name, sold }))
    .sort((a, b) => b.sold - a.sold)
    .slice(0, 5)

  if (sorted.length > 0) return sorted

  // Fallback if no sales recorded yet
  return productStore.products.slice(0, 5).map(p => ({
    name: p.name,
    sold: 0
  }))
})

const chartData = computed(() => ({
  labels: products.value.map(p => p.name),
  datasets: [{
    data: products.value.map(p => p.sold),
    backgroundColor: [
      'rgba(16, 185, 129, 0.8)',
      'rgba(59, 130, 246, 0.8)',
      'rgba(245, 158, 11, 0.8)',
      'rgba(139, 92, 246, 0.8)',
      'rgba(236, 72, 153, 0.8)'
    ],
    borderRadius: 6,
    borderSkipped: false,
    barThickness: 24
  }]
}))

const chartOptions = computed(() => {
  const isDark = colorMode.value === 'dark'
  const textColor = isDark ? '#94a3b8' : '#64748b'

  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y' as const,
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
          label: (ctx: any) => `${ctx.raw} units sold`
        }
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: textColor, font: { size: 11 } },
        border: { display: false }
      },
      y: {
        grid: { display: false },
        ticks: {
          color: textColor,
          font: { size: 11 },
          callback: function(_: any, index: number) {
            const label = products.value[index]?.name || ''
            return label.length > 18 ? label.slice(0, 18) + '…' : label
          }
        },
        border: { display: false }
      }
    }
  }
})
</script>

<template>
  <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-medium text-(--ui-text-muted)">Top Selling Products</h3>
        <p class="text-xs text-(--ui-text-dimmed) mt-0.5">By units sold</p>
      </div>
    </div>
    <div v-if="products.length > 0" class="h-[250px]">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="py-8 text-center">
      <UIcon name="i-lucide-package-open" class="w-8 h-8 text-(--ui-text-dimmed) mx-auto mb-2 opacity-60" />
      <p class="text-xs font-medium text-(--ui-text-muted)">No top selling products</p>
      <p class="text-[11px] text-(--ui-text-dimmed) mt-0.5">Add products to track sales data.</p>
    </div>
  </div>
</template>
