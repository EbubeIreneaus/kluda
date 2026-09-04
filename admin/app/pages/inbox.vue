<script setup lang="ts">
const { apiFetch } = useAdminApi();
const { adminUser } = useAdminAuth();
const { canManageEmails } = useAdminPermission();

const mailboxes = ref<any[]>([]);
const selectedMailbox = ref<any | null>(null);
const selectedFolder = ref<"inbox" | "sent" | "unread" | "archived" | "spam">(
  "inbox",
);
const threads = ref<any[]>([]);
const isLoadingThreads = ref(true);
const search = ref("");

// Thread Detail Modal
const isThreadModalOpen = ref(false);
const selectedThread = ref<any | null>(null);
const isLoadingThreadDetail = ref(false);
const expandedMessageIds = ref<Set<string>>(new Set());
const replyText = ref("");
const isSendingReply = ref(false);

// Compose Outbound Modal
const isComposeOpen = ref(false);
const isComposing = ref(false);
const composeForm = ref({
  mailbox_id: "",
  to_email: "",
  subject: "",
  body: "<p>Hello,</p><p>How can we assist you today?</p>",
});

const folderTabs = [
  { id: "inbox", label: "Inbox", icon: "i-lucide-inbox" },
  { id: "sent", label: "Sent", icon: "i-lucide-send" },
  { id: "unread", label: "Unread", icon: "i-lucide-mail" },
  { id: "archived", label: "Archived", icon: "i-lucide-archive" },
  { id: "spam", label: "Spam", icon: "i-lucide-alert-triangle" },
];

const quickReplySnippets = [
  "Thank you for contacting Kluda Support. We are investigating this and will update you shortly.",
  "This issue has been resolved. Please refresh your dashboard and confirm on your end.",
  "Could you please provide additional details or a screenshot to help us assist you faster?",
  "Thank you for your feedback! We appreciate your patience as we improve our services.",
];

function stripHtml(html?: string): string {
  if (!html) return "";
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

const myPersonalMailbox = computed(() => {
  return mailboxes.value.find(
    (m) =>
      m.type === "personal" &&
      (m.owner_admin_id === adminUser.value?.admin_id ||
        m.email?.toLowerCase() ===
          adminUser.value?.company_email?.toLowerCase()),
  );
});

const sharedMailboxes = computed(() => {
  return mailboxes.value.filter((m) => m.type === "shared");
});

const isPersonalActive = computed(() => {
  return (
    selectedMailbox.value?.mailbox_id === myPersonalMailbox.value?.mailbox_id
  );
});

function selectPersonalInbox() {
  if (myPersonalMailbox.value) {
    selectedMailbox.value = myPersonalMailbox.value;
  }
}

function selectSharedInbox(mb?: any) {
  if (mb) {
    selectedMailbox.value = mb;
  } else if (sharedMailboxes.value.length > 0) {
    selectedMailbox.value = sharedMailboxes.value[0];
  }
}

function openComposeModal() {
  composeForm.value.mailbox_id =
    selectedMailbox.value?.mailbox_id ||
    myPersonalMailbox.value?.mailbox_id ||
    mailboxes.value[0]?.mailbox_id ||
    "";
  isComposeOpen.value = true;
}

async function fetchMailboxes() {
  try {
    const data = await apiFetch<any[]>("/admin/mailboxes");
    mailboxes.value = data || [];
    if (mailboxes.value.length > 0 && !selectedMailbox.value) {
      selectedMailbox.value = myPersonalMailbox.value || mailboxes.value[0];
      composeForm.value.mailbox_id = selectedMailbox.value.mailbox_id;
      await fetchThreads();
    }
  } catch {
    mailboxes.value = [];
  }
}

async function fetchThreads() {
  isLoadingThreads.value = true;
  try {
    const params = new URLSearchParams();
    if (selectedMailbox.value?.mailbox_id) {
      params.append("mailbox_id", selectedMailbox.value.mailbox_id);
    }
    params.append("folder", selectedFolder.value);
    if (search.value) {
      params.append("search", search.value);
    }
    const data = await apiFetch<any[]>(
      `/admin/inbox/threads?${params.toString()}`,
    );
    threads.value = data || [];
  } catch {
    threads.value = [];
  } finally {
    isLoadingThreads.value = false;
  }
}

async function openThread(t: any) {
  selectedThread.value = { ...t, messages: [] };
  isThreadModalOpen.value = true;
  isLoadingThreadDetail.value = true;
  expandedMessageIds.value.clear();
  replyText.value = "";

  try {
    const detail = await apiFetch<any>(`/admin/inbox/threads/${t.thread_id}`);
    selectedThread.value = detail;
    t.status = "read";

    // Expand the latest (last) message by default
    if (detail.messages && detail.messages.length > 0) {
      const lastMsg = detail.messages[detail.messages.length - 1];
      expandedMessageIds.value.add(lastMsg.message_id);
    }
  } catch {
    // Keep preview
  } finally {
    isLoadingThreadDetail.value = false;
  }
}

function toggleMessageExpand(id: string) {
  if (expandedMessageIds.value.has(id)) {
    expandedMessageIds.value.delete(id);
  } else {
    expandedMessageIds.value.add(id);
  }
}

function expandAllMessages() {
  if (!selectedThread.value?.messages) return;
  for (const m of selectedThread.value.messages) {
    expandedMessageIds.value.add(m.message_id);
  }
}

function collapseAllMessages() {
  expandedMessageIds.value.clear();
  if (selectedThread.value?.messages?.length) {
    const last =
      selectedThread.value.messages[selectedThread.value.messages.length - 1];
    expandedMessageIds.value.add(last.message_id);
  }
}

async function handleComposeSend() {
  if (
    !composeForm.value.mailbox_id ||
    !composeForm.value.to_email ||
    !composeForm.value.subject ||
    !composeForm.value.body
  ) {
    alert("Please fill out all email fields");
    return;
  }
  isComposing.value = true;
  try {
    await apiFetch<any>("/admin/inbox/compose", {
      method: "POST",
      body: composeForm.value,
    });
    isComposeOpen.value = false;
    composeForm.value = {
      mailbox_id: selectedMailbox.value?.mailbox_id || "",
      to_email: "",
      subject: "",
      body: "<p>Hello,</p><p>How can we assist you today?</p>",
    };
    await fetchThreads();
  } catch (err: any) {
    alert(err?.data?.detail || "Failed to dispatch email");
  } finally {
    isComposing.value = false;
  }
}

async function handleSendReply() {
  if (!replyText.value.trim() || !selectedThread.value) return;
  isSendingReply.value = true;
  try {
    const newMsg = await apiFetch<any>(
      `/admin/inbox/threads/${selectedThread.value.thread_id}/reply`,
      {
        method: "POST",
        body: { body: replyText.value },
      },
    );
    if (!selectedThread.value.messages) {
      selectedThread.value.messages = [];
    }
    selectedThread.value.messages.push(newMsg);
    expandedMessageIds.value.add(newMsg.message_id);
    replyText.value = "";
    await fetchThreads();
  } catch (err: any) {
    alert(err?.data?.detail || "Failed to send reply");
  } finally {
    isSendingReply.value = false;
  }
}

async function setThreadStatus(st: string) {
  if (!selectedThread.value) return;
  try {
    await apiFetch(
      `/admin/inbox/threads/${selectedThread.value.thread_id}/status?status_val=${st}`,
      {
        method: "PUT",
      },
    );
    selectedThread.value.status = st;
    const target = threads.value.find(
      (x) => x.thread_id === selectedThread.value.thread_id,
    );
    if (target) target.status = st;
    await fetchThreads();
  } catch {
    // ignore
  }
}

async function deleteCurrentThread() {
  if (!selectedThread.value) return;
  if (
    !confirm(
      `Are you sure you want to permanently delete conversation "${selectedThread.value.subject}"?`,
    )
  )
    return;

  try {
    await apiFetch(`/admin/inbox/threads/${selectedThread.value.thread_id}`, {
      method: "DELETE",
    });
    isThreadModalOpen.value = false;
    selectedThread.value = null;
    await fetchThreads();
  } catch (err: any) {
    alert(err?.data?.detail || "Failed to delete thread");
  }
}

function applySnippet(snippet: string) {
  if (!replyText.value) {
    replyText.value = snippet;
  } else {
    replyText.value += `\n\n${snippet}`;
  }
}

onMounted(() => {
  fetchMailboxes();
});

watch([selectedMailbox, selectedFolder], () => {
  fetchThreads();
});

watch(search, () => {
  fetchThreads();
});
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
    <!-- Header & Desk Controls -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <UIcon name="i-lucide-mail" class="size-6 text-emerald-400" />
          Support & Email Desk
        </h1>
        <p class="text-xs text-zinc-400 mt-0.5">
          Omnichannel merchant inbox, shared operational addresses, and direct outbound dispatch
        </p>
      </div>

      <div class="flex items-center gap-2.5">
        <UButton
          label="Compose Outbound Email"
          icon="i-lucide-square-pen"
          size="sm"
          color="primary"
          :disabled="!canManageEmails"
          @click="openComposeModal"
        />
      </div>
    </div>

    <!-- Mailbox Selector & Folder Filter Tabs Bar -->
    <div class="bg-zinc-900/80 border border-zinc-800 p-4 rounded-2xl flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center backdrop-blur-sm shadow-sm">
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <!-- Personal vs Shared Toggle -->
        <div class="grid grid-cols-2 gap-1 bg-zinc-950 p-1 rounded-xl border border-zinc-800 shrink-0">
          <button
            type="button"
            :class="[
              'px-3 py-1.5 text-xs rounded-lg font-medium flex items-center justify-center gap-1.5 transition-all cursor-pointer',
              isPersonalActive
                ? 'bg-zinc-800 text-emerald-400 font-bold shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200',
            ]"
            @click="selectPersonalInbox"
          >
            <UIcon name="i-lucide-user" class="size-3.5" />
            <span>My Inbox</span>
          </button>
          <button
            type="button"
            :class="[
              'px-3 py-1.5 text-xs rounded-lg font-medium flex items-center justify-center gap-1.5 transition-all cursor-pointer',
              !isPersonalActive && selectedMailbox?.type === 'shared'
                ? 'bg-zinc-800 text-emerald-400 font-bold shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200',
            ]"
            @click="selectSharedInbox()"
          >
            <UIcon name="i-lucide-users" class="size-3.5" />
            <span>Shared</span>
          </button>
        </div>

        <!-- Mailbox Dropdown Select -->
        <select
          v-model="selectedMailbox"
          class="bg-zinc-950 border border-zinc-800 text-xs rounded-xl px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500 font-medium"
        >
          <optgroup v-if="myPersonalMailbox" label="My Personal Mailbox">
            <option :value="myPersonalMailbox">
              👤 {{ myPersonalMailbox.name }} ({{ myPersonalMailbox.email }})
            </option>
          </optgroup>
          <optgroup v-if="sharedMailboxes.length > 0" label="Shared Mailboxes">
            <option
              v-for="mb in sharedMailboxes"
              :key="mb.mailbox_id"
              :value="mb"
            >
              🏢 {{ mb.name }} ({{ mb.email }})
            </option>
          </optgroup>
        </select>
      </div>

      <!-- Folder Tabs -->
      <div class="flex items-center gap-1 bg-zinc-950 p-1 rounded-xl border border-zinc-800 overflow-x-auto">
        <button
          v-for="f in folderTabs"
          :key="f.id"
          :class="[
            'px-3 py-1.5 text-xs rounded-lg font-medium flex items-center gap-1.5 transition-colors shrink-0 cursor-pointer',
            selectedFolder === f.id
              ? 'bg-zinc-800 text-emerald-400 font-bold shadow-xs'
              : 'text-zinc-400 hover:text-zinc-200',
          ]"
          @click="selectedFolder = f.id as any"
        >
          <UIcon :name="f.icon" class="size-3.5" />
          <span>{{ f.label }}</span>
        </button>
      </div>
    </div>

    <!-- Search & Counter Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="text-xs text-zinc-400 flex items-center gap-2">
        <span class="font-medium text-zinc-200 uppercase tracking-wider text-[11px]">
          Viewing {{ selectedFolder }}
        </span>
        <span>•</span>
        <span>{{ threads.length }} conversation{{ threads.length === 1 ? '' : 's' }}</span>
      </div>

      <div class="w-full sm:w-80">
        <UInput
          v-model="search"
          placeholder="Search by sender, customer, or subject..."
          icon="i-lucide-search"
          size="sm"
        />
      </div>
    </div>

    <!-- Conversations Table / Card List -->
    <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl overflow-hidden backdrop-blur-sm shadow-sm">
      <div v-if="isLoadingThreads" class="p-12 text-center text-xs text-zinc-500 flex flex-col items-center gap-2">
        <UIcon name="i-lucide-loader-2" class="size-5 animate-spin text-emerald-400" />
        Loading email conversations...
      </div>

      <div v-else-if="threads.length === 0" class="p-12 text-center text-xs text-zinc-500 flex flex-col items-center gap-2">
        <div class="p-3 rounded-full bg-zinc-800/50 border border-zinc-700/50 text-zinc-400">
          <UIcon name="i-lucide-inbox" class="size-6" />
        </div>
        <p class="font-medium text-zinc-300">No conversations in {{ selectedFolder }}</p>
        <p class="text-[11px] text-zinc-500">Emails dispatched or received for this mailbox will appear here.</p>
      </div>

      <div v-else class="divide-y divide-zinc-800/60">
        <div
          v-for="t in threads"
          :key="t.thread_id"
          class="p-4.5 hover:bg-zinc-800/40 transition-colors flex items-start gap-4 cursor-pointer group"
          @click="openThread(t)"
        >
          <!-- Unread Dot & Avatar -->
          <div class="flex items-center gap-3 shrink-0 pt-0.5">
            <div
              :class="[
                'size-2 rounded-full transition-colors',
                t.status === 'unread' ? 'bg-emerald-400 ring-4 ring-emerald-400/20' : 'bg-transparent'
              ]"
            />
            <div class="size-9 rounded-xl bg-zinc-800 border border-zinc-700/80 flex items-center justify-center font-bold text-xs text-zinc-200">
              {{ (t.customer_email || 'U')[0].toUpperCase() }}
            </div>
          </div>

          <!-- Main Content -->
          <div class="flex-1 min-w-0 flex flex-col gap-1">
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-2 min-w-0">
                <span :class="['text-xs truncate', t.status === 'unread' ? 'font-bold text-white' : 'font-medium text-zinc-300']">
                  {{ t.customer_email }}
                </span>
                <span
                  v-if="t.status === 'unread'"
                  class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider"
                >
                  New
                </span>
                <span
                  v-else-if="t.status === 'archived'"
                  class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-zinc-800 text-zinc-400"
                >
                  Archived
                </span>
                <span
                  v-else-if="t.status === 'spam'"
                  class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-rose-950/40 border border-rose-500/30 text-rose-400"
                >
                  Spam
                </span>
              </div>

              <div class="text-[11px] text-zinc-500 font-mono shrink-0">
                {{ new Date(t.last_message_at || t.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }}
              </div>
            </div>

            <div :class="['text-xs truncate', t.status === 'unread' ? 'font-bold text-zinc-100' : 'font-medium text-zinc-300']">
              {{ t.subject }}
            </div>

            <!-- Clean Snippet (Never displays HTML tags) -->
            <div class="text-[11px] text-zinc-400 line-clamp-1 leading-relaxed">
              {{ stripHtml(t.snippet) || 'No message preview' }}
            </div>
          </div>

          <!-- Chevron -->
          <div class="shrink-0 self-center text-zinc-600 group-hover:text-zinc-300 transition-colors pl-2">
            <UIcon name="i-lucide-chevron-right" class="size-4" />
          </div>
        </div>
      </div>
    </div>

    <!-- Gmail-Style Thread Inspection Full-Screen Modal -->
    <AdminFullScreenModal
      v-if="selectedThread"
      v-model="isThreadModalOpen"
      :title="selectedThread.subject"
      :description="`Customer: ${selectedThread.customer_email} • Mailbox: ${selectedThread.to || selectedMailbox?.email}`"
      max-width="max-w-4xl"
    >
      <!-- Thread Action Toolbar in Modal -->
      <div class="flex flex-wrap items-center justify-between gap-3 p-3 bg-zinc-950 rounded-xl border border-zinc-800">
        <div class="flex items-center gap-2 text-xs">
          <span
            :class="[
              'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border',
              selectedThread.status === 'unread'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : selectedThread.status === 'archived'
                ? 'bg-zinc-800 text-zinc-400 border-zinc-700'
                : selectedThread.status === 'spam'
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
            ]"
          >
            {{ selectedThread.status }}
          </span>

          <span class="text-zinc-400 text-[11px]">
            {{ selectedThread.messages?.length || 1 }} message{{ (selectedThread.messages?.length || 1) === 1 ? '' : 's' }}
          </span>
        </div>

        <div class="flex items-center gap-1.5">
          <UButton
            v-if="selectedThread.messages?.length > 1"
            label="Expand All"
            icon="i-lucide-chevrons-up-down"
            color="neutral"
            variant="ghost"
            size="xs"
            @click="expandAllMessages"
          />
          <UButton
            v-if="selectedThread.status !== 'unread'"
            label="Mark Unread"
            icon="i-lucide-mail"
            color="neutral"
            variant="ghost"
            size="xs"
            @click="setThreadStatus('unread')"
          />
          <UButton
            v-if="selectedThread.status !== 'archived'"
            label="Archive"
            icon="i-lucide-archive"
            color="neutral"
            variant="ghost"
            size="xs"
            @click="setThreadStatus('archived')"
          />
          <UButton
            v-if="selectedThread.status !== 'spam'"
            label="Spam"
            icon="i-lucide-alert-triangle"
            color="neutral"
            variant="ghost"
            size="xs"
            @click="setThreadStatus('spam')"
          />
          <UButton
            label="Delete"
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            size="xs"
            @click="deleteCurrentThread"
          />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoadingThreadDetail" class="py-12 text-center text-xs text-zinc-400 flex flex-col items-center gap-2">
        <UIcon name="i-lucide-loader-2" class="size-6 animate-spin text-emerald-400" />
        Fetching conversation history...
      </div>

      <!-- Message History Stack (Oldest to Newest, Gmail-style) -->
      <div v-else class="flex flex-col gap-4">
        <div
          v-for="(msg, idx) in selectedThread.messages || []"
          :key="msg.message_id"
          class="border rounded-2xl overflow-hidden transition-all shadow-sm"
          :class="[
            expandedMessageIds.has(msg.message_id)
              ? 'bg-zinc-950/80 border-zinc-800'
              : 'bg-zinc-950/40 border-zinc-850 hover:border-zinc-700 hover:bg-zinc-950/60 cursor-pointer'
          ]"
          @click="!expandedMessageIds.has(msg.message_id) && toggleMessageExpand(msg.message_id)"
        >
          <!-- Message Header Bar -->
          <div
            class="p-4 flex items-center justify-between gap-3 border-b"
            :class="expandedMessageIds.has(msg.message_id) ? 'border-zinc-800/80 bg-zinc-900/50' : 'border-transparent'"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div
                class="size-8 rounded-xl flex items-center justify-center font-bold text-xs shrink-0"
                :class="msg.direction === 'outgoing' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'"
              >
                {{ (msg.sender || 'U')[0].toUpperCase() }}
              </div>

              <div class="min-w-0 flex flex-col">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-zinc-100 truncate">{{ msg.sender }}</span>
                  <span
                    :class="[
                      'px-1.5 py-0.2 rounded text-[9px] font-bold uppercase tracking-wider',
                      msg.direction === 'outgoing'
                        ? 'bg-emerald-500/15 text-emerald-300'
                        : 'bg-blue-500/15 text-blue-300'
                    ]"
                  >
                    {{ msg.direction === 'outgoing' ? 'Sent' : 'Received' }}
                  </span>
                </div>
                <span class="text-[11px] text-zinc-400 truncate">to {{ msg.recipients }}</span>
              </div>
            </div>

            <div class="flex items-center gap-2 shrink-0">
              <span class="text-[11px] text-zinc-400 font-mono">
                {{ new Date(msg.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) }}
              </span>

              <button
                type="button"
                class="p-1 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
                :title="expandedMessageIds.has(msg.message_id) ? 'Collapse' : 'Expand'"
                @click.stop="toggleMessageExpand(msg.message_id)"
              >
                <UIcon
                  :name="expandedMessageIds.has(msg.message_id) ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
                  class="size-4"
                />
              </button>
            </div>
          </div>

          <!-- Collapsed Preview (2-3 line clamped summary, Gmail style) -->
          <div
            v-if="!expandedMessageIds.has(msg.message_id)"
            class="px-4 py-3 text-xs text-zinc-400 line-clamp-2 leading-relaxed border-t border-zinc-850/50"
          >
            {{ stripHtml(msg.body) }}
          </div>

          <!-- Fully Expanded Message Body -->
          <div
            v-else
            class="p-5 bg-white text-zinc-900 rounded-b-2xl overflow-x-auto text-xs leading-relaxed"
          >
            <div
              class="prose prose-sm max-w-none text-zinc-900"
              v-html="msg.body"
            />
          </div>
        </div>
      </div>

      <!-- Quick Reply Box Inside Modal -->
      <div class="mt-6 p-4 rounded-2xl bg-zinc-950 border border-zinc-800 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <label class="text-xs font-bold text-zinc-200 flex items-center gap-1.5">
            <UIcon name="i-lucide-reply" class="size-4 text-emerald-400" />
            Quick Reply to Customer
          </label>
          <span class="text-[11px] text-zinc-400 font-mono">
            Replying from: {{ selectedThread.to || selectedMailbox?.email }}
          </span>
        </div>

        <!-- Canned Responses Quick Pills -->
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="(snippet, sIdx) in quickReplySnippets"
            :key="sIdx"
            type="button"
            class="px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-zinc-200 text-zinc-400 text-[11px] transition text-left cursor-pointer truncate max-w-xs"
            @click="applySnippet(snippet)"
          >
            {{ snippet }}
          </button>
        </div>

        <textarea
          v-model="replyText"
          rows="3"
          placeholder="Type reply message... (will be formatted into branded email automatically)"
          class="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
        />

        <div class="flex justify-end gap-2">
          <UButton
            label="Send Reply"
            icon="i-lucide-send"
            color="primary"
            size="sm"
            :disabled="!canManageEmails || !replyText.trim()"
            :loading="isSendingReply"
            @click="handleSendReply"
          />
        </div>
      </div>
    </AdminFullScreenModal>

    <!-- Compose Outbound Email Modal -->
    <AdminFullScreenModal
      v-model="isComposeOpen"
      title="Compose Outbound Email"
      description="Dispatch direct email communication with branded HTML formatting"
      max-width="max-w-3xl"
    >
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">From Sender Mailbox</label>
            <select
              v-model="composeForm.mailbox_id"
              class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <optgroup v-if="myPersonalMailbox" label="My Personal Mailbox">
                <option :value="myPersonalMailbox.mailbox_id">
                  {{ myPersonalMailbox.name }} ({{ myPersonalMailbox.email }})
                </option>
              </optgroup>
              <optgroup v-if="sharedMailboxes.length > 0" label="Public / Shared Mailboxes">
                <option
                  v-for="mb in sharedMailboxes"
                  :key="mb.mailbox_id"
                  :value="mb.mailbox_id"
                >
                  {{ mb.name }} ({{ mb.email }})
                </option>
              </optgroup>
              <optgroup
                v-if="!myPersonalMailbox && sharedMailboxes.length === 0 && mailboxes.length > 0"
                label="Available Mailboxes"
              >
                <option
                  v-for="mb in mailboxes"
                  :key="mb.mailbox_id"
                  :value="mb.mailbox_id"
                >
                  {{ mb.name }} ({{ mb.email }})
                </option>
              </optgroup>
            </select>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">To Recipient Email</label>
            <UInput
              v-model="composeForm.to_email"
              placeholder="client@example.com or user@kluda.app"
              size="sm"
            />
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Subject</label>
          <UInput
            v-model="composeForm.subject"
            placeholder="Assistance regarding your retail store..."
            size="sm"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Visual Message Body</label>
          <TiptapEditor v-model="composeForm.body" />
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <UButton
            label="Cancel"
            color="neutral"
            variant="ghost"
            size="sm"
            @click="isComposeOpen = false"
          />
          <UButton
            label="Send Message"
            icon="i-lucide-send"
            color="primary"
            size="sm"
            :disabled="!canManageEmails"
            :loading="isComposing"
            @click="handleComposeSend"
          />
        </div>
      </template>
    </AdminFullScreenModal>
  </div>
</template>
