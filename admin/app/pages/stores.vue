<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { canManageStores } = useAdminPermission()

interface StoreStaffItem {
  id: number
  user_id: string
  fullname: string
  email: string
  role: string
  status: string
  created_at: string
}

interface StoreDetail {
  id: number
  store_id: string
  owner_id: string
  owner_name: string | null
  owner_email: string | null
  name: string
  address: string | null
  category: string | null
  currency: string
  status: string
  staff_count: number
  product_count: number
  customer_count: number
  total_sales_count: number
  total_revenue: number
  staff: StoreStaffItem[]
  created_at: string
  updated_at: string
}

const stores = ref<any[]>([])
const isLoading = ref(true)
const search = ref('')
const selectedStatus = ref('')
const selectedStore = ref<StoreDetail | null>(null)
const isDetailOpen = ref(false)
const isUpdating = ref(false)

function isActive(status?: string | null) {
  return (status || '').toLowerCase() === 'active'
}

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
    const detail = await apiFetch<StoreDetail>(`/admin/stores/${store.store_id}`)
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
    const updated = await apiFetch<StoreDetail>(`/admin/stores/${selectedStore.value.store_id}/status`, {
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

function roleBadgeColor(role: string) {
  const r = (role || '').toLowerCase()
  if (r.includes('owner')) return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  if (r.includes('manager')) return 'bg-violet-500/10 text-violet-400 border-violet-500/20'
  return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
}

onMounted(() => {
  fetchStores()
})

watch([search, selectedStatus], () => {
  fetchStores()
})
</script>

<template>
  <div class="overflow-y-auto p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
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
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="deactivated">Deactivated</option>
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
                    'px-2 py-0.5 rounded text-[10px] font-semibold border uppercase',
                    isActive(s.status)
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
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

    <!-- Store Deep Inspection FullScreen Modal -->
    <AdminFullScreenModal
      v-if="selectedStore"
      v-model="isDetailOpen"
      :title="selectedStore.name"
      :description="'Store ID: ' + selectedStore.store_id"
      max-width="max-w-3xl"
    >
      <div class="flex flex-col gap-6 text-xs">
        <!-- Store Overview Header Banner -->
        <div class="p-4 rounded-2xl bg-zinc-950/80 border border-zinc-800/90 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="size-12 rounded-2xl bg-gradient-to-tr from-emerald-600/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
              <UIcon name="i-lucide-store" class="size-6 text-emerald-400" />
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-base font-bold text-white">{{ selectedStore.name }}</h3>
                <span
                  :class="[
                    'px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider',
                    isActive(selectedStore.status)
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                      : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  ]"
                >
                  {{ selectedStore.status }}
                </span>
              </div>
              <p class="text-zinc-400 text-xs mt-0.5 flex items-center gap-2">
                <span>{{ selectedStore.category || 'General Retail' }}</span>
                <span>•</span>
                <span>Currency: {{ selectedStore.currency }}</span>
                <span v-if="selectedStore.address">•</span>
                <span v-if="selectedStore.address" class="text-zinc-300">{{ selectedStore.address }}</span>
              </p>
            </div>
          </div>
          <div class="text-left md:text-right text-[11px] text-zinc-500 font-mono">
            Created: {{ new Date(selectedStore.created_at).toLocaleDateString() }}
          </div>
        </div>

        <!-- Metric KPI Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-zinc-400">Total Revenue</span>
              <UIcon name="i-lucide-banknote" class="size-4 text-emerald-400" />
            </div>
            <span class="font-mono font-bold text-lg text-emerald-400">₦{{ Number(selectedStore.total_revenue || 0).toLocaleString() }}</span>
            <span class="text-[10px] text-zinc-500">Gross sales processed</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-zinc-400">Total Sales</span>
              <UIcon name="i-lucide-receipt" class="size-4 text-blue-400" />
            </div>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ selectedStore.total_sales_count }}</span>
            <span class="text-[10px] text-zinc-500">Transactions logged</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-zinc-400">Products</span>
              <UIcon name="i-lucide-package" class="size-4 text-amber-400" />
            </div>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ selectedStore.product_count }}</span>
            <span class="text-[10px] text-zinc-500">Inventory items (privacy safe)</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-zinc-400">Customers</span>
              <UIcon name="i-lucide-users" class="size-4 text-purple-400" />
            </div>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ selectedStore.customer_count }}</span>
            <span class="text-[10px] text-zinc-500">Profiles on record</span>
          </div>
        </div>

        <!-- Store Owner Profile Card -->
        <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="size-10 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-zinc-200">
              {{ (selectedStore.owner_name || 'U').charAt(0).toUpperCase() }}
            </div>
            <div>
              <div class="text-[10px] uppercase tracking-wider font-semibold text-zinc-500">Merchant Account (Owner)</div>
              <div class="font-medium text-zinc-100 text-sm">{{ selectedStore.owner_name || 'Unknown' }}</div>
              <div class="text-zinc-400 font-mono text-[11px]">{{ selectedStore.owner_email }}</div>
            </div>
          </div>
          <div class="text-right sm:text-right">
            <span class="text-[10px] text-zinc-500 font-mono block">Owner ID:</span>
            <span class="text-[11px] font-mono text-zinc-300">{{ selectedStore.owner_id }}</span>
          </div>
        </div>

        <!-- Staff Roster Section -->
        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-user-check" class="size-4 text-emerald-400" />
              <h4 class="font-semibold text-zinc-200 text-sm">Store Staff & Cashiers ({{ selectedStore.staff?.length || 0 }})</h4>
            </div>
            <span class="text-[11px] text-zinc-500">Assigned operators</span>
          </div>

          <div class="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs">
                <thead class="bg-zinc-950 border-b border-zinc-800/80 text-zinc-400 font-semibold uppercase text-[10px] tracking-wider">
                  <tr>
                    <th class="px-4 py-3">Member</th>
                    <th class="px-4 py-3">Role</th>
                    <th class="px-4 py-3">Status</th>
                    <th class="px-4 py-3 text-right">Joined</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-800/50">
                  <tr v-if="!selectedStore.staff || selectedStore.staff.length === 0">
                    <td colspan="4" class="px-4 py-6 text-center text-zinc-500">
                      No staff members registered for this store branch.
                    </td>
                  </tr>
                  <tr
                    v-for="st in selectedStore.staff"
                    v-else
                    :key="st.id"
                    class="hover:bg-zinc-800/20 transition-colors"
                  >
                    <td class="px-4 py-3">
                      <div class="font-medium text-zinc-200">{{ st.fullname }}</div>
                      <div class="text-zinc-500 font-mono text-[11px]">{{ st.email }}</div>
                    </td>
                    <td class="px-4 py-3">
                      <span :class="['px-2 py-0.5 rounded text-[10px] font-semibold border uppercase', roleBadgeColor(st.role)]">
                        {{ st.role }}
                      </span>
                    </td>
                    <td class="px-4 py-3">
                      <span
                        :class="[
                          'px-2 py-0.5 rounded text-[10px] font-semibold border uppercase',
                          isActive(st.status)
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                        ]"
                      >
                        {{ st.status }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-right text-zinc-400 font-mono text-[11px]">
                      {{ new Date(st.created_at).toLocaleDateString() }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-3">
          <div class="text-xs text-zinc-500">
            Current Status: <span class="font-semibold uppercase text-zinc-300">{{ selectedStore.status }}</span>
          </div>
          <div class="flex items-center gap-2">
            <UButton
              v-if="!isActive(selectedStore.status)"
              label="Activate Store"
              icon="i-lucide-check-circle"
              color="primary"
              :disabled="!canManageStores"
              :loading="isUpdating"
              @click="setStoreStatus('active')"
            />
            <UButton
              v-else
              label="Suspend Store"
              icon="i-lucide-ban"
              color="error"
              :disabled="!canManageStores"
              :loading="isUpdating"
              @click="setStoreStatus('suspended')"
            />
          </div>
        </div>
      </template>
    </AdminFullScreenModal>
  </div>
</template>
