<script setup lang="ts">
import { ref, computed } from 'vue'

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

const currentPage = ref(1)
const pageSize = ref(15)

const totalPages = computed(() => Math.max(1, Math.ceil(filteredSales.value.length / pageSize.value)))

const paginatedSales = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredSales.value.slice(start, start + pageSize.value)
})

watch([search, methodFilter, statusFilter], () => {
  currentPage.value = 1
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
    <div>
      <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Sales History</h2>
      <p class="text-sm text-(--ui-text-muted)">{{ filteredSales.length }} transactions</p>
    </div>

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

    <!-- Desktop Table View (>= md) -->
    <div class="hidden md:block rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden">
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
              v-for="sale in paginatedSales"
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

    <!-- Mobile Card List View (< md) -->
    <div class="block md:hidden space-y-3">
      <div
        v-if="filteredSales.length === 0"
        class="text-center py-12 px-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)"
      >
        <UIcon name="i-lucide-receipt" class="size-10 text-(--ui-text-dimmed) mx-auto mb-2" />
        <p class="text-sm font-semibold text-(--ui-text-highlighted)">No sales transactions found</p>
        <p class="text-xs text-(--ui-text-dimmed) mt-1">Transactions completed in the register will show up here</p>
      </div>

      <div
        v-for="sale in paginatedSales"
        :key="sale.sale_id"
        class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4 shadow-sm space-y-3 cursor-pointer active:scale-[0.99] transition"
        @click="openDetail(sale)"
      >
        <!-- Top: Sale ID, Date & Badges -->
        <div class="flex items-start justify-between gap-2">
          <div>
            <span class="font-mono text-xs font-semibold text-(--ui-text-dimmed)">
              #{{ sale.sale_id.slice(-8) }}
            </span>
            <p class="text-[11px] text-(--ui-text-dimmed) mt-0.5">
              {{ sale.date }}
            </p>
          </div>
          <div class="flex items-center gap-1.5">
            <UBadge :color="methodColors[sale.method] as any" variant="subtle" size="xs" class="capitalize">
              {{ sale.method }}
            </UBadge>
            <UBadge :color="statusColors[sale.status] as any" variant="subtle" size="xs" class="capitalize">
              {{ sale.status }}
            </UBadge>
          </div>
        </div>

        <!-- Middle: Customer & Item Count -->
        <div class="flex items-center justify-between text-xs py-2 px-3 rounded-xl bg-(--ui-bg-accented)/30 border border-(--ui-border)/40">
          <div class="flex items-center gap-1.5 min-w-0">
            <UIcon name="i-lucide-user" class="size-3.5 text-(--ui-text-dimmed) shrink-0" />
            <span class="font-medium text-(--ui-text-highlighted) truncate">
              {{ sale.customer || 'Walk-in Customer' }}
            </span>
          </div>
          <span class="text-(--ui-text-dimmed) font-mono shrink-0 ml-2">
            {{ sale.items.length }} {{ sale.items.length === 1 ? 'item' : 'items' }}
          </span>
        </div>

        <!-- Bottom: Total & View Receipt Affordance -->
        <div class="flex items-center justify-between pt-1 border-t border-(--ui-border)/40">
          <div>
            <span class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider block">Total Amount</span>
            <span class="text-base font-black text-green-600 dark:text-green-400 font-mono">
              {{ format(sale.total) }}
            </span>
          </div>
          <span class="text-xs font-semibold text-emerald-500 hover:text-emerald-400 flex items-center gap-1">
            Receipt
            <UIcon name="i-lucide-chevron-right" class="size-4" />
          </span>
        </div>
      </div>
    </div>

    <!-- Pagination Controls -->
    <div
      v-if="filteredSales.length > pageSize"
      class="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 text-xs text-(--ui-text-muted)"
    >
      <p>
        Showing
        <span class="font-bold text-(--ui-text-highlighted)">{{ (currentPage - 1) * pageSize + 1 }}</span>
        to
        <span class="font-bold text-(--ui-text-highlighted)">{{ Math.min(currentPage * pageSize, filteredSales.length) }}</span>
        of
        <span class="font-bold text-(--ui-text-highlighted)">{{ filteredSales.length }}</span>
        sales
      </p>

      <div class="flex items-center gap-1.5">
        <UButton
          size="xs"
          variant="outline"
          color="neutral"
          icon="i-lucide-chevron-left"
          :disabled="currentPage <= 1"
          @click="currentPage--"
        >
          Previous
        </UButton>

        <span class="px-3 py-1 rounded-lg bg-(--ui-bg-elevated) border border-(--ui-border) font-bold text-(--ui-text-highlighted) font-mono">
          {{ currentPage }} / {{ totalPages }}
        </span>

        <UButton
          size="xs"
          variant="outline"
          color="neutral"
          trailing-icon="i-lucide-chevron-right"
          :disabled="currentPage >= totalPages"
          @click="currentPage++"
        >
          Next
        </UButton>
      </div>
    </div>

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
