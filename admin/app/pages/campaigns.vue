<script setup lang="ts">
const { apiFetch } = useAdminApi();
const { adminUser } = useAdminAuth();
const { canManageEmails } = useAdminPermission();
const config = useRuntimeConfig();
const domain = (config.public.domainName as string) || "kluda.app";

const campaigns = ref<any[]>([]);
const stores = ref<any[]>([]);
const mailboxes = ref<any[]>([]);
const isLoading = ref(true);
const isComposing = ref(false);
const isSending = ref(false);
const editingCampaignId = ref<string | null>(null);
const editorRef = ref<any>(null);
const previewDevice = ref<"desktop" | "mobile">("desktop");

const audienceType = ref<
  | "all_merchants"
  | "all_staff"
  | "all_users"
  | "specific_store"
  | "custom_emails"
>("all_merchants");
const selectedStoreId = ref("");
const customEmailList = ref("");

const form = ref({
  title: "Platform Stability & Offline Multi-Counter Upgrade",
  subject: "🚀 Introducing Kluda Multi-Counter Offline Sync",
  sender: "",
  body: `<h2>🚀 Introducing Multi-Counter Offline Sync</h2>
<p>We are excited to announce our biggest stability release yet for <strong>Kluda POS</strong>. Your cashier terminals can now operate completely offline and automatically synchronize when internet connectivity resumes.</p>

<blockquote style="margin: 16px 0; padding: 14px 18px; border-left: 4px solid #059669; background-color: #f8fafc; color: #1e293b; border-radius: 0 8px 8px 0;">
  <strong>What this means for your business:</strong> Zero interrupted sales during peak network congestion, seamless split payments across counters, and instant receipts.
</blockquote>

<h3>Key Highlights in this Update:</h3>
<ul>
  <li><strong>Offline Ledger Caching:</strong> Continuous checkout capability without relying on active internet connection.</li>
  <li><strong>Instant Barcode Lookup:</strong> Faster product scanning from cached store inventory catalog.</li>
  <li><strong>Thermal Printer Optimization:</strong> Enhanced ESC/POS and Bluetooth receipt compatibility.</li>
</ul>

<p>To upgrade your store terminals, simply open the POS app settings and tap <em>Check for Updates</em>.</p>
<p style="margin: 20px 0;">
  <a href="https://app.kluda.app" style="display: inline-block; background-color: #059669; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 14px;">Open Merchant Portal &rarr;</a>
</p>`,
});

const templatePresets = [
  {
    id: "feature_launch",
    name: "🚀 Major Feature Release",
    description:
      "Announce new capabilities, speed improvements, and terminal upgrades",
    title: "Platform Upgrade: Multi-Counter Offline Sync",
    subject: "🚀 Introducing Kluda Multi-Counter Offline Sync",
    body: `<h2>🚀 Major Upgrade: Multi-Counter Offline Sync is Live!</h2>
<p>We are thrilled to bring you our most requested feature: <strong>Full Offline Multi-Counter Synchronization</strong>.</p>
<blockquote style="margin: 16px 0; padding: 14px 18px; border-left: 4px solid #059669; background-color: #f8fafc; color: #1e293b; border-radius: 0 8px 8px 0;">
  <strong>Key Benefit:</strong> Even if your store Wi-Fi drops, your cashiers can continue taking orders and printing receipts without interruption.
</blockquote>
<h3>What's New in this Version:</h3>
<ul>
  <li>Ultra-fast local barcode and product lookup.</li>
  <li>Automatic cloud synchronization when internet connection resumes.</li>
  <li>Multi-terminal real-time inventory deduction.</li>
</ul>
<p>Update your desktop and mobile POS terminals today to take advantage of these improvements.</p>
<p style="margin: 20px 0;">
  <a href="https://app.kluda.app" style="display: inline-block; background-color: #059669; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 14px;">Update Store App &rarr;</a>
</p>`,
  },
  {
    id: "monthly_digest",
    name: "📈 Monthly Merchant Digest",
    description:
      "Platform statistics, best practices, and merchant performance insights",
    title: "Monthly Retail Growth Digest",
    subject: "📈 Your Monthly Kluda Merchant Growth Digest",
    body: `<h2>📈 Monthly Merchant Growth & Performance Insights</h2>
<p>Here is your monthly summary of platform updates, retail operational tips, and growth features designed to help your store thrive.</p>
<blockquote style="margin: 16px 0; padding: 14px 18px; border-left: 4px solid #059669; background-color: #f8fafc; color: #1e293b; border-radius: 0 8px 8px 0;">
  <strong>Retail Pro-Tip:</strong> Stores using our automated barcode catalog checkout faster by an average of 42% per customer.
</blockquote>
<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px;">
  <thead>
    <tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
      <th style="padding: 10px; text-align: left;">Feature</th>
      <th style="padding: 10px; text-align: left;">Benefit</th>
      <th style="padding: 10px; text-align: left;">Status</th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom: 1px solid #e2e8f0;">
      <td style="padding: 10px; font-weight: 600;">Barcode Batch Scanner</td>
      <td style="padding: 10px;">Quick inventory restocking</td>
      <td style="padding: 10px; color: #059669; font-weight: 700;">Live</td>
    </tr>
    <tr>
      <td style="padding: 10px; font-weight: 600;">SMS Receipts</td>
      <td style="padding: 10px;">Paperless digital receipts</td>
      <td style="padding: 10px; color: #059669; font-weight: 700;">Live</td>
    </tr>
  </tbody>
</table>
<p>Need assistance optimizing your inventory catalog? Our retail support team is available 24/7 via the merchant help desk.</p>`,
  },
  {
    id: "maintenance_notice",
    name: "⚠️ Scheduled Maintenance",
    description: "Inform merchants in advance about scheduled cloud upgrades",
    title: "Scheduled Cloud Infrastructure Upgrade",
    subject: "⚠️ Scheduled Platform Maintenance Notice",
    body: `<h2>⚠️ Scheduled Cloud Infrastructure Upgrade</h2>
<p>To ensure peak performance and server reliability, our cloud infrastructure will undergo scheduled maintenance during off-peak hours.</p>
<div style="margin: 16px 0; padding: 14px 18px; border-left: 4px solid #f59e0b; background-color: #fffbeb; border-radius: 0 8px 8px 0;">
  <p style="margin: 0; font-size: 13px; color: #78350f;"><strong>POS Impact:</strong> Cashier checkout will continue working normally in offline mode. Analytics syncing will resume immediately after the upgrade.</p>
</div>
<p>No action is required from your staff. We appreciate your partnership as we continue improving platform performance.</p>`,
  },
  {
    id: "promo_upgrade",
    name: "🎁 Promotional & Incentive Offer",
    description: "Hardware discounts, referral bonuses, and add-on promotions",
    title: "Exclusive Merchant Upgrade Offer",
    subject: "🎁 Exclusive Store Upgrade: Free Cloud Receipt Printing",
    body: `<h2>🎁 Special Promotion for Verified Retail Stores</h2>
<p>As a valued merchant on <strong>Kluda POS</strong>, we are pleased to offer you complimentary access to our <strong>Digital SMS & WhatsApp Receipt Service</strong> for the next 3 months.</p>
<div style="background-color: #f8fafc; border: 1px dashed #059669; border-radius: 12px; padding: 18px; margin: 20px 0; text-align: center;">
  <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b; letter-spacing: 0.05em;">Promo Voucher Code</div>
  <div style="font-size: 22px; font-weight: 900; font-family: monospace; color: #059669; margin: 8px 0;">KLUDA-GROWTH-2026</div>
  <div style="font-size: 11px; color: #94a3b8;">Valid through the end of the current quarter</div>
</div>
<p>Redeem this code directly from your merchant billing settings or contact our support team to activate it on your account.</p>`,
  },
];

function applyTemplate(tpl: any) {
  form.value.title = tpl.title;
  form.value.subject = tpl.subject;
  form.value.body = tpl.body;
}

function handleInsertSnippet(type: string) {
  if (editorRef.value?.insertSnippet) {
    editorRef.value.insertSnippet(type);
  }
}

function insertVariable(tag: string) {
  form.value.body += ` ${tag} `;
}

const renderedPreviewHtml = computed(() => {
  const bodyContent =
    form.value.body ||
    '<p style="color: #94a3b8; font-style: italic;">Start typing your campaign content...</p>';
  const currentYear = new Date().getFullYear();
  const cleanSubject = form.value.subject
    ? form.value.subject
    : "Campaign Communication";

  return `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${cleanSubject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155; -webkit-font-smoothing: antialiased;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f4f5; padding: 24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
          <tr>
            <td style="background-color: #0f172a; padding: 20px 28px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td>
                    <div style="display: inline-block; background-color: #059669; color: #ffffff; font-weight: 900; font-size: 16px; width: 32px; height: 32px; line-height: 32px; text-align: center; border-radius: 8px; font-family: monospace;">K</div>
                    <span style="font-size: 18px; font-weight: 800; color: #ffffff; margin-left: 10px; vertical-align: middle; letter-spacing: -0.02em;">Kluda</span>
                  </td>
                  <td align="right">
                    <span style="display: inline-block; background-color: rgba(5, 150, 105, 0.15); border: 1px solid rgba(5, 150, 105, 0.4); color: #34d399; font-size: 10px; font-weight: 700; text-transform: uppercase; padding: 4px 8px; border-radius: 6px; letter-spacing: 0.05em;">RETAIL POS</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 28px; font-size: 14px; line-height: 1.6; color: #334155;">
              ${bodyContent}
            </td>
          </tr>
          <tr>
            <td style="background-color: #f8fafc; padding: 20px 28px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #64748b;">
              <p style="margin: 0 0 6px 0; font-weight: 600; color: #475569;">Kluda Retail Platform &bull; Operations &amp; Merchant Control</p>
              <p style="margin: 0 0 10px 0; font-size: 11px; color: #94a3b8;">This is an official administrative broadcast sent to registered stores.</p>
              <p style="margin: 0; font-size: 11px;">
                <a href="https://${domain}" style="color: #059669; text-decoration: none; font-weight: 600;">Kluda Portal</a>
                &bull;
                <a href="mailto:support@${domain}" style="color: #059669; text-decoration: none; font-weight: 600;">Contact Support</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
});

async function fetchCampaigns() {
  isLoading.value = true;
  try {
    const [cData, sData, mData] = await Promise.all([
      apiFetch<any[]>("/admin/campaigns"),
      apiFetch<any[]>("/admin/stores"),
      apiFetch<any[]>("/admin/mailboxes"),
    ]);
    campaigns.value = cData || [];
    stores.value = sData || [];
    mailboxes.value = mData || [];

    if (!form.value.sender) {
      const shared = mailboxes.value.find((m) => m.type === "shared");
      if (shared) {
        form.value.sender = shared.email;
      } else if (adminUser.value?.company_email) {
        form.value.sender = adminUser.value.company_email;
      } else {
        form.value.sender = `team@${domain}`;
      }
    }
  } catch {
    campaigns.value = [];
    stores.value = [];
    mailboxes.value = [];
  } finally {
    isLoading.value = false;
  }
}

function openCreateComposer() {
  editingCampaignId.value = null;
  form.value = {
    title: "",
    subject: "",
    sender: form.value.sender || `team@${domain}`,
    body: "<p>Start writing your broadcast announcement here...</p>",
  };
  audienceType.value = "all_merchants";
  selectedStoreId.value = "";
  customEmailList.value = "";
  isComposing.value = true;
}

function openEditComposer(c: any) {
  editingCampaignId.value = c.campaign_id;
  form.value = {
    title: c.title,
    subject: c.subject,
    sender: c.sender,
    body: c.body,
  };
  if (c.target_audience?.startsWith("specific_store:")) {
    audienceType.value = "specific_store";
    selectedStoreId.value = c.target_audience.split(":")[1] || "";
  } else if (
    ["all_merchants", "all_staff", "all_users"].includes(c.target_audience)
  ) {
    audienceType.value = c.target_audience;
  } else {
    audienceType.value = "custom_emails";
    customEmailList.value = c.target_audience;
  }
  isComposing.value = true;
}

async function handleSaveCampaign(sendNow: boolean) {
  if (
    !form.value.title ||
    !form.value.subject ||
    !form.value.body ||
    !form.value.sender
  ) {
    alert("Please fill all required campaign fields");
    return;
  }

  let finalTarget: string = audienceType.value;
  if (audienceType.value === "specific_store") {
    if (!selectedStoreId.value) {
      alert("Please select a specific store");
      return;
    }
    finalTarget = `specific_store:${selectedStoreId.value}`;
  } else if (audienceType.value === "custom_emails") {
    if (!customEmailList.value) {
      alert("Please enter at least one recipient email address");
      return;
    }
    finalTarget = customEmailList.value;
  }

  isSending.value = true;
  try {
    if (editingCampaignId.value) {
      await apiFetch(`/admin/campaigns/${editingCampaignId.value}?send_now=${sendNow}`, {
        method: "PUT",
        body: {
          title: form.value.title,
          subject: form.value.subject,
          body: form.value.body,
          sender: form.value.sender,
          target_audience: finalTarget,
        },
      });
    } else {
      await apiFetch(`/admin/campaigns?send_now=${sendNow}`, {
        method: "POST",
        body: {
          title: form.value.title,
          subject: form.value.subject,
          body: form.value.body,
          sender: form.value.sender,
          target_audience: finalTarget,
        },
      });
    }
    isComposing.value = false;
    editingCampaignId.value = null;
    await fetchCampaigns();
  } catch (err: any) {
    alert(err?.data?.detail || "Failed to save campaign");
  } finally {
    isSending.value = false;
  }
}

async function handleSendNow(c: any) {
  if (!confirm(`Are you sure you want to dispatch "${c.title}" to ${c.target_audience}?`)) {
    return;
  }
  try {
    await apiFetch(`/admin/campaigns/${c.campaign_id}/send`, {
      method: "POST",
    });
    await fetchCampaigns();
  } catch (err: any) {
    alert(err?.data?.detail || "Failed to dispatch campaign");
  }
}

async function handleDeleteCampaign(c: any) {
  if (!confirm(`Are you sure you want to delete "${c.title}"?`)) {
    return;
  }
  try {
    await apiFetch(`/admin/campaigns/${c.campaign_id}`, {
      method: "DELETE",
    });
    await fetchCampaigns();
  } catch (err: any) {
    alert(err?.data?.detail || "Failed to delete campaign");
  }
}

onMounted(() => {
  fetchCampaigns();
});
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
    <div
      class="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
    >
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white">
          Email Campaigns & Broadcasts
        </h1>
        <p class="text-xs text-zinc-400 mt-0.5">
          Design responsive, branded merchant announcements with visual
          templates and live split preview
        </p>
      </div>
      <UButton
        label="Compose Campaign"
        icon="i-lucide-plus"
        color="primary"
        size="sm"
        :disabled="!canManageEmails"
        @click="openCreateComposer"
      />
    </div>

    <div
      v-if="isComposing"
      class="bg-zinc-900/90 border border-zinc-800 p-6 rounded-2xl flex flex-col gap-6 backdrop-blur-xl"
    >
      <div
        class="flex items-center justify-between border-b border-zinc-800 pb-4"
      >
        <div>
          <h2 class="text-base font-bold text-white">
            {{ editingCampaignId ? 'Edit Campaign Draft' : 'Visual Campaign Studio' }}
          </h2>
          <p class="text-xs text-zinc-400">
            WYSIWYG Email Paper Canvas with Instant Split Preview
          </p>
        </div>
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="isComposing = false"
        />
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-xs font-semibold text-zinc-300"
          >Choose a Pre-Designed Campaign Preset</label
        >
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            v-for="tpl in templatePresets"
            :key="tpl.id"
            type="button"
            class="text-left p-3.5 rounded-xl border transition-all flex flex-col gap-1.5 group"
            :class="
              form.title === tpl.title
                ? 'bg-emerald-950/30 border-emerald-500/50 ring-1 ring-emerald-500/30'
                : 'bg-zinc-950/80 border-zinc-800/80 hover:border-zinc-700 hover:bg-zinc-950'
            "
            @click="applyTemplate(tpl)"
          >
            <div
              class="font-bold text-xs text-zinc-100 group-hover:text-emerald-400 transition-colors"
            >
              {{ tpl.name }}
            </div>
            <div class="text-[11px] text-zinc-400 line-clamp-2 leading-relaxed">
              {{ tpl.description }}
            </div>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300"
            >Internal Campaign Name</label
          >
          <UInput
            v-model="form.title"
            placeholder="e.g. Q3 Feature Release Blast"
            size="sm"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300"
            >Email Subject Line</label
          >
          <UInput
            v-model="form.subject"
            placeholder="e.g. 🚀 Exciting Platform Updates"
            size="sm"
          />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300"
            >From Sender Address</label
          >
          <select
            v-model="form.sender"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
          >
            <optgroup label="My Personal Company Email">
              <option
                v-if="adminUser?.company_email"
                :value="adminUser.company_email"
              >
                {{ adminUser.fullname }} ({{ adminUser.company_email }})
              </option>
            </optgroup>
            <optgroup label="Public / Shared Mailboxes">
              <option
                v-for="mb in mailboxes.filter((m) => m.type === 'shared')"
                :key="mb.mailbox_id"
                :value="mb.email"
              >
                {{ mb.name }} ({{ mb.email }})
              </option>
            </optgroup>
          </select>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300"
            >Target Recipient Audience</label
          >
          <select
            v-model="audienceType"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="all_merchants">All Store Owners (Merchants)</option>
            <option value="all_users">All Registered Users</option>
            <option value="specific_store">Specific Retail Store</option>
            <option value="custom_emails">Custom Email List</option>
          </select>
        </div>
      </div>

      <div
        v-if="audienceType === 'specific_store'"
        class="flex flex-col gap-1.5 p-3 rounded-xl bg-zinc-950 border border-zinc-800"
      >
        <label class="text-xs font-medium text-zinc-300">Select Store</label>
        <select
          v-model="selectedStoreId"
          class="bg-zinc-900 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
        >
          <option value="" disabled>Choose a retail store...</option>
          <option v-for="s in stores" :key="s.store_id" :value="s.store_id">
            {{ s.name }} (Owner: {{ s.owner_email || "N/A" }})
          </option>
        </select>
      </div>

      <div
        v-if="audienceType === 'custom_emails'"
        class="flex flex-col gap-1.5 p-3 rounded-xl bg-zinc-950 border border-zinc-800"
      >
        <label class="text-xs font-medium text-zinc-300"
          >Comma-separated email addresses</label
        >
        <UInput
          v-model="customEmailList"
          placeholder="merchant1@example.com, merchant2@example.com"
          size="sm"
        />
      </div>

      <div
        class="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-xl bg-zinc-950 border border-zinc-800"
      >
        <div class="flex flex-wrap items-center gap-1.5 text-xs">
          <span
            class="text-zinc-400 font-medium text-[11px] flex items-center gap-1"
          >
            <UIcon
              name="i-lucide-wand-2"
              class="w-3.5 h-3.5 text-emerald-400"
            />
            Quick Insert Snippets:
          </span>
          <button
            type="button"
            class="px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-white text-zinc-300 text-xs font-medium transition-colors flex items-center gap-1"
            @click="handleInsertSnippet('callout')"
          >
            <UIcon name="i-lucide-sparkles" class="w-3 h-3 text-emerald-400" />
            Callout Box
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-white text-zinc-300 text-xs font-medium transition-colors flex items-center gap-1"
            @click="handleInsertSnippet('warning')"
          >
            <UIcon
              name="i-lucide-alert-triangle"
              class="w-3 h-3 text-amber-400"
            />
            Alert Box
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-white text-zinc-300 text-xs font-medium transition-colors flex items-center gap-1"
            @click="handleInsertSnippet('button')"
          >
            <UIcon
              name="i-lucide-arrow-up-right"
              class="w-3 h-3 text-emerald-400"
            />
            Action Button
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-white text-zinc-300 text-xs font-medium transition-colors flex items-center gap-1"
            @click="handleInsertSnippet('table')"
          >
            <UIcon name="i-lucide-table" class="w-3 h-3 text-blue-400" />
            Data Table
          </button>
        </div>

        <div class="flex items-center gap-1.5 text-xs text-zinc-400">
          <span class="text-[11px]">Variables:</span>
          <button
            type="button"
            class="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 hover:border-emerald-500 text-emerald-400 font-mono text-[11px]"
            @click="insertVariable('{{merchant_name}}')"
          >
            &#123;&#123;merchant_name&#125;&#125;
          </button>
          <button
            type="button"
            class="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 hover:border-emerald-500 text-emerald-400 font-mono text-[11px]"
            @click="insertVariable('{{store_name}}')"
          >
            &#123;&#123;store_name&#125;&#125;
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div class="xl:col-span-7 flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label
              class="text-xs font-medium text-zinc-300 flex items-center gap-1.5"
            >
              <UIcon
                name="i-lucide-edit-3"
                class="w-3.5 h-3.5 text-emerald-400"
              />
              WYSIWYG Email Paper Canvas
            </label>
            <span class="text-[11px] text-zinc-500"
              >Edit directly inside styled card</span
            >
          </div>
          <TiptapEditor
            ref="editorRef"
            v-model="form.body"
            variant="email-light"
          />
        </div>

        <div class="xl:col-span-5 flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label
              class="text-xs font-medium text-zinc-300 flex items-center gap-1.5"
            >
              <UIcon name="i-lucide-eye" class="w-3.5 h-3.5 text-emerald-400" />
              Real-Time Client Preview
            </label>
            <div
              class="flex bg-zinc-950 p-0.5 rounded-lg border border-zinc-800"
            >
              <button
                type="button"
                :class="[
                  'px-2 py-0.5 text-[11px] rounded-md font-medium transition-colors flex items-center gap-1',
                  previewDevice === 'desktop'
                    ? 'bg-zinc-800 text-white shadow-xs'
                    : 'text-zinc-400',
                ]"
                @click="previewDevice = 'desktop'"
              >
                <UIcon name="i-lucide-monitor" class="w-3 h-3" />
                Desktop
              </button>
              <button
                type="button"
                :class="[
                  'px-2 py-0.5 text-[11px] rounded-md font-medium transition-colors flex items-center gap-1',
                  previewDevice === 'mobile'
                    ? 'bg-zinc-800 text-white shadow-xs'
                    : 'text-zinc-400',
                ]"
                @click="previewDevice = 'mobile'"
              >
                <UIcon name="i-lucide-smartphone" class="w-3 h-3" />
                Mobile
              </button>
            </div>
          </div>

          <div
            class="bg-zinc-950 border border-zinc-800 rounded-xl p-3 flex justify-center overflow-x-auto min-h-[440px]"
          >
            <div
              :style="{ width: previewDevice === 'mobile' ? '360px' : '100%' }"
              class="transition-all duration-300 rounded-lg overflow-hidden border border-zinc-800/80 bg-[#f4f4f5] shadow-lg"
            >
              <iframe
                :srcdoc="renderedPreviewHtml"
                class="w-full h-[460px] border-0"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-zinc-800 pt-4">
        <UButton
          label="Cancel"
          color="neutral"
          variant="ghost"
          size="sm"
          @click="isComposing = false"
        />
        <div class="flex items-center gap-2">
          <UButton
            label="Save as Draft"
            icon="i-lucide-save"
            color="neutral"
            variant="outline"
            size="sm"
            :disabled="!canManageEmails"
            :loading="isSending"
            @click="handleSaveCampaign(false)"
          />
          <UButton
            label="Dispatch Broadcast Now"
            icon="i-lucide-send"
            color="primary"
            size="sm"
            :disabled="!canManageEmails"
            :loading="isSending"
            @click="handleSaveCampaign(true)"
          />
        </div>
      </div>
    </div>

    <div
      class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl overflow-hidden backdrop-blur-sm"
    >
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead
            class="bg-zinc-950/60 border-b border-zinc-800 text-zinc-400 font-semibold uppercase text-[10px] tracking-wider"
          >
            <tr>
              <th class="px-5 py-3.5">Campaign</th>
              <th class="px-5 py-3.5">Subject</th>
              <th class="px-5 py-3.5">Audience Target</th>
              <th class="px-5 py-3.5">Delivered</th>
              <th class="px-5 py-3.5">Status</th>
              <th class="px-5 py-3.5">Created</th>
              <th class="px-5 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60">
            <tr v-if="isLoading">
              <td colspan="7" class="px-5 py-8 text-center text-zinc-500">
                Loading campaigns...
              </td>
            </tr>
            <tr v-else-if="campaigns.length === 0">
              <td colspan="7" class="px-5 py-8 text-center text-zinc-500">
                No campaigns created yet. Click "Compose Campaign" to get
                started.
              </td>
            </tr>
            <tr
              v-for="c in campaigns"
              v-else
              :key="c.campaign_id"
              class="hover:bg-zinc-800/30 transition-colors"
            >
              <td class="px-5 py-3.5 font-medium text-zinc-100">
                {{ c.title }}
              </td>
              <td class="px-5 py-3.5 text-zinc-300">{{ c.subject }}</td>
              <td class="px-5 py-3.5 text-zinc-400 capitalize">
                {{ c.target_audience }}
              </td>
              <td class="px-5 py-3.5 font-mono text-emerald-400">
                {{ c.total_delivered }} / {{ c.total_recipients }}
              </td>
              <td class="px-5 py-3.5">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-semibold border',
                    c.status === 'sent'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : c.status === 'sending'
                        ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                        : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
                  ]"
                >
                  {{ c.status }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-zinc-400">
                {{ new Date(c.created_at).toLocaleDateString() }}
              </td>
              <td class="px-5 py-3.5 text-right">
                <div class="flex items-center justify-end gap-1.5">
                  <UButton
                    v-if="c.status === 'draft'"
                    label="Send"
                    icon="i-lucide-send"
                    color="primary"
                    size="xs"
                    :disabled="!canManageEmails"
                    @click="handleSendNow(c)"
                  />
                  <UButton
                    v-if="c.status === 'draft'"
                    label="Edit"
                    icon="i-lucide-edit-2"
                    color="neutral"
                    variant="ghost"
                    size="xs"
                    :disabled="!canManageEmails"
                    @click="openEditComposer(c)"
                  />
                  <UButton
                    icon="i-lucide-trash-2"
                    color="error"
                    variant="ghost"
                    size="xs"
                    :disabled="!canManageEmails || c.status === 'sending'"
                    @click="handleDeleteCampaign(c)"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
