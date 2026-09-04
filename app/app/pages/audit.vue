<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

const auth = useAuthStore()
const { api } = useApi()
const toast = useToast()

const canViewAudit = computed(() => {
  return auth.isOwner || auth.hasPermission('view:audit-log') || auth.hasPermission('manage:all')
})

const effectiveStoreId = computed(() => {
  return auth.store_id || auth.staff?.store_id || ''
})

const loading = ref(false)
const logs = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(25)
const search = ref('')
const selectedCategory = ref('all')
const selectedAction = ref('all')

const showDetailModal = ref(false)
const activeLog = ref<any>(null)

const categories = [
  { label: 'All Activities', value: 'all', icon: 'i-lucide-activity' },
  { label: 'Products', value: 'product', icon: 'i-lucide-package' },
  { label: 'Stock Adjustments', value: 'stock', icon: 'i-lucide-boxes' },
  { label: 'Customers', value: 'customer', icon: 'i-lucide-users' },
  { label: 'Debts', value: 'debt', icon: 'i-lucide-credit-card' },
  { label: 'Staff & Team', value: 'staff', icon: 'i-lucide-shield-check' }
]

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit.value)))

async function fetchAuditLogs() {
  const storeId = effectiveStoreId.value
  if (!storeId || !canViewAudit.value) return

  loading.value = true
  try {
    const params: Record<string, any> = {
      limit: limit.value,
      offset: (page.value - 1) * limit.value
    }
    if (search.value.trim()) {
      params.search = search.value.trim()
    }
    if (selectedCategory.value !== 'all') {
      params.target_type = selectedCategory.value
    }
    if (selectedAction.value !== 'all') {
      params.action = selectedAction.value
    }

    const queryStr = new URLSearchParams(params).toString()
    const res = await api<any>(`/${storeId}/audit-logs?${queryStr}`)
    logs.value = res.items || []
    total.value = res.total || 0
  } catch (err: any) {
    toast.add({
      title: 'Failed to load audit logs',
      description: err?.data?.detail || err?.message || 'Server error',
      color: 'error'
    })
    logs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null
watch(search, () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    page.value = 1
    fetchAuditLogs()
  }, 350)
})

watch([selectedCategory, selectedAction], () => {
  page.value = 1
  fetchAuditLogs()
})

watch(page, () => {
  fetchAuditLogs()
})

watch(effectiveStoreId, (newId) => {
  if (newId) {
    page.value = 1
    fetchAuditLogs()
  }
})

onMounted(() => {
  fetchAuditLogs()
})

function inspectLog(log: any) {
  activeLog.value = log
  showDetailModal.value = true
}

function formatDate(isoString: string): string {
  if (!isoString) return '—'
  try {
    const d = new Date(isoString)
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return isoString
  }
}

function formatRelativeTime(isoString: string): string {
  if (!isoString) return ''
  try {
    const diffMs = Date.now() - new Date(isoString).getTime()
    const diffSec = Math.floor(diffMs / 1000)
    if (diffSec < 60) return 'just now'
    const diffMin = Math.floor(diffSec / 60)
    if (diffMin < 60) return `${diffMin}m ago`
    const diffHrs = Math.floor(diffMin / 60)
    if (diffHrs < 24) return `${diffHrs}h ago`
    const diffDays = Math.floor(diffHrs / 24)
    return `${diffDays}d ago`
  } catch {
    return ''
  }
}

function getActionMeta(action: string): { label: string; colorClass: string; icon: string; bgClass: string } {
  const lower = (action || '').toLowerCase()
  if (lower.includes('create') || lower.includes('add') || lower.includes('record')) {
    return {
      label: action,
      colorClass: 'text-emerald-400 border-emerald-500/30',
      bgClass: 'bg-emerald-500/10',
      icon: 'i-lucide-plus-circle'
    }
  }
  if (lower.includes('update') || lower.includes('edit')) {
    return {
      label: action,
      colorClass: 'text-amber-400 border-amber-500/30',
      bgClass: 'bg-amber-500/10',
      icon: 'i-lucide-edit-3'
    }
  }
  if (lower.includes('delete') || lower.includes('cancel') || lower.includes('terminate')) {
    return {
      label: action,
      colorClass: 'text-rose-400 border-rose-500/30',
      bgClass: 'bg-rose-500/10',
      icon: 'i-lucide-trash-2'
    }
  }
  if (lower.includes('adjust')) {
    return {
      label: action,
      colorClass: 'text-sky-400 border-sky-500/30',
      bgClass: 'bg-sky-500/10',
      icon: 'i-lucide-sliders'
    }
  }
  if (lower.includes('settle') || lower.includes('paid')) {
    return {
      label: action,
      colorClass: 'text-teal-400 border-teal-500/30',
      bgClass: 'bg-teal-500/10',
      icon: 'i-lucide-check-circle-2'
    }
  }
  return {
    label: action,
    colorClass: 'text-(--ui-text-muted) border-(--ui-border)',
    bgClass: 'bg-(--ui-bg-accented)/40',
    icon: 'i-lucide-info'
  }
}

function getTargetIcon(targetType: string): string {
  switch (targetType) {
    case 'product':
      return 'i-lucide-package'
    case 'stock':
      return 'i-lucide-boxes'
    case 'customer':
      return 'i-lucide-user'
    case 'debt':
      return 'i-lucide-credit-card'
    case 'staff':
      return 'i-lucide-shield-check'
    case 'sale':
      return 'i-lucide-shopping-cart'
    default:
      return 'i-lucide-folder'
  }
}
</script>

<template>
  <div class="space-y-6">
    <div
      v-if="!canViewAudit"
      class="p-8 text-center rounded-2xl border border-rose-500/20 bg-rose-500/5 max-w-lg mx-auto space-y-3"
    >
      <div class="size-12 rounded-full bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto">
        <UIcon name="i-lucide-shield-alert" class="size-6" />
      </div>
      <h3 class="text-base font-bold text-(--ui-text-highlighted)">Access Restricted</h3>
      <p class="text-xs text-(--ui-text-muted)">
        You do not have permission to view store audit logs. Please contact your store owner or manager.
      </p>
    </div>

    <template v-else>
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2.5">
            <div class="size-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <UIcon name="i-lucide-shield-check" class="size-5" />
            </div>
            <div>
              <h1 class="text-xl font-bold text-(--ui-text-highlighted) tracking-tight">
                Store Audit Trail
              </h1>
              <p class="text-xs text-(--ui-text-muted)">
                Immutable chronological log of sensitive staff operations and store actions
              </p>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2.5">
          <UButton
            variant="outline"
            color="neutral"
            icon="i-lucide-refresh-cw"
            :loading="loading"
            class="text-xs font-semibold cursor-pointer"
            @click="fetchAuditLogs"
          >
            Refresh
          </UButton>

          <div class="px-3 py-1.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/30 flex items-center gap-2">
            <span class="size-2 rounded-full bg-emerald-400 animate-pulse" />
            <span class="text-xs font-mono font-bold text-(--ui-text-highlighted)">
              {{ total }} Total Logs
            </span>
          </div>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-1.5 p-1 rounded-2xl border border-(--ui-border) bg-(--ui-bg-accented)/20">
        <button
          v-for="cat in categories"
          :key="cat.value"
          type="button"
          class="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer"
          :class="[
            selectedCategory === cat.value
              ? 'bg-(--ui-bg) text-(--ui-text-highlighted) shadow-sm border border-(--ui-border)'
              : 'text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented)/40'
          ]"
          @click="selectedCategory = cat.value"
        >
          <UIcon :name="cat.icon" class="size-3.5" />
          <span>{{ cat.label }}</span>
        </button>
      </div>

      <div class="flex flex-col sm:flex-row items-center gap-3">
        <div class="relative w-full sm:flex-1">
          <UInput
            v-model="search"
            placeholder="Search by actor, target name, action..."
            icon="i-lucide-search"
            class="w-full"
          />
          <button
            v-if="search"
            type="button"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-(--ui-text-dimmed) hover:text-(--ui-text-highlighted) text-xs"
            @click="search = ''"
          >
            <UIcon name="i-lucide-x" class="size-3.5" />
          </button>
        </div>
      </div>

      <div class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-accented)/10 overflow-hidden">
        <div v-if="loading && logs.length === 0" class="p-8 space-y-4">
          <div v-for="i in 5" :key="i" class="flex items-center gap-4 animate-pulse">
            <div class="size-8 rounded-full bg-(--ui-bg-accented)" />
            <div class="flex-1 space-y-2">
              <div class="h-3 w-1/3 rounded bg-(--ui-bg-accented)" />
              <div class="h-2.5 w-1/4 rounded bg-(--ui-bg-accented)/60" />
            </div>
            <div class="h-6 w-24 rounded-full bg-(--ui-bg-accented)" />
          </div>
        </div>

        <div v-else-if="logs.length === 0" class="p-12 text-center space-y-3">
          <div class="size-12 rounded-2xl bg-(--ui-bg-accented)/40 text-(--ui-text-dimmed) flex items-center justify-center mx-auto">
            <UIcon name="i-lucide-file-text" class="size-6" />
          </div>
          <h4 class="text-sm font-bold text-(--ui-text-highlighted)">No audit records found</h4>
          <p class="text-xs text-(--ui-text-muted) max-w-sm mx-auto">
            {{ search ? 'Try refining your search keyword or clearing active filters.' : 'Staff operations will appear here as activity occurs in this store.' }}
          </p>
          <UButton
            v-if="search || selectedCategory !== 'all'"
            variant="ghost"
            size="xs"
            color="primary"
            class="font-semibold cursor-pointer"
            @click="search = ''; selectedCategory = 'all'"
          >
            Reset Filters
          </UButton>
        </div>

        <div v-else>
          <div class="hidden md:block overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="bg-(--ui-bg-accented)/30 border-b border-(--ui-border) text-[11px] font-bold uppercase tracking-wider text-(--ui-text-dimmed)">
                <tr>
                  <th class="py-3 px-4">Timestamp</th>
                  <th class="py-3 px-4">Actor</th>
                  <th class="py-3 px-4">Action</th>
                  <th class="py-3 px-4">Target Entity</th>
                  <th class="py-3 px-4">Context / Diff</th>
                  <th class="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-(--ui-border)/40">
                <tr
                  v-for="log in logs"
                  :key="log.log_id"
                  class="hover:bg-(--ui-bg-accented)/20 transition cursor-pointer"
                  @click="inspectLog(log)"
                >
                  <td class="py-3 px-4 whitespace-nowrap">
                    <div class="font-medium text-(--ui-text-highlighted)">
                      {{ formatRelativeTime(log.created_at) }}
                    </div>
                    <div class="text-[10px] text-(--ui-text-dimmed) font-mono">
                      {{ formatDate(log.created_at) }}
                    </div>
                  </td>

                  <td class="py-3 px-4">
                    <div class="flex items-center gap-2.5">
                      <div class="size-7 rounded-full bg-emerald-500/10 text-emerald-400 font-bold flex items-center justify-center text-[11px] shrink-0">
                        {{ (log.actor_name || 'U').charAt(0).toUpperCase() }}
                      </div>
                      <div class="min-w-0">
                        <div class="font-bold text-(--ui-text-highlighted) truncate">
                          {{ log.actor_name || 'Unknown User' }}
                        </div>
                        <div class="text-[10px] text-(--ui-text-dimmed) truncate">
                          {{ log.actor_role || log.actor_email || 'Staff' }}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td class="py-3 px-4 whitespace-nowrap">
                    <span
                      class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-mono font-bold"
                      :class="[getActionMeta(log.action).bgClass, getActionMeta(log.action).colorClass]"
                    >
                      <UIcon :name="getActionMeta(log.action).icon" class="size-3 shrink-0" />
                      {{ log.action }}
                    </span>
                  </td>

                  <td class="py-3 px-4">
                    <div class="flex items-center gap-2">
                      <UIcon :name="getTargetIcon(log.target_type)" class="size-4 text-(--ui-text-dimmed) shrink-0" />
                      <div class="min-w-0">
                        <div class="font-semibold text-(--ui-text-highlighted) truncate">
                          {{ log.target_name || log.target_id || '—' }}
                        </div>
                        <div class="text-[10px] text-(--ui-text-dimmed) font-mono uppercase">
                          {{ log.target_type }}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td class="py-3 px-4 max-w-xs">
                    <div v-if="log.details?.changes" class="text-[11px] text-amber-400 font-medium truncate flex items-center gap-1.5">
                      <UIcon name="i-lucide-git-commit" class="size-3.5 shrink-0" />
                      <span>Modified: {{ Object.keys(log.details.changes).join(', ') }}</span>
                    </div>
                    <div v-else-if="log.details?.action_type && log.details?.quantity" class="text-[11px] text-sky-400 font-medium truncate flex items-center gap-1.5">
                      <UIcon name="i-lucide-arrow-left-right" class="size-3.5 shrink-0" />
                      <span>{{ log.details.action_type }}: {{ log.details.quantity }} units</span>
                    </div>
                    <div v-else-if="log.details?.price" class="text-[11px] text-(--ui-text-muted) truncate">
                      Price: ₦{{ Number(log.details.price).toLocaleString() }}
                    </div>
                    <div v-else-if="log.details?.amount" class="text-[11px] text-(--ui-text-muted) truncate">
                      Amount: ₦{{ Number(log.details.amount).toLocaleString() }}
                    </div>
                    <div v-else class="text-[11px] text-(--ui-text-dimmed) italic truncate">
                      {{ log.details ? 'Payload recorded' : 'No extra details' }}
                    </div>
                  </td>

                  <td class="py-3 px-4 text-right whitespace-nowrap">
                    <UButton
                      size="xs"
                      variant="ghost"
                      color="neutral"
                      icon="i-lucide-eye"
                      class="cursor-pointer"
                      @click.stop="inspectLog(log)"
                    >
                      Inspect
                    </UButton>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="md:hidden divide-y divide-(--ui-border)/40">
            <div
              v-for="log in logs"
              :key="log.log_id"
              class="p-4 space-y-2.5 hover:bg-(--ui-bg-accented)/20 transition cursor-pointer"
              @click="inspectLog(log)"
            >
              <div class="flex items-center justify-between gap-2">
                <span
                  class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-mono font-bold"
                  :class="[getActionMeta(log.action).bgClass, getActionMeta(log.action).colorClass]"
                >
                  <UIcon :name="getActionMeta(log.action).icon" class="size-3" />
                  {{ log.action }}
                </span>
                <span class="text-[10px] text-(--ui-text-dimmed)">
                  {{ formatRelativeTime(log.created_at) }}
                </span>
              </div>

              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <div class="text-xs font-bold text-(--ui-text-highlighted) truncate">
                    {{ log.target_name || log.target_id || log.target_type }}
                  </div>
                  <div class="text-[11px] text-(--ui-text-dimmed) flex items-center gap-1.5 mt-0.5">
                    <span>by</span>
                    <span class="font-medium text-(--ui-text-muted)">{{ log.actor_name || 'Staff' }}</span>
                    <span v-if="log.actor_role" class="px-1.5 py-0.2 rounded bg-(--ui-bg-accented) text-[9px] uppercase font-mono">
                      {{ log.actor_role }}
                    </span>
                  </div>
                </div>

                <UButton
                  size="xs"
                  variant="outline"
                  color="neutral"
                  icon="i-lucide-chevron-right"
                  class="shrink-0"
                />
              </div>

              <div v-if="log.details?.changes" class="text-[10px] text-amber-400 font-mono bg-amber-500/5 p-1.5 rounded-lg border border-amber-500/10">
                Modified: {{ Object.keys(log.details.changes).join(', ') }}
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="total > limit"
          class="p-4 bg-(--ui-bg-accented)/20 border-t border-(--ui-border) flex items-center justify-between gap-2"
        >
          <span class="text-xs text-(--ui-text-dimmed)">
            Page {{ page }} of {{ totalPages }} ({{ total }} total)
          </span>

          <div class="flex items-center gap-2">
            <UButton
              size="xs"
              variant="outline"
              color="neutral"
              icon="i-lucide-chevron-left"
              :disabled="page <= 1 || loading"
              class="cursor-pointer"
              @click="page--"
            >
              Previous
            </UButton>
            <UButton
              size="xs"
              variant="outline"
              color="neutral"
              icon="i-lucide-chevron-right"
              :disabled="page >= totalPages || loading"
              class="cursor-pointer"
              @click="page++"
            >
              Next
            </UButton>
          </div>
        </div>
      </div>
    </template>

    <AppBottomSheet
      v-model="showDetailModal"
      title="Audit Event Details"
      description="Immutable activity record captured at event execution."
      max-width="max-w-xl"
    >
      <div v-if="activeLog" class="space-y-4 p-1">
        <div class="flex items-center justify-between p-3.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/20">
          <div class="space-y-1">
            <span class="text-[10px] font-bold uppercase tracking-wider text-(--ui-text-dimmed)">
              Event Action
            </span>
            <div class="flex items-center gap-2">
              <span
                class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-mono font-bold"
                :class="[getActionMeta(activeLog.action).bgClass, getActionMeta(activeLog.action).colorClass]"
              >
                <UIcon :name="getActionMeta(activeLog.action).icon" class="size-3.5 shrink-0" />
                {{ activeLog.action }}
              </span>
            </div>
          </div>

          <div class="text-right space-y-1">
            <span class="text-[10px] font-bold uppercase tracking-wider text-(--ui-text-dimmed)">
              Timestamp
            </span>
            <div class="text-xs font-mono text-(--ui-text-highlighted)">
              {{ formatDate(activeLog.created_at) }}
            </div>
          </div>
        </div>

        <div class="p-3.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/10 space-y-3">
          <h5 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-dimmed) flex items-center gap-2">
            <UIcon name="i-lucide-user" class="size-3.5" />
            Actor Information
          </h5>

          <div class="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span class="text-[10px] text-(--ui-text-dimmed) block">Full Name</span>
              <span class="font-bold text-(--ui-text-highlighted)">{{ activeLog.actor_name || 'System / Unknown' }}</span>
            </div>
            <div>
              <span class="text-[10px] text-(--ui-text-dimmed) block">Role</span>
              <span class="font-mono text-emerald-400 capitalize">{{ activeLog.actor_role || 'Staff' }}</span>
            </div>
            <div>
              <span class="text-[10px] text-(--ui-text-dimmed) block">Email</span>
              <span class="font-mono text-(--ui-text-muted) truncate block">{{ activeLog.actor_email || '—' }}</span>
            </div>
            <div>
              <span class="text-[10px] text-(--ui-text-dimmed) block">Client IP Address</span>
              <span class="font-mono text-(--ui-text-muted)">{{ activeLog.ip_address || '0.0.0.0' }}</span>
            </div>
          </div>
        </div>

        <div class="p-3.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/10 space-y-3">
          <h5 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-dimmed) flex items-center gap-2">
            <UIcon name="i-lucide-target" class="size-3.5" />
            Target Entity
          </h5>

          <div class="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span class="text-[10px] text-(--ui-text-dimmed) block">Entity Type</span>
              <span class="font-bold text-(--ui-text-highlighted) uppercase font-mono">{{ activeLog.target_type }}</span>
            </div>
            <div>
              <span class="text-[10px] text-(--ui-text-dimmed) block">Entity Identifier</span>
              <span class="font-mono text-(--ui-text-muted) truncate block">{{ activeLog.target_id || '—' }}</span>
            </div>
            <div class="col-span-2">
              <span class="text-[10px] text-(--ui-text-dimmed) block">Entity Name / Label</span>
              <span class="font-semibold text-(--ui-text-highlighted)">{{ activeLog.target_name || '—' }}</span>
            </div>
          </div>
        </div>

        <div class="p-3.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/10 space-y-3">
          <h5 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-dimmed) flex items-center gap-2">
            <UIcon name="i-lucide-file-code" class="size-3.5" />
            Captured Context & Diff
          </h5>

          <div v-if="activeLog.details?.changes" class="space-y-2">
            <div
              v-for="(diff, field) in activeLog.details.changes"
              :key="field"
              class="p-2.5 rounded-lg border border-(--ui-border) bg-(--ui-bg) space-y-1.5"
            >
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold font-mono text-(--ui-text-highlighted)">{{ field }}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono">modified</span>
              </div>

              <div class="grid grid-cols-2 gap-2 text-xs font-mono">
                <div class="p-2 rounded bg-rose-500/5 border border-rose-500/10 text-rose-400">
                  <span class="text-[9px] text-rose-300 uppercase block">Previous</span>
                  <span class="truncate block">{{ diff.old !== null && diff.old !== undefined ? diff.old : 'null' }}</span>
                </div>
                <div class="p-2 rounded bg-emerald-500/5 border border-emerald-500/10 text-emerald-400">
                  <span class="text-[9px] text-emerald-300 uppercase block">New</span>
                  <span class="truncate block">{{ diff.new !== null && diff.new !== undefined ? diff.new : 'null' }}</span>
                </div>
              </div>
            </div>
          </div>

          <pre
            v-else-if="activeLog.details"
            class="p-3 rounded-lg bg-(--ui-bg) border border-(--ui-border) text-[11px] font-mono text-(--ui-text-muted) overflow-x-auto max-h-48"
          >{{ JSON.stringify(activeLog.details, null, 2) }}</pre>

          <p v-else class="text-xs text-(--ui-text-dimmed) italic">
            No additional payload was attached to this event.
          </p>
        </div>

        <div class="text-[10px] font-mono text-(--ui-text-dimmed) text-center">
          Event ID: {{ activeLog.log_id }}
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end">
          <UButton
            variant="outline"
            color="neutral"
            class="cursor-pointer"
            @click="showDetailModal = false"
          >
            Close
          </UButton>
        </div>
      </template>
    </AppBottomSheet>
  </div>
</template>
