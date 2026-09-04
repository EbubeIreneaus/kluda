<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { canManageMerchants, canManageStores } = useAdminPermission()

interface MerchantSubscription {
  plan_slug: string
  plan_name: string
  interval: string | null
  status: string
  amount: number
  is_trial: boolean
  next_renewal: string | null
}

interface MerchantStoreSummary {
  store_id: string
  name: string
  category: string | null
  status: string
  staff_count: number
  product_count: number
  total_sales_count: number
  total_revenue: number
  created_at: string
}

interface MerchantDetail {
  id: number
  user_id: string
  fullname: string
  email: string
  phone: string | null
  status: string
  subscription: MerchantSubscription | null
  stores: MerchantStoreSummary[]
  created_at: string
  last_login: string | null
}

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

const merchants = ref<any[]>([])
const isLoading = ref(true)
const search = ref('')
const selectedStatus = ref('')
const selectedMerchant = ref<MerchantDetail | null>(null)
const isDetailOpen = ref(false)
const isActionLoading = ref(false)

// For deep-inspecting a store from merchant detail
const selectedStoreDetail = ref<StoreDetail | null>(null)
const isStoreDetailOpen = ref(false)
const isStoreActionLoading = ref(false)

function isActive(status?: string | null) {
  return (status || '').toLowerCase() === 'active'
}

async function fetchMerchants() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    if (search.value) params.append('search', search.value)
    if (selectedStatus.value) params.append('status', selectedStatus.value)

    const data = await apiFetch<any[]>(`/admin/merchants?${params.toString()}`)
    merchants.value = data || []
  } catch {
    merchants.value = []
  } finally {
    isLoading.value = false
  }
}

async function viewMerchant(m: any) {
  try {
    const detail = await apiFetch<MerchantDetail>(`/admin/merchants/${m.user_id}`)
    selectedMerchant.value = detail
    isDetailOpen.value = true
  } catch {
    // ignore
  }
}

async function inspectStore(storeId: string) {
  try {
    const detail = await apiFetch<StoreDetail>(`/admin/stores/${storeId}`)
    selectedStoreDetail.value = detail
    isStoreDetailOpen.value = true
  } catch {
    // ignore
  }
}

async function toggleStoreStatus(newStatus?: string) {
  if (!selectedStoreDetail.value) return
  const targetStatus = newStatus || (isActive(selectedStoreDetail.value.status) ? 'suspended' : 'active')
  const reason = prompt(`Reason for setting store status to ${targetStatus}:`, 'Administrative review')
  if (reason === null) return

  isStoreActionLoading.value = true
  try {
    const updated = await apiFetch<StoreDetail>(`/admin/stores/${selectedStoreDetail.value.store_id}/status`, {
      method: 'PUT',
      body: { status: targetStatus, reason }
    })
    selectedStoreDetail.value = updated
    // Also update in selectedMerchant if open
    if (selectedMerchant.value) {
      const match = selectedMerchant.value.stores.find(s => s.store_id === updated.store_id)
      if (match) match.status = updated.status
    }
  } catch {
    // ignore
  } finally {
    isStoreActionLoading.value = false
  }
}

async function toggleMerchantStatus(m: any) {
  const currentlyActive = isActive(m.status)
  const newStatus = currentlyActive ? 'suspended' : 'active'
  const reason = prompt(`Reason for setting status to ${newStatus}:`, 'Security check')
  if (reason === null) return

  isActionLoading.value = true
  try {
    await apiFetch(`/admin/merchants/${m.user_id}/status`, {
      method: 'PUT',
      body: { status: newStatus, reason }
    })
    m.status = newStatus
    if (selectedMerchant.value && selectedMerchant.value.user_id === m.user_id) {
      selectedMerchant.value.status = newStatus
    }
    await fetchMerchants()
  } catch {
    // ignore
  } finally {
    isActionLoading.value = false
  }
}

async function triggerReset(m: any) {
  try {
    await apiFetch(`/admin/merchants/${m.user_id}/reset-password`, {
      method: 'POST'
    })
    alert(`Password reset code has been dispatched to ${m.email}`)
  } catch {
    alert('Failed to send reset code')
  }
}

const merchantTotalRevenue = computed(() => {
  if (!selectedMerchant.value?.stores) return 0
  return selectedMerchant.value.stores.reduce((acc, s) => acc + (s.total_revenue || 0), 0)
})

const merchantTotalStaff = computed(() => {
  if (!selectedMerchant.value?.stores) return 0
  return selectedMerchant.value.stores.reduce((acc, s) => acc + (s.staff_count || 0), 0)
})

const merchantTotalProducts = computed(() => {
  if (!selectedMerchant.value?.stores) return 0
  return selectedMerchant.value.stores.reduce((acc, s) => acc + (s.product_count || 0), 0)
})

function roleBadgeColor(role: string) {
  const r = (role || '').toLowerCase()
  if (r.includes('owner')) return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  if (r.includes('manager')) return 'bg-violet-500/10 text-violet-400 border-violet-500/20'
  return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
}

onMounted(() => {
  fetchMerchants()
})

watch([search, selectedStatus], () => {
  fetchMerchants()
})
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white">Merchant Accounts</h1>
        <p class="text-xs text-zinc-400 mt-0.5">Manage store owners, subscriptions, linked retail stores, and account security</p>
      </div>
      <div class="flex items-center gap-2">
        <UInput
          v-model="search"
          placeholder="Search by name or email..."
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
        </select>
      </div>
    </div>

    <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl overflow-hidden backdrop-blur-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px] tracking-wider">
            <tr>
              <th class="px-5 py-3.5">Merchant</th>
              <th class="px-5 py-3.5">Contact</th>
              <th class="px-5 py-3.5">Stores Owned</th>
              <th class="px-5 py-3.5">Status</th>
              <th class="px-5 py-3.5">Registered</th>
              <th class="px-5 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60">
            <tr v-if="isLoading">
              <td colspan="6" class="px-5 py-8 text-center text-zinc-500">Loading merchants...</td>
            </tr>
            <tr v-else-if="merchants.length === 0">
              <td colspan="6" class="px-5 py-8 text-center text-zinc-500">No merchants found.</td>
            </tr>
            <tr
              v-for="m in merchants"
              v-else
              :key="m.user_id"
              class="hover:bg-zinc-800/30 transition-colors"
            >
              <td class="px-5 py-3.5 font-medium text-zinc-100">{{ m.fullname }}</td>
              <td class="px-5 py-3.5">
                <div class="text-zinc-200">{{ m.email }}</div>
                <div class="text-[11px] text-zinc-400 font-mono">{{ m.phone || 'No phone' }}</div>
              </td>
              <td class="px-5 py-3.5 font-mono text-zinc-300">{{ m.store_count }}</td>
              <td class="px-5 py-3.5">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-semibold border uppercase',
                    isActive(m.status)
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  ]"
                >
                  {{ m.status }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-zinc-400">{{ new Date(m.created_at).toLocaleDateString() }}</td>
              <td class="px-5 py-3.5 text-right flex items-center justify-end gap-1.5">
                <UButton
                  label="Inspect"
                  size="xs"
                  color="neutral"
                  variant="outline"
                  icon="i-lucide-eye"
                  @click="viewMerchant(m)"
                />
                <UButton
                  :label="isActive(m.status) ? 'Suspend' : 'Activate'"
                  size="xs"
                  :color="isActive(m.status) ? 'error' : 'primary'"
                  variant="soft"
                  :loading="isActionLoading"
                  @click="toggleMerchantStatus(m)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Merchant FullScreen Inspection Modal -->
    <AdminFullScreenModal
      v-if="selectedMerchant"
      v-model="isDetailOpen"
      :title="selectedMerchant.fullname"
      :description="'User ID: ' + selectedMerchant.user_id"
      max-width="max-w-3xl"
    >
      <div class="flex flex-col gap-6 text-xs">
        <!-- Merchant Profile Header Card -->
        <div class="p-4 rounded-2xl bg-zinc-950/80 border border-zinc-800/90 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="size-12 rounded-2xl bg-gradient-to-tr from-blue-600/20 to-indigo-500/10 border border-blue-500/30 flex items-center justify-center font-bold text-base text-blue-400 shrink-0">
              {{ selectedMerchant.fullname.charAt(0).toUpperCase() }}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-base font-bold text-white">{{ selectedMerchant.fullname }}</h3>
                <span
                  :class="[
                    'px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider',
                    isActive(selectedMerchant.status)
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                      : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  ]"
                >
                  {{ selectedMerchant.status }}
                </span>
              </div>
              <p class="text-zinc-400 text-xs mt-0.5 flex items-center gap-2">
                <span class="font-mono text-zinc-300">{{ selectedMerchant.email }}</span>
                <span>•</span>
                <span>{{ selectedMerchant.phone || 'No phone' }}</span>
              </p>
            </div>
          </div>
          <div class="text-left sm:text-right text-[11px] text-zinc-500 font-mono">
            <div>Joined: {{ new Date(selectedMerchant.created_at).toLocaleDateString() }}</div>
            <div v-if="selectedMerchant.last_login">Last login: {{ new Date(selectedMerchant.last_login).toLocaleDateString() }}</div>
          </div>
        </div>

        <!-- Subscription Overview Card -->
        <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-credit-card" class="size-4 text-emerald-400" />
              <h4 class="font-semibold text-zinc-200 text-sm">Subscription Plan</h4>
            </div>
            <span
              v-if="selectedMerchant.subscription"
              :class="[
                'px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider',
                isActive(selectedMerchant.subscription.status)
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
              ]"
            >
              {{ selectedMerchant.subscription.status }}
            </span>
            <span v-else class="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-zinc-800/50 text-zinc-400 border-zinc-700/50">
              FREE TIER
            </span>
          </div>

          <div v-if="selectedMerchant.subscription" class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
            <div class="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/50">
              <div class="text-[10px] text-zinc-400 uppercase tracking-wider">Plan Name</div>
              <div class="font-bold text-zinc-100 text-sm mt-0.5">{{ selectedMerchant.subscription.plan_name }}</div>
              <span v-if="selectedMerchant.subscription.is_trial" class="inline-block mt-1 text-[9px] font-semibold text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                Trial Period
              </span>
            </div>
            <div class="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/50">
              <div class="text-[10px] text-zinc-400 uppercase tracking-wider">Price / Rate</div>
              <div class="font-bold text-emerald-400 font-mono text-sm mt-0.5">₦{{ Number(selectedMerchant.subscription.amount || 0).toLocaleString() }}</div>
              <div class="text-[10px] text-zinc-500">{{ selectedMerchant.subscription.interval || 'Monthly' }}</div>
            </div>
            <div class="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/50">
              <div class="text-[10px] text-zinc-400 uppercase tracking-wider">Plan Slug</div>
              <div class="font-mono text-zinc-300 text-xs mt-0.5">{{ selectedMerchant.subscription.plan_slug }}</div>
            </div>
            <div class="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/50">
              <div class="text-[10px] text-zinc-400 uppercase tracking-wider">Next Renewal</div>
              <div class="font-mono text-zinc-300 text-xs mt-0.5">
                {{ selectedMerchant.subscription.next_renewal ? new Date(selectedMerchant.subscription.next_renewal).toLocaleDateString() : 'N/A' }}
              </div>
            </div>
          </div>
          <div v-else class="text-zinc-500 text-xs py-2">
            This merchant does not have an active paid subscription plan.
          </div>
        </div>

        <!-- Aggregate Stats Cards -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <span class="text-[11px] font-medium text-zinc-400">Stores Owned</span>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ selectedMerchant.stores?.length || 0 }}</span>
            <span class="text-[10px] text-zinc-500">Retail branches</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <span class="text-[11px] font-medium text-zinc-400">Combined Revenue</span>
            <span class="font-mono font-bold text-lg text-emerald-400">₦{{ Number(merchantTotalRevenue).toLocaleString() }}</span>
            <span class="text-[10px] text-zinc-500">Across all stores</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <span class="text-[11px] font-medium text-zinc-400">Staff Employed</span>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ merchantTotalStaff }}</span>
            <span class="text-[10px] text-zinc-500">Total team members</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <span class="text-[11px] font-medium text-zinc-400">Catalog Size</span>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ merchantTotalProducts }}</span>
            <span class="text-[10px] text-zinc-500">Items across stores</span>
          </div>
        </div>

        <!-- Retail Stores Section with Deep Actions -->
        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-store" class="size-4 text-emerald-400" />
              <h4 class="font-semibold text-zinc-200 text-sm">Retail Stores & Branches ({{ selectedMerchant.stores?.length || 0 }})</h4>
            </div>
            <span class="text-[11px] text-zinc-500">Click inspect on any branch to view staff & details</span>
          </div>

          <div v-if="!selectedMerchant.stores || selectedMerchant.stores.length === 0" class="p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/40 text-center text-zinc-500">
            No retail stores registered under this merchant account.
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              v-for="st in selectedMerchant.stores"
              :key="st.store_id"
              class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col justify-between gap-3 hover:border-zinc-700/80 transition-all"
            >
              <div>
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <h5 class="font-bold text-zinc-100 text-sm">{{ st.name }}</h5>
                    <p class="text-[11px] text-zinc-400 mt-0.5">{{ st.category || 'Retail Store' }}</p>
                  </div>
                  <span
                    :class="[
                      'px-2 py-0.5 rounded text-[10px] font-bold border uppercase',
                      isActive(st.status)
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    ]"
                  >
                    {{ st.status }}
                  </span>
                </div>

                <!-- Mini metrics -->
                <div class="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-zinc-800/60 text-center">
                  <div class="p-1.5 rounded-lg bg-zinc-900/50">
                    <span class="text-[10px] text-zinc-500 block">Staff</span>
                    <span class="font-mono font-semibold text-zinc-200 text-xs">{{ st.staff_count }}</span>
                  </div>
                  <div class="p-1.5 rounded-lg bg-zinc-900/50">
                    <span class="text-[10px] text-zinc-500 block">Products</span>
                    <span class="font-mono font-semibold text-zinc-200 text-xs">{{ st.product_count }}</span>
                  </div>
                  <div class="p-1.5 rounded-lg bg-zinc-900/50">
                    <span class="text-[10px] text-zinc-500 block">Revenue</span>
                    <span class="font-mono font-semibold text-emerald-400 text-xs">₦{{ Number(st.total_revenue || 0).toLocaleString() }}</span>
                  </div>
                </div>
              </div>

              <!-- Store Action Button -->
              <div class="pt-2 flex items-center justify-end">
                <UButton
                  label="Inspect Store"
                  icon="i-lucide-external-link"
                  size="xs"
                  color="primary"
                  variant="soft"
                  @click="inspectStore(st.store_id)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-3">
          <UButton
            label="Send Password Reset"
            icon="i-lucide-key-round"
            color="neutral"
            variant="outline"
            :disabled="!canManageMerchants"
            @click="triggerReset(selectedMerchant)"
          />
          <UButton
            :label="isActive(selectedMerchant.status) ? 'Suspend Merchant' : 'Activate Merchant'"
            :color="isActive(selectedMerchant.status) ? 'error' : 'primary'"
            :disabled="!canManageMerchants"
            :loading="isActionLoading"
            @click="toggleMerchantStatus(selectedMerchant)"
          />
        </div>
      </template>
    </AdminFullScreenModal>

    <!-- Nested Store Inspection Modal for Deep Linking from Merchant -->
    <AdminFullScreenModal
      v-if="selectedStoreDetail"
      v-model="isStoreDetailOpen"
      :title="selectedStoreDetail.name"
      :description="'Store ID: ' + selectedStoreDetail.store_id"
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
                <h3 class="text-base font-bold text-white">{{ selectedStoreDetail.name }}</h3>
                <span
                  :class="[
                    'px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider',
                    isActive(selectedStoreDetail.status)
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                      : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  ]"
                >
                  {{ selectedStoreDetail.status }}
                </span>
              </div>
              <p class="text-zinc-400 text-xs mt-0.5 flex items-center gap-2">
                <span>{{ selectedStoreDetail.category || 'General Retail' }}</span>
                <span>•</span>
                <span>Currency: {{ selectedStoreDetail.currency }}</span>
                <span v-if="selectedStoreDetail.address">•</span>
                <span v-if="selectedStoreDetail.address" class="text-zinc-300">{{ selectedStoreDetail.address }}</span>
              </p>
            </div>
          </div>
          <div class="text-left md:text-right text-[11px] text-zinc-500 font-mono">
            Created: {{ new Date(selectedStoreDetail.created_at).toLocaleDateString() }}
          </div>
        </div>

        <!-- Metric KPI Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-zinc-400">Total Revenue</span>
              <UIcon name="i-lucide-banknote" class="size-4 text-emerald-400" />
            </div>
            <span class="font-mono font-bold text-lg text-emerald-400">₦{{ Number(selectedStoreDetail.total_revenue || 0).toLocaleString() }}</span>
            <span class="text-[10px] text-zinc-500">Gross sales</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-zinc-400">Total Sales</span>
              <UIcon name="i-lucide-receipt" class="size-4 text-blue-400" />
            </div>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ selectedStoreDetail.total_sales_count }}</span>
            <span class="text-[10px] text-zinc-500">Transactions</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-zinc-400">Products</span>
              <UIcon name="i-lucide-package" class="size-4 text-amber-400" />
            </div>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ selectedStoreDetail.product_count }}</span>
            <span class="text-[10px] text-zinc-500">Inventory items</span>
          </div>

          <div class="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-zinc-400">Customers</span>
              <UIcon name="i-lucide-users" class="size-4 text-purple-400" />
            </div>
            <span class="font-mono font-bold text-lg text-zinc-100">{{ selectedStoreDetail.customer_count }}</span>
            <span class="text-[10px] text-zinc-500">Clients recorded</span>
          </div>
        </div>

        <!-- Staff Roster Section -->
        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-user-check" class="size-4 text-emerald-400" />
              <h4 class="font-semibold text-zinc-200 text-sm">Staff & Cashiers Roster ({{ selectedStoreDetail.staff?.length || 0 }})</h4>
            </div>
            <span class="text-[11px] text-zinc-500">Store personnel</span>
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
                  <tr v-if="!selectedStoreDetail.staff || selectedStoreDetail.staff.length === 0">
                    <td colspan="4" class="px-4 py-6 text-center text-zinc-500">
                      No staff members registered for this store branch.
                    </td>
                  </tr>
                  <tr
                    v-for="st in selectedStoreDetail.staff"
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
          <UButton
            label="Close Store View"
            color="neutral"
            variant="outline"
            @click="isStoreDetailOpen = false"
          />
          <div class="flex items-center gap-2">
            <UButton
              v-if="!isActive(selectedStoreDetail.status)"
              label="Activate Store"
              icon="i-lucide-check-circle"
              color="primary"
              :disabled="!canManageStores"
              :loading="isStoreActionLoading"
              @click="toggleStoreStatus('active')"
            />
            <UButton
              v-else
              label="Suspend Store"
              icon="i-lucide-ban"
              color="error"
              :disabled="!canManageStores"
              :loading="isStoreActionLoading"
              @click="toggleStoreStatus('suspended')"
            />
          </div>
        </div>
      </template>
    </AdminFullScreenModal>
  </div>
</template>
