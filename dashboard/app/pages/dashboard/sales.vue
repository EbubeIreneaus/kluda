<script setup lang="ts">
definePageMeta({ layout: 'dashboard' })

const { format } = useFormatCurrency()

const search = ref('')
const dateFilter = ref('')
const methodFilter = ref('all')
const statusFilter = ref('all')
const showDetailModal = ref(false)
const selectedSale = ref<any>(null)

const paymentOptions = ['all', 'cash', 'pos', 'transfer', 'online', 'debt']
const statusOptions = ['all', 'completed', 'pending', 'cancelled']

const salesStore = useSalesStore()


const sales = computed(() => {
  return salesStore.sales
})

const filteredSales = computed(() => {
  return sales.value.filter(sale => {
    if (search.value) {
      const q = search.value.toLowerCase()
      const matchId = sale.sale_id.toLowerCase().includes(q)
      const matchCustomer = sale.customer?.toLowerCase().includes(q)
      if (!matchId && !matchCustomer) return false
    }
    if (methodFilter.value && methodFilter.value !== 'all' && sale.method !== methodFilter.value) return false
    if (statusFilter.value && statusFilter.value !== 'all' && sale.status !== statusFilter.value) return false
    return true
  })
})

function openDetail(sale: any) {
  selectedSale.value = sale
  showDetailModal.value = true
}

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
  <div class="space-y-5">
    <!-- Header -->
    <div>
      <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Sales History</h2>
      <p class="text-sm text-(--ui-text-muted)">{{ filteredSales.length }} transactions</p>
    </div>

    <!-- Filters -->
    <div class="flex flex-col sm:flex-row gap-3">
      <UInput
        v-model="search"
        placeholder="Search by sale ID or customer..."
        icon="i-lucide-search"
        class="flex-1 max-w-sm"
      />
      <USelect
        v-model="methodFilter"
        :items="paymentOptions.map(v => ({ label: v === 'all' ? 'All Methods' : v.charAt(0).toUpperCase() + v.slice(1), value: v }))"
        placeholder="Payment Method"
        class="w-44"
      />
      <USelect
        v-model="statusFilter"
        :items="statusOptions.map(v => ({ label: v === 'all' ? 'All Status' : v.charAt(0).toUpperCase() + v.slice(1), value: v }))"
        placeholder="Status"
        class="w-36"
      />
    </div>

    <!-- Sales Table -->
    <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-(--ui-border) bg-(--ui-bg-accented)/30">
              <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Sale ID</th>
              <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Date</th>
              <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Customer</th>
              <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Items</th>
              <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Total</th>
              <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Method</th>
              <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Status</th>
              <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="sale in filteredSales"
              :key="sale.sale_id"
              class="border-b border-(--ui-border)/50 last:border-0 hover:bg-(--ui-bg-accented)/30 transition cursor-pointer"
              @click="openDetail(sale)"
            >
              <td class="py-3 px-4 font-mono text-xs text-(--ui-text-muted)">{{ sale.sale_id }}</td>
              <td class="py-3 px-4 text-(--ui-text-muted) text-xs">{{ sale.date }}</td>
              <td class="py-3 px-4 text-(--ui-text-highlighted)">{{ sale.customer || 'Walk-in' }}</td>
              <td class="py-3 px-4 text-center text-(--ui-text-muted)">{{ sale.items.length }}</td>
              <td class="py-3 px-4 text-right font-semibold text-(--ui-text-highlighted)">{{ format(sale.total) }}</td>
              <td class="py-3 px-4 text-center">
                <UBadge :color="methodColors[sale.method] as any" variant="subtle" size="xs">{{ sale.method }}</UBadge>
              </td>
              <td class="py-3 px-4 text-center">
                <UBadge :color="statusColors[sale.status] as any" variant="subtle" size="xs">{{ sale.status }}</UBadge>
              </td>
              <td class="py-3 px-4 text-right">
                <UButton variant="ghost" color="neutral" size="xs" icon="i-lucide-eye" @click.stop="openDetail(sale)" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Sale Detail Modal -->
    <UModal v-model:open="showDetailModal" title="Sale Details">
      <template #body>
        <div v-if="selectedSale" class="p-5 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="font-mono text-sm text-(--ui-text-muted)">{{ selectedSale.sale_id }}</p>
              <p class="text-xs text-(--ui-text-dimmed)">{{ selectedSale.date }}</p>
            </div>
            <UBadge :color="statusColors[selectedSale.status] as any" variant="subtle">
              {{ selectedSale.status }}
            </UBadge>
          </div>

          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-xs text-(--ui-text-dimmed)">Customer</p>
              <p class="font-medium text-(--ui-text-highlighted)">{{ selectedSale.customer || 'Walk-in' }}</p>
            </div>
            <div>
              <p class="text-xs text-(--ui-text-dimmed)">Staff</p>
              <p class="font-medium text-(--ui-text-highlighted)">{{ selectedSale.staff }}</p>
            </div>
            <div>
              <p class="text-xs text-(--ui-text-dimmed)">Payment Method</p>
              <UBadge :color="methodColors[selectedSale.method] as any" variant="subtle" size="xs" class="mt-1">
                {{ selectedSale.method }}
              </UBadge>
            </div>
          </div>

          <div class="border-t border-(--ui-border) pt-3">
            <p class="text-xs font-medium text-(--ui-text-dimmed) uppercase mb-2">Items</p>
            <div class="space-y-2">
              <div
                v-for="(item, idx) in selectedSale.items"
                :key="idx"
                class="flex justify-between text-sm p-2 rounded-lg bg-(--ui-bg-accented)/50"
              >
                <div>
                  <span class="text-(--ui-text-highlighted)">{{ item.name }}</span>
                  <span class="text-(--ui-text-dimmed) ml-2">× {{ item.qty }}</span>
                </div>
                <span class="font-medium text-(--ui-text-highlighted)">{{ format(item.price * item.qty) }}</span>
              </div>
            </div>
          </div>

          <div class="flex justify-between font-bold text-lg pt-2 border-t border-(--ui-border)">
            <span class="text-(--ui-text-highlighted)">Total</span>
            <span class="text-green-600 dark:text-green-400">{{ format(selectedSale.total) }}</span>
          </div>

          <div v-if="selectedSale.note" class="text-sm p-3 rounded-lg bg-(--ui-bg-accented)/50">
            <p class="text-xs text-(--ui-text-dimmed) mb-1">Staff Note</p>
            <p class="text-(--ui-text-muted)">{{ selectedSale.note }}</p>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
