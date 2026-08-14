<script setup lang="ts">
import { computed } from 'vue'

definePageMeta({ layout: 'dashboard' })

const productStore = useProductsStore()
const salesStore = useSalesStore()
const { formatCompact } = useFormatCurrency()

const todayStr = computed(() => {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
})

const todaySales = computed(() => {
  return salesStore.sales.filter(s => s.date.startsWith(todayStr.value) && s.status !== 'cancelled')
})

const todayRevenueKobo = computed(() => {
  return todaySales.value.reduce((sum, s) => sum + (s.total || 0), 0)
})

const salesCount = computed(() => {
  return todaySales.value.length || salesStore.sales.length
})

const totalProducts = computed(() => {
  return productStore.productCount
})

const productsSoldToday = computed(() => {
  let count = 0
  todaySales.value.forEach(s => {
    s.items?.forEach((item: any) => {
      count += (item.qty || 1)
    })
  })
  return count
})

const kpis = computed(() => [
  { 
    title: "Today's Revenue", 
    value: formatCompact(todayRevenueKobo.value), 
    icon: 'i-lucide-banknote', 
    subtitle: `${todaySales.value.length} sales today`, 
    color: 'green' as const 
  },
  { 
    title: 'Sales Count', 
    value: String(salesCount.value), 
    icon: 'i-lucide-shopping-cart', 
    subtitle: `${todaySales.value.length} completed today`, 
    color: 'blue' as const 
  },
  { 
    title: 'Total Products', 
    value: String(totalProducts.value), 
    icon: 'i-lucide-package-check', 
    subtitle: `${productStore.lowStockProducts.length} low in stock`, 
    color: 'amber' as const 
  },
  { 
    title: 'Products Sold', 
    value: String(productsSoldToday.value), 
    icon: 'i-lucide-box', 
    subtitle: 'Units sold today', 
    color: 'violet' as const 
  }
])
</script>

<template>
  <div class="space-y-6">
    <!-- Welcome Header -->
    <div>
      <h2 class="text-2xl font-bold text-(--ui-text-highlighted)">Good day 👋</h2>
      <p class="text-sm text-(--ui-text-muted) mt-1">Here's what's happening with your store today.</p>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <DashboardKpiCard
        v-for="kpi in kpis"
        :key="kpi.title"
        v-bind="kpi"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="xl:col-span-2">
        <DashboardRevenueChart />
      </div>
      <DashboardPaymentMethodChart />
    </div>

    <!-- Bottom Row -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="xl:col-span-2">
        <DashboardRecentSalesTable />
      </div>
      <div class="space-y-4">
        <DashboardTopProductsChart />
        <DashboardLowStockAlert />
      </div>
    </div>
  </div>
</template>
