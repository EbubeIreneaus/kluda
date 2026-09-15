<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { debtStatusColors } from './types'

const props = defineProps<{
  debts: any[]
  search: string
}>()

const emit = defineEmits<{
  (e: 'edit-debt', debt: any): void
  (e: 'add-debt'): void
}>()

const { format } = useFormatCurrency()
const toast = useToast()
const customerStore = useCustomerStore()

const isMarkingPaid = ref<string | null>(null)
const statusFilter = ref<'all' | 'unpaid' | 'paid' | 'overdue'>('all')
const currentPage = ref(1)
const pageSize = ref(10)

const statusCounts = computed(() => ({
  all: props.debts.length,
  unpaid: props.debts.filter((d) => d.status === 'unpaid').length,
  overdue: props.debts.filter((d) => d.status === 'overdue').length,
  paid: props.debts.filter((d) => d.status === 'paid').length,
}))

const filteredDebts = computed(() => {
  return props.debts.filter((d) => {
    const matchesStatus =
      statusFilter.value === 'all' || d.status === statusFilter.value
    if (!matchesStatus) return false

    if (!props.search) return true
    const q = props.search.toLowerCase()
    return (
      (d.customer_name && d.customer_name.toLowerCase().includes(q)) ||
      (d.note && d.note.toLowerCase().includes(q)) ||
      (d.debtor_id && d.debtor_id.toLowerCase().includes(q))
    )
  })
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredDebts.value.length / pageSize.value))
)

const paginatedDebts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredDebts.value.slice(start, start + pageSize.value)
})

watch([() => props.search, statusFilter], () => {
  currentPage.value = 1
})

const totalOutstanding = computed(() =>
  props.debts
    .filter((d) => d.status !== 'paid')
    .reduce((sum, d) => sum + d.amount, 0)
)

const unpaidCount = computed(() =>
  props.debts.filter((d) => d.status === 'unpaid').length
)

async function markAsPaid(debt: any) {
  isMarkingPaid.value = debt.debtor_id
  try {
    await customerStore.deleteDebtor(debt.debtor_id)
    toast.add({
      title: 'Debt marked as paid',
      description: `${debt.customer_name} — ${format(debt.amount)}`,
      color: 'success',
      icon: 'i-lucide-check-circle',
    })
  } catch (err: any) {
    toast.add({
      title: 'Failed to mark as paid',
      description: err?.data?.detail ?? 'Unknown error',
      color: 'error',
      icon: 'i-lucide-alert-circle',
    })
  } finally {
    isMarkingPaid.value = null
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Stat Summary Cards + Quick Action -->
    <div class="grid grid-cols-2 gap-4">
      <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4">
        <p class="text-xs text-(--ui-text-dimmed)">Total Outstanding</p>
        <p class="text-xl font-bold text-amber-500 mt-1">
          {{ format(totalOutstanding) }}
        </p>
      </div>
      <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4">
        <p class="text-xs text-(--ui-text-dimmed)">Unpaid Debts</p>
        <p class="text-xl font-bold text-(--ui-text-highlighted) mt-1">
          {{ unpaidCount }}
        </p>
      </div>
    </div>

    <!-- Status Filter Pills -->
    <div class="flex flex-wrap items-center gap-1.5 pt-1">
      <button
        v-for="filter in [
          { key: 'all', label: 'All Debts', count: statusCounts.all },
          { key: 'unpaid', label: 'Unpaid', count: statusCounts.unpaid },
          { key: 'overdue', label: 'Overdue', count: statusCounts.overdue },
          { key: 'paid', label: 'Paid', count: statusCounts.paid }
        ]"
        :key="filter.key"
        type="button"
        :class="[
          'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer border',
          statusFilter === filter.key
            ? 'bg-green-500/10 text-green-600 dark:text-green-400 ring-1 ring-green-500/20 border-green-500/30 font-semibold'
            : 'border-(--ui-border)/60 bg-(--ui-bg-elevated) text-(--ui-text-muted) hover:bg-(--ui-bg-accented)'
        ]"
        @click="statusFilter = filter.key as any"
      >
        <span>{{ filter.label }}</span>
        <span
          :class="[
            'px-1.5 py-0.5 rounded-full text-[10px] tabular-nums font-mono',
            statusFilter === filter.key
              ? 'bg-green-500/20 text-green-700 dark:text-green-300 font-bold'
              : 'bg-(--ui-bg-accented) text-(--ui-text-dimmed)'
          ]"
        >
          {{ filter.count }}
        </span>
      </button>
    </div>

    <!-- Empty State -->
    <div
      v-if="filteredDebts.length === 0"
      class="text-center py-12 px-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)"
    >
      <UIcon name="i-lucide-banknote" class="size-10 text-(--ui-text-dimmed) mx-auto mb-2" />
      <p class="text-sm font-semibold text-(--ui-text-highlighted)">No debt records found</p>
      <p class="text-xs text-(--ui-text-dimmed) mt-1">
        {{ statusFilter !== 'all' ? `No debts matching the "${statusFilter}" filter` : 'Customers with credit or unpaid balances will appear here' }}
      </p>
      <UButton
        size="sm"
        color="primary"
        variant="soft"
        icon="i-lucide-plus"
        class="mt-4"
        @click="emit('add-debt')"
      >
        Record Debt
      </UButton>
    </div>

    <!-- Debts List -->
    <div v-else class="space-y-3">
      <div
        v-for="debt in paginatedDebts"
        :key="debt.debtor_id"
        :class="[
          'rounded-xl border p-4 transition-all',
          debt.status === 'overdue'
            ? 'border-rose-500/30 bg-rose-500/5'
            : 'border-(--ui-border) bg-(--ui-bg-elevated)'
        ]"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <UAvatar
              :text="debt.customer_name ? debt.customer_name.split(' ').map((n: string) => n[0]).join('') : 'D'"
              size="sm"
            />
            <div class="min-w-0">
              <p class="font-medium text-(--ui-text-highlighted) truncate">
                {{ debt.customer_name || 'Walk-in Customer' }}
              </p>
              <p v-if="debt.note" class="text-xs text-(--ui-text-dimmed) mt-0.5 truncate">
                {{ debt.note }}
              </p>
            </div>
          </div>
          <div class="text-right shrink-0">
            <p class="text-lg font-bold text-(--ui-text-highlighted) font-mono">
              {{ format(debt.amount) }}
            </p>
            <UBadge :color="debtStatusColors[debt.status] as any" variant="subtle" size="xs" class="capitalize">
              {{ debt.status }}
            </UBadge>
          </div>
        </div>

        <div class="flex items-center justify-between mt-3 pt-3 border-t border-(--ui-border)/50 text-xs">
          <span class="text-(--ui-text-dimmed)">Created: {{ new Date(debt.created_at).toLocaleDateString() }}</span>
          <div class="flex items-center gap-2">
            <UButton
              size="xs"
              variant="ghost"
              color="primary"
              icon="i-lucide-pencil"
              title="Edit Debt"
              @click="emit('edit-debt', debt)"
            />
            <UButton
              v-if="debt.status !== 'paid'"
              size="xs"
              variant="soft"
              color="success"
              icon="i-lucide-check"
              :loading="isMarkingPaid === debt.debtor_id"
              @click="markAsPaid(debt)"
            >
              Mark Paid
            </UButton>
            <UBadge v-else color="success" variant="subtle" size="xs">
              <UIcon name="i-lucide-check-circle" class="w-3 h-3 mr-1" />
              Paid
            </UBadge>
          </div>
        </div>
      </div>

      <!-- Pagination Controls -->
      <div
        v-if="filteredDebts.length > pageSize"
        class="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 text-xs text-(--ui-text-muted)"
      >
        <p>
          Showing
          <span class="font-bold text-(--ui-text-highlighted)">{{
            (currentPage - 1) * pageSize + 1
          }}</span>
          to
          <span class="font-bold text-(--ui-text-highlighted)">{{
            Math.min(currentPage * pageSize, filteredDebts.length)
          }}</span>
          of
          <span class="font-bold text-(--ui-text-highlighted)">{{
            filteredDebts.length
          }}</span>
          debts
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

          <span
            class="px-3 py-1 rounded-lg bg-(--ui-bg-elevated) border border-(--ui-border) font-bold text-(--ui-text-highlighted) font-mono"
          >
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
    </div>
  </div>
</template>
