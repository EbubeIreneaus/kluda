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

// Full audit log modal state
const isAuditModalOpen = ref(false)
const auditModalLogs = ref<any[]>([])
const auditModalPage = ref(1)
const auditModalPageSize = 25
const auditModalTotal = ref(0)
const auditModalLoading = ref(false)
const auditModalLoadingMore = ref(false)
const auditModalScrollContainer = ref<HTMLElement | null>(null)

const toast = useToast()

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
    const res = await subscribePush()
    if (res.success) {
      toast.add({
        title: 'Push Notifications Enabled',
        description: res.message || 'You will now receive system notifications and security alerts.',
        color: 'success',
      })
    } else {
      toast.add({
        title: 'Could Not Enable Notifications',
        description: res.message || 'Please check your browser notification permissions.',
        color: 'error',
      })
    }
  } else {
    const res = await unsubscribePush()
    if (res.success) {
      toast.add({
        title: 'Push Notifications Disabled',
        description: res.message || 'This device will no longer receive alerts.',
        color: 'neutral',
      })
    }
  }
}

async function handleSendTestAlert() {
  const res = await sendTestNotification()
  if (res.success) {
    toast.add({
      title: 'Test Alert Sent',
      description: res.message || 'Test notification dispatched to your registered devices!',
      color: 'success',
    })
  } else {
    toast.add({
      title: 'Failed to Send Test Alert',
      description: res.message || 'Ensure push notifications are enabled on your account.',
      color: 'error',
    })
  }
}

async function fetchData() {
  isLoading.value = true
  try {
    const [sets, logs, mbs, admList] = await Promise.all([
      apiFetch<any[]>('/admin/settings'),
      apiFetch<any[]>('/admin/audit?limit=10'),
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

    const contactSetting = sets?.find(s => s.key === 'platform_contact_info')
    if (contactSetting?.value) {
      contactForm.value = { ...contactForm.value, ...contactSetting.value }
    }
  } catch {
    // fallback
  } finally {
    isLoading.value = false
  }
}

const isSavingContact = ref(false)
const contactForm = ref({
  email: '',
  phone: '',
  whatsapp: '',
  address: '',
  hours: '',
  facebook: '',
  twitter: '',
  linkedin: '',
  instagram: ''
})

async function saveContactSettings() {
  isSavingContact.value = true
  try {
    await apiFetch('/admin/settings/platform_contact_info', {
      method: 'PUT',
      body: {
        value: contactForm.value,
        description: 'Public platform contact info and social links'
      }
    })
    toast.add({
      title: 'Contact Information Updated',
      description: 'Platform contact details updated and public cache invalidated.',
      color: 'success'
    })
    await fetchData()
  } catch (err: any) {
    toast.add({
      title: 'Failed to Save',
      description: err?.data?.detail || 'Could not update contact settings',
      color: 'error'
    })
  } finally {
    isSavingContact.value = false
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
    toast.add({
      title: 'Settings Updated',
      description: 'System settings updated successfully.',
      color: 'success'
    })
    await fetchData()
  } catch (err: any) {
    toast.add({
      title: 'Error Saving Settings',
      description: err?.data?.detail || 'Failed to save settings',
      color: 'error'
    })
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

// ---- Full Audit Log Modal ----
async function openAuditModal() {
  isAuditModalOpen.value = true
  auditModalLogs.value = []
  auditModalPage.value = 1
  auditModalTotal.value = 0
  await fetchAuditPage()
}

async function fetchAuditPage() {
  if (auditModalLoading.value || auditModalLoadingMore.value) return
  const isFirst = auditModalPage.value === 1
  if (isFirst) auditModalLoading.value = true
  else auditModalLoadingMore.value = true
  try {
    const data = await apiFetch<any>(`/admin/audit/paginated?page=${auditModalPage.value}&size=${auditModalPageSize}`)
    auditModalLogs.value = [...auditModalLogs.value, ...(data.items || [])]
    auditModalTotal.value = data.total ?? 0
    auditModalPage.value += 1
  } catch {
    // ignore
  } finally {
    auditModalLoading.value = false
    auditModalLoadingMore.value = false
  }
}

const hasMoreAudit = computed(() => auditModalLogs.value.length < auditModalTotal.value)

function onAuditScroll(e: Event) {
  const el = e.target as HTMLElement
  if (!el) return
  const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 120
  if (nearBottom && hasMoreAudit.value && !auditModalLoadingMore.value) {
    fetchAuditPage()
  }
}

function closeAuditModal() {
  isAuditModalOpen.value = false
  auditModalLogs.value = []
  auditModalPage.value = 1
}

onMounted(() => {
  fetchData()
  checkPushStatus()
})
</script>

<template>
  <div class="overflow-y-auto p-6 md:p-8 flex flex-col gap-8 max-w-7xl w-full mx-auto">
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

        <!-- Platform Contact Information Card -->
        <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-5 backdrop-blur-sm">
          <div>
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <UIcon name="i-lucide-contact" class="w-4 h-4 text-emerald-400" />
              Platform Contact & Support Info
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5">Displayed publicly on website footer, legal docs, and app support</p>
          </div>

          <div class="flex flex-col gap-3.5">
            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-zinc-300">Support Email</label>
              <UInput v-model="contactForm.email" placeholder="support@kluda.com" size="sm" icon="i-lucide-mail" />
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-zinc-300">Phone</label>
                <UInput v-model="contactForm.phone" placeholder="+234..." size="sm" icon="i-lucide-phone" />
              </div>
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-zinc-300">WhatsApp</label>
                <UInput v-model="contactForm.whatsapp" placeholder="234..." size="sm" icon="i-lucide-message-circle" />
              </div>
            </div>

            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-zinc-300">Physical Address</label>
              <UInput v-model="contactForm.address" placeholder="Lagos, Nigeria" size="sm" icon="i-lucide-map-pin" />
            </div>

            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-zinc-300">Operating Hours</label>
              <UInput v-model="contactForm.hours" placeholder="Mon - Sat: 8:00 AM - 8:00 PM WAT" size="sm" icon="i-lucide-clock" />
            </div>

            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-zinc-300">Social Handles / Links</label>
              <div class="space-y-1.5">
                <UInput v-model="contactForm.facebook" placeholder="https://facebook.com/kluda.pos" size="xs" icon="i-lucide-facebook" />
                <UInput v-model="contactForm.twitter" placeholder="https://x.com/kluda_app" size="xs" icon="i-lucide-twitter" />
                <UInput v-model="contactForm.instagram" placeholder="https://instagram.com/kluda.pos" size="xs" icon="i-lucide-instagram" />
                <UInput v-model="contactForm.linkedin" placeholder="https://linkedin.com/company/kluda" size="xs" icon="i-lucide-linkedin" />
              </div>
            </div>

            <UButton
              label="Save Contact Information"
              icon="i-lucide-save"
              color="primary"
              size="sm"
              :disabled="!canManageSettings"
              :loading="isSavingContact"
              @click="saveContactSettings"
            />
          </div>
        </div>

        <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-5 backdrop-blur-sm">
          <div>
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <UIcon name="i-lucide-bell-ring" class="w-4 h-4 text-emerald-400" />
              Notifications
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5">Real-time alerts for incoming tickets and system events</p>
          </div>

          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between p-3.5 rounded-xl bg-zinc-950/60 border border-zinc-800/80">
              <div>
                <div class="text-xs font-semibold text-zinc-200">Notifications</div>
                <div class="text-[11px] text-zinc-400">
                  {{ isPushSubscribed ? 'Notifications active on this browser' : 'Receive instant notifications' }}
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
                label="Send Test Notification"
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

    <!-- Audit Trail Card (preview: 10 rows) -->
    <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-4 backdrop-blur-sm">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold text-white flex items-center gap-2">
            <UIcon name="i-lucide-shield-check" class="w-4 h-4 text-emerald-400" />
            Security &amp; Administrative Audit Trail
          </h2>
          <p class="text-xs text-zinc-400 mt-0.5">Recent admin actions — click any row to inspect, or view the full log</p>
        </div>
        <UButton
          label="View All"
          icon="i-lucide-external-link"
          color="neutral"
          variant="outline"
          size="xs"
          @click="openAuditModal"
        />
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
              v-for="l in auditLogs.slice(0, 10)"
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

      <!-- Show More footer -->
      <div class="flex items-center justify-between pt-1 border-t border-zinc-800/50">
        <span class="text-[11px] text-zinc-500">Showing last {{ Math.min(10, auditLogs.length) }} events</span>
        <UButton
          label="View Full Audit Log →"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="openAuditModal"
        />
      </div>
    </div>

    <!-- Full-Screen Audit Log Modal with Infinite Scroll -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-opacity duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="isAuditModalOpen"
          class="fixed inset-0 z-50 flex items-stretch justify-end"
        >
          <!-- Backdrop -->
          <div class="fixed inset-0 bg-black/70 backdrop-blur-xs" @click="closeAuditModal" />

          <!-- Slide-in Panel -->
          <Transition
            appear
            enter-active-class="transition-transform duration-300 ease-out"
            enter-from-class="translate-x-full"
            enter-to-class="translate-x-0"
            leave-active-class="transition-transform duration-200 ease-in"
            leave-from-class="translate-x-0"
            leave-to-class="translate-x-full"
          >
            <div
              v-if="isAuditModalOpen"
              class="relative z-10 w-full max-w-5xl bg-zinc-900 border-l border-zinc-800 flex flex-col h-screen shadow-2xl rounded-l-3xl"
            >
              <!-- Header -->
              <div class="shrink-0 px-6 py-4.5 border-b border-zinc-800/80 flex items-center justify-between bg-zinc-900">
                <div>
                  <h3 class="text-base font-bold text-white flex items-center gap-2">
                    <UIcon name="i-lucide-shield-check" class="size-5 text-emerald-400" />
                    Full Audit Trail
                  </h3>
                  <p class="text-xs text-zinc-400 mt-0.5">
                    {{ auditModalTotal }} total recorded events · scroll down to load more
                  </p>
                </div>
                <button
                  type="button"
                  class="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition shrink-0 cursor-pointer"
                  @click="closeAuditModal"
                >
                  <UIcon name="i-lucide-x" class="size-5" />
                </button>
              </div>

              <!-- Scrollable Table Area -->
              <div
                class="flex-1 overflow-y-auto"
                @scroll="onAuditScroll"
              >
                <!-- Initial Loading -->
                <div v-if="auditModalLoading" class="py-20 flex flex-col items-center gap-3 text-zinc-500 text-xs">
                  <UIcon name="i-lucide-loader-2" class="size-6 animate-spin text-emerald-400" />
                  Loading audit events...
                </div>

                <div v-else>
                  <table class="w-full text-left text-xs">
                    <thead class="sticky top-0 bg-zinc-950/95 backdrop-blur-sm border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px] z-10">
                      <tr>
                        <th class="px-5 py-3">Action</th>
                        <th class="px-5 py-3">Target</th>
                        <th class="px-5 py-3">Performed By</th>
                        <th class="px-5 py-3">IP Address</th>
                        <th class="px-5 py-3">Timestamp</th>
                        <th class="px-5 py-3 text-right">Inspect</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-zinc-800/40">
                      <tr v-if="auditModalLogs.length === 0">
                        <td colspan="6" class="px-5 py-10 text-center text-zinc-500">No audit events recorded yet.</td>
                      </tr>
                      <tr
                        v-for="l in auditModalLogs"
                        :key="l.log_id"
                        class="hover:bg-zinc-800/40 transition-colors cursor-pointer"
                        @click="selectedAuditLog = l"
                      >
                        <td class="px-5 py-3">
                          <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {{ l.action }}
                          </span>
                        </td>
                        <td class="px-5 py-3 text-zinc-300">
                          <span class="capitalize text-[11px] font-medium">{{ l.target_type }}</span>
                          <span v-if="l.target_id" class="text-zinc-500 font-mono text-[10px] ml-1">#{{ String(l.target_id).slice(0, 8) }}</span>
                        </td>
                        <td class="px-5 py-3 text-zinc-200">
                          <div class="font-medium">{{ l.admin_name || 'System / Automated' }}</div>
                          <div v-if="l.admin_email" class="text-[10px] text-zinc-500">{{ l.admin_email }}</div>
                        </td>
                        <td class="px-5 py-3 font-mono text-[11px] text-zinc-400">{{ l.ip_address || '—' }}</td>
                        <td class="px-5 py-3 text-zinc-500 text-[11px] font-mono whitespace-nowrap">
                          {{ new Date(l.created_at).toLocaleString() }}
                        </td>
                        <td class="px-5 py-3 text-right">
                          <UButton
                            icon="i-lucide-eye"
                            color="neutral"
                            variant="ghost"
                            size="xs"
                            @click.stop="selectedAuditLog = l"
                          />
                        </td>
                      </tr>
                    </tbody>
                  </table>

                  <!-- Load More Indicator -->
                  <div class="py-6 flex flex-col items-center gap-2">
                    <div v-if="auditModalLoadingMore" class="flex items-center gap-2 text-xs text-zinc-400">
                      <UIcon name="i-lucide-loader-2" class="size-4 animate-spin text-emerald-400" />
                      Loading more events...
                    </div>
                    <div v-else-if="!hasMoreAudit && auditModalLogs.length > 0" class="text-[11px] text-zinc-600">
                      All {{ auditModalTotal }} events loaded
                    </div>
                    <UButton
                      v-else-if="hasMoreAudit && !auditModalLoadingMore"
                      label="Load More"
                      icon="i-lucide-chevron-down"
                      color="neutral"
                      variant="ghost"
                      size="xs"
                      @click="fetchAuditPage"
                    />
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <AdminBottomSheet
      v-model="isMailboxModalOpen"
      title="Create Public / Shared Mailbox"
      description="Create a shared inbox address for your team"
      max-width="max-w-lg"
    >
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

      <template #footer>
        <div class="flex items-center justify-end gap-2">
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
      </template>
    </AdminBottomSheet>

    <AdminBottomSheet
      v-if="editingMailbox"
      v-model="isEditMailboxModalOpen"
      title="Manage Mailbox Access"
      :description="editingMailbox.email"
      max-width="max-w-lg"
    >
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

      <template #footer>
        <div class="flex items-center justify-end gap-2">
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
      </template>
    </AdminBottomSheet>

    <AdminFullScreenModal
      v-if="selectedAuditLog"
      :model-value="!!selectedAuditLog"
      title="Audit Event Details"
      :description="selectedAuditLog.log_id"
      max-width="max-w-lg"
      @close="selectedAuditLog = null"
    >
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

      <template #footer>
        <div class="flex items-center justify-end">
          <UButton label="Close" color="neutral" variant="ghost" size="sm" @click="selectedAuditLog = null" />
        </div>
      </template>
    </AdminFullScreenModal>
  </div>
</template>
