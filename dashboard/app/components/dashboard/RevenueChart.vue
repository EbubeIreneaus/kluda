<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const colorMode = useColorMode()
const { format } = useFormatCurrency()
const salesStore = useSalesStore()

const chartSeries = computed(() => {
  // Generate past 7 days dates as YYYY-MM-DD
  const days: { dateStr: string; label: string; totalKobo: number }[] = []
  const today = new Date()

  for (let i = 6; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const yyyy = d.getFullYear()
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const dateStr = `${yyyy}-${mm}-${dd}`
    const label = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    days.push({ dateStr, label, totalKobo: 0 })
  }

  // Sum sales per day
  salesStore.sales.forEach(sale => {
    if (sale.status === 'cancelled') return
    const saleDateStr = sale.date ? sale.date.split(' ')[0] : ''
    const match = days.find(d => d.dateStr === saleDateStr)
    if (match) {
      match.totalKobo += (sale.total || 0)
    }
  })

  return {
    labels: days.map(d => d.label),
    data: days.map(d => d.totalKobo)
  }
})

const chartData = computed(() => {
  const isDark = colorMode.value === 'dark'
  return {
    labels: chartSeries.value.labels,
    datasets: [{
      label: 'Revenue',
      data: chartSeries.value.data,
      borderColor: '#10B981',
      backgroundColor: isDark
        ? 'rgba(16, 185, 129, 0.08)'
        : 'rgba(16, 185, 129, 0.12)',
      borderWidth: 2.5,
      fill: true,
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 6,
      pointHoverBackgroundColor: '#10B981',
      pointHoverBorderColor: isDark ? '#1e293b' : '#ffffff',
      pointHoverBorderWidth: 3
    }]
  }
})

const chartOptions = computed(() => {
  const isDark = colorMode.value === 'dark'
  const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(148, 163, 184, 0.15)'
  const textColor = isDark ? '#94a3b8' : '#64748b'

  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index' as const
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: isDark ? '#1e293b' : '#ffffff',
        titleColor: isDark ? '#e2e8f0' : '#0f172a',
        bodyColor: isDark ? '#94a3b8' : '#64748b',
        borderColor: isDark ? '#334155' : '#e2e8f0',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          label: (ctx: any) => `Revenue: ${format(ctx.raw)}`
        }
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: textColor,
          font: { size: 11 }
        },
        border: { display: false }
      },
      y: {
        grid: { color: gridColor },
        ticks: {
          color: textColor,
          font: { size: 11 },
          callback: (val: any) => `₦${(val / 100).toLocaleString()}`
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
        <h3 class="text-sm font-medium text-(--ui-text-muted)">Revenue Overview</h3>
        <p class="text-xs text-(--ui-text-dimmed) mt-0.5">Last 7 days</p>
      </div>
    </div>
    <div class="h-[280px]">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
