<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { canManageSupport } = useAdminPermission()

const tickets = ref<any[]>([])
const isLoading = ref(true)
const selectedStatus = ref('')
const selectedPriority = ref('')
const selectedTicket = ref<any | null>(null)
const isDrawerOpen = ref(false)
const isUpdating = ref(false)
const resolutionNotes = ref('')

async function fetchTickets() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    if (selectedStatus.value) params.append('status', selectedStatus.value)
    if (selectedPriority.value) params.append('priority', selectedPriority.value)

    const data = await apiFetch<any[]>(`/admin/tickets?${params.toString()}`)
    tickets.value = data || []
  } catch {
    tickets.value = []
  } finally {
    isLoading.value = false
  }
}

async function viewTicket(t: any) {
  try {
    const detail = await apiFetch<any>(`/admin/tickets/${t.ticket_id}`)
    selectedTicket.value = detail
    resolutionNotes.value = detail.resolution_notes || ''
    isDrawerOpen.value = true
  } catch {
    // ignore
  }
}

async function updateTicketStatus(newStatus: string) {
  if (!selectedTicket.value) return
  isUpdating.value = true
  try {
    const updated = await apiFetch<any>(`/admin/tickets/${selectedTicket.value.ticket_id}`, {
      method: 'PUT',
      body: { status: newStatus, resolution_notes: resolutionNotes.value }
    })
    selectedTicket.value = updated
    await fetchTickets()
  } catch {
    // ignore
  } finally {
    isUpdating.value = false
  }
}

onMounted(() => {
  fetchTickets()
})

watch([selectedStatus, selectedPriority], () => {
  fetchTickets()
})
</script>

<template>
  <div class="overflow-y-auto p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white">Support & Bug Reports</h1>
        <p class="text-xs text-zinc-400 mt-0.5">Diagnose cashier hardware issues, offline sync bugs, and merchant requests</p>
      </div>
      <div class="flex items-center gap-2">
        <select
          v-model="selectedStatus"
          class="bg-zinc-900 border border-zinc-800 text-xs rounded-lg px-3 py-1.5 text-zinc-300 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
        <select
          v-model="selectedPriority"
          class="bg-zinc-900 border border-zinc-800 text-xs rounded-lg px-3 py-1.5 text-zinc-300 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All Priorities</option>
          <option value="urgent">Urgent</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
    </div>

    <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl overflow-hidden backdrop-blur-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px] tracking-wider">
            <tr>
              <th class="px-5 py-3.5">Ticket</th>
              <th class="px-5 py-3.5">Type</th>
              <th class="px-5 py-3.5">Reporter</th>
              <th class="px-5 py-3.5">Priority</th>
              <th class="px-5 py-3.5">Status</th>
              <th class="px-5 py-3.5">Created</th>
              <th class="px-5 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60">
            <tr v-if="isLoading">
              <td colspan="7" class="px-5 py-8 text-center text-zinc-500">Loading tickets...</td>
            </tr>
            <tr v-else-if="tickets.length === 0">
              <td colspan="7" class="px-5 py-8 text-center text-zinc-500">No support tickets found.</td>
            </tr>
            <tr
              v-for="t in tickets"
              v-else
              :key="t.ticket_id"
              class="hover:bg-zinc-800/30 transition-colors"
            >
              <td class="px-5 py-3.5">
                <div class="font-medium text-zinc-100">{{ t.subject }}</div>
                <div class="text-[11px] text-zinc-400 line-clamp-1 mt-0.5">{{ t.description }}</div>
              </td>
              <td class="px-5 py-3.5 uppercase font-mono text-[10px] text-zinc-300">{{ t.type }}</td>
              <td class="px-5 py-3.5 text-zinc-400 capitalize">{{ t.reporter_type }}</td>
              <td class="px-5 py-3.5">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-semibold uppercase border',
                    t.priority === 'urgent' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                    t.priority === 'high' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                    'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                  ]"
                >
                  {{ t.priority }}
                </span>
              </td>
              <td class="px-5 py-3.5">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-semibold uppercase border',
                    t.status === 'open' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                    t.status === 'resolved' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                    'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                  ]"
                >
                  {{ t.status }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-zinc-400">{{ new Date(t.created_at).toLocaleDateString() }}</td>
              <td class="px-5 py-3.5 text-right">
                <UButton
                  label="Inspect"
                  size="xs"
                  color="neutral"
                  variant="outline"
                  icon="i-lucide-wrench"
                  @click="viewTicket(t)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminFullScreenModal
      v-if="selectedTicket"
      v-model="isDrawerOpen"
      :title="selectedTicket.subject"
      :description="'Ticket ID: ' + selectedTicket.ticket_id"
      max-width="max-w-lg"
    >
      <div class="flex flex-col gap-6">
        <div class="p-4 rounded-xl bg-zinc-950 border border-zinc-800 text-xs text-zinc-200 leading-relaxed">
          {{ selectedTicket.description }}
        </div>

        <div v-if="selectedTicket.device_diagnostics" class="flex flex-col gap-2">
          <span class="text-xs font-semibold text-zinc-300">Device & Runtime Diagnostics</span>
          <div class="p-4 rounded-xl bg-zinc-950 border border-zinc-800 font-mono text-[11px] text-emerald-400 overflow-x-auto">
            <pre>{{ JSON.stringify(selectedTicket.device_diagnostics, null, 2) }}</pre>
          </div>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs font-semibold text-zinc-300">Resolution Notes</label>
          <textarea
            v-model="resolutionNotes"
            rows="3"
            class="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500"
            placeholder="Add resolution or troubleshooting steps..."
          />
        </div>
      </div>

      <template #footer>
        <div class="flex gap-2">
          <UButton
            v-if="selectedTicket.status !== 'resolved'"
            label="Mark Resolved"
            icon="i-lucide-check-circle"
            color="primary"
            block
            :disabled="!canManageSupport"
            :loading="isUpdating"
            @click="updateTicketStatus('resolved')"
          />
          <UButton
            v-else
            label="Re-open Ticket"
            icon="i-lucide-rotate-ccw"
            color="neutral"
            variant="outline"
            block
            :disabled="!canManageSupport"
            :loading="isUpdating"
            @click="updateTicketStatus('open')"
          />
        </div>
      </template>
    </AdminFullScreenModal>
  </div>
</template>
