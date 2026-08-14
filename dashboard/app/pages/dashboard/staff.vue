<script setup lang="ts">
definePageMeta({ layout: 'dashboard' })

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

// Add Staff Modal State
const showAddModal = ref(false)
const isAddingStaff = ref(false)
const newStaff = ref({
  first_name: '',
  last_name: '',
  other_name: '',
  email: '',
  phone: '',
  role: 'staff',
  password: '',
  permissions: ['manage:user'] as string[],
  status: 'active'
})

// Edit Staff Modal State
const showEditModal = ref(false)
const isEditingStaff = ref(false)
const selectedStaffId = ref('')
const editStaffForm = ref({
  first_name: '',
  last_name: '',
  other_name: '',
  email: '',
  phone: '',
  role: 'staff',
  status: 'active',
  permissions: [] as string[]
})

const roles = [
  { label: 'Staff / Cashier', value: 'staff' },
  { label: 'Manager', value: 'manager' },
  { label: 'Admin', value: 'admin' }
]

const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Suspended', value: 'suspended' },
  { label: 'Terminated', value: 'terminated' }
]

const permissionOptions = [
  { label: 'Manage All (Super Admin)', value: 'manage:all' },
  { label: 'Manage Staff', value: 'manage:staff' },
  { label: 'Manage Products & Stock', value: 'manage:product' },
  { label: 'POS & Record Sales', value: 'record:sales' },
  { label: 'Manage Customers & Debts', value: 'manage:user' },
  { label: 'View Analytics & Reports', value: 'view:analytics' }
]

const statusColors: Record<string, string> = {
  active: 'success',
  suspended: 'warning',
  terminated: 'error'
}

async function fetchStaffs() {
  isLoading.value = true
  try {
    const data = await $fetch<StaffMember[]>(`${apiBase}/staff/`, {
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

async function handleAddStaff() {
  if (!newStaff.value.first_name || !newStaff.value.last_name || !newStaff.value.email || !newStaff.value.password) {
    toast.add({ title: 'Missing required fields', color: 'warning' })
    return
  }

  isAddingStaff.value = true
  try {
    const payload = {
      first_name: newStaff.value.first_name,
      last_name: newStaff.value.last_name,
      other_name: newStaff.value.other_name || undefined,
      email: newStaff.value.email,
      phone: newStaff.value.phone || undefined,
      role: newStaff.value.role,
      password: newStaff.value.password,
      permission: newStaff.value.permissions,
      status: newStaff.value.status
    }

    const created = await $fetch<StaffMember>(`${apiBase}/staff/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.token ?? ''}`
      },
      body: payload
    })

    toast.add({
      title: 'Staff member added',
      description: `${created.first_name} ${created.last_name} (${created.staff_id})`,
      color: 'success'
    })

    showAddModal.value = false
    newStaff.value = {
      first_name: '',
      last_name: '',
      other_name: '',
      email: '',
      phone: '',
      role: 'staff',
      password: '',
      permissions: ['manage:user'],
      status: 'active'
    }

    await fetchStaffs()
  } catch (err: any) {
    toast.add({
      title: 'Failed to add staff',
      description: err?.data?.detail || 'Server error',
      color: 'error'
    })
  } finally {
    isAddingStaff.value = false
  }
}

function openEditStaff(staff: StaffMember) {
  selectedStaffId.value = staff.staff_id
  editStaffForm.value = {
    first_name: staff.first_name,
    last_name: staff.last_name,
    other_name: staff.other_name || '',
    email: staff.email,
    phone: staff.phone || '',
    role: staff.role || 'staff',
    status: staff.status || 'active',
    permissions: [...(staff.permission || [])]
  }
  showEditModal.value = true
}

async function handleUpdateStaff() {
  if (!selectedStaffId.value) return

  isEditingStaff.value = true
  try {
    const payload = {
      first_name: editStaffForm.value.first_name,
      last_name: editStaffForm.value.last_name,
      other_name: editStaffForm.value.other_name || undefined,
      email: editStaffForm.value.email,
      phone: editStaffForm.value.phone || undefined,
      role: editStaffForm.value.role,
      status: editStaffForm.value.status,
      permission: editStaffForm.value.permissions
    }

    await $fetch(`${apiBase}/staff/${selectedStaffId.value}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.token ?? ''}`
      },
      body: payload
    })

    toast.add({
      title: 'Staff member updated',
      description: `${editStaffForm.value.first_name} ${editStaffForm.value.last_name}`,
      color: 'success'
    })

    showEditModal.value = false
    await fetchStaffs()
  } catch (err: any) {
    toast.add({
      title: 'Failed to update staff',
      description: err?.data?.detail || 'Server error',
      color: 'error'
    })
  } finally {
    isEditingStaff.value = false
  }
}

async function changeStatus(staff: StaffMember, status: string) {
  try {
    await $fetch(`${apiBase}/staff/${staff.staff_id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.token ?? ''}`
      },
      body: { status }
    })

    staff.status = status
    const actionLabel = status === 'active' ? 'Reactivated' : status === 'suspended' ? 'Suspended' : 'Terminated'
    toast.add({
      title: actionLabel,
      description: `${staff.first_name} ${staff.last_name}`,
      color: status === 'active' ? 'success' : 'warning'
    })
  } catch (err: any) {
    toast.add({
      title: 'Failed to update status',
      description: err?.data?.detail || 'Server error',
      color: 'error'
    })
  }
}

onMounted(() => {
  if (auth.hasPermission('manage:staff')) {
    fetchStaffs()
  }
})
</script>

<template>
  <div class="space-y-5">
    <!-- Permission guard fallback -->
    <template v-if="!auth.hasPermission('manage:staff')">
      <div class="flex flex-col items-center justify-center py-20 text-center">
        <div class="w-16 h-16 rounded-full bg-rose-500/10 flex items-center justify-center mb-4">
          <UIcon name="i-lucide-shield-x" class="w-8 h-8 text-rose-500" />
        </div>
        <h3 class="text-lg font-semibold text-(--ui-text-highlighted)">Access Denied</h3>
        <p class="text-sm text-(--ui-text-muted) mt-1">You don't have permission to manage staff.</p>
      </div>
    </template>

    <template v-else>
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Staff Management</h2>
          <p class="text-sm text-(--ui-text-muted)">
            {{ staffList.filter(s => s.status === 'active').length }} active staff members • {{ staffList.length }} total
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
          <UButton icon="i-lucide-user-plus" @click="showAddModal = true">
            Add Staff
          </UButton>
        </div>
      </div>

      <!-- Search -->
      <UInput
        v-model="search"
        placeholder="Search staff by ID, name, email, or role..."
        icon="i-lucide-search"
        class="max-w-sm"
      />

      <!-- Staff Table -->
      <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-(--ui-border) bg-(--ui-bg-accented)/30">
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Staff ID</th>
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Staff Member</th>
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Role</th>
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Permissions</th>
                <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Status</th>
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Last Login</th>
                <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading && staffList.length === 0">
                <td colspan="7" class="py-8 text-center text-(--ui-text-dimmed)">
                  <UIcon name="i-lucide-loader-2" class="w-5 h-5 animate-spin inline mr-2" />
                  Loading staff members...
                </td>
              </tr>
              <tr v-else-if="filteredStaff.length === 0">
                <td colspan="7" class="py-8 text-center text-(--ui-text-dimmed)">
                  No staff members found
                </td>
              </tr>
              <tr
                v-for="staff in filteredStaff"
                :key="staff.staff_id"
                class="border-b border-(--ui-border)/50 last:border-0 hover:bg-(--ui-bg-accented)/30 transition"
              >
                <td class="py-3 px-4 font-mono text-xs font-semibold text-(--ui-text-highlighted)">
                  {{ staff.staff_id }}
                </td>
                <td class="py-3 px-4">
                  <div class="flex items-center gap-3">
                    <UAvatar :text="`${staff.first_name[0]}${staff.last_name[0]}`" size="sm" />
                    <div>
                      <p class="font-medium text-(--ui-text-highlighted)">
                        {{ staff.first_name }} {{ staff.last_name }}
                        <span v-if="staff.other_name" class="text-xs text-(--ui-text-dimmed)">({{ staff.other_name }})</span>
                      </p>
                      <p class="text-xs text-(--ui-text-dimmed)">{{ staff.email }} • {{ staff.phone || 'No phone' }}</p>
                    </div>
                  </div>
                </td>
                <td class="py-3 px-4">
                  <UBadge color="neutral" variant="subtle" size="xs" class="capitalize">{{ staff.role?.replace('_', ' ') }}</UBadge>
                </td>
                <td class="py-3 px-4">
                  <div class="flex flex-wrap gap-1">
                    <UBadge
                      v-for="perm in (staff.permission || []).slice(0, 3)"
                      :key="perm"
                      :color="perm === 'manage:all' ? 'error' : 'info'"
                      variant="subtle"
                      size="xs"
                    >
                      {{ perm }}
                    </UBadge>
                    <UBadge v-if="(staff.permission || []).length > 3" color="neutral" variant="subtle" size="xs">
                      +{{ staff.permission.length - 3 }}
                    </UBadge>
                  </div>
                </td>
                <td class="py-3 px-4 text-center">
                  <UBadge :color="statusColors[staff.status] as any" variant="subtle" size="xs" class="capitalize">
                    {{ staff.status }}
                  </UBadge>
                </td>
                <td class="py-3 px-4 text-xs text-(--ui-text-dimmed)">
                  {{ staff.last_login ? new Date(staff.last_login).toLocaleDateString() : 'Never' }}
                </td>
                <td class="py-3 px-4 text-right">
                  <div class="flex items-center justify-end gap-1">
                    <UButton
                      variant="ghost"
                      color="primary"
                      size="xs"
                      icon="i-lucide-pencil"
                      title="Edit Staff"
                      @click="openEditStaff(staff)"
                    />
                    <UDropdownMenu
                      :items="[
                        [
                          ...(staff.status !== 'active' ? [{ label: 'Activate', icon: 'i-lucide-check-circle', onSelect: () => changeStatus(staff, 'active'), click: () => changeStatus(staff, 'active') }] : []),
                          ...(staff.status === 'active' ? [{ label: 'Suspend', icon: 'i-lucide-pause-circle', onSelect: () => changeStatus(staff, 'suspended'), click: () => changeStatus(staff, 'suspended') }] : []),
                          ...(staff.status !== 'terminated' ? [{ label: 'Terminate', icon: 'i-lucide-x-circle', onSelect: () => changeStatus(staff, 'terminated'), click: () => changeStatus(staff, 'terminated') }] : [])
                        ]
                      ]"
                    >
                      <UButton variant="ghost" color="neutral" size="xs" icon="i-lucide-more-horizontal" />
                    </UDropdownMenu>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Add Staff Modal -->
      <UModal v-model:open="showAddModal" title="Add Staff Member">
        <template #body>
          <form class="p-5 space-y-4" @submit.prevent="handleAddStaff">
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="First Name" required>
                <UInput v-model="newStaff.first_name" placeholder="First name" />
              </UFormField>
              <UFormField label="Last Name" required>
                <UInput v-model="newStaff.last_name" placeholder="Last name" />
              </UFormField>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="Other Name">
                <UInput v-model="newStaff.other_name" placeholder="Middle / other name" />
              </UFormField>
              <UFormField label="Phone">
                <UInput v-model="newStaff.phone" placeholder="08012345678" />
              </UFormField>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="Email" required>
                <UInput v-model="newStaff.email" type="email" placeholder="staff@store.com" />
              </UFormField>
              <UFormField label="Role">
                <USelect v-model="newStaff.role" :items="roles" value-key="value" label-key="label" />
              </UFormField>
            </div>
            <UFormField label="Initial Password" required>
              <UInput v-model="newStaff.password" type="password" placeholder="••••••••" />
            </UFormField>
            <UFormField label="Assigned Permissions">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <label
                  v-for="perm in permissionOptions"
                  :key="perm.value"
                  :class="[
                    'flex items-center gap-2 p-2 rounded-lg cursor-pointer text-xs transition border',
                    newStaff.permissions.includes(perm.value)
                      ? 'bg-green-500/10 border-green-500/30 text-green-600 dark:text-green-400 font-medium'
                      : 'border-(--ui-border) bg-(--ui-bg-accented)/40 text-(--ui-text-muted)'
                  ]"
                >
                  <input
                    type="checkbox"
                    :value="perm.value"
                    v-model="newStaff.permissions"
                    class="rounded"
                  />
                  {{ perm.label }}
                </label>
              </div>
            </UFormField>
            <div class="flex justify-end gap-2 pt-2">
              <UButton variant="outline" color="neutral" @click="showAddModal = false">Cancel</UButton>
              <UButton type="submit" :loading="isAddingStaff">Add Staff Member</UButton>
            </div>
          </form>
        </template>
      </UModal>

      <!-- Edit Staff Modal -->
      <UModal v-model:open="showEditModal" title="Edit Staff Member">
        <template #body>
          <form class="p-5 space-y-4" @submit.prevent="handleUpdateStaff">
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="First Name" required>
                <UInput v-model="editStaffForm.first_name" placeholder="First name" />
              </UFormField>
              <UFormField label="Last Name" required>
                <UInput v-model="editStaffForm.last_name" placeholder="Last name" />
              </UFormField>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="Other Name">
                <UInput v-model="editStaffForm.other_name" placeholder="Middle / other name" />
              </UFormField>
              <UFormField label="Phone">
                <UInput v-model="editStaffForm.phone" placeholder="08012345678" />
              </UFormField>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="Email" required>
                <UInput v-model="editStaffForm.email" type="email" placeholder="staff@store.com" />
              </UFormField>
              <UFormField label="Role">
                <USelect v-model="editStaffForm.role" :items="roles" value-key="value" label-key="label" />
              </UFormField>
            </div>
            <UFormField label="Status">
              <USelect v-model="editStaffForm.status" :items="statusOptions" value-key="value" label-key="label" />
            </UFormField>
            <UFormField label="Assigned Permissions">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <label
                  v-for="perm in permissionOptions"
                  :key="perm.value"
                  :class="[
                    'flex items-center gap-2 p-2 rounded-lg cursor-pointer text-xs transition border',
                    editStaffForm.permissions.includes(perm.value)
                      ? 'bg-green-500/10 border-green-500/30 text-green-600 dark:text-green-400 font-medium'
                      : 'border-(--ui-border) bg-(--ui-bg-accented)/40 text-(--ui-text-muted)'
                  ]"
                >
                  <input
                    type="checkbox"
                    :value="perm.value"
                    v-model="editStaffForm.permissions"
                    class="rounded"
                  />
                  {{ perm.label }}
                </label>
              </div>
            </UFormField>
            <div class="flex justify-end gap-2 pt-2">
              <UButton variant="outline" color="neutral" @click="showEditModal = false">Cancel</UButton>
              <UButton type="submit" :loading="isEditingStaff">Save Changes</UButton>
            </div>
          </form>
        </template>
      </UModal>
    </template>
  </div>
</template>
