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

const permissionList = [
  { label: 'POS Terminal & Record Sales', value: 'record:sales' },
  { label: 'View Products & Inventory', value: 'view:product' },
  { label: 'Manage Products (Add/Edit)', value: 'manage:product' },
  { label: 'Manage Customers & Debts', value: 'manage:user' },
  { label: 'View Analytics & Reports', value: 'view:analytics' },
  { label: 'Manage Staff Members', value: 'manage:staff' }
]

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

      <div v-else class="overflow-hidden rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xs">
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

    <UModal v-model:open="showAddStaffModal" title="Add Cashier / Staff Member">
      <template #body>
        <form class="p-6 space-y-4" @submit.prevent="handleCreateStaff">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">First Name *</label>
              <input
                v-model="newStaff.first_name"
                type="text"
                required
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
              />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">Last Name *</label>
              <input
                v-model="newStaff.last_name"
                type="text"
                required
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-xs font-bold text-(--ui-text-highlighted)">Email Address *</label>
            <input
              v-model="newStaff.email"
              type="email"
              required
              class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
            />
            <p class="text-[11px] text-(--ui-text-dimmed)">Staff member can reset password via email upon login.</p>
          </div>

          <div class="space-y-1">
            <label class="text-xs font-bold text-(--ui-text-highlighted)">Phone Number</label>
            <input
              v-model="newStaff.phone"
              type="tel"
              class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
            />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">Role</label>
              <select
                v-model="newStaff.role"
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
              >
                <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">Status</label>
              <select
                v-model="newStaff.status"
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
              >
                <option v-for="st in statusOptions" :key="st.value" :value="st.value">{{ st.label }}</option>
              </select>
            </div>
          </div>

          <div class="space-y-2 pt-2">
            <label class="text-xs font-bold text-(--ui-text-highlighted)">Permissions</label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <label
                v-for="perm in permissionList"
                :key="perm.value"
                class="flex items-center gap-2 p-2.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/20 cursor-pointer text-xs font-medium text-(--ui-text-highlighted)"
              >
                <input
                  v-model="newStaff.permissions"
                  type="checkbox"
                  :value="perm.value"
                  class="rounded border-zinc-700 text-amber-500 focus:ring-0"
                />
                <span>{{ perm.label }}</span>
              </label>
            </div>
          </div>

          <div class="flex items-center justify-end gap-3 pt-4 border-t border-(--ui-border)">
            <UButton
              type="button"
              variant="ghost"
              color="neutral"
              @click="showAddStaffModal = false"
            >
              Cancel
            </UButton>
            <UButton
              type="submit"
              color="primary"
              :loading="isSubmittingStaff"
              class="font-bold px-5 py-2"
            >
              Add Staff
            </UButton>
          </div>
        </form>
      </template>
    </UModal>

    <UModal v-model:open="showEditStaffModal" title="Edit Staff Member">
      <template #body>
        <form class="p-6 space-y-4" @submit.prevent="handleUpdateStaff">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">First Name</label>
              <input
                v-model="editStaffForm.first_name"
                type="text"
                required
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
              />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">Last Name</label>
              <input
                v-model="editStaffForm.last_name"
                type="text"
                required
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-xs font-bold text-(--ui-text-highlighted)">Phone Number</label>
            <input
              v-model="editStaffForm.phone"
              type="tel"
              class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
            />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">Role</label>
              <select
                v-model="editStaffForm.role"
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
              >
                <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">Status</label>
              <select
                v-model="editStaffForm.status"
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
              >
                <option v-for="st in statusOptions" :key="st.value" :value="st.value">{{ st.label }}</option>
              </select>
            </div>
          </div>

          <div class="space-y-2 pt-2">
            <label class="text-xs font-bold text-(--ui-text-highlighted)">Permissions</label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <label
                v-for="perm in permissionList"
                :key="perm.value"
                class="flex items-center gap-2 p-2.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/20 cursor-pointer text-xs font-medium text-(--ui-text-highlighted)"
              >
                <input
                  v-model="editStaffForm.permissions"
                  type="checkbox"
                  :value="perm.value"
                  class="rounded border-zinc-700 text-amber-500 focus:ring-0"
                />
                <span>{{ perm.label }}</span>
              </label>
            </div>
          </div>

          <div class="flex items-center justify-end gap-3 pt-4 border-t border-(--ui-border)">
            <UButton
              type="button"
              variant="ghost"
              color="neutral"
              @click="showEditStaffModal = false"
            >
              Cancel
            </UButton>
            <UButton
              type="submit"
              color="primary"
              :loading="isEditingStaff"
              class="font-bold px-5 py-2"
            >
              Save Changes
            </UButton>
          </div>
        </form>
      </template>
    </UModal>
  </div>
</template>
