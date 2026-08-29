<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { canManageStores } = useAdminPermission()

const stores = ref<any[]>([])
const isLoading = ref(true)
const search = ref('')
const selectedStatus = ref('')
const selectedStore = ref<any | null>(null)
const isDetailOpen = ref(false)
const isUpdating = ref(false)

async function fetchStores() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    if (search.value) params.append('search', search.value)
    if (selectedStatus.value) params.append('status', selectedStatus.value)

    const data = await apiFetch<any[]>(`/admin/stores?${params.toString()}`)
    stores.value = data || []
  } catch {
    stores.value = []
  } finally {
    isLoading.value = false
  }
}

async function viewStore(store: any) {
  try {
    const detail = await apiFetch<any>(`/admin/stores/${store.store_id}`)
    selectedStore.value = detail
    isDetailOpen.value = true
  } catch {
    // ignore
  }
}

async function setStoreStatus(newStatus: string) {
  if (!selectedStore.value) return
  const reason = prompt(`Reason for setting store status to ${newStatus}:`, 'Administrative review')
  if (reason === null) return

  isUpdating.value = true
  try {
    const updated = await apiFetch<any>(`/admin/stores/${selectedStore.value.store_id}/status`, {
      method: 'PUT',
      body: { status: newStatus, reason }
    })
    selectedStore.value = updated
    await fetchStores()
  } catch {
    // ignore
  } finally {
    isUpdating.value = false
  }
}

onMounted(() => {
  fetchStores()
})

watch([search, selectedStatus], () => {
  fetchStores()
})
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white">Store Moderation</h1>
        <p class="text-xs text-zinc-400 mt-0.5">Inspect retail branches, sales transactions, staff accounts, and status</p>
      </div>
      <div class="flex items-center gap-2">
        <UInput
          v-model="search"
          placeholder="Search by store name..."
          icon="i-lucide-search"
          size="sm"
          class="w-64"
        />
        <select
          v-model="selectedStatus"
          class="bg-zinc-900 border border-zinc-800 text-xs rounded-lg px-3 py-1.5 text-zinc-300 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All Statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
          <option value="SUSPENDED">Suspended</option>
        </select>
      </div>
    </div>

    <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl overflow-hidden backdrop-blur-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px] tracking-wider">
            <tr>
              <th class="px-5 py-3.5">Store</th>
              <th class="px-5 py-3.5">Category</th>
              <th class="px-5 py-3.5">Staff</th>
              <th class="px-5 py-3.5">Products</th>
              <th class="px-5 py-3.5">Gross Sales</th>
              <th class="px-5 py-3.5">Status</th>
              <th class="px-5 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60">
            <tr v-if="isLoading">
              <td colspan="7" class="px-5 py-8 text-center text-zinc-500">Loading stores...</td>
            </tr>
            <tr v-else-if="stores.length === 0">
              <td colspan="7" class="px-5 py-8 text-center text-zinc-500">No stores found matching criteria.</td>
            </tr>
            <tr
              v-for="s in stores"
              v-else
              :key="s.store_id"
              class="hover:bg-zinc-800/30 transition-colors"
            >
              <td class="px-5 py-3.5 font-medium text-zinc-100">{{ s.name }}</td>
              <td class="px-5 py-3.5 text-zinc-400">{{ s.category || 'Retail' }}</td>
              <td class="px-5 py-3.5 font-mono text-zinc-300">{{ s.staff_count }}</td>
              <td class="px-5 py-3.5 font-mono text-zinc-300">{{ s.product_count }}</td>
              <td class="px-5 py-3.5 font-mono font-semibold text-emerald-400">₦{{ Number(s.total_revenue || 0).toLocaleString() }}</td>
              <td class="px-5 py-3.5">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-semibold border',
                    s.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                    s.status === 'SUSPENDED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                    'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                  ]"
                >
                  {{ s.status }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-right">
                <UButton
                  label="Inspect"
                  size="xs"
                  color="neutral"
                  variant="outline"
                  icon="i-lucide-eye"
                  @click="viewStore(s)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      v-if="isDetailOpen && selectedStore"
      class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end"
      @click="isDetailOpen = false"
    >
      <div
        class="w-full max-w-lg bg-zinc-900 border-l border-zinc-800 h-full p-6 flex flex-col justify-between overflow-y-auto"
        @click.stop
      >
        <div class="flex flex-col gap-6">
          <div class="flex items-center justify-between border-b border-zinc-800 pb-4">
            <div>
              <h2 class="text-base font-bold text-white">{{ selectedStore.name }}</h2>
              <div class="text-[11px] text-zinc-400 font-mono mt-0.5">Store ID: {{ selectedStore.store_id }}</div>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="sm" @click="isDetailOpen = false" />
          </div>

          <div class="flex flex-col gap-3 text-xs">
            <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between items-center">
              <span class="text-zinc-400">Store Owner</span>
              <div class="text-right">
                <div class="font-medium text-zinc-100">{{ selectedStore.owner_name || 'N/A' }}</div>
                <div class="text-[11px] text-emerald-400 font-mono">{{ selectedStore.owner_email }}</div>
              </div>
            </div>

            <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between">
              <span class="text-zinc-400">Address / Location</span>
              <span class="font-medium text-zinc-200">{{ selectedStore.address || 'Not specified' }}</span>
            </div>

            <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between">
              <span class="text-zinc-400">Category & Currency</span>
              <span class="font-medium text-zinc-200">{{ selectedStore.category || 'General' }} ({{ selectedStore.currency }})</span>
            </div>

            <div class="grid grid-cols-2 gap-2.5">
              <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex flex-col gap-1">
                <span class="text-[11px] text-zinc-400">Staff Cashiers</span>
                <span class="font-bold text-base text-zinc-100 font-mono">{{ selectedStore.staff_count }}</span>
              </div>
              <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex flex-col gap-1">
                <span class="text-[11px] text-zinc-400">Catalog Products</span>
                <span class="font-bold text-base text-zinc-100 font-mono">{{ selectedStore.product_count }}</span>
              </div>
            </div>

            <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between items-center">
              <div>
                <div class="text-zinc-400">Gross Sales Processed</div>
                <div class="text-[11px] text-zinc-400 mt-0.5">{{ selectedStore.total_sales_count }} sales transactions</div>
              </div>
              <span class="font-mono font-bold text-base text-emerald-400">₦{{ Number(selectedStore.total_revenue || 0).toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <div class="border-t border-zinc-800 pt-4 flex gap-2">
          <UButton
            v-if="selectedStore.status !== 'ACTIVE'"
            label="Activate Store"
            icon="i-lucide-check-circle"
            color="primary"
            block
            :disabled="!canManageStores"
            :loading="isUpdating"
            @click="setStoreStatus('ACTIVE')"
          />
          <UButton
            v-else
            label="Suspend Store"
            icon="i-lucide-ban"
            color="error"
            block
            :disabled="!canManageStores"
            :loading="isUpdating"
            @click="setStoreStatus('SUSPENDED')"
          />
        </div>
      </div>
    </div>
  </div>
</template>
