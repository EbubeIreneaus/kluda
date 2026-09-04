<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { canManageAdmins, canManageEmails } = useAdminPermission()
const canBroadcast = computed(() => canManageAdmins.value || canManageEmails.value)

const notifications = ref<any[]>([])
const stores = ref<any[]>([])
const isLoading = ref(true)
const isBroadcastOpen = ref(false)
const isSending = ref(false)

const broadcastForm = ref({
  title: '',
  message: '',
  scope: 'global',
  target_id: '',
  action_url: ''
})

async function fetchData() {
  isLoading.value = true
  try {
    const [notifData, storeData] = await Promise.all([
      apiFetch<any[]>('/admin/notifications'),
      apiFetch<any[]>('/admin/stores')
    ])
    notifications.value = notifData || []
    stores.value = storeData || []
  } catch {
    notifications.value = []
    stores.value = []
  } finally {
    isLoading.value = false
  }
}

async function handleSendBroadcast() {
  if (!broadcastForm.value.title || !broadcastForm.value.message) {
    alert('Please enter a title and message')
    return
  }

  isSending.value = true
  try {
    await apiFetch('/admin/notifications/broadcast', {
      method: 'POST',
      body: {
        title: broadcastForm.value.title,
        message: broadcastForm.value.message,
        scope: broadcastForm.value.scope,
        target_id: broadcastForm.value.target_id || null,
        action_url: broadcastForm.value.action_url || null
      }
    })
    isBroadcastOpen.value = false
    broadcastForm.value = {
      title: '',
      message: '',
      scope: 'global',
      target_id: '',
      action_url: ''
    }
    await fetchData()
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to dispatch broadcast')
  } finally {
    isSending.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white">Push & In-App Notifications</h1>
        <p class="text-xs text-zinc-400 mt-0.5">Broadcast push notifications and announcements directly to cashier devices and store owners</p>
      </div>
      <UButton
        label="Send Broadcast"
        icon="i-lucide-send"
        color="primary"
        size="sm"
        :disabled="!canBroadcast"
        @click="isBroadcastOpen = true"
      />
    </div>

    <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl overflow-hidden backdrop-blur-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px] tracking-wider">
            <tr>
              <th class="px-5 py-3.5">Title & Message</th>
              <th class="px-5 py-3.5">Scope Target</th>
              <th class="px-5 py-3.5">Action URL</th>
              <th class="px-5 py-3.5">Dispatched At</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60">
            <tr v-if="isLoading">
              <td colspan="4" class="px-5 py-8 text-center text-zinc-500">Loading notifications...</td>
            </tr>
            <tr v-else-if="notifications.length === 0">
              <td colspan="4" class="px-5 py-8 text-center text-zinc-500">No broadcasts recorded yet.</td>
            </tr>
            <tr
              v-for="n in notifications"
              :key="n.id"
              class="hover:bg-zinc-800/30 transition-colors"
            >
              <td class="px-5 py-3.5">
                <div class="font-semibold text-zinc-100">{{ n.title }}</div>
                <div class="text-[11px] text-zinc-400 mt-0.5 line-clamp-1">{{ n.message }}</div>
              </td>
              <td class="px-5 py-3.5">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-semibold uppercase border',
                    n.scope === 'global' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                    n.scope === 'store' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  ]"
                >
                  {{ n.scope }}
                </span>
              </td>
              <td class="px-5 py-3.5 font-mono text-[11px] text-zinc-400">{{ n.data?.action_url || 'None' }}</td>
              <td class="px-5 py-3.5 text-zinc-400 font-mono text-[11px] whitespace-nowrap">{{ n.created_at ? new Date(n.created_at).toLocaleString() : 'N/A' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminBottomSheet
      v-model="isBroadcastOpen"
      title="Broadcast Push Notification"
      description="Send instant announcements and alerts to merchants or staff"
      max-width="max-w-lg"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Notification Title</label>
          <UInput v-model="broadcastForm.title" placeholder="System Maintenance Notice" size="sm" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Message Content</label>
          <textarea
            v-model="broadcastForm.message"
            rows="3"
            class="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500"
            placeholder="Important update details..."
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Target Scope</label>
          <select
            v-model="broadcastForm.scope"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="global">All Platform Users & Cashiers</option>
            <option value="store">Specific Retail Store</option>
            <option value="personal">Specific Individual Staff Member</option>
          </select>
        </div>

        <div v-if="broadcastForm.scope === 'store'" class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Select Store</label>
          <select
            v-model="broadcastForm.target_id"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="" disabled>Choose a store...</option>
            <option v-for="s in stores" :key="s.store_id" :value="s.store_id">
              {{ s.name }} ({{ s.owner_email || 'N/A' }})
            </option>
          </select>
        </div>

        <div v-else-if="broadcastForm.scope === 'personal'" class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Target User / Staff UUID</label>
          <UInput v-model="broadcastForm.target_id" placeholder="00000000-0000-0000-0000-000000000000" size="sm" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Action Deep-Link URL (Optional)</label>
          <UInput v-model="broadcastForm.action_url" placeholder="/inventory or https://..." size="sm" />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isBroadcastOpen = false" />
          <UButton
            label="Dispatch Broadcast"
            icon="i-lucide-send"
            color="primary"
            size="sm"
            :disabled="!canBroadcast"
            :loading="isSending"
            @click="handleSendBroadcast"
          />
        </div>
      </template>
    </AdminBottomSheet>
  </div>
</template>
