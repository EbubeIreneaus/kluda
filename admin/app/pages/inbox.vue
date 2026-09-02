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
const selectedThread = ref<any | null>(null);
const isLoadingThreads = ref(true);
const replyText = ref("");
const isSendingReply = ref(false);
const search = ref("");

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
    if (threads.value.length > 0 && !selectedThread.value) {
      await selectThread(threads.value[0]);
    }
  } catch {
    threads.value = [];
  } finally {
    isLoadingThreads.value = false;
  }
}

async function selectThread(t: any) {
  try {
    const detail = await apiFetch<any>(`/admin/inbox/threads/${t.thread_id}`);
    selectedThread.value = detail;
    t.status = "read";
  } catch {
    selectedThread.value = t;
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
    const newThread = await apiFetch<any>("/admin/inbox/compose", {
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
    if (newThread) {
      selectedThread.value = newThread;
    }
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
    if (selectedThread.value.messages) {
      selectedThread.value.messages.push(newMsg);
    } else {
      selectedThread.value.messages = [newMsg];
    }
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
    await fetchThreads();
  } catch {
    // ignore
  }
}

onMounted(() => {
  fetchMailboxes();
});

watch([selectedMailbox, selectedFolder], () => {
  selectedThread.value = null;
  fetchThreads();
});

watch(search, () => {
  fetchThreads();
});
</script>

<template>
  <div
    class="h-[calc(100vh-65px)] md:h-screen flex flex-col md:flex-row min-w-0 bg-zinc-950 text-zinc-100 overflow-hidden"
  >
    <div
      class="w-full md:w-88 border-r border-zinc-800/80 bg-zinc-900/40 flex flex-col shrink-0 h-full"
    >
      <div class="p-4 border-b border-zinc-800 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-white"
              >Support & Email Desk</span
            >
          </div>
          <UButton
            label="Compose"
            icon="i-lucide-square-pen"
            size="xs"
            color="primary"
            :disabled="!canManageEmails"
            @click="openComposeModal"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <div
            class="flex items-center justify-between text-[11px] font-medium text-zinc-400"
          >
            <span>Mailbox View</span>
            <span
              v-if="selectedMailbox"
              class="text-[10px] text-emerald-400 font-semibold uppercase tracking-wider"
            >
              {{ selectedMailbox.type === "personal" ? "Personal" : "Shared" }}
            </span>
          </div>

          <div
            class="grid grid-cols-2 gap-1 bg-zinc-950 p-1 rounded-lg border border-zinc-800"
          >
            <button
              type="button"
              :class="[
                'px-2 py-1 text-xs rounded-md font-medium flex items-center justify-center gap-1.5 transition-all',
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
                'px-2 py-1 text-xs rounded-md font-medium flex items-center justify-center gap-1.5 transition-all',
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

          <select
            v-model="selectedMailbox"
            class="w-full bg-zinc-950 border border-zinc-800 text-sm rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500 mt-0.5"
          >
            <optgroup v-if="myPersonalMailbox" label="Personal Mailbox">
              <option :value="myPersonalMailbox">
                👤 {{ myPersonalMailbox.name }} ({{ myPersonalMailbox.email }})
              </option>
            </optgroup>
            <optgroup
              v-if="sharedMailboxes.length > 0"
              label="Shared Mailboxes"
            >
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

        <div
          class="flex bg-zinc-950 p-1 rounded-lg border border-zinc-800 gap-0.5 overflow-x-auto"
        >
          <button
            v-for="f in folderTabs"
            :key="f.id"
            :class="[
              'px-2.5 py-1 text-[11px] rounded-md font-medium flex items-center gap-1 transition-colors shrink-0',
              selectedFolder === f.id
                ? 'bg-zinc-800 text-emerald-400 font-bold shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200',
            ]"
            @click="selectedFolder = f.id as any"
          >
            <UIcon :name="f.icon" class="w-3.5 h-3.5" />
            <span>{{ f.label }}</span>
          </button>
        </div>

        <UInput
          v-model="search"
          placeholder="Search by email or subject..."
          icon="i-lucide-search"
          size="xs"
        />
      </div>

      <div class="flex-1 overflow-y-auto divide-y divide-zinc-800/50">
        <div
          v-if="isLoadingThreads"
          class="p-6 text-center text-xs text-zinc-500"
        >
          Loading messages...
        </div>
        <div
          v-else-if="threads.length === 0"
          class="p-6 text-center text-xs text-zinc-500"
        >
          No conversations found in {{ selectedFolder }}.
        </div>
        <div
          v-for="t in threads"
          v-else
          :key="t.thread_id"
          :class="[
            'p-4 cursor-pointer transition-colors flex flex-col gap-1.5',
            selectedThread?.thread_id === t.thread_id
              ? 'bg-zinc-800/60 border-l-2 border-emerald-500'
              : 'hover:bg-zinc-800/30',
          ]"
          @click="selectThread(t)"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-zinc-200 truncate">{{
              t.customer_email
            }}</span>
            <span class="text-[10px] text-zinc-400 shrink-0">{{
              new Date(t.last_message_at).toLocaleDateString()
            }}</span>
          </div>
          <div class="text-xs text-zinc-300 font-medium truncate">
            {{ t.subject }}
          </div>
          <div class="text-[11px] text-zinc-400 line-clamp-2">
            {{ t.snippet || "No preview" }}
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="selectedThread"
      class="flex-1 flex flex-col h-full min-w-0 bg-zinc-950"
    >
      <div
        class="p-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/60 backdrop-blur-sm"
      >
        <div class="min-w-0">
          <h2 class="text-sm font-bold text-white truncate">
            {{ selectedThread.subject }}
          </h2>
          <div class="text-xs text-zinc-400 mt-0.5 flex items-center gap-2">
            <span>Customer: {{ selectedThread.customer_email }}</span>
            <span>•</span>
            <span class="font-mono text-[11px] text-emerald-400"
              >Mailbox: {{ selectedThread.to }}</span
            >
          </div>
        </div>

        <div class="flex items-center gap-2">
          <UButton
            icon="i-lucide-archive"
            color="neutral"
            variant="ghost"
            size="xs"
            title="Archive Conversation"
            @click="setThreadStatus('archived')"
          />
          <UButton
            icon="i-lucide-alert-triangle"
            color="neutral"
            variant="ghost"
            size="xs"
            title="Mark Spam"
            @click="setThreadStatus('spam')"
          />
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
        <div
          v-for="msg in selectedThread.messages || []"
          :key="msg.message_id"
          :class="[
            'p-4 rounded-2xl max-w-2xl text-xs flex flex-col gap-2 shadow-sm',
            msg.direction === 'outgoing'
              ? 'ml-auto bg-emerald-950/40 border border-emerald-500/20 text-emerald-100'
              : 'mr-auto bg-zinc-900 border border-zinc-800 text-zinc-200',
          ]"
        >
          <div
            class="flex items-center justify-between gap-4 text-[10px] text-zinc-400"
          >
            <div class="flex items-center gap-1.5">
              <span
                :class="[
                  'px-1.5 py-0.2 rounded text-[9px] font-bold uppercase',
                  msg.direction === 'outgoing'
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-blue-500/20 text-blue-300',
                ]"
              >
                {{ msg.direction }}
              </span>
              <span class="font-semibold">{{ msg.sender }}</span>
            </div>
            <span>{{
              new Date(msg.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })
            }}</span>
          </div>
          <div
            class="prose prose-invert prose-xs max-w-none text-zinc-100"
            v-html="msg.body"
          />
        </div>
      </div>

      <div
        class="p-4 border-t border-zinc-800 bg-zinc-900/60 flex flex-col gap-3"
      >
        <textarea
          v-model="replyText"
          rows="3"
          placeholder="Type reply to customer..."
          class="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500"
        />
        <div class="flex justify-between items-center">
          <span class="text-[11px] text-zinc-400"
            >Replying from
            {{ selectedThread.to || adminUser?.company_email }}</span
          >
          <UButton
            label="Send Reply"
            icon="i-lucide-send"
            color="primary"
            size="sm"
            :disabled="!canManageEmails"
            :loading="isSendingReply"
            @click="handleSendReply"
          />
        </div>
      </div>
    </div>

    <div
      v-else
      class="flex-1 flex items-center justify-center text-zinc-500 text-xs"
    >
      Select a conversation from the list to view message history.
    </div>

    <Teleport to="body">
      <div
        v-if="isComposeOpen"
        class="fixed inset-0 z-[999999] bg-black/80 backdrop-blur-md flex justify-center items-center overflow-y-auto p-4 sm:p-6 md:p-8"
      >
        <div
          class="w-full max-w-3xl bg-zinc-900 border border-zinc-800 rounded-2xl p-5 sm:p-6 flex flex-col shadow-2xl h-[88vh] max-h-[760px] my-auto"
        >
          <div
            class="flex items-center justify-between border-b border-zinc-800 pb-3 shrink-0"
          >
            <div>
              <h2 class="text-base font-bold text-white">
                Compose Outbound Email
              </h2>
              <p class="text-xs text-zinc-400">
                Dispatch direct email communication to user or customer
              </p>
            </div>
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="xs"
              @click="isComposeOpen = false"
            />
          </div>

          <div
            class="flex flex-col gap-3.5 overflow-y-auto pr-1.5 py-3 flex-1 min-h-0"
          >
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-zinc-300"
                  >From Mailbox</label
                >
                <select
                  v-model="composeForm.mailbox_id"
                  class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
                >
                  <optgroup
                    v-if="myPersonalMailbox"
                    label="My Personal Mailbox"
                  >
                    <option :value="myPersonalMailbox.mailbox_id">
                      {{ myPersonalMailbox.name }} ({{
                        myPersonalMailbox.email
                      }})
                    </option>
                  </optgroup>
                  <optgroup
                    v-if="sharedMailboxes.length > 0"
                    label="Public / Shared Mailboxes"
                  >
                    <option
                      v-for="mb in sharedMailboxes"
                      :key="mb.mailbox_id"
                      :value="mb.mailbox_id"
                    >
                      {{ mb.name }} ({{ mb.email }})
                    </option>
                  </optgroup>
                  <optgroup
                    v-if="
                      !myPersonalMailbox &&
                      sharedMailboxes.length === 0 &&
                      mailboxes.length > 0
                    "
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

              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-zinc-300"
                  >To Recipient Email</label
                >
                <UInput
                  v-model="composeForm.to_email"
                  placeholder="client@example.com or user@kluda.app"
                  size="sm"
                />
              </div>
            </div>

            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-zinc-300">Subject</label>
              <UInput
                v-model="composeForm.subject"
                placeholder="Assistance regarding your retail store..."
                size="sm"
              />
            </div>

            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-zinc-300"
                >Visual Message Body</label
              >
              <TiptapEditor v-model="composeForm.body" />
            </div>
          </div>

          <div
            class="flex justify-end gap-2 border-t border-zinc-800 pt-3 shrink-0"
          >
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
        </div>
      </div>
    </Teleport>
  </div>
</template>
