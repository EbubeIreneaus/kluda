<script setup lang="ts">
import { computed } from 'vue'

const { format } = useFormatCurrency()
const salesStore = useSalesStore()

const sales = computed(() => {
  return salesStore.sales.slice(0, 6).map(s => ({
    sale_id: s.sale_id,
    customer: s.customer,
    amount: s.total,
    method: s.method,
    status: s.status,
    time: s.date ? s.date.split(' ')[1] || s.date : 'Just now'
  }))
})

const methodColors: Record<string, string> = {
  cash: 'success',
  pos: 'info',
  transfer: 'warning',
  online: 'secondary',
  debt: 'error'
}

const statusColors: Record<string, string> = {
  completed: 'success',
  pending: 'warning',
  cancelled: 'error'
}
</script>

<template>
  <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-medium text-(--ui-text-muted)">Recent Sales</h3>
        <p class="text-xs text-(--ui-text-dimmed) mt-0.5">Latest transactions</p>
      </div>
      <UButton to="/sales" variant="ghost" color="neutral" size="xs" trailing-icon="i-lucide-arrow-right">
        View all
      </UButton>
    </div>

    <div v-if="sales.length > 0" class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-(--ui-border)">
            <th class="text-left py-2.5 px-3 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">ID</th>
            <th class="text-left py-2.5 px-3 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Customer</th>
            <th class="text-right py-2.5 px-3 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Amount</th>
            <th class="text-center py-2.5 px-3 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Method</th>
            <th class="text-center py-2.5 px-3 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Status</th>
            <th class="text-right py-2.5 px-3 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Time</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="sale in sales"
            :key="sale.sale_id"
            class="border-b border-(--ui-border)/50 last:border-0 hover:bg-(--ui-bg-accented)/50 transition"
          >
            <td class="py-2.5 px-3 font-mono text-xs text-(--ui-text-muted)">{{ sale.sale_id }}</td>
            <td class="py-2.5 px-3 text-(--ui-text-highlighted)">{{ sale.customer || 'Walk-in' }}</td>
            <td class="py-2.5 px-3 text-right font-medium text-(--ui-text-highlighted)">{{ format(sale.amount) }}</td>
            <td class="py-2.5 px-3 text-center">
              <UBadge :color="methodColors[sale.method] || 'neutral' as any" variant="subtle" size="xs">{{ sale.method }}</UBadge>
            </td>
            <td class="py-2.5 px-3 text-center">
              <UBadge :color="statusColors[sale.status] || 'neutral' as any" variant="subtle" size="xs">{{ sale.status }}</UBadge>
            </td>
            <td class="py-2.5 px-3 text-right text-(--ui-text-dimmed) text-xs">{{ sale.time }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="py-8 text-center">
      <UIcon name="i-lucide-shopping-bag" class="w-8 h-8 text-(--ui-text-dimmed) mx-auto mb-2 opacity-60" />
      <p class="text-xs font-medium text-(--ui-text-muted)">No recent transactions</p>
      <p class="text-[11px] text-(--ui-text-dimmed) mt-0.5">Sales made at the POS terminal will show up here.</p>
    </div>
  </div>
</template>
