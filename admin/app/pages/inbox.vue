<script setup lang="ts">
const { apiFetch } = useAdminApi();
const { adminUser } = useAdminAuth();
const { canManageEmails } = useAdminPermission();

const mailboxes = ref<any[]>([]);
const selectedMailbox = ref<any | null>(null);
const selectedFolder = ref<"inbox" | "sent" | "unread" | "archived" | "spam">("inbox");
const threads = ref<any[]>([]);
const isLoadingThreads = ref(true);
const search = ref("");

// Thread Detail
const selectedThread = ref<any | null>(null);
const isLoadingThreadDetail = ref(false);
const expandedMessageIds = ref<Set<string>>(new Set());
const replyText = ref("");
const isSendingReply = ref(false);
const showReplyBox = ref(false);

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

function formatDate(dateStr: string) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  if (isToday) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

function formatDateFull(dateStr: string) {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function getInitial(str?: string) {
  return (str || "?").charAt(0).toUpperCase();
}

const myPersonalMailbox = computed(() => {
  return mailboxes.value.find(
    (m) =>
      m.type === "personal" &&
      (m.owner_admin_id === adminUser.value?.admin_id ||
        m.email?.toLowerCase() === adminUser.value?.company_email?.toLowerCase()),
  );
});

const sharedMailboxes = computed(() => {
  return mailboxes.value.filter((m) => m.type === "shared");
});

const isPersonalActive = computed(() => {
  return selectedMailbox.value?.mailbox_id === myPersonalMailbox.value?.mailbox_id;
});

function selectPersonalInbox() {
  if (myPersonalMailbox.value) selectedMailbox.value = myPersonalMailbox.value;
}

function selectSharedInbox(mb?: any) {
  if (mb) selectedMailbox.value = mb;
  else if (sharedMailboxes.value.length > 0) selectedMailbox.value = sharedMailboxes.value[0];
}

function openComposeModal() {
  composeForm.value.mailbox_id =
    selectedMailbox.value?.mailbox_id ||
    myPersonalMailbox.value?.mailbox_id ||
    mailboxes.value[0]?.mailbox_id || "";
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
    if (selectedMailbox.value?.mailbox_id) params.append("mailbox_id", selectedMailbox.value.mailbox_id);
    params.append("folder", selectedFolder.value);
    if (search.value) params.append("search", search.value);
    const data = await apiFetch<any[]>(`/admin/inbox/threads?${params.toString()}`);
    threads.value = data || [];
  } catch {
    threads.value = [];
  } finally {
    isLoadingThreads.value = false;
  }
}

async function openThread(t: any) {
  selectedThread.value = { ...t, messages: [] };
  isLoadingThreadDetail.value = true;
  expandedMessageIds.value.clear();
  replyText.value = "";
  showReplyBox.value = false;

  try {
    const detail = await apiFetch<any>(`/admin/inbox/threads/${t.thread_id}`);
    selectedThread.value = detail;
    t.status = "read";
    if (detail.messages && detail.messages.length > 0) {
      const lastMsg = detail.messages[detail.messages.length - 1];
      expandedMessageIds.value.add(lastMsg.message_id);
    }
  } catch {
    // keep preview
  } finally {
    isLoadingThreadDetail.value = false;
  }
}

function toggleMessageExpand(id: string) {
  if (expandedMessageIds.value.has(id)) expandedMessageIds.value.delete(id);
  else expandedMessageIds.value.add(id);
}

function expandAllMessages() {
  if (!selectedThread.value?.messages) return;
  for (const m of selectedThread.value.messages) expandedMessageIds.value.add(m.message_id);
}

function collapseAllMessages() {
  expandedMessageIds.value.clear();
  if (selectedThread.value?.messages?.length) {
    const last = selectedThread.value.messages[selectedThread.value.messages.length - 1];
    expandedMessageIds.value.add(last.message_id);
  }
}

async function handleComposeSend() {
  if (!composeForm.value.mailbox_id || !composeForm.value.to_email || !composeForm.value.subject || !composeForm.value.body) {
    alert("Please fill out all email fields");
    return;
  }
  isComposing.value = true;
  try {
    await apiFetch<any>("/admin/inbox/compose", { method: "POST", body: composeForm.value });
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
      { method: "POST", body: { body: replyText.value } },
    );
    if (!selectedThread.value.messages) selectedThread.value.messages = [];
    selectedThread.value.messages.push(newMsg);
    expandedMessageIds.value.add(newMsg.message_id);
    replyText.value = "";
    showReplyBox.value = false;
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
    await apiFetch(`/admin/inbox/threads/${selectedThread.value.thread_id}/status?status_val=${st}`, { method: "PUT" });
    selectedThread.value.status = st;
    const target = threads.value.find((x) => x.thread_id === selectedThread.value.thread_id);
    if (target) target.status = st;
    await fetchThreads();
  } catch {
    // ignore
  }
}

async function deleteCurrentThread() {
  if (!selectedThread.value) return;
  if (!confirm(`Are you sure you want to permanently delete conversation "${selectedThread.value.subject}"?`)) return;
  try {
    await apiFetch(`/admin/inbox/threads/${selectedThread.value.thread_id}`, { method: "DELETE" });
    selectedThread.value = null;
    await fetchThreads();
  } catch (err: any) {
    alert(err?.data?.detail || "Failed to delete thread");
  }
}

function applySnippet(snippet: string) {
  if (!replyText.value) replyText.value = snippet;
  else replyText.value += `\n\n${snippet}`;
}

onMounted(() => { fetchMailboxes(); });
watch([selectedMailbox, selectedFolder], () => { fetchThreads(); });
watch(search, () => { fetchThreads(); });
</script>

<template>
  <div class="flex flex-col flex-1 overflow-hidden min-h-0">
    <!-- Top Toolbar Bar -->
    <div class="shrink-0 px-5 py-3 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-sm flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
      <div class="flex items-center gap-3">
        <div class="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <UIcon name="i-lucide-mail" class="size-4 text-emerald-400" />
        </div>
        <div>
          <h1 class="text-sm font-bold text-white tracking-tight">Support &amp; Email Desk</h1>
          <p class="text-[11px] text-zinc-500 leading-none mt-0.5">Omnichannel merchant inbox</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <select
          v-model="selectedMailbox"
          class="bg-zinc-900 border border-zinc-800 text-xs rounded-lg px-3 py-1.5 text-zinc-200 focus:outline-none focus:border-emerald-500 font-medium"
        >
          <optgroup v-if="myPersonalMailbox" label="My Personal Mailbox">
            <option :value="myPersonalMailbox">{{ "👤" }} {{ myPersonalMailbox.name }} ({{ myPersonalMailbox.email }})</option>
          </optgroup>
          <optgroup v-if="sharedMailboxes.length > 0" label="Shared Mailboxes">
            <option v-for="mb in sharedMailboxes" :key="mb.mailbox_id" :value="mb">
              {{ "🏢" }} {{ mb.name }} ({{ mb.email }})
            </option>
          </optgroup>
        </select>

        <UButton
          label="Compose"
          icon="i-lucide-square-pen"
          size="sm"
          color="primary"
          :disabled="!canManageEmails"
          @click="openComposeModal"
        />
      </div>
    </div>

    <!-- Main Two-Pane Layout -->
    <div class="flex flex-1 overflow-hidden">

      <!-- LEFT: Thread List Pane -->
      <div
        class="flex flex-col border-r border-zinc-800/80 bg-zinc-950 shrink-0 overflow-hidden"
        :class="selectedThread ? 'w-80 xl:w-96 hidden md:flex' : 'flex-1'"
      >
        <!-- Folder Tabs + Search -->
        <div class="px-3 pt-3 pb-2 border-b border-zinc-800/60 shrink-0 flex flex-col gap-2">
          <div class="flex items-center gap-0.5 overflow-x-auto">
            <button
              v-for="f in folderTabs"
              :key="f.id"
              :class="[
                'px-3 py-1.5 text-xs rounded-lg font-medium flex items-center gap-1.5 transition-colors shrink-0 cursor-pointer whitespace-nowrap',
                selectedFolder === f.id
                  ? 'bg-zinc-800 text-emerald-400 font-bold'
                  : 'text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/50',
              ]"
              @click="selectedFolder = f.id as any"
            >
              <UIcon :name="f.icon" class="size-3.5" />
              <span>{{ f.label }}</span>
            </button>
          </div>
          <UInput
            v-model="search"
            placeholder="Search conversations..."
            icon="i-lucide-search"
            size="sm"
          />
        </div>

        <!-- Thread Count -->
        <div class="px-4 py-2 text-[11px] text-zinc-500 font-medium uppercase tracking-wider border-b border-zinc-800/40 shrink-0">
          {{ threads.length }} conversation{{ threads.length === 1 ? "" : "s" }}
        </div>

        <!-- Thread List -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="isLoadingThreads" class="py-16 flex flex-col items-center gap-3 text-zinc-500 text-xs">
            <UIcon name="i-lucide-loader-2" class="size-5 animate-spin text-emerald-400" />
            Loading...
          </div>

          <div v-else-if="threads.length === 0" class="py-16 flex flex-col items-center gap-3 text-zinc-500 text-xs text-center px-6">
            <div class="p-3 rounded-full bg-zinc-800/50 border border-zinc-700/50">
              <UIcon name="i-lucide-inbox" class="size-6 text-zinc-400" />
            </div>
            <p class="font-medium text-zinc-400">No conversations in {{ selectedFolder }}</p>
            <p class="text-[11px] text-zinc-600">Emails will appear here when received.</p>
          </div>

          <div v-else>
            <button
              v-for="t in threads"
              :key="t.thread_id"
              type="button"
              class="w-full text-left px-4 py-3.5 border-b border-zinc-800/50 hover:bg-zinc-900/60 transition-colors cursor-pointer flex items-start gap-3 relative border-l-2"
              :class="selectedThread?.thread_id === t.thread_id ? 'bg-zinc-900 border-l-emerald-500' : 'border-l-transparent'"
              @click="openThread(t)"
            >
              <div class="mt-1.5 shrink-0">
                <div :class="['size-2 rounded-full', t.status === 'unread' ? 'bg-emerald-400' : 'bg-transparent']" />
              </div>

              <div
                class="size-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 border"
                :class="t.status === 'unread' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-zinc-800 text-zinc-300 border-zinc-700'"
              >
                {{ getInitial(t.customer_email) }}
              </div>

              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-1 mb-0.5">
                  <span :class="['text-xs truncate', t.status === 'unread' ? 'font-bold text-white' : 'font-medium text-zinc-300']">
                    {{ t.customer_email }}
                  </span>
                  <span class="text-[10px] text-zinc-500 shrink-0 font-mono">{{ formatDate(t.last_message_at || t.created_at) }}</span>
                </div>
                <div :class="['text-[11px] truncate mb-0.5', t.status === 'unread' ? 'font-semibold text-zinc-100' : 'text-zinc-400']">
                  {{ t.subject }}
                </div>
                <div class="text-[10px] text-zinc-600 line-clamp-1">{{ stripHtml(t.snippet) || "No preview" }}</div>
                <div class="mt-1 flex items-center gap-1">
                  <span v-if="t.status === 'spam'" class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-950/40 border border-rose-500/30 text-rose-400">Spam</span>
                  <span v-else-if="t.status === 'archived'" class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-zinc-800 text-zinc-400">Archived</span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- RIGHT: Thread Reader Pane -->
      <div v-if="selectedThread" class="flex-1 flex flex-col overflow-hidden bg-zinc-950/50">
        <!-- Reader Toolbar -->
        <div class="shrink-0 px-5 py-3 border-b border-zinc-800/80 bg-zinc-950/90 backdrop-blur-sm flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="md:hidden p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
              @click="selectedThread = null"
            >
              <UIcon name="i-lucide-arrow-left" class="size-4" />
            </button>
            <span
              :class="[
                'px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border',
                selectedThread.status === 'unread' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : selectedThread.status === 'archived' ? 'bg-zinc-800 text-zinc-400 border-zinc-700'
                : selectedThread.status === 'spam' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
              ]"
            >{{ selectedThread.status }}</span>
            <span class="text-xs text-zinc-500">
              {{ selectedThread.messages?.length || 0 }} message{{ (selectedThread.messages?.length || 0) === 1 ? "" : "s" }}
            </span>
          </div>

          <div class="flex items-center gap-1">
            <UButton v-if="selectedThread.messages?.length > 1" icon="i-lucide-chevrons-up-down" color="neutral" variant="ghost" size="xs" title="Expand All" @click="expandAllMessages" />
            <UButton v-if="selectedThread.status !== 'unread'" icon="i-lucide-mail" color="neutral" variant="ghost" size="xs" title="Mark Unread" @click="setThreadStatus('unread')" />
            <UButton v-if="selectedThread.status !== 'archived'" icon="i-lucide-archive" color="neutral" variant="ghost" size="xs" title="Archive" @click="setThreadStatus('archived')" />
            <UButton v-if="selectedThread.status !== 'spam'" icon="i-lucide-alert-triangle" color="neutral" variant="ghost" size="xs" title="Mark as Spam" @click="setThreadStatus('spam')" />
            <UButton icon="i-lucide-trash-2" color="error" variant="ghost" size="xs" title="Delete" @click="deleteCurrentThread" />
          </div>
        </div>

        <!-- Scrollable Message Area -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="isLoadingThreadDetail" class="py-20 flex flex-col items-center gap-3 text-zinc-500 text-xs">
            <UIcon name="i-lucide-loader-2" class="size-6 animate-spin text-emerald-400" />
            Fetching conversation...
          </div>

          <div v-else class="max-w-3xl mx-auto px-5 py-6 flex flex-col gap-2">
            <!-- Thread Subject Header -->
            <div class="mb-5">
              <h2 class="text-xl font-bold text-white leading-snug">{{ selectedThread.subject }}</h2>
              <div class="flex items-center gap-2 mt-1.5 flex-wrap">
                <span class="text-[11px] text-zinc-500">{{ selectedThread.messages?.length || 0 }} messages</span>
                <span class="text-zinc-700">·</span>
                <span class="text-[11px] text-zinc-500">Customer: <span class="text-zinc-300">{{ selectedThread.customer_email }}</span></span>
              </div>
            </div>

            <!-- Message Cards -->
            <div
              v-for="(msg) in selectedThread.messages || []"
              :key="msg.message_id"
              class="rounded-2xl border overflow-hidden transition-all"
              :class="[
                expandedMessageIds.has(msg.message_id) ? 'border-zinc-700 shadow-lg' : 'border-zinc-800/60 hover:border-zinc-700 cursor-pointer',
                msg.direction === 'outgoing' ? 'bg-zinc-900/80' : 'bg-zinc-900/50'
              ]"
            >
              <!-- Message Header -->
              <div
                class="px-5 py-3.5 flex items-center justify-between gap-3 cursor-pointer select-none"
                :class="expandedMessageIds.has(msg.message_id) ? 'border-b border-zinc-800/60' : ''"
                @click="toggleMessageExpand(msg.message_id)"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <div
                    class="size-9 rounded-full flex items-center justify-center font-bold text-sm shrink-0 border"
                    :class="msg.direction === 'outgoing' ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25' : 'bg-blue-500/15 text-blue-300 border-blue-500/25'"
                  >{{ getInitial(msg.sender) }}</div>

                  <div class="min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="text-sm font-semibold text-zinc-100 truncate">{{ msg.sender }}</span>
                      <span :class="['px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider', msg.direction === 'outgoing' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-blue-500/15 text-blue-300']">
                        {{ msg.direction === "outgoing" ? "Sent" : "Received" }}
                      </span>
                    </div>
                    <div v-if="!expandedMessageIds.has(msg.message_id)" class="text-[11px] text-zinc-500 truncate mt-0.5">
                      {{ stripHtml(msg.body).slice(0, 80) }}{{ stripHtml(msg.body).length > 80 ? "…" : "" }}
                    </div>
                    <div v-else class="text-[11px] text-zinc-500 mt-0.5">to {{ msg.recipients }}</div>
                  </div>
                </div>

                <div class="flex items-center gap-2 shrink-0">
                  <span class="text-[11px] text-zinc-500 font-mono">{{ formatDateFull(msg.created_at) }}</span>
                  <UIcon :name="expandedMessageIds.has(msg.message_id) ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'" class="size-4 text-zinc-500" />
                </div>
              </div>

              <!-- Expanded: full HTML email body on white bg -->
              <div v-if="expandedMessageIds.has(msg.message_id)" class="bg-white rounded-b-2xl overflow-x-auto">
                <div class="p-6 prose prose-sm max-w-none text-zinc-900" v-html="msg.body" />
              </div>
            </div>

            <!-- Reply Trigger / Reply Box -->
            <div class="mt-3">
              <div
                v-if="!showReplyBox"
                class="rounded-2xl border border-zinc-800/60 bg-zinc-900/40 hover:bg-zinc-900 hover:border-zinc-700 transition-all cursor-pointer px-5 py-3.5 flex items-center gap-3"
                @click="showReplyBox = true"
              >
                <div class="size-8 rounded-full flex items-center justify-center font-bold text-xs bg-emerald-500/15 text-emerald-300 border border-emerald-500/25 shrink-0">
                  {{ getInitial(adminUser?.company_email) }}
                </div>
                <span class="text-sm text-zinc-500">Reply to {{ selectedThread.customer_email }}…</span>
              </div>

              <!-- Full Reply Box -->
              <div v-else class="rounded-2xl border border-emerald-500/30 bg-zinc-900 shadow-xl overflow-hidden">
                <div class="px-5 py-3 border-b border-zinc-800/60 flex items-center justify-between">
                  <div class="text-xs text-zinc-400">
                    Reply to <span class="text-zinc-200 font-medium">{{ selectedThread.customer_email }}</span>
                    <span class="text-zinc-600 mx-1">from</span>
                    <span class="text-zinc-200 font-medium">{{ selectedThread.to || selectedMailbox?.email }}</span>
                  </div>
                  <button type="button" class="p-1 rounded text-zinc-500 hover:text-zinc-300 transition cursor-pointer" @click="showReplyBox = false">
                    <UIcon name="i-lucide-x" class="size-4" />
                  </button>
                </div>

                <div class="px-5 pt-3 pb-2 flex flex-wrap gap-1.5">
                  <button
                    v-for="(snippet, sIdx) in quickReplySnippets"
                    :key="sIdx"
                    type="button"
                    class="px-2.5 py-1 rounded-lg bg-zinc-800/80 border border-zinc-700/60 hover:border-zinc-600 hover:text-zinc-200 text-zinc-400 text-[11px] transition cursor-pointer truncate max-w-xs"
                    @click="applySnippet(snippet)"
                  >{{ snippet }}</button>
                </div>

                <div class="px-5 pb-3">
                  <textarea
                    v-model="replyText"
                    rows="4"
                    placeholder="Write your reply… (will be formatted into a branded email)"
                    class="w-full bg-transparent text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none resize-none leading-relaxed"
                  />
                </div>

                <div class="px-5 py-3 border-t border-zinc-800/60 flex items-center justify-between bg-zinc-950/50">
                  <UButton
                    label="Send Reply"
                    icon="i-lucide-send"
                    color="primary"
                    size="sm"
                    :disabled="!canManageEmails || !replyText.trim()"
                    :loading="isSendingReply"
                    @click="handleSendReply"
                  />
                  <button type="button" class="text-xs text-zinc-500 hover:text-zinc-300 transition cursor-pointer" @click="showReplyBox = false; replyText = ''">Discard</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state when no thread selected (desktop) -->
      <div v-else class="flex-1 hidden md:flex flex-col items-center justify-center gap-4 text-center bg-zinc-950/30">
        <div class="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800">
          <UIcon name="i-lucide-mail-open" class="size-10 text-zinc-600" />
        </div>
        <div>
          <p class="text-sm font-medium text-zinc-400">Select a conversation</p>
          <p class="text-xs text-zinc-600 mt-1">Click any thread on the left to read it</p>
        </div>
      </div>
    </div>

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
                <option :value="myPersonalMailbox.mailbox_id">{{ myPersonalMailbox.name }} ({{ myPersonalMailbox.email }})</option>
              </optgroup>
              <optgroup v-if="sharedMailboxes.length > 0" label="Public / Shared Mailboxes">
                <option v-for="mb in sharedMailboxes" :key="mb.mailbox_id" :value="mb.mailbox_id">{{ mb.name }} ({{ mb.email }})</option>
              </optgroup>
              <optgroup v-if="!myPersonalMailbox && sharedMailboxes.length === 0 && mailboxes.length > 0" label="Available Mailboxes">
                <option v-for="mb in mailboxes" :key="mb.mailbox_id" :value="mb.mailbox_id">{{ mb.name }} ({{ mb.email }})</option>
              </optgroup>
            </select>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">To Recipient Email</label>
            <UInput v-model="composeForm.to_email" placeholder="client@example.com" size="sm" />
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Subject</label>
          <UInput v-model="composeForm.subject" placeholder="Assistance regarding your retail store..." size="sm" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Visual Message Body</label>
          <TiptapEditor v-model="composeForm.body" />
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isComposeOpen = false" />
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