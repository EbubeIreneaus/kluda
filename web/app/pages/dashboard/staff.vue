<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

definePageMeta({ layout: 'dashboard' })

const ownerStore = useOwnerStore()
const toast = useToast()
const route = useRoute()

const showAddModal = ref(false)
const isSubmitting = ref(false)

const selectedStoreForStaff = ref(ownerStore.selectedStoreId || '')


const {form: newStaff, reset: resetNewStaff} = useForm({
  first_name: '',
  last_name: '',
  other_name: '',
  role: 'staff',
  email: '',
  phone: '',
  password: '',
  permission: ['record:sales', 'view:product'] as string[]
})

const permissionList = [
  { label: 'POS & Record Sales', value: 'record:sales' },
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

onMounted(async () => {
  if (route.query.store_id) {
    selectedStoreForStaff.value = String(route.query.store_id)
  } else if (ownerStore.selectedStoreId) {
    selectedStoreForStaff.value = ownerStore.selectedStoreId
  }
  await fetchStaffList()
})

watch(() => selectedStoreForStaff.value, async (newStoreId) => {
  if (newStoreId) {
    await fetchStaffList()
  }
})

async function fetchStaffList() {
  if (selectedStoreForStaff.value) {
    await ownerStore.fetchStaffs(selectedStoreForStaff.value)
  }
}

async function handleCreateStaff() {
  if (!selectedStoreForStaff.value) {
    toast.add({ title: 'Please select a store first', color: 'warning' })
    return
  }

  if (!newStaff.value.first_name || !newStaff.value.last_name || !newStaff.value.email || !newStaff.value.password) {
    toast.add({ title: 'Please fill in all required fields', color: 'warning' })
    return
  }

  isSubmitting.value = true
  try {
    const created = await ownerStore.createStaff(selectedStoreForStaff.value, {
      ...newStaff.value,
      other_name: newStaff.value.other_name || undefined,
      phone: newStaff.value.phone || undefined,
    })

    toast.add({
      title: 'Cashier Account Created!',
      description: `Staff ID: ${created.staff_id} for ${created.first_name} ${created.last_name}`,
      color: 'success'
    })

    showAddModal.value = false
    resetNewStaff()
  } catch (err: any) {
    toast.add({
      title: 'Failed to create staff',
      description: err?.data?.detail || 'Server error',
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

async function handleRevoke(staffId: string) {
  if (!selectedStoreForStaff.value) return
  try {
    await ownerStore.revokeStaffAccess(staffId, selectedStoreForStaff.value)
    toast.add({ title: 'Session revoked', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Failed to revoke access', color: 'error' })
  }
}

function copyStaffId(id: string) {
  navigator.clipboard.writeText(id)
  toast.add({ title: `Staff ID '${id}' copied!`, color: 'success' })
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-(--ui-text-highlighted)">Staff & Cashiers</h1>
        <p class="text-sm text-(--ui-text-muted) mt-1">
          Generate Staff IDs and manage cashier permissions for each store branch.
        </p>
      </div>

      <UButton color="primary" size="sm" class="font-semibold" @click="showAddModal = true">
        <UIcon name="i-lucide-user-plus" class="w-4 h-4 mr-1.5" />
        Add Cashier / Staff
      </UButton>
    </div>

    <!-- Store Selector filter -->
    <div class="p-4 rounded-2xl border border-(--ui-border) glass-panel bg-(--ui-bg-elevated)/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-store" class="w-4 h-4 text-emerald-500" />
        <span class="text-xs font-semibold text-(--ui-text-highlighted)">Managing Branch:</span>
      </div>

      <div class="w-full sm:w-72">
        <select
          v-model="selectedStoreForStaff"
          class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3 py-2 text-xs font-semibold text-(--ui-text-highlighted) outline-none focus:border-emerald-500"
        >
          <option v-for="s in ownerStore.activeStores" :key="s.store_id" :value="s.store_id">
            {{ s.name }} ({{ s.category }})
          </option>
        </select>
      </div>
    </div>

    <!-- Staff Table / Cards -->
    <div v-if="ownerStore.staffs.length === 0" class="py-16 text-center rounded-3xl border border-(--ui-border) glass-panel">
      <UIcon name="i-lucide-users" class="w-12 h-12 mx-auto mb-3 text-slate-500" />
      <h3 class="text-base font-bold text-(--ui-text-highlighted)">No Cashiers Yet</h3>
      <p class="text-sm text-(--ui-text-muted) mt-1 mb-4">Add your first cashier to give them POS terminal access.</p>
      <UButton color="primary" size="sm" @click="showAddModal = true">Add Cashier</UButton>
    </div>

    <div v-else class="overflow-hidden rounded-3xl border border-(--ui-border) glass-panel">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-(--ui-border) bg-(--ui-bg-elevated)">
              <th class="p-4 font-semibold text-(--ui-text-muted)">Staff ID</th>
              <th class="p-4 font-semibold text-(--ui-text-muted)">Name</th>
              <th class="p-4 font-semibold text-(--ui-text-muted)">Role</th>
              <th class="p-4 font-semibold text-(--ui-text-muted)">Email / Contact</th>
              <th class="p-4 font-semibold text-(--ui-text-muted)">Status</th>
              <th class="p-4 font-semibold text-(--ui-text-muted)">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-(--ui-border)">
            <tr v-for="staff in ownerStore.staffs" :key="staff.staff_id" class="hover:bg-(--ui-bg-muted)/40 transition">
              <td class="p-4">
                <div class="flex items-center gap-2">
                  <span class="font-mono font-bold text-emerald-500">{{ staff.staff_id }}</span>
                  <button
                    @click="copyStaffId(staff.staff_id)"
                    class="text-(--ui-text-muted) hover:text-emerald-500 p-1"
                    title="Copy Staff ID"
                  >
                    <UIcon name="i-lucide-copy" class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
              <td class="p-4 font-semibold text-(--ui-text-highlighted)">
                {{ staff.first_name }} {{ staff.last_name }}
              </td>
              <td class="p-4">
                <span class="text-xs px-2.5 py-1 rounded-full bg-(--ui-bg-muted) font-medium text-(--ui-text-muted) capitalize">
                  {{ staff.role }}
                </span>
              </td>
              <td class="p-4 text-xs text-(--ui-text-muted)">
                <div>{{ staff.email }}</div>
                <div v-if="staff.phone" class="text-[11px] text-(--ui-text-dimmed)">{{ staff.phone }}</div>
              </td>
              <td class="p-4">
                <span
                  class="text-xs px-2.5 py-0.5 rounded-full font-semibold"
                  :class="staff.status === 'active' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'"
                >
                  {{ staff.status }}
                </span>
              </td>
              <td class="p-4">
                <UButton
                  size="xs"
                  variant="ghost"
                  color="error"
                  @click="handleRevoke(staff.staff_id)"
                >
                  Revoke Session
                </UButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <UModal v-model:open="showAddModal" title="Add Cashier / Staff Member">
      <template #body>
        <form class="space-y-4" @submit.prevent="handleCreateStaff">
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="First Name" required>
              <UInput v-model="newStaff.first_name" placeholder="Joy" required />
            </UFormField>
            <UFormField label="Last Name" required>
              <UInput v-model="newStaff.last_name" placeholder="Okonkwo" required />
            </UFormField>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Email" required>
              <UInput v-model="newStaff.email" type="email" placeholder="joy@store.com" required />
            </UFormField>
            <UFormField label="Phone (Optional)">
              <UInput v-model="newStaff.phone" type="tel" placeholder="08012345678" />
            </UFormField>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Role">
              <USelect
                v-model="newStaff.role"
                :items="roles"
              />
            </UFormField>
            <UFormField label="Initial Password" required>
              <UInput v-model="newStaff.password" type="password" placeholder="••••••••" required />
            </UFormField>
          </div>

          <div class="pt-3 border-t border-(--ui-border)">
            <label class="block text-xs font-semibold text-(--ui-text-highlighted) mb-2">Permissions</label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <label
                v-for="perm in permissionList"
                :key="perm.value"
                class="flex items-center gap-2 p-2 rounded-xl border border-(--ui-border) text-xs cursor-pointer hover:bg-(--ui-bg-muted)/40 transition"
              >
                <input
                  type="checkbox"
                  :value="perm.value"
                  v-model="newStaff.permission"
                  class="rounded text-emerald-500 focus:ring-emerald-500"
                />
                <span class="text-(--ui-text)">{{ perm.label }}</span>
              </label>
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-4">
            <UButton variant="ghost" color="neutral" @click="showAddModal = false">Cancel</UButton>
            <UButton type="submit" color="primary" :loading="isSubmitting">Create Cashier Account</UButton>
          </div>
        </form>
      </template>
    </UModal>
  </div>
</template>
