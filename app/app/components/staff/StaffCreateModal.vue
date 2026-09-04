<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  modelValue?: boolean
  storeId?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  storeId: ''
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'created': [staff: any]
}>()

const auth = useAuthStore()
const toast = useToast()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const isSubmitting = ref(false)

const effectiveStoreId = computed(() => {
  return props.storeId || auth.store_id || auth.staff?.store_id || ''
})

const form = ref({
  first_name: '',
  last_name: '',
  other_name: '',
  role: 'staff',
  email: '',
  phone: '',
  permissions: ['record:sales', 'view:product'] as string[],
  status: 'active'
})

const roles = [
  { label: 'Cashier / Staff', value: 'staff' },
  { label: 'Store Manager', value: 'manager' },
  { label: 'Administrator', value: 'admin' }
]

interface PermissionItem {
  label: string
  value: string
  description?: string
}

interface PermissionGroup {
  id: string
  title: string
  icon: string
  description: string
  permissions: PermissionItem[]
}

const permissionGroups: PermissionGroup[] = [
  {
    id: 'product',
    title: 'Product & Inventory',
    icon: 'i-lucide-package',
    description: 'Control product catalog, stock adjustments, and pricing updates.',
    permissions: [
      { label: 'View Products', value: 'view:product', description: 'Browse items and catalog' },
      { label: 'Create Products', value: 'create:product', description: 'Add new items to inventory' },
      { label: 'Edit Products', value: 'edit:product', description: 'Update price, barcode, details' },
      { label: 'Delete Products', value: 'delete:product', description: 'Archive/delete items' },
      { label: 'Adjust Stock', value: 'adjust:stock', description: 'Record quantity in/out adjustments' },
      { label: 'Restore Products', value: 'restore:product', description: 'Restore soft-deleted products' }
    ]
  },
  {
    id: 'sales',
    title: 'Sales & POS Terminal',
    icon: 'i-lucide-shopping-cart',
    description: 'Manage terminal checkout, order cancellations, and customer discounts.',
    permissions: [
      { label: 'Record Sales', value: 'record:sales', description: 'Process POS checkout transactions' },
      { label: 'View Sales', value: 'view:sales', description: 'View sale history and receipts' },
      { label: 'Cancel Sales', value: 'cancel:sales', description: 'Void or cancel transactions' },
      { label: 'Apply Discount', value: 'apply:discount', description: 'Grant custom discounts at checkout' }
    ]
  },
  {
    id: 'staff',
    title: 'Staff Management',
    icon: 'i-lucide-users',
    description: 'Control team access, roles, and member management.',
    permissions: [
      { label: 'View Staff', value: 'view:staff', description: 'View team members and roles' },
      { label: 'Create Staff', value: 'create:staff', description: 'Invite or add new staff members' },
      { label: 'Edit Staff', value: 'edit:staff', description: 'Update member info and roles' },
      { label: 'Delete Staff', value: 'delete:staff', description: 'Terminate and remove staff' },
      { label: 'Manage Permissions', value: 'staff:permission', description: 'Modify assigned staff permissions' }
    ]
  },
  {
    id: 'customers',
    title: 'Customers & Debts',
    icon: 'i-lucide-user-check',
    description: 'Maintain customer contacts and credit/debt bookkeeping.',
    permissions: [
      { label: 'View Customers', value: 'view:customer', description: 'Browse customer list' },
      { label: 'Create Customers', value: 'create:customer', description: 'Register new customers' },
      { label: 'Edit Customers', value: 'edit:customer', description: 'Modify customer contact info' },
      { label: 'Delete Customers', value: 'delete:customer', description: 'Deactivate customer records' },
      { label: 'Record Debt', value: 'record:debt', description: 'Log unpaid debt balances' },
      { label: 'View Debt', value: 'view:debt', description: 'Review store debt records' },
      { label: 'Settle Debt', value: 'settle:debt', description: 'Mark debts as paid or settled' }
    ]
  },
  {
    id: 'store',
    title: 'Store & Analytics',
    icon: 'i-lucide-bar-chart-3',
    description: 'Access store analytics, audit logs, and system settings.',
    permissions: [
      { label: 'View Analytics', value: 'view:analytics', description: 'View sales and revenue metrics' },
      { label: 'Export Reports', value: 'export:report', description: 'Download CSV and audit reports' },
      { label: 'View Audit Logs', value: 'view:audit-log', description: 'View activity logs' },
      { label: 'View Settings', value: 'view:app-settings', description: 'Read store configuration' },
      { label: 'Edit Settings', value: 'edit:app-settings', description: 'Update store and hardware settings' },
      { label: 'Full Access (Super Manager)', value: 'manage:all', description: 'Bypass all permission checks' }
    ]
  }
]

function applyRolePresets(newRole: string) {
  if (newRole === 'staff') {
    form.value.permissions = ['record:sales', 'view:product', 'view:customer', 'create:customer']
  } else if (newRole === 'manager') {
    form.value.permissions = [
      'record:sales', 'view:sales', 'cancel:sales', 'apply:discount',
      'view:product', 'create:product', 'edit:product', 'adjust:stock',
      'view:customer', 'create:customer', 'edit:customer', 'record:debt', 'view:debt', 'settle:debt',
      'view:staff', 'view:analytics'
    ]
  } else if (newRole === 'admin') {
    form.value.permissions = ['manage:all']
  }
}

function isGroupAllSelected(group: PermissionGroup): boolean {
  return group.permissions.every(p => form.value.permissions.includes(p.value))
}

function toggleGroupAll(group: PermissionGroup) {
  const allValues = group.permissions.map(p => p.value)
  const allSelected = isGroupAllSelected(group)
  if (allSelected) {
    form.value.permissions = form.value.permissions.filter(p => !allValues.includes(p))
  } else {
    const combined = new Set([...form.value.permissions, ...allValues])
    form.value.permissions = Array.from(combined)
  }
}

function togglePermission(permVal: string) {
  const idx = form.value.permissions.indexOf(permVal)
  if (idx > -1) {
    form.value.permissions.splice(idx, 1)
  } else {
    form.value.permissions.push(permVal)
  }
}

function resetForm() {
  form.value = {
    first_name: '',
    last_name: '',
    other_name: '',
    role: 'staff',
    email: '',
    phone: '',
    permissions: ['record:sales', 'view:product'],
    status: 'active'
  }
}

async function handleSubmit() {
  if (!form.value.first_name.trim() || !form.value.last_name.trim() || !form.value.email.trim()) {
    toast.add({
      title: 'Missing Required Fields',
      description: 'Please fill in first name, last name, and a valid email.',
      color: 'error'
    })
    return
  }

  const sId = effectiveStoreId.value
  if (!sId) {
    toast.add({
      title: 'Store Not Found',
      description: 'Unable to detect active store terminal ID.',
      color: 'error'
    })
    return
  }

  isSubmitting.value = true
  try {
    const res = await $fetch<any>(`${apiBase}/${sId}/staff/`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${auth.token ?? ''}`,
        'Content-Type': 'application/json'
      },
      body: {
        first_name: form.value.first_name.trim(),
        last_name: form.value.last_name.trim(),
        other_name: form.value.other_name.trim() || null,
        role: form.value.role,
        email: form.value.email.trim(),
        phone: form.value.phone.trim() || null,
        permission: form.value.permissions,
        status: form.value.status
      }
    })

    toast.add({
      title: 'Staff Member Added',
      description: `${form.value.first_name} ${form.value.last_name} has been added to this store.`,
      color: 'success'
    })

    emit('created', res)
    emit('update:modelValue', false)
    resetForm()
  } catch (err: any) {
    toast.add({
      title: 'Failed to Add Staff',
      description: err?.data?.detail || err?.message || 'Server error occurred',
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AppFullScreenModal
    :model-value="modelValue"
    title="Add Team Member"
    description="Assign roles and granular store permissions to cashiers and managers."
    max-width="max-w-3xl"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <form id="staff-create-form" class="space-y-6" @submit.prevent="handleSubmit">
      <div class="p-4 rounded-2xl bg-(--ui-bg-accented)/30 border border-(--ui-border) space-y-4">
        <h4 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-dimmed)">
          Basic Information
        </h4>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <UFormField label="First Name" required>
            <UInput
              v-model="form.first_name"
              placeholder="e.g. Samuel"
              icon="i-lucide-user"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Last Name" required>
            <UInput
              v-model="form.last_name"
              placeholder="e.g. Adeleke"
              icon="i-lucide-user"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Other Name (Optional)">
            <UInput
              v-model="form.other_name"
              placeholder="Middle or nickname"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Email Address" required>
            <UInput
              v-model="form.email"
              type="email"
              placeholder="samuel@example.com"
              icon="i-lucide-mail"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Phone Number (Optional)">
            <UInput
              v-model="form.phone"
              type="tel"
              placeholder="08012345678"
              icon="i-lucide-phone"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Assigned Role" required>
            <USelect
              v-model="form.role"
              :items="roles"
              value-key="value"
              class="w-full"
              @update:model-value="applyRolePresets"
            />
          </UFormField>
        </div>
      </div>

      <div class="space-y-4">
        <div class="flex items-center justify-between gap-2">
          <div>
            <h4 class="text-sm font-bold text-(--ui-text-highlighted)">
              Granular Store Permissions
            </h4>
            <p class="text-xs text-(--ui-text-muted) mt-0.5">
              Select specific actions this team member is permitted to perform in this store terminal.
            </p>
          </div>

          <span class="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
            {{ form.permissions.length }} selected
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
                <div class="min-w-0">
                  <h5 class="text-xs font-bold text-(--ui-text-highlighted) truncate">
                    {{ group.title }}
                  </h5>
                  <p class="text-[11px] text-(--ui-text-dimmed) truncate">
                    {{ group.description }}
                  </p>
                </div>
              </div>

              <button
                type="button"
                class="text-[11px] font-bold text-emerald-400 hover:underline px-2 py-1 shrink-0 cursor-pointer"
                @click="toggleGroupAll(group)"
              >
                {{ isGroupAllSelected(group) ? 'Deselect All' : 'Select All' }}
              </button>
            </div>

            <div class="p-3.5 grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div
                v-for="perm in group.permissions"
                :key="perm.value"
                class="flex items-start gap-2.5 p-2.5 rounded-xl border transition cursor-pointer select-none"
                :class="[
                  form.permissions.includes(perm.value)
                    ? 'border-emerald-500/40 bg-emerald-500/10 text-(--ui-text-highlighted)'
                    : 'border-(--ui-border)/50 hover:bg-(--ui-bg-accented)/40 text-(--ui-text-muted)'
                ]"
                @click="togglePermission(perm.value)"
              >
                <div
                  class="size-4 rounded-md mt-0.5 flex items-center justify-center shrink-0 border transition"
                  :class="[
                    form.permissions.includes(perm.value)
                      ? 'bg-emerald-500 border-emerald-500 text-black'
                      : 'border-(--ui-border) bg-(--ui-bg)'
                  ]"
                >
                  <UIcon
                    v-if="form.permissions.includes(perm.value)"
                    name="i-lucide-check"
                    class="size-3 font-bold"
                  />
                </div>

                <div class="min-w-0 flex-1">
                  <div class="text-xs font-bold leading-tight">
                    {{ perm.label }}
                  </div>
                  <div class="text-[10px] text-(--ui-text-dimmed) leading-tight mt-0.5">
                    {{ perm.description }}
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
          :disabled="isSubmitting"
          @click="$emit('update:modelValue', false)"
        >
          Cancel
        </UButton>

        <UButton
          type="submit"
          form="staff-create-form"
          color="primary"
          icon="i-lucide-user-plus"
          :loading="isSubmitting"
          class="font-bold"
        >
          Add Staff Member
        </UButton>
      </div>
    </template>
  </AppFullScreenModal>
</template>
