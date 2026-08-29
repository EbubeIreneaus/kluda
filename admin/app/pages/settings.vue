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

async function handleCreatePublicMailbox() {
  if (!mailboxForm.value.name || !mailboxForm.value.emailPrefix) {
    alert('Please enter mailbox name and email prefix')
    return
  }

  isCreatingMailbox.value = true
  const fullEmail = `${mailboxForm.value.emailPrefix.trim().toLowerCase()}@${domain}`
  try {
    await apiFetch('/admin/mailboxes', {
      method: 'POST',
      body: {
        name: mailboxForm.value.name,
        email: fullEmail,
        type: 'shared',
        allowed_admin_ids: mailboxForm.value.allowed_admin_ids
      }
    })
    isMailboxModalOpen.value = false
    mailboxForm.value = {
      name: '',
      emailPrefix: '',
      allowed_admin_ids: []
    }
    await fetchData()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to create public mailbox')
  } finally {
    isCreatingMailbox.value = false
  }
}

async function handleDeleteMailbox(mbId: string) {
  if (!confirm('Are you sure you want to delete this shared mailbox?')) return
  try {
    await apiFetch(`/admin/mailboxes/${mbId}`, { method: 'DELETE' })
    await fetchData()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to delete mailbox')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-8 max-w-7xl w-full mx-auto">
    <div>
      <h1 class="text-xl font-bold tracking-tight text-white">System Settings & Public Inboxes</h1>
      <p class="text-xs text-zinc-400 mt-0.5">Dynamic platform configurations, shared email mailboxes, and audit trails</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-6 backdrop-blur-sm">
        <h2 class="text-sm font-bold text-white">Remote Platform Controls</h2>

        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between p-3 rounded-xl bg-zinc-950 border border-zinc-800">
            <div>
              <div class="text-xs font-semibold text-zinc-200">Maintenance Mode</div>
              <div class="text-[11px] text-zinc-400 mt-0.5">Temporarily pauses all POS sync and portal access</div>
            </div>
            <input
              v-model="maintenanceEnabled"
              type="checkbox"
              class="w-5 h-5 rounded bg-zinc-900 border-zinc-700 text-emerald-500 focus:ring-0 cursor-pointer"
            >
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Maintenance Message</label>
            <UInput v-model="maintenanceMessage" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Minimum POS App Version</label>
            <UInput v-model="minPosVersion" placeholder="1.0.0" size="sm" />
          </div>

          <UButton
            label="Save Remote Settings"
            icon="i-lucide-save"
            color="primary"
            block
            size="sm"
            :disabled="!canManageSettings"
            :loading="isSaving"
            @click="saveSettings"
          />
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
                <th class="px-4 py-3 text-right">Action</th>
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
                  <span v-else-if="!mb.allowed_admin_ids || mb.allowed_admin_ids.length === 0" class="text-emerald-400">All Admins</span>
                  <span v-else class="text-blue-400 font-mono">{{ mb.allowed_admin_ids.length }} assigned admins</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <UButton
                    v-if="mb.type === 'shared'"
                    icon="i-lucide-trash-2"
                    color="error"
                    variant="ghost"
                    size="xs"
                    title="Delete Public Mailbox"
                    @click="handleDeleteMailbox(mb.mailbox_id)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-4 backdrop-blur-sm">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-bold text-white">Security & Administrative Audit Trail</h2>
        <span class="text-[11px] text-zinc-400 font-mono">{{ auditLogs.length }} recorded events</span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px]">
            <tr>
              <th class="px-4 py-3">Action</th>
              <th class="px-4 py-3">Target</th>
              <th class="px-4 py-3">Details</th>
              <th class="px-4 py-3">Timestamp</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/50">
            <tr v-if="isLoading">
              <td colspan="4" class="px-4 py-6 text-center text-zinc-500">Loading audit trail...</td>
            </tr>
            <tr v-else-if="auditLogs.length === 0">
              <td colspan="4" class="px-4 py-6 text-center text-zinc-500">No audit events recorded yet.</td>
            </tr>
            <tr
              v-for="l in auditLogs"
              :key="l.log_id"
              class="hover:bg-zinc-800/30 transition-colors"
            >
              <td class="px-4 py-3 font-mono font-semibold text-emerald-400">{{ l.action }}</td>
              <td class="px-4 py-3 uppercase text-[10px] text-zinc-300">{{ l.target_type }}</td>
              <td class="px-4 py-3 text-zinc-400 font-mono text-[11px] max-w-xs truncate">
                {{ l.details ? JSON.stringify(l.details) : 'None' }}
              </td>
              <td class="px-4 py-3 text-zinc-500 text-[11px] font-mono whitespace-nowrap">
                {{ new Date(l.created_at).toLocaleString() }}
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
  </div>
</template>
