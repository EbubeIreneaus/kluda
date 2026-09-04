<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { adminUser } = useAdminAuth()
const { canManageAdmins } = useAdminPermission()

const admins = ref<any[]>([])
const isLoading = ref(true)
const isInviteOpen = ref(false)
const isInviting = ref(false)
const selectedAdmin = ref<any | null>(null)
const isDetailOpen = ref(false)
const isSaving = ref(false)

const inviteForm = ref({
  fullname: '',
  personal_email: '',
  phone: '',
  role: 'MODERATOR',
  permission: ['manage:support', 'manage:emails']
})

const allPermissions = [
  { value: 'manage:all', label: 'Full Access (All Permissions)' },
  { value: 'manage:admins', label: 'Manage Team & Permissions' },
  { value: 'manage:billings', label: 'Manage Plans & Billings' },
  { value: 'manage:stores', label: 'Moderate Stores' },
  { value: 'manage:users', label: 'Manage Merchants' },
  { value: 'manage:emails', label: 'Campaigns & Inboxes' },
  { value: 'manage:support', label: 'Resolve Support Tickets' },
  { value: 'manage:settings', label: 'Edit System Settings' },
  { value: 'view:audit_logs', label: 'View Audit Logs' },
  { value: 'view:analytics', label: 'View Analytics' }
]

async function fetchAdmins() {
  isLoading.value = true
  try {
    const data = await apiFetch<any[]>('/admin/admins')
    admins.value = data || []
  } catch {
    admins.value = []
  } finally {
    isLoading.value = false
  }
}

const isEditingSelf = computed(() => {
  return !!(selectedAdmin.value && adminUser.value && selectedAdmin.value.admin_id === adminUser.value.admin_id)
})

const isSuperAdmin = computed(() => {
  return adminUser.value?.role === 'SUPER_ADMIN'
})

const isTargetSuperAdmin = computed(() => {
  return selectedAdmin.value?.role === 'SUPER_ADMIN'
})

const canEditPermissionsAndRole = computed(() => {
  if (isSuperAdmin.value) return true
  if (isEditingSelf.value) return false
  if (isTargetSuperAdmin.value) return false
  return canManageAdmins.value
})

function viewAdmin(a: any) {
  selectedAdmin.value = JSON.parse(JSON.stringify(a))
  isDetailOpen.value = true
}

function togglePermission(formObj: any, perm: string) {
  if (!canEditPermissionsAndRole.value && formObj === selectedAdmin.value) return
  const index = formObj.permission.indexOf(perm)
  if (index > -1) {
    formObj.permission.splice(index, 1)
  } else {
    formObj.permission.push(perm)
  }
}

async function handleInviteAdmin() {
  if (!inviteForm.value.fullname || !inviteForm.value.personal_email) {
    alert('Please enter name and personal email')
    return
  }
  isInviting.value = true
  try {
    await apiFetch('/admin/admins', {
      method: 'POST',
      body: inviteForm.value
    })
    isInviteOpen.value = false
    inviteForm.value = {
      fullname: '',
      personal_email: '',
      phone: '',
      role: 'MODERATOR',
      permission: ['manage:support', 'manage:emails']
    }
    await fetchAdmins()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to invite admin')
  } finally {
    isInviting.value = false
  }
}

async function handleUpdateAdmin() {
  if (!selectedAdmin.value) return
  isSaving.value = true
  try {
    await apiFetch(`/admin/admins/${selectedAdmin.value.admin_id}`, {
      method: 'PUT',
      body: {
        fullname: selectedAdmin.value.fullname,
        role: selectedAdmin.value.role,
        permission: selectedAdmin.value.permission,
        status: selectedAdmin.value.status
      }
    })
    isDetailOpen.value = false
    await fetchAdmins()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to update admin')
  } finally {
    isSaving.value = false
  }
}

async function handleDeleteAdmin(adminId: string) {
  if (!confirm('Are you sure you want to revoke this admin account?')) return
  try {
    await apiFetch(`/admin/admins/${adminId}`, { method: 'DELETE' })
    await fetchAdmins()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to delete admin')
  }
}

onMounted(() => {
  fetchAdmins()
})
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white">Admin Team Management</h1>
        <p class="text-xs text-zinc-400 mt-0.5">Control operator access, permissions matrix, and company mailboxes</p>
      </div>
      <UButton
        v-if="canManageAdmins"
        label="Invite New Admin"
        icon="i-lucide-user-plus"
        color="primary"
        size="sm"
        @click="isInviteOpen = true"
      />
    </div>

    <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl overflow-hidden backdrop-blur-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px] tracking-wider">
            <tr>
              <th class="px-5 py-3.5">Admin</th>
              <th class="px-5 py-3.5">Company Mailbox</th>
              <th class="px-5 py-3.5">Recovery Email</th>
              <th class="px-5 py-3.5">Role</th>
              <th class="px-5 py-3.5">Status</th>
              <th class="px-5 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60">
            <tr v-if="isLoading">
              <td colspan="6" class="px-5 py-8 text-center text-zinc-500">Loading admin team...</td>
            </tr>
            <tr
              v-for="a in admins"
              v-else
              :key="a.admin_id"
              class="hover:bg-zinc-800/30 transition-colors"
            >
              <td class="px-5 py-3.5 font-medium text-zinc-100">{{ a.fullname }}</td>
              <td class="px-5 py-3.5 font-mono text-emerald-400">{{ a.company_email }}</td>
              <td class="px-5 py-3.5 text-zinc-400">{{ a.personal_email }}</td>
              <td class="px-5 py-3.5">
                <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-zinc-800 text-zinc-200 border border-zinc-700">
                  {{ a.role }}
                </span>
              </td>
              <td class="px-5 py-3.5">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-semibold border',
                    a.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  ]"
                >
                  {{ a.status }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-right flex items-center justify-end gap-1.5">
                <UButton
                  label="Inspect"
                  size="xs"
                  color="neutral"
                  variant="outline"
                  icon="i-lucide-eye"
                  @click="viewAdmin(a)"
                />
                <UButton
                  v-if="adminUser?.admin_id !== a.admin_id"
                  icon="i-lucide-trash-2"
                  color="error"
                  variant="ghost"
                  size="xs"
                  title="Revoke Admin"
                  @click="handleDeleteAdmin(a.admin_id)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminFullScreenModal
      v-if="selectedAdmin"
      v-model="isDetailOpen"
      :title="selectedAdmin.fullname"
      :description="selectedAdmin.company_email"
      max-width="max-w-xl"
    >
      <div class="flex flex-col gap-4">
        <div
          v-if="isEditingSelf && !isSuperAdmin"
          class="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-300 flex items-center gap-2"
        >
          <UIcon name="i-lucide-shield-alert" class="size-4 shrink-0" />
          <span>You cannot modify your own role, status, or permissions.</span>
        </div>

        <div
          v-else-if="isTargetSuperAdmin && !isSuperAdmin"
          class="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300 flex items-center gap-2"
        >
          <UIcon name="i-lucide-shield-check" class="size-4 shrink-0" />
          <span>Only Super Admins can modify a Super Admin account.</span>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Role</label>
          <select
            v-model="selectedAdmin.role"
            :disabled="!canEditPermissionsAndRole"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value="MODERATOR">Moderator</option>
            <option value="ADMIN">Admin</option>
            <option v-if="isSuperAdmin" value="SUPER_ADMIN">Super Admin</option>
          </select>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Status</label>
          <select
            v-model="selectedAdmin.status"
            :disabled="!canEditPermissionsAndRole"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value="ACTIVE">Active</option>
            <option value="SUSPENDED">Suspended</option>
          </select>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs font-medium text-zinc-300">Permissions Matrix</label>
          <div
            class="grid grid-cols-1 gap-2 bg-zinc-950 p-3.5 rounded-xl border border-zinc-800 max-h-60 overflow-y-auto"
            :class="{ 'opacity-60 pointer-events-none': !canEditPermissionsAndRole }"
          >
            <label
              v-for="p in allPermissions"
              :key="p.value"
              class="flex items-center gap-2 text-xs text-zinc-300"
              :class="canEditPermissionsAndRole ? 'cursor-pointer' : 'cursor-not-allowed'"
            >
              <input
                type="checkbox"
                :disabled="!canEditPermissionsAndRole"
                :checked="selectedAdmin.permission?.includes(p.value)"
                class="rounded bg-zinc-900 border-zinc-700 text-emerald-500 focus:ring-0 disabled:opacity-50"
                @change="togglePermission(selectedAdmin, p.value)"
              >
              <span>{{ p.label }}</span>
            </label>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isDetailOpen = false" />
          <UButton
            label="Save Changes"
            icon="i-lucide-save"
            color="primary"
            size="sm"
            :disabled="!canManageAdmins"
            :loading="isSaving"
            @click="handleUpdateAdmin"
          />
        </div>
      </template>
    </AdminFullScreenModal>

    <AdminFullScreenModal
      v-model="isInviteOpen"
      title="Invite Administrator"
      description="Send an invitation email to a new team member."
      max-width="max-w-xl"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Full Name</label>
          <UInput v-model="inviteForm.fullname" placeholder="John Doe" size="sm" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Personal Recovery Email</label>
          <UInput v-model="inviteForm.personal_email" placeholder="john.doe@gmail.com" size="sm" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Admin Role</label>
          <select
            v-model="inviteForm.role"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="MODERATOR">Moderator</option>
            <option value="ADMIN">Admin</option>
            <option v-if="isSuperAdmin" value="SUPER_ADMIN">Super Admin</option>
          </select>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs font-medium text-zinc-300">Permissions Matrix</label>
          <div class="grid grid-cols-1 gap-2 bg-zinc-950 p-3 rounded-xl border border-zinc-800 max-h-60 overflow-y-auto">
            <label
              v-for="p in allPermissions"
              :key="p.value"
              class="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer"
            >
              <input
                type="checkbox"
                :checked="inviteForm.permission.includes(p.value)"
                class="rounded bg-zinc-900 border-zinc-700 text-emerald-500 focus:ring-0"
                @change="togglePermission(inviteForm, p.value)"
              >
              <span>{{ p.label }}</span>
            </label>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isInviteOpen = false" />
          <UButton
            label="Send Invitation"
            icon="i-lucide-mail"
            color="primary"
            size="sm"
            :loading="isInviting"
            @click="handleInviteAdmin"
          />
        </div>
      </template>
    </AdminFullScreenModal>
  </div>
</template>
