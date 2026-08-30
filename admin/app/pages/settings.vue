<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { canManageSettings } = useAdminPermission()
const config = useRuntimeConfig()
const domain = (config.public.domainName as string) || 'kluda.app'

const settingsList = ref<any[]>([])
const auditLogs = ref<any[]>([])
const mailboxes = ref<any[]>([])
const admins = ref<any[]>([])
const isLoading = ref(true)
const isSaving = ref(false)

const maintenanceEnabled = ref(false)
const maintenanceMessage = ref('Scheduled maintenance in progress. We will be back shortly.')
const minPosVersion = ref('1.0.0')

const isMailboxModalOpen = ref(false)
const isCreatingMailbox = ref(false)
const mailboxForm = ref({
  name: '',
  emailPrefix: '',
  allowed_admin_ids: [] as string[]
})

const isEditMailboxModalOpen = ref(false)
const isUpdatingMailbox = ref(false)
const editingMailbox = ref<any>(null)
const editingMailboxForm = ref({
  name: '',
  allowed_admin_ids: [] as string[]
})

const selectedAuditLog = ref<any>(null)

const {
  isSupported: isPushSupported,
  isSubscribed: isPushSubscribed,
  isLoading: isPushLoading,
  permissionStatus: pushPermissionStatus,
  checkSupportAndStatus: checkPushStatus,
  subscribe: subscribePush,
  unsubscribe: unsubscribePush,
  sendTestNotification,
} = useAdminPushNotification()

async function handleTogglePush(val: boolean) {
  if (val) {
    const success = await subscribePush()
    if (!success) {
      alert('Could not enable notifications. Please ensure you allowed notification permissions in your browser.')
    }
  } else {
    await unsubscribePush()
  }
}

async function handleSendTestAlert() {
  const success = await sendTestNotification()
  if (success) {
    alert('Test notification dispatched to your registered devices!')
  } else {
    alert('Failed to send test notification. Ensure push notifications are enabled.')
  }
}

async function fetchData() {
  isLoading.value = true
  try {
    const [sets, logs, mbs, admList] = await Promise.all([
      apiFetch<any[]>('/admin/settings'),
      apiFetch<any[]>('/admin/audit'),
      apiFetch<any[]>('/admin/mailboxes'),
      apiFetch<any[]>('/admin/admins')
    ])
    settingsList.value = sets || []
    auditLogs.value = logs || []
    mailboxes.value = mbs || []
    admins.value = admList || []

    const maint = sets?.find(s => s.key === 'maintenance_mode')
    if (maint?.value) {
      maintenanceEnabled.value = !!maint.value.enabled
      maintenanceMessage.value = maint.value.message || maintenanceMessage.value
    }

    const posVer = sets?.find(s => s.key === 'min_pos_version')
    if (posVer?.value) {
      minPosVersion.value = posVer.value.version || '1.0.0'
    }
  } catch {
    // fallback
  } finally {
    isLoading.value = false
  }
}

async function saveSettings() {
  isSaving.value = true
  try {
    await Promise.all([
      apiFetch('/admin/settings/maintenance_mode', {
        method: 'PUT',
        body: {
          value: { enabled: maintenanceEnabled.value, message: maintenanceMessage.value },
          description: 'Global maintenance mode state'
        }
      }),
      apiFetch('/admin/settings/min_pos_version', {
        method: 'PUT',
        body: {
          value: { version: minPosVersion.value },
          description: 'Minimum required POS version'
        }
      })
    ])
    alert('System settings updated successfully')
    await fetchData()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to save settings')
  } finally {
    isSaving.value = false
  }
}

function toggleAdminAccess(adminId: string) {
  const idx = mailboxForm.value.allowed_admin_ids.indexOf(adminId)
  if (idx > -1) {
    mailboxForm.value.allowed_admin_ids.splice(idx, 1)
  } else {
    mailboxForm.value.allowed_admin_ids.push(adminId)
  }
}

function toggleEditAdminAccess(adminId: string) {
  const idx = editingMailboxForm.value.allowed_admin_ids.indexOf(adminId)
  if (idx > -1) {
    editingMailboxForm.value.allowed_admin_ids.splice(idx, 1)
  } else {
    editingMailboxForm.value.allowed_admin_ids.push(adminId)
  }
}

async function handleCreatePublicMailbox() {
  if (!mailboxForm.value.name || !mailboxForm.value.emailPrefix) {
    alert('Please provide a name and email prefix for the public mailbox')
    return
  }
  isCreatingMailbox.value = true
  try {
    await apiFetch('/admin/mailboxes', {
      method: 'POST',
      body: {
        name: mailboxForm.value.name,
        email: `${mailboxForm.value.emailPrefix.trim()}@${domain}`,
        type: 'shared',
        allowed_admin_ids: mailboxForm.value.allowed_admin_ids
      }
    })
    isMailboxModalOpen.value = false
    mailboxForm.value = { name: '', emailPrefix: '', allowed_admin_ids: [] }
    await fetchData()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to create mailbox')
  } finally {
    isCreatingMailbox.value = false
  }
}

function openEditMailbox(mb: any) {
  editingMailbox.value = mb
  editingMailboxForm.value = {
    name: mb.name,
    allowed_admin_ids: mb.allowed_admin_ids ? [...mb.allowed_admin_ids] : []
  }
  isEditMailboxModalOpen.value = true
}

async function handleUpdateMailbox() {
  if (!editingMailbox.value) return
  isUpdatingMailbox.value = true
  try {
    await apiFetch(`/admin/mailboxes/${editingMailbox.value.mailbox_id}`, {
      method: 'PUT',
      body: {
        name: editingMailboxForm.value.name,
        allowed_admin_ids: editingMailboxForm.value.allowed_admin_ids
      }
    })
    isEditMailboxModalOpen.value = false
    editingMailbox.value = null
    await fetchData()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to update mailbox access')
  } finally {
    isUpdatingMailbox.value = false
  }
}

async function handleDeleteMailbox(id: string) {
  if (!confirm('Are you sure you want to delete this shared mailbox?')) return
  try {
    await apiFetch(`/admin/mailboxes/${id}`, { method: 'DELETE' })
    await fetchData()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to delete mailbox')
  }
}

onMounted(() => {
  fetchData()
  checkPushStatus()
})
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-8 max-w-7xl w-full mx-auto">
    <div>
      <h1 class="text-xl font-bold tracking-tight text-white">System Settings & Infrastructure Control</h1>
      <p class="text-xs text-zinc-400 mt-0.5">Dynamic platform configurations, shared email mailboxes, and audit trails</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="flex flex-col gap-6">
        <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-5 backdrop-blur-sm">
          <div>
            <h2 class="text-sm font-bold text-white">Platform Controls</h2>
            <p class="text-xs text-zinc-400 mt-0.5">Maintenance switches and terminal requirements</p>
          </div>

          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between p-3.5 rounded-xl bg-zinc-950/60 border border-zinc-800/80">
              <div>
                <div class="text-xs font-semibold text-zinc-200">Maintenance Mode</div>
                <div class="text-[11px] text-zinc-400">Lock merchant and POS apps for updates</div>
              </div>
              <USwitch v-model="maintenanceEnabled" :disabled="!canManageSettings" />
            </div>

            <div v-if="maintenanceEnabled" class="flex flex-col gap-1.5">
              <label class="text-xs font-medium text-zinc-300">Public Maintenance Message</label>
              <UInput
                v-model="maintenanceMessage"
                placeholder="e.g. Upgrading database clusters..."
                size="sm"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-medium text-zinc-300">Minimum POS App Version</label>
              <UInput v-model="minPosVersion" placeholder="1.0.0" size="sm" />
              <span class="text-[10px] text-zinc-500">Older client versions will be prompted to reload.</span>
            </div>

            <UButton
              label="Save Configurations"
              icon="i-lucide-check"
              color="primary"
              size="sm"
              :disabled="!canManageSettings"
              :loading="isSaving"
              @click="saveSettings"
            />
          </div>
        </div>

        <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-5 backdrop-blur-sm">
          <div>
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <UIcon name="i-lucide-bell-ring" class="w-4 h-4 text-emerald-400" />
              Admin Push Notifications
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5">Real-time alerts for incoming tickets and system events</p>
          </div>

          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between p-3.5 rounded-xl bg-zinc-950/60 border border-zinc-800/80">
              <div>
                <div class="text-xs font-semibold text-zinc-200">Browser Push Alerts</div>
                <div class="text-[11px] text-zinc-400">
                  {{ isPushSubscribed ? 'Alerts active on this browser' : 'Receive instant operational alerts' }}
                </div>
              </div>
              <USwitch
                :model-value="isPushSubscribed"
                :loading="isPushLoading"
                :disabled="!isPushSupported"
                @update:model-value="handleTogglePush"
              />
            </div>

            <div v-if="pushPermissionStatus === 'denied'" class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs flex items-start gap-2">
              <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <p class="font-bold">Notifications Blocked</p>
                <p class="text-[11px] text-amber-300/80 mt-0.5">Please click the site permissions icon in your address bar and set Notifications to "Allow".</p>
              </div>
            </div>

            <div v-if="isPushSubscribed" class="flex items-center justify-between pt-1">
              <span class="text-[11px] text-zinc-400">Verify device connectivity</span>
              <UButton
                label="Send Test Alert"
                icon="i-lucide-send"
                color="neutral"
                variant="outline"
                size="xs"
                @click="handleSendTestAlert"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="lg:col-span-2 bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-4 backdrop-blur-sm">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-bold text-white">Public & Shared Company Mailboxes</h2>
            <p class="text-xs text-zinc-400 mt-0.5">Create global email inboxes (e.g. support@, billing@) and configure admin access</p>
          </div>
          <UButton
            label="Create Public Email"
            icon="i-lucide-plus"
            size="xs"
            color="primary"
            :disabled="!canManageSettings"
            @click="isMailboxModalOpen = true"
          />
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px]">
              <tr>
                <th class="px-4 py-3">Mailbox Name</th>
                <th class="px-4 py-3">Public Email</th>
                <th class="px-4 py-3">Type</th>
                <th class="px-4 py-3">Access Scope</th>
                <th class="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-800/50">
              <tr v-if="isLoading">
                <td colspan="5" class="px-4 py-6 text-center text-zinc-500">Loading mailboxes...</td>
              </tr>
              <tr v-else-if="mailboxes.length === 0">
                <td colspan="5" class="px-4 py-6 text-center text-zinc-500">No public mailboxes created yet.</td>
              </tr>
              <tr
                v-for="mb in mailboxes"
                v-else
                :key="mb.mailbox_id"
                class="hover:bg-zinc-800/30 transition-colors"
              >
                <td class="px-4 py-3 font-medium text-zinc-200">{{ mb.name }}</td>
                <td class="px-4 py-3 font-mono text-emerald-400">{{ mb.email }}</td>
                <td class="px-4 py-3 uppercase text-[10px] text-zinc-400">{{ mb.type }}</td>
                <td class="px-4 py-3 text-zinc-300">
                  <span v-if="mb.type === 'personal'" class="text-zinc-500">Personal (Owner only)</span>
                  <span v-else-if="!mb.allowed_admin_ids || mb.allowed_admin_ids.length === 0" class="text-emerald-400 font-medium">All Admins</span>
                  <span v-else class="text-blue-400 font-mono">{{ mb.allowed_admin_ids.length }} assigned admins</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <div class="flex items-center justify-end gap-1.5">
                    <UButton
                      v-if="mb.type === 'shared'"
                      icon="i-lucide-user-check"
                      color="neutral"
                      variant="ghost"
                      size="xs"
                      title="Manage Access"
                      :disabled="!canManageSettings"
                      @click="openEditMailbox(mb)"
                    />
                    <UButton
                      v-if="mb.type === 'shared'"
                      icon="i-lucide-trash-2"
                      color="error"
                      variant="ghost"
                      size="xs"
                      title="Delete Public Mailbox"
                      :disabled="!canManageSettings"
                      @click="handleDeleteMailbox(mb.mailbox_id)"
                    />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-4 backdrop-blur-sm">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold text-white">Security & Administrative Audit Trail</h2>
          <p class="text-xs text-zinc-400 mt-0.5">Click on any record to inspect structured event details</p>
        </div>
        <span class="text-[11px] text-zinc-400 font-mono">{{ auditLogs.length }} recorded events</span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px]">
            <tr>
              <th class="px-4 py-3">Action</th>
              <th class="px-4 py-3">Target</th>
              <th class="px-4 py-3">Performed By</th>
              <th class="px-4 py-3">IP Address</th>
              <th class="px-4 py-3">Timestamp</th>
              <th class="px-4 py-3 text-right">Inspect</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/50">
            <tr v-if="isLoading">
              <td colspan="6" class="px-4 py-6 text-center text-zinc-500">Loading audit trail...</td>
            </tr>
            <tr v-else-if="auditLogs.length === 0">
              <td colspan="6" class="px-4 py-6 text-center text-zinc-500">No audit events recorded yet.</td>
            </tr>
            <tr
              v-for="l in auditLogs"
              v-else
              :key="l.log_id"
              class="hover:bg-zinc-800/40 transition-colors cursor-pointer"
              @click="selectedAuditLog = l"
            >
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {{ l.action }}
                </span>
              </td>
              <td class="px-4 py-3 text-zinc-300">
                <span class="capitalize text-[11px] font-medium">{{ l.target_type }}</span>
                <span v-if="l.target_id" class="text-zinc-500 font-mono text-[10px] ml-1">#{{ String(l.target_id).slice(0, 8) }}</span>
              </td>
              <td class="px-4 py-3 text-zinc-200">
                <div class="font-medium">{{ l.admin_name || 'System / Automated' }}</div>
                <div v-if="l.admin_email" class="text-[10px] text-zinc-500">{{ l.admin_email }}</div>
              </td>
              <td class="px-4 py-3 font-mono text-[11px] text-zinc-400">{{ l.ip_address || '—' }}</td>
              <td class="px-4 py-3 text-zinc-500 text-[11px] font-mono whitespace-nowrap">
                {{ new Date(l.created_at).toLocaleString() }}
              </td>
              <td class="px-4 py-3 text-right">
                <UButton
                  icon="i-lucide-eye"
                  color="neutral"
                  variant="ghost"
                  size="xs"
                  title="Inspect Event"
                  @click.stop="selectedAuditLog = l"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      v-if="isMailboxModalOpen"
      class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      @click="isMailboxModalOpen = false"
    >
      <div
        class="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col gap-5 shadow-2xl"
        @click.stop
      >
        <div class="flex items-center justify-between border-b border-zinc-800 pb-3">
          <h2 class="text-base font-bold text-white">Create Public / Shared Mailbox</h2>
          <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="xs" @click="isMailboxModalOpen = false" />
        </div>

        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Mailbox Display Name</label>
            <UInput v-model="mailboxForm.name" placeholder="Billing & Subscriptions" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Email Address Prefix</label>
            <div class="flex items-center">
              <UInput
                v-model="mailboxForm.emailPrefix"
                placeholder="billing"
                size="sm"
                class="flex-1 rounded-r-none"
              />
              <span class="px-3 py-1.5 bg-zinc-950 border border-l-0 border-zinc-800 text-xs font-mono text-zinc-400 rounded-r-lg">
                @{{ domain }}
              </span>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-zinc-300">Allowed Admins with Access</label>
              <span class="text-[11px] text-zinc-500">Leave empty for All Admins</span>
            </div>
            <div class="grid grid-cols-1 gap-2 bg-zinc-950 p-3 rounded-xl border border-zinc-800 max-h-48 overflow-y-auto">
              <label
                v-for="adm in admins"
                :key="adm.admin_id"
                class="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="mailboxForm.allowed_admin_ids.includes(adm.admin_id)"
                  class="rounded bg-zinc-900 border-zinc-700 text-emerald-500 focus:ring-0"
                  @change="toggleAdminAccess(adm.admin_id)"
                >
                <span>{{ adm.fullname }} ({{ adm.company_email }})</span>
              </label>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 border-t border-zinc-800 pt-3">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isMailboxModalOpen = false" />
          <UButton
            label="Create Public Mailbox"
            icon="i-lucide-plus"
            color="primary"
            size="sm"
            :disabled="!canManageSettings"
            :loading="isCreatingMailbox"
            @click="handleCreatePublicMailbox"
          />
        </div>
      </div>
    </div>

    <div
      v-if="isEditMailboxModalOpen && editingMailbox"
      class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      @click="isEditMailboxModalOpen = false"
    >
      <div
        class="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col gap-5 shadow-2xl"
        @click.stop
      >
        <div class="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div>
            <h2 class="text-base font-bold text-white">Manage Mailbox Access</h2>
            <p class="text-xs text-zinc-400">{{ editingMailbox.email }}</p>
          </div>
          <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="xs" @click="isEditMailboxModalOpen = false" />
        </div>

        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Mailbox Display Name</label>
            <UInput v-model="editingMailboxForm.name" placeholder="Support Desk" size="sm" />
          </div>

          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-zinc-300">Assigned Admins</label>
              <button
                type="button"
                class="text-[11px] text-emerald-400 hover:underline"
                @click="editingMailboxForm.allowed_admin_ids = []"
              >
                Reset to All Admins
              </button>
            </div>
            <div class="grid grid-cols-1 gap-2 bg-zinc-950 p-3 rounded-xl border border-zinc-800 max-h-48 overflow-y-auto">
              <label
                v-for="adm in admins"
                :key="adm.admin_id"
                class="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="editingMailboxForm.allowed_admin_ids.includes(adm.admin_id)"
                  class="rounded bg-zinc-900 border-zinc-700 text-emerald-500 focus:ring-0"
                  @change="toggleEditAdminAccess(adm.admin_id)"
                >
                <span>{{ adm.fullname }} ({{ adm.company_email }})</span>
              </label>
            </div>
            <p class="text-[11px] text-zinc-500">
              {{ editingMailboxForm.allowed_admin_ids.length === 0 ? 'Currently accessible by All Admins.' : `Restricted to ${editingMailboxForm.allowed_admin_ids.length} selected admin(s).` }}
            </p>
          </div>
        </div>

        <div class="flex justify-end gap-2 border-t border-zinc-800 pt-3">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isEditMailboxModalOpen = false" />
          <UButton
            label="Save Access Permissions"
            icon="i-lucide-check"
            color="primary"
            size="sm"
            :disabled="!canManageSettings"
            :loading="isUpdatingMailbox"
            @click="handleUpdateMailbox"
          />
        </div>
      </div>
    </div>

    <div
      v-if="selectedAuditLog"
      class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end"
      @click="selectedAuditLog = null"
    >
      <div
        class="w-full max-w-md bg-zinc-900 border-l border-zinc-800 h-full p-6 flex flex-col gap-5 shadow-2xl overflow-y-auto animate-in slide-in-from-right duration-200"
        @click.stop
      >
        <div class="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div>
            <h2 class="text-base font-bold text-white">Audit Event Details</h2>
            <p class="text-[11px] text-zinc-400 font-mono">{{ selectedAuditLog.log_id }}</p>
          </div>
          <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="xs" @click="selectedAuditLog = null" />
        </div>

        <div class="flex flex-col gap-4 text-xs">
          <div class="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-zinc-950 border border-zinc-800">
            <div>
              <span class="text-zinc-500 block text-[10px] uppercase font-bold">Action</span>
              <span class="font-mono text-emerald-400 font-bold">{{ selectedAuditLog.action }}</span>
            </div>
            <div>
              <span class="text-zinc-500 block text-[10px] uppercase font-bold">Target</span>
              <span class="font-medium text-zinc-200 uppercase">{{ selectedAuditLog.target_type }}</span>
            </div>
            <div>
              <span class="text-zinc-500 block text-[10px] uppercase font-bold">Performed By</span>
              <span class="font-medium text-zinc-200">{{ selectedAuditLog.admin_name || 'System' }}</span>
            </div>
            <div>
              <span class="text-zinc-500 block text-[10px] uppercase font-bold">IP Address</span>
              <span class="font-mono text-zinc-400">{{ selectedAuditLog.ip_address || '—' }}</span>
            </div>
          </div>

          <div class="flex flex-col gap-1.5">
            <span class="text-zinc-400 font-semibold text-[11px]">Event Payload & Metadata</span>
            <pre class="bg-zinc-950 p-4 rounded-xl border border-zinc-800 font-mono text-[11px] text-emerald-400 overflow-x-auto whitespace-pre-wrap leading-relaxed">{{ JSON.stringify(selectedAuditLog.details, null, 2) || '{}' }}</pre>
          </div>

          <div class="flex flex-col gap-1 text-[11px] text-zinc-500">
            <span>Timestamp: {{ new Date(selectedAuditLog.created_at).toLocaleString() }}</span>
            <span v-if="selectedAuditLog.target_id">Target ID: {{ selectedAuditLog.target_id }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
