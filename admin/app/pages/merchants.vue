<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { canManageMerchants } = useAdminPermission()

const merchants = ref<any[]>([])
const isLoading = ref(true)
const search = ref('')
const selectedStatus = ref('')
const selectedMerchant = ref<any | null>(null)
const isDetailOpen = ref(false)
const isActionLoading = ref(false)

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
    const detail = await apiFetch<any>(`/admin/merchants/${m.user_id}`)
    selectedMerchant.value = detail
    isDetailOpen.value = true
  } catch {
    // ignore
  }
}

async function toggleMerchantStatus(m: any) {
  const newStatus = m.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE'
  const reason = prompt(`Reason for setting status to ${newStatus}:`, 'Security check')
  if (reason === null) return

  isActionLoading.value = true
  try {
    await apiFetch(`/admin/merchants/${m.user_id}/status`, {
      method: 'PUT',
      body: { status: newStatus, reason }
    })
    if (selectedMerchant.value) {
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
        <p class="text-xs text-zinc-400 mt-0.5">Manage store owners, linked retail stores, and account security</p>
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
          <option value="ACTIVE">Active</option>
          <option value="SUSPENDED">Suspended</option>
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
                    'px-2 py-0.5 rounded text-[10px] font-semibold border',
                    m.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
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
                  :label="m.status === 'ACTIVE' ? 'Suspend' : 'Activate'"
                  size="xs"
                  :color="m.status === 'ACTIVE' ? 'error' : 'primary'"
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

    <AdminFullScreenModal
      v-if="selectedMerchant"
      v-model="isDetailOpen"
      :title="selectedMerchant.fullname"
      :description="'User ID: ' + selectedMerchant.user_id"
      max-width="max-w-lg"
    >
      <div class="flex flex-col gap-3 text-xs">
        <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between">
          <span class="text-zinc-400">Account Email</span>
          <span class="font-mono text-zinc-100">{{ selectedMerchant.email }}</span>
        </div>

        <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between">
          <span class="text-zinc-400">Phone Contact</span>
          <span class="font-mono text-zinc-100">{{ selectedMerchant.phone || 'None' }}</span>
        </div>

        <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between">
          <span class="text-zinc-400">Account Status</span>
          <span
            :class="[
              'px-2 py-0.5 rounded text-[10px] font-semibold border',
              selectedMerchant.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            ]"
          >
            {{ selectedMerchant.status }}
          </span>
        </div>

        <div class="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between">
          <span class="text-zinc-400">Registered On</span>
          <span class="text-zinc-200">{{ new Date(selectedMerchant.created_at).toLocaleString() }}</span>
        </div>

        <div class="flex flex-col gap-2 mt-2">
          <span class="font-semibold text-zinc-300">Retail Stores Owned ({{ selectedMerchant.stores?.length || 0 }})</span>
          <div class="flex flex-col gap-2">
            <div
              v-for="st in selectedMerchant.stores || []"
              :key="st.store_id"
              class="p-3 rounded-xl bg-zinc-950 border border-zinc-800 flex justify-between items-center"
            >
              <div class="font-medium text-zinc-200">{{ st.name }}</div>
              <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-zinc-800 text-zinc-300">
                {{ st.status }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex gap-2">
          <UButton
            label="Send Reset Code"
            icon="i-lucide-key-round"
            color="neutral"
            variant="outline"
            block
            :disabled="!canManageMerchants"
            @click="triggerReset(selectedMerchant)"
          />
          <UButton
            :label="selectedMerchant.status === 'ACTIVE' ? 'Suspend Merchant' : 'Activate Merchant'"
            :color="selectedMerchant.status === 'ACTIVE' ? 'error' : 'primary'"
            block
            :disabled="!canManageMerchants"
            :loading="isActionLoading"
            @click="toggleMerchantStatus(selectedMerchant)"
          />
        </div>
      </template>
    </AdminFullScreenModal>
  </div>
</template>
