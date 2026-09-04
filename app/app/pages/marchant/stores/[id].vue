<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({ layout: 'marchant' })

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToast()
const { api } = useApi()

const storeId = computed(() => String(route.params.id))
const currentBranch = computed(() => auth.stores.find(s => s.store_id === storeId.value))

const activeTab = ref<'staff' | 'settings'>('staff')

const staffList = ref<any[]>([])
const isLoadingStaff = ref(false)

const showAddStaffModal = ref(false)
const isSubmittingStaff = ref(false)

const showEditStaffModal = ref(false)
const isEditingStaff = ref(false)
const selectedStaff = ref<any>(null)

const editStoreForm = ref({
  name: '',
  category: 'General Retail',
  address: '',
  phone: '',
  website: ''
})
const isSavingStore = ref(false)

const newStaff = ref({
  first_name: '',
  last_name: '',
  other_name: '',
  role: 'staff',
  email: '',
  phone: '',
  permissions: ['record:sales', 'view:product'] as string[],
  status: 'active'
})

const editStaffForm = ref({
  first_name: '',
  last_name: '',
  other_name: '',
  role: 'staff',
  phone: '',
  permissions: [] as string[],
  status: 'active'
})

const permissionGroups = [
  {
    id: 'product',
    title: 'Product & Inventory',
    icon: 'i-lucide-package',
    permissions: [
      { label: 'View Products', value: 'view:product' },
      { label: 'Create Products', value: 'create:product' },
      { label: 'Edit Products', value: 'edit:product' },
      { label: 'Delete Products', value: 'delete:product' },
      { label: 'Adjust Stock', value: 'adjust:stock' },
      { label: 'Restore Products', value: 'restore:product' }
    ]
  },
  {
    id: 'sales',
    title: 'Sales & POS Terminal',
    icon: 'i-lucide-shopping-cart',
    permissions: [
      { label: 'Record Sales', value: 'record:sales' },
      { label: 'View Sales', value: 'view:sales' },
      { label: 'Cancel Sales', value: 'cancel:sales' },
      { label: 'Apply Discount', value: 'apply:discount' }
    ]
  },
  {
    id: 'staff',
    title: 'Staff Management',
    icon: 'i-lucide-users',
    permissions: [
      { label: 'View Staff', value: 'view:staff' },
      { label: 'Create Staff', value: 'create:staff' },
      { label: 'Edit Staff', value: 'edit:staff' },
      { label: 'Delete Staff', value: 'delete:staff' },
      { label: 'Staff Permissions', value: 'staff:permission' }
    ]
  },
  {
    id: 'customers',
    title: 'Customers & Debts',
    icon: 'i-lucide-user-check',
    permissions: [
      { label: 'View Customers', value: 'view:customer' },
      { label: 'Create Customers', value: 'create:customer' },
      { label: 'Edit Customers', value: 'edit:customer' },
      { label: 'Delete Customers', value: 'delete:customer' },
      { label: 'Record Debt', value: 'record:debt' },
      { label: 'View Debt', value: 'view:debt' },
      { label: 'Settle Debt', value: 'settle:debt' }
    ]
  },
  {
    id: 'store',
    title: 'Store & Analytics',
    icon: 'i-lucide-bar-chart-3',
    permissions: [
      { label: 'View Analytics', value: 'view:analytics' },
      { label: 'Export Reports', value: 'export:report' },
      { label: 'View Audit Logs', value: 'view:audit-log' },
      { label: 'View App Settings', value: 'view:app-settings' },
      { label: 'Edit App Settings', value: 'edit:app-settings' },
      { label: 'Full Access (Super Manager)', value: 'manage:all' }
    ]
  }
]

function isEditGroupAllSelected(group: any): boolean {
  return group.permissions.every((p: any) => editStaffForm.value.permissions.includes(p.value))
}

function toggleEditGroupAll(group: any) {
  const allValues = group.permissions.map((p: any) => p.value)
  const allSelected = isEditGroupAllSelected(group)
  if (allSelected) {
    editStaffForm.value.permissions = editStaffForm.value.permissions.filter((p: string) => !allValues.includes(p))
  } else {
    const combined = new Set([...editStaffForm.value.permissions, ...allValues])
    editStaffForm.value.permissions = Array.from(combined)
  }
}

function toggleEditPermission(permVal: string) {
  const idx = editStaffForm.value.permissions.indexOf(permVal)
  if (idx > -1) {
    editStaffForm.value.permissions.splice(idx, 1)
  } else {
    editStaffForm.value.permissions.push(permVal)
  }
}


const roles = [
  { label: 'Cashier / Staff', value: 'staff' },
  { label: 'Store Manager', value: 'manager' },
  { label: 'Administrator', value: 'admin' }
]

const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Suspended', value: 'suspended' },
  { label: 'Terminated', value: 'terminated' }
]

const categories = [
  'General Retail',
  'Supermarket & Grocery',
  'Pharmacy & Chemist',
  'Fashion Boutique',
  'Electronics & Gadgets',
  'Restaurant & Cafe',
  'Cosmetics & Beauty',
  'Hardware & Building Materials'
]

onMounted(async () => {
  if (currentBranch.value) {
    editStoreForm.value = {
      name: currentBranch.value.name || '',
      category: currentBranch.value.category || 'General Retail',
      address: currentBranch.value.address || '',
      phone: currentBranch.value.phone || '',
      website: currentBranch.value.website || ''
    }
  }
  await fetchStoreStaff()
})

async function fetchStoreStaff() {
  if (!storeId.value) return
  isLoadingStaff.value = true
  try {
    const res = await api<any[]>(`/${storeId.value}/staff`)
    if (res && Array.isArray(res)) {
      staffList.value = res.map((s: any) => ({
        ...s,
        permission: Array.isArray(s.permission)
          ? s.permission.map((p: any) => (typeof p === 'string' ? p : p.value || String(p)))
          : []
      }))
    }
  } catch (err: any) {
    toast.add({
      title: 'Failed to load staff list',
      description: err?.data?.detail || err?.message || 'Server error',
      color: 'error'
    })
  } finally {
    isLoadingStaff.value = false
  }
}

async function handleCreateStaff() {
  if (!newStaff.value.first_name || !newStaff.value.last_name || !newStaff.value.email) {
    toast.add({ title: 'Please fill in required fields (First name, Last name, Email)', color: 'warning' })
    return
  }

  isSubmittingStaff.value = true
  try {
    const payload = {
      first_name: newStaff.value.first_name,
      last_name: newStaff.value.last_name,
      other_name: newStaff.value.other_name || undefined,
      email: newStaff.value.email,
      phone: newStaff.value.phone || undefined,
      role: newStaff.value.role,
      permission: newStaff.value.permissions,
      status: newStaff.value.status
    }

    const created = await api<any>(`/${storeId.value}/staff`, {
      method: 'POST',
      body: payload
    })

    toast.add({
      title: 'Cashier Account Created!',
      description: `${created.first_name} ${created.last_name} (${created.staff_id}) added to this branch.`,
      color: 'success'
    })

    showAddStaffModal.value = false
    newStaff.value = {
      first_name: '',
      last_name: '',
      other_name: '',
      role: 'staff',
      email: '',
      phone: '',
      permissions: ['record:sales', 'view:product'],
      status: 'active'
    }

    await fetchStoreStaff()
  } catch (err: any) {
    toast.add({
      title: 'Failed to create staff',
      description: err?.data?.detail || err?.message || 'Server error',
      color: 'error'
    })
  } finally {
    isSubmittingStaff.value = false
  }
}

function openEditStaff(staff: any) {
  selectedStaff.value = staff
  editStaffForm.value = {
    first_name: staff.first_name || '',
    last_name: staff.last_name || '',
    other_name: staff.other_name || '',
    role: staff.role || 'staff',
    phone: staff.phone || '',
    permissions: Array.isArray(staff.permission) ? [...staff.permission] : [],
    status: staff.status || 'active'
  }
  showEditStaffModal.value = true
}

async function handleUpdateStaff() {
  if (!selectedStaff.value || !storeId.value) return

  isEditingStaff.value = true
  try {
    const payload = {
      first_name: editStaffForm.value.first_name,
      last_name: editStaffForm.value.last_name,
      other_name: editStaffForm.value.other_name || undefined,
      role: editStaffForm.value.role,
      phone: editStaffForm.value.phone || undefined,
      permission: editStaffForm.value.permissions,
      status: editStaffForm.value.status
    }

    await api(`/${storeId.value}/staff/${selectedStaff.value.staff_id}`, {
      method: 'PUT',
      body: payload
    })

    toast.add({
      title: 'Staff Updated',
      description: 'Permissions and details updated successfully.',
      color: 'success'
    })

    showEditStaffModal.value = false
    await fetchStoreStaff()
  } catch (err: any) {
    toast.add({
      title: 'Failed to update staff',
      description: err?.data?.detail || err?.message || 'Server error',
      color: 'error'
    })
  } finally {
    isEditingStaff.value = false
  }
}

async function handleRevokeSession(staffId: string) {
  try {
    await api(`/${storeId.value}/staff/${staffId}/revoke`, { method: 'POST' })
    toast.add({ title: 'Active sessions revoked', color: 'success' })
  } catch (err: any) {
    toast.add({
      title: 'Failed to revoke session',
      description: err?.data?.detail || 'Server error',
      color: 'error'
    })
  }
}

async function handleSaveStoreSettings() {
  if (!editStoreForm.value.name) {
    toast.add({ title: 'Store name is required', color: 'warning' })
    return
  }

  isSavingStore.value = true
  try {
    await api(`/${storeId.value}/stores`, {
      method: 'PUT',
      body: editStoreForm.value
    })

    toast.add({
      title: 'Store Settings Saved',
      description: 'Branch details updated.',
      color: 'success'
    })

    await auth.fetchMe()
  } catch (err: any) {
    toast.add({
      title: 'Failed to update store',
      description: err?.data?.detail || err?.message || 'Server error',
      color: 'error'
    })
  } finally {
    isSavingStore.value = false
  }
}

function handleLaunchTerminal() {
  auth.switchStore(storeId.value)
  navigateTo('/')
}

function copyStoreId() {
  navigator.clipboard.writeText(storeId.value)
  toast.add({ title: 'Store ID copied to clipboard', color: 'success' })
}
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <div class="flex items-center gap-2 text-xs text-(--ui-text-muted)">
      <NuxtLink to="/marchant/stores" class="hover:text-(--ui-text-highlighted) transition flex items-center gap-1">
        <UIcon name="i-lucide-arrow-left" class="w-3.5 h-3.5" />
        All Branches
      </NuxtLink>
      <span>/</span>
      <span class="text-(--ui-text-highlighted) font-semibold">{{ currentBranch?.name || storeId }}</span>
    </div>

    <div class="p-6 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="space-y-1.5">
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-black text-(--ui-text-highlighted)">
            {{ currentBranch?.name || 'Store Branch' }}
          </h1>
          <span
            v-if="currentBranch?.is_owner"
            class="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20"
          >
            Owner
          </span>
        </div>
        <p class="text-xs text-amber-400 font-semibold">{{ currentBranch?.category }}</p>
        <div class="flex items-center gap-2 pt-1">
          <span class="font-mono text-xs text-emerald-400 select-all">{{ storeId }}</span>
          <button
            type="button"
            class="text-(--ui-text-dimmed) hover:text-emerald-400 p-1 transition"
            title="Copy Store ID"
            @click="copyStoreId"
          >
            <UIcon name="i-lucide-copy" class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <UButton
          size="md"
          color="primary"
          icon="i-lucide-scan-barcode"
          class="font-bold px-5 py-2.5"
          @click="handleLaunchTerminal"
        >
          Open POS Terminal
        </UButton>
      </div>
    </div>

    <div class="flex border-b border-(--ui-border) gap-6 text-sm font-bold">
      <button
        type="button"
        class="pb-3 border-b-2 transition cursor-pointer flex items-center gap-2"
        :class="activeTab === 'staff' ? 'border-amber-500 text-amber-400' : 'border-transparent text-(--ui-text-muted) hover:text-(--ui-text-highlighted)'"
        @click="activeTab = 'staff'"
      >
        <UIcon name="i-lucide-users" class="w-4 h-4" />
        Branch Staff & Cashiers ({{ staffList.length }})
      </button>

      <button
        type="button"
        class="pb-3 border-b-2 transition cursor-pointer flex items-center gap-2"
        :class="activeTab === 'settings' ? 'border-amber-500 text-amber-400' : 'border-transparent text-(--ui-text-muted) hover:text-(--ui-text-highlighted)'"
        @click="activeTab = 'settings'"
      >
        <UIcon name="i-lucide-settings-2" class="w-4 h-4" />
        Branch Settings & Info
      </button>
    </div>

    <div v-if="activeTab === 'staff'" class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-bold text-(--ui-text-highlighted)">Store Team & Cashiers</h3>
          <p class="text-xs text-(--ui-text-muted)">Staff members authorized to operate this retail branch.</p>
        </div>

        <UButton
          color="primary"
          size="sm"
          class="font-bold px-3.5 py-2"
          @click="showAddStaffModal = true"
        >
          <UIcon name="i-lucide-user-plus" class="w-4 h-4 mr-1.5" />
          Add Cashier
        </UButton>
      </div>

      <div v-if="isLoadingStaff" class="py-16 text-center">
        <UIcon name="i-lucide-loader" class="w-8 h-8 mx-auto animate-spin text-amber-500" />
        <p class="text-xs text-(--ui-text-muted) mt-2">Loading branch team...</p>
      </div>

      <div v-else-if="staffList.length === 0" class="py-16 text-center rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)">
        <UIcon name="i-lucide-users" class="w-12 h-12 mx-auto mb-3 text-zinc-500" />
        <h3 class="text-base font-bold text-(--ui-text-highlighted)">No Cashiers Assigned</h3>
        <p class="text-sm text-(--ui-text-muted) mt-1 mb-4">Add cashiers and managers for this branch.</p>
        <UButton color="primary" size="md" class="font-bold px-5 py-2.5" @click="showAddStaffModal = true">
          Add First Cashier
        </UButton>
      </div>

      <div v-else class="space-y-4">
        <!-- Desktop Table View (>= md) -->
        <div class="hidden md:block overflow-hidden rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xs">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-sm">
              <thead>
                <tr class="border-b border-(--ui-border) bg-(--ui-bg-accented)/30">
                  <th class="p-4 font-bold text-xs text-(--ui-text-muted)">Staff ID</th>
                  <th class="p-4 font-bold text-xs text-(--ui-text-muted)">Full Name</th>
                  <th class="p-4 font-bold text-xs text-(--ui-text-muted)">Role</th>
                  <th class="p-4 font-bold text-xs text-(--ui-text-muted)">Contact</th>
                  <th class="p-4 font-bold text-xs text-(--ui-text-muted)">Status</th>
                  <th class="p-4 font-bold text-xs text-(--ui-text-muted)">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-(--ui-border)">
                <tr v-for="staff in staffList" :key="staff.staff_id" class="hover:bg-(--ui-bg-accented)/20 transition">
                  <td class="p-4 font-mono font-bold text-emerald-400">{{ staff.staff_id }}</td>
                  <td class="p-4 font-bold text-(--ui-text-highlighted)">{{ staff.first_name }} {{ staff.last_name }}</td>
                  <td class="p-4">
                    <span class="text-xs px-2.5 py-1 rounded-full bg-(--ui-bg-accented) font-semibold text-(--ui-text-highlighted) capitalize">
                      {{ staff.role }}
                    </span>
                  </td>
                  <td class="p-4 text-xs text-(--ui-text-muted)">
                    <div class="font-medium text-(--ui-text-highlighted)">{{ staff.email }}</div>
                    <div v-if="staff.phone" class="text-[11px] text-(--ui-text-dimmed)">{{ staff.phone }}</div>
                  </td>
                  <td class="p-4">
                    <span
                      class="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider"
                      :class="{
                        'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': staff.status === 'active',
                        'bg-amber-500/10 text-amber-400 border border-amber-500/20': staff.status === 'suspended',
                        'bg-rose-500/10 text-rose-400 border border-rose-500/20': staff.status === 'terminated'
                      }"
                    >
                      {{ staff.status }}
                    </span>
                  </td>
                  <td class="p-4">
                    <div class="flex items-center gap-2">
                      <UButton
                        size="xs"
                        variant="soft"
                        color="neutral"
                        icon="i-lucide-pencil"
                        @click="openEditStaff(staff)"
                      >
                        Edit
                      </UButton>
                      <UButton
                        size="xs"
                        variant="ghost"
                        color="neutral"
                        title="Revoke active sessions"
                        @click="handleRevokeSession(staff.staff_id)"
                      >
                        Revoke
                      </UButton>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Mobile Card List View (< md) -->
        <div class="block md:hidden space-y-3">
          <div
            v-for="staff in staffList"
            :key="staff.staff_id"
            class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4 shadow-sm space-y-3"
          >
            <!-- Top: Avatar, Name, Role, Status -->
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-center gap-2.5 min-w-0">
                <UAvatar
                  :text="`${staff.first_name?.[0] || ''}${staff.last_name?.[0] || ''}`"
                  size="md"
                />
                <div class="min-w-0">
                  <h3 class="font-bold text-sm text-(--ui-text-highlighted) truncate">
                    {{ staff.first_name }} {{ staff.last_name }}
                  </h3>
                  <span class="text-[11px] px-2 py-0.5 rounded-full bg-(--ui-bg-accented) font-semibold text-(--ui-text-muted) capitalize inline-block mt-0.5">
                    {{ staff.role }}
                  </span>
                </div>
              </div>

              <span
                class="text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider shrink-0"
                :class="{
                  'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': staff.status === 'active',
                  'bg-amber-500/10 text-amber-400 border border-amber-500/20': staff.status === 'suspended',
                  'bg-rose-500/10 text-rose-400 border border-rose-500/20': staff.status === 'terminated'
                }"
              >
                {{ staff.status }}
              </span>
            </div>

            <!-- Middle: Staff ID, Email, Phone -->
            <div class="space-y-1.5 py-2 px-3 rounded-xl bg-(--ui-bg-accented)/30 border border-(--ui-border)/40 text-xs">
              <div class="flex items-center justify-between gap-2">
                <span class="text-(--ui-text-dimmed) text-[11px]">Staff ID:</span>
                <span class="font-mono text-emerald-400 font-bold text-xs">{{ staff.staff_id }}</span>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span class="text-(--ui-text-dimmed) text-[11px]">Email:</span>
                <a :href="`mailto:${staff.email}`" class="text-(--ui-text-highlighted) font-medium truncate hover:underline">
                  {{ staff.email }}
                </a>
              </div>
              <div v-if="staff.phone" class="flex items-center justify-between gap-2">
                <span class="text-(--ui-text-dimmed) text-[11px]">Phone:</span>
                <a :href="`tel:${staff.phone}`" class="text-emerald-500 font-mono font-medium hover:underline">
                  {{ staff.phone }}
                </a>
              </div>
            </div>

            <!-- Bottom: Action Buttons -->
            <div class="grid grid-cols-2 gap-2 pt-1">
              <UButton
                size="xs"
                variant="outline"
                color="primary"
                icon="i-lucide-pencil"
                class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
                @click="openEditStaff(staff)"
              >
                Edit Staff
              </UButton>
              <UButton
                size="xs"
                variant="outline"
                color="neutral"
                icon="i-lucide-shield-alert"
                class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
                @click="handleRevokeSession(staff.staff_id)"
              >
                Revoke Sessions
              </UButton>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="activeTab === 'settings'" class="p-6 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xs max-w-3xl">
      <form class="space-y-4" @submit.prevent="handleSaveStoreSettings">
        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Store Name *</label>
          <input
            v-model="editStoreForm.name"
            type="text"
            required
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          />
        </div>

        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Business Category</label>
          <select
            v-model="editStoreForm.category"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          >
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Branch Physical Address</label>
          <input
            v-model="editStoreForm.address"
            type="text"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          />
        </div>

        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Contact Phone Number</label>
          <input
            v-model="editStoreForm.phone"
            type="tel"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          />
        </div>

        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Website / Social Handle</label>
          <input
            v-model="editStoreForm.website"
            type="text"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          />
        </div>

        <div class="pt-4 border-t border-(--ui-border)">
          <UButton
            type="submit"
            color="primary"
            :loading="isSavingStore"
            class="font-bold px-5 py-2.5"
          >
            Save Branch Settings
          </UButton>
        </div>
      </form>
    </div>

    <StaffCreateModal
      v-model="showAddStaffModal"
      :store-id="storeId"
      @created="fetchStoreStaff"
    />

    <AppFullScreenModal
      v-model="showEditStaffModal"
      title="Edit Staff Member"
      description="Update staff profile and assigned permissions."
      max-width="max-w-3xl"
    >
      <form id="edit-staff-form" class="space-y-6" @submit.prevent="handleUpdateStaff">
        <div class="p-4 rounded-2xl bg-(--ui-bg-accented)/30 border border-(--ui-border) space-y-4">
          <h4 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-dimmed)">
            Staff Information
          </h4>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <UFormField label="First Name" required>
              <UInput
                v-model="editStaffForm.first_name"
                class="w-full"
              />
            </UFormField>

            <UFormField label="Last Name" required>
              <UInput
                v-model="editStaffForm.last_name"
                class="w-full"
              />
            </UFormField>

            <UFormField label="Other Name (Optional)">
              <UInput
                v-model="editStaffForm.other_name"
                class="w-full"
              />
            </UFormField>

            <UFormField label="Phone Number">
              <UInput
                v-model="editStaffForm.phone"
                type="tel"
                class="w-full"
              />
            </UFormField>

            <UFormField label="Role">
              <USelect
                v-model="editStaffForm.role"
                :items="roles"
                value-key="value"
                class="w-full"
              />
            </UFormField>

            <UFormField label="Account Status">
              <USelect
                v-model="editStaffForm.status"
                :items="statusOptions"
                value-key="value"
                class="w-full"
              />
            </UFormField>
          </div>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between gap-2">
            <div>
              <h4 class="text-sm font-bold text-(--ui-text-highlighted)">
                Assigned Store Permissions
              </h4>
              <p class="text-xs text-(--ui-text-muted) mt-0.5">
                Enable or revoke specific permissions for this team member.
              </p>
            </div>

            <span class="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
              {{ editStaffForm.permissions.length }} selected
            </span>
          </div>

          <div class="space-y-4">
            <div
              v-for="group in permissionGroups"
              :key="group.id"
              class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-accented)/20 overflow-hidden"
            >
              <div class="flex items-center justify-between px-4 py-3 bg-(--ui-bg-accented)/40 border-b border-(--ui-border)/60">
                <div class="flex items-center gap-2.5 min-w-0">
                  <UIcon :name="group.icon" class="size-4 text-emerald-400 shrink-0" />
                  <h5 class="text-xs font-bold text-(--ui-text-highlighted) truncate">
                    {{ group.title }}
                  </h5>
                </div>

                <button
                  type="button"
                  class="text-[11px] font-bold text-emerald-400 hover:underline px-2 py-1 shrink-0 cursor-pointer"
                  @click="toggleEditGroupAll(group)"
                >
                  {{ isEditGroupAllSelected(group) ? 'Deselect All' : 'Select All' }}
                </button>
              </div>

              <div class="p-3.5 grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div
                  v-for="perm in group.permissions"
                  :key="perm.value"
                  class="flex items-start gap-2.5 p-2.5 rounded-xl border transition cursor-pointer select-none"
                  :class="[
                    editStaffForm.permissions.includes(perm.value)
                      ? 'border-emerald-500/40 bg-emerald-500/10 text-(--ui-text-highlighted)'
                      : 'border-(--ui-border)/50 hover:bg-(--ui-bg-accented)/40 text-(--ui-text-muted)'
                  ]"
                  @click="toggleEditPermission(perm.value)"
                >
                  <div
                    class="size-4 rounded-md mt-0.5 flex items-center justify-center shrink-0 border transition"
                    :class="[
                      editStaffForm.permissions.includes(perm.value)
                        ? 'bg-emerald-500 border-emerald-500 text-black'
                        : 'border-(--ui-border) bg-(--ui-bg)'
                    ]"
                  >
                    <UIcon
                      v-if="editStaffForm.permissions.includes(perm.value)"
                      name="i-lucide-check"
                      class="size-3 font-bold"
                    />
                  </div>

                  <div class="min-w-0 flex-1">
                    <div class="text-xs font-bold leading-tight">
                      {{ perm.label }}
                    </div>
                    <div class="text-[9px] font-mono text-(--ui-text-dimmed) mt-1 opacity-70">
                      {{ perm.value }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </form>

      <template #footer>
        <div class="flex items-center justify-end gap-2.5">
          <UButton
            type="button"
            variant="outline"
            color="neutral"
            :disabled="isEditingStaff"
            @click="showEditStaffModal = false"
          >
            Cancel
          </UButton>

          <UButton
            type="submit"
            form="edit-staff-form"
            color="primary"
            :loading="isEditingStaff"
            class="font-bold"
          >
            Save Changes
          </UButton>
        </div>
      </template>
    </AppFullScreenModal>
  </div>
</template>
