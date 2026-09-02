<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface StaffMember {
  staff_id: string
  first_name: string
  last_name: string
  other_name?: string
  role: string
  email: string
  phone?: string
  permission: string[]
  status: string
  last_login?: string
  created_at: string
}

const auth = useAuthStore()
const toast = useToast()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const staffList = ref<StaffMember[]>([])
const isLoading = ref(false)
const search = ref('')

const statusColors: Record<string, string> = {
  active: 'success',
  suspended: 'warning',
  terminated: 'error'
}

function getStaffUrl(path = '') {
  const storeId = auth.store_id || auth.staff?.store_id || ''
  return `${apiBase}/${storeId}/staff${path}`
}

async function fetchStaffs() {
  const storeId = auth.store_id || auth.staff?.store_id
  if (!storeId) return

  isLoading.value = true
  try {
    const data = await $fetch<StaffMember[]>(getStaffUrl('/'), {
      headers: { Authorization: `Bearer ${auth.token ?? ''}` }
    })
    if (data && Array.isArray(data)) {
      staffList.value = data.map((s: any) => ({
        ...s,
        permission: Array.isArray(s.permission)
          ? s.permission.map((p: any) => (typeof p === 'string' ? p : p.value || String(p)))
          : []
      }))
    }
  } catch (err: any) {
    toast.add({
      title: 'Failed to load staff list',
      description: err?.data?.detail || 'Server error',
      color: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

const filteredStaff = computed(() => {
  if (!search.value) return staffList.value
  const q = search.value.toLowerCase()
  return staffList.value.filter(s =>
    `${s.first_name} ${s.last_name}`.toLowerCase().includes(q) ||
    s.email.toLowerCase().includes(q) ||
    s.role.toLowerCase().includes(q) ||
    s.staff_id.toLowerCase().includes(q)
  )
})

function formatLastLogin(dateStr?: string) {
  if (!dateStr) return 'Never'
  try {
    return new Date(dateStr).toLocaleDateString('en-NG', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

function copyStaffId(id: string) {
  navigator.clipboard.writeText(id)
  toast.add({ title: `Staff ID '${id}' copied`, color: 'success' })
}

onMounted(() => {
  fetchStaffs()
})
</script>

<template>
  <div class="space-y-5 max-w-7xl mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black tracking-tight text-(--ui-text-highlighted)">
          Store Team & Cashiers
        </h1>
        <p class="text-sm text-(--ui-text-muted) mt-1">
          {{ staffList.filter(s => s.status === 'active').length }} active team members assigned to this terminal branch.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <UButton
          icon="i-lucide-refresh-cw"
          variant="outline"
          color="neutral"
          :loading="isLoading"
          @click="fetchStaffs"
        >
          Refresh
        </UButton>

        <NuxtLink v-if="auth.isOwner" :to="`/marchant/stores/${auth.store_id || ''}`">
          <UButton color="primary" icon="i-lucide-user-plus" class="font-bold">
            Manage & Add Staff
          </UButton>
        </NuxtLink>
      </div>
    </div>

    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <UInput
        v-model="search"
        placeholder="Search staff by ID, name, email, role..."
        icon="i-lucide-search"
        class="max-w-sm w-full"
      />
    </div>

    <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden shadow-xs">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-(--ui-border) bg-(--ui-bg-accented)/30">
              <th class="text-left py-3.5 px-4 font-bold text-xs text-(--ui-text-muted)">Staff ID</th>
              <th class="text-left py-3.5 px-4 font-bold text-xs text-(--ui-text-muted)">Name</th>
              <th class="text-left py-3.5 px-4 font-bold text-xs text-(--ui-text-muted)">Role</th>
              <th class="text-left py-3.5 px-4 font-bold text-xs text-(--ui-text-muted)">Email & Contact</th>
              <th class="text-left py-3.5 px-4 font-bold text-xs text-(--ui-text-muted)">Permissions</th>
              <th class="text-center py-3.5 px-4 font-bold text-xs text-(--ui-text-muted)">Status</th>
              <th class="text-left py-3.5 px-4 font-bold text-xs text-(--ui-text-muted)">Last Active</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-(--ui-border)">
            <tr v-if="isLoading && staffList.length === 0">
              <td colspan="7" class="py-12 text-center text-(--ui-text-muted)">
                <UIcon name="i-lucide-loader" class="w-6 h-6 animate-spin inline-block mr-2 text-emerald-500" />
                Loading staff team...
              </td>
            </tr>
            <tr v-else-if="filteredStaff.length === 0">
              <td colspan="7" class="py-12 text-center text-(--ui-text-muted)">
                No staff members found.
              </td>
            </tr>
            <tr
              v-for="staff in filteredStaff"
              :key="staff.staff_id"
              class="hover:bg-(--ui-bg-accented)/20 transition"
            >
              <td class="py-3.5 px-4 font-mono text-xs font-bold text-emerald-400">
                <div class="flex items-center gap-1.5">
                  <span>{{ staff.staff_id }}</span>
                  <button
                    type="button"
                    class="text-(--ui-text-dimmed) hover:text-emerald-400 p-1 transition"
                    title="Copy Staff ID"
                    @click="copyStaffId(staff.staff_id)"
                  >
                    <UIcon name="i-lucide-copy" class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
              <td class="py-3.5 px-4 font-bold text-(--ui-text-highlighted)">
                {{ staff.first_name }} {{ staff.last_name }}
              </td>
              <td class="py-3.5 px-4">
                <span class="text-xs px-2.5 py-1 rounded-full bg-(--ui-bg-accented) font-semibold text-(--ui-text-highlighted) capitalize">
                  {{ staff.role }}
                </span>
              </td>
              <td class="py-3.5 px-4 text-xs text-(--ui-text-muted)">
                <div class="font-medium text-(--ui-text-highlighted)">{{ staff.email }}</div>
                <div v-if="staff.phone" class="text-[11px] text-(--ui-text-dimmed)">{{ staff.phone }}</div>
              </td>
              <td class="py-3.5 px-4 text-xs">
                <div class="flex flex-wrap gap-1 max-w-xs">
                  <span
                    v-for="perm in staff.permission.slice(0, 3)"
                    :key="perm"
                    class="text-[10px] px-2 py-0.5 rounded-md bg-(--ui-bg-accented) text-(--ui-text-muted) font-mono"
                  >
                    {{ perm }}
                  </span>
                  <span
                    v-if="staff.permission.length > 3"
                    class="text-[10px] px-1.5 py-0.5 rounded-md bg-(--ui-bg-accented) text-(--ui-text-dimmed)"
                  >
                    +{{ staff.permission.length - 3 }}
                  </span>
                </div>
              </td>
              <td class="py-3.5 px-4 text-center">
                <UBadge
                  :color="(statusColors[staff.status] as any) || 'neutral'"
                  size="sm"
                  variant="subtle"
                  class="font-bold uppercase tracking-wider text-[10px]"
                >
                  {{ staff.status }}
                </UBadge>
              </td>
              <td class="py-3.5 px-4 text-xs text-(--ui-text-muted)">
                {{ formatLastLogin(staff.last_login) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
