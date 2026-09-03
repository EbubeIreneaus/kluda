<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({ layout: 'marchant' })

const route = useRoute()
const toast = useToast()
const {
  plan: currentPlan,
  status,
  priceFormatted,
  nextRenewalFormatted,
  daysRemaining,
  usage,
  availablePlans,
  hasUsedTrial,
  isLoading,
  isLoadingPlans,
  fetchCurrentSubscription,
  fetchAvailablePlans,
  subscribePlan,
  cancelPlan,
  fetchSubscriptionHistory,
  isOwner
} = useSubscription()

const subscriptionHistory = ref<any[]>([])
const isLoadingHistory = ref(false)

async function loadHistory() {
  isLoadingHistory.value = true
  try {
    subscriptionHistory.value = await fetchSubscriptionHistory()
  } finally {
    isLoadingHistory.value = false
  }
}

const isProcessing = ref(false)
const selectedInterval = ref<string>('monthly')

// Detail modal state for subscription history
const showHistoryModal = ref(false)
const selectedHistoryItem = ref<any | null>(null)

function openHistoryDetails(item: any) {
  selectedHistoryItem.value = item
  showHistoryModal.value = true
}

async function copyToClipboard(text: string, label = 'Copied') {
  if (!text) return
  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      await navigator.clipboard.writeText(text)
      toast.add({
        title: 'Copied to Clipboard',
        description: `${label}: ${text}`,
        color: 'success',
        icon: 'i-lucide-check'
      })
    }
  } catch {
    toast.add({
      title: 'Copy Failed',
      description: 'Could not copy to clipboard.',
      color: 'warning'
    })
  }
}

function copyFullBillingRecord(item: any) {
  if (!item) return
  const dateStr = new Date(item.created_at).toLocaleString()
  const renewalStr = item.next_renewal ? new Date(item.next_renewal).toLocaleString() : 'Never expires'
  const text = [
    `=== KLUDA BILLING RECEIPT ===`,
    `Plan: ${item.plan_name} (${item.plan_slug})`,
    `Subscription ID: ${item.subscription_id || 'N/A'}`,
    `Reference: ${item.reference || 'N/A'}`,
    `Status: ${item.status}`,
    `Amount: ${item.amount === 0 ? 'Free' : '₦' + (item.amount / 100).toLocaleString()}`,
    `Channel: ${item.payment_channel || 'System / Auto'}`,
    `Activated: ${dateStr}`,
    `Valid Until: ${renewalStr}`,
    item.description ? `Note: ${item.description}` : null
  ].filter(Boolean).join('\n')

  copyToClipboard(text, 'Full receipt record copied')
}

// Dynamically extract unique intervals present in availablePlans (excluding standalone trial)
const availableIntervals = computed(() => {
  if (!availablePlans.value || availablePlans.value.length === 0) {
    return ['monthly']
  }
  const cleanPlans = availablePlans.value.filter((p: any) => p.slug !== 'trial')
  const intervals = Array.from(new Set(cleanPlans.map((p: any) => (p.interval || 'monthly').toLowerCase())))
  return intervals.length > 0 ? intervals : ['monthly']
})

// Auto-select first available interval if selectedInterval is not in list
watch(availableIntervals, (intervals) => {
  if (intervals.length > 0 && !intervals.includes(selectedInterval.value)) {
    selectedInterval.value = intervals[0]
  }
}, { immediate: true })

const displayPlans = computed(() => {
  if (!availablePlans.value || availablePlans.value.length === 0) {
    return []
  }
  // Standalone trial is NEVER shown
  const plans = availablePlans.value.filter((p: any) => p.slug !== 'trial')
  
  // Filter by selectedInterval if availableIntervals has multiple
  const filtered = plans.filter((p: any) => {
    const planInterval = (p.interval || 'monthly').toLowerCase()
    return planInterval === selectedInterval.value.toLowerCase()
  })

  const targetPlans = filtered.length > 0 ? filtered : plans

  return targetPlans.map((p: any) => {
    const isCurrent = currentPlan.value?.slug === p.slug
    const priceNaira = (p.price || 0) / 100
    const inv = (p.interval || 'monthly').toLowerCase()
    const intervalLabel = inv === 'daily' ? 'day' : (inv === 'weekly' ? 'wk' : (inv === 'yearly' ? 'yr' : (inv === 'quarterly' ? 'quarter' : 'mo')))
    
    // Check if trial is available for this plan AND user hasn't used trial before
    const canTrial = Boolean(p.has_trial && p.trial_duration_days && p.trial_duration_days > 0 && !hasUsedTrial.value)

    return {
      slug: p.slug,
      name: p.name,
      price: p.price,
      interval: p.interval || 'monthly',
      priceFormatted: p.price === 0 ? 'Free' : `₦${priceNaira.toLocaleString()} / ${intervalLabel}`,
      badge: isCurrent ? 'Active' : (canTrial ? `${p.trial_duration_days}-Day Trial` : (p.price > 2000000 ? 'Enterprise' : 'Available')),
      description: p.description || 'Retail point-of-sale tier with automated inventory sync.',
      hasTrial: canTrial,
      trialDurationDays: p.trial_duration_days || 0,
      features: [
        `${p.store_limit && p.store_limit > 0 ? p.store_limit : 'Unlimited'} Store ${p.store_limit === 1 ? 'Branch' : 'Branches'}`,
        `${p.product_limit && p.product_limit > 0 ? p.product_limit.toLocaleString() : 'Unlimited'} Products`,
        `${p.sales_limit_per_month && p.sales_limit_per_month > 0 ? p.sales_limit_per_month.toLocaleString() : 'Unlimited'} Monthly Sales`,
        'Real-time Multi-Branch Sales Sync',
        'Automated Thermal Receipts'
      ],
      isCurrent
    }
  })
})

async function handleSubscribe(planSlug: string, isTrial = false) {
  isProcessing.value = true
  try {
    const res = await subscribePlan(planSlug, isTrial)
    if (res.redirect_url) {
      toast.add({
        title: 'Redirecting to Checkout',
        description: 'Forwarding to Paystack secure payment gateway...',
        color: 'info'
      })
      window.location.href = res.redirect_url
    } else if (res.status === 'active') {
      toast.add({
        title: isTrial ? 'Free Trial Activated!' : 'Subscription Updated',
        description: res.message || 'Your subscription is now active.',
        color: 'success'
      })
    }
  } catch (err: any) {
    toast.add({
      title: 'Subscription Action Failed',
      description: err?.data?.detail || 'Could not process plan request. Please try again.',
      color: 'error'
    })
  } finally {
    isProcessing.value = false
  }
}

async function handleCancelSubscription() {
  if (!confirm('Are you sure you want to cancel your subscription? Your current plan will expire at the end of this billing period.')) {
    return
  }

  isProcessing.value = true
  try {
    const res = await cancelPlan()
    toast.add({
      title: 'Subscription Cancelled',
      description: res.message || 'Your subscription has been cancelled.',
      color: 'warning'
    })
  } catch (err: any) {
    toast.add({
      title: 'Cancellation Error',
      description: err?.data?.detail || err?.message || 'Failed to cancel subscription.',
      color: 'error'
    })
  } finally {
    isProcessing.value = false
  }
}

const highlightedSlug = ref('')

onMounted(async () => {
  await Promise.all([fetchCurrentSubscription(), fetchAvailablePlans()])

  const targetSlug = (route.hash ? route.hash.replace('#', '') : (route.query.plan as string))?.toLowerCase()
  if (targetSlug) {
    highlightedSlug.value = targetSlug
    nextTick(() => {
      const el = document.getElementById(targetSlug) || document.getElementById(`plan-${targetSlug}`)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    })
  }

  if (route.query.reference) {
    toast.add({
      title: 'Payment Confirmed',
      description: 'Your subscription status has been synced with Paystack.',
      color: 'success'
    })
  }

  loadHistory()
})
</script>

<template>
  <div class="space-y-6 max-w-6xl mx-auto">
    <div>
      <h1 class="text-2xl font-black tracking-tight text-(--ui-text-highlighted)">
        Billing & Subscription
      </h1>
      <p class="text-sm text-(--ui-text-muted) mt-1">
        Manage your merchant organization plan, subscription renewals, and feature limits.
      </p>
    </div>

    <!-- Active Subscription Overview Card -->
    <div class="p-6 rounded-3xl border border-amber-500/30 bg-amber-500/5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="space-y-1">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold text-amber-800 dark:text-amber-400">Current Subscription</span>
          <span
            :class="[
              'text-[10px] px-2.5 py-0.5 rounded-full font-bold border',
              status === 'ACTIVE'
                ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border-emerald-500/30'
                : (status === 'DUE' ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border-amber-500/30' : 'bg-rose-500/15 text-rose-800 dark:text-rose-300 border-rose-500/30')
            ]"
          >
            {{ status === 'ACTIVE' ? 'Active Plan' : (status === 'DUE' ? 'Payment Due' : 'Expired') }}
          </span>
        </div>
        <h3 class="text-xl font-extrabold text-(--ui-text-highlighted)">{{ currentPlan.name }}</h3>
        <p class="text-xs text-(--ui-text-muted)">
          {{ currentPlan.description || 'Full multi-branch retail suite with real-time cloud synchronization.' }}
        </p>

        <div class="pt-2 flex items-center gap-4 text-xs font-medium text-(--ui-text-dimmed)">
          <span>Combined Sales: <strong class="text-(--ui-text-highlighted)">{{ usage.monthlySalesCount }} / {{ usage.monthlySalesLimit > 0 ? usage.monthlySalesLimit : '∞' }}</strong></span>
          <span>Stores: <strong class="text-(--ui-text-highlighted)">{{ usage.storesCount }} / {{ usage.storesLimit > 0 ? usage.storesLimit : '∞' }}</strong></span>
        </div>
      </div>

      <div class="flex flex-col sm:items-end gap-3 self-start sm:self-auto">
        <div class="text-left sm:text-right">
          <p class="text-xs text-(--ui-text-dimmed)">Next Renewal</p>
          <p class="text-xs font-bold text-(--ui-text-highlighted)">
            {{ nextRenewalFormatted }} ({{ daysRemaining }}d left)
          </p>
        </div>

        <div v-if="isOwner && status === 'ACTIVE' && currentPlan.slug !== 'free'" class="flex items-center gap-2">
          <UButton
            size="xs"
            color="error"
            variant="ghost"
            icon="i-lucide-x-circle"
            :loading="isProcessing"
            @click="handleCancelSubscription"
          >
            Cancel Subscription
          </UButton>
        </div>
      </div>
    </div>

    <!-- Available Plans Section -->
    <div class="space-y-4 pt-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold text-(--ui-text-highlighted)">Available Plans</h2>
          <p class="text-xs text-(--ui-text-muted)">Scale your retail business with our tiered offerings.</p>
        </div>

        <!-- Dynamic Interval Selector -->
        <div v-if="availableIntervals.length > 1" class="flex items-center p-1 bg-(--ui-bg-elevated) border border-(--ui-border) rounded-2xl">
          <button
            v-for="inv in availableIntervals"
            :key="inv"
            type="button"
            class="px-4 py-1.5 rounded-xl text-xs font-bold transition capitalize"
            :class="selectedInterval === inv ? 'bg-amber-500 text-slate-950 shadow-xs' : 'text-(--ui-text-muted) hover:text-(--ui-text-highlighted)'"
            @click="selectedInterval = inv"
          >
            {{ inv === 'yearly' ? 'Yearly (Save 15%)' : (inv === 'daily' ? 'Daily Pass' : inv) }}
          </button>
        </div>
      </div>

      <!-- Loading State for Plans -->
      <div v-if="isLoadingPlans" class="py-16 flex flex-col items-center justify-center gap-3">
        <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-amber-500" />
        <span class="text-xs text-(--ui-text-muted)">Loading active subscription plans from server...</span>
      </div>

      <!-- Empty State for Plans -->
      <div v-else-if="displayPlans.length === 0" class="p-8 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) text-center space-y-3">
        <UIcon name="i-lucide-alert-circle" class="w-8 h-8 text-(--ui-text-dimmed) mx-auto" />
        <h3 class="text-sm font-bold text-(--ui-text-highlighted)">No Subscription Plans Configured</h3>
        <p class="text-xs text-(--ui-text-muted) max-w-sm mx-auto">
          No active subscription tiers were found for this interval. Create or activate plans in the Admin panel.
        </p>
        <UButton size="xs" variant="soft" color="primary" @click="fetchAvailablePlans">
          Refresh Plans
        </UButton>
      </div>

      <!-- Plan Cards Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
        <div
          v-for="p in displayPlans"
          :key="p.slug"
          :id="p.slug"
          class="rounded-3xl p-6 border bg-(--ui-bg-elevated) flex flex-col justify-between shadow-xs transition-all duration-300 relative scroll-mt-24"
          :class="[
            p.isCurrent ? 'border-amber-500/60 shadow-lg shadow-amber-500/10' : 'border-(--ui-border)',
            highlightedSlug === p.slug ? 'ring-2 ring-emerald-400 border-emerald-400 shadow-xl shadow-emerald-500/25 scale-[1.02]' : ''
          ]"
        >
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-bold text-(--ui-text-highlighted)">{{ p.name }}</h3>
              <span
                class="text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider"
                :class="p.isCurrent ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30' : 'bg-(--ui-bg-accented) text-(--ui-text-muted)'"
              >
                {{ p.badge }}
              </span>
            </div>

            <div class="text-2xl font-black text-(--ui-text-highlighted)">
              {{ p.priceFormatted }}
            </div>

            <p class="text-xs text-(--ui-text-muted) min-h-[32px]">{{ p.description }}</p>

            <div class="pt-3 border-t border-(--ui-border) space-y-2.5 text-xs">
              <div v-for="feat in p.features" :key="feat" class="flex items-center gap-2 text-(--ui-text-highlighted)">
                <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{{ feat }}</span>
              </div>
            </div>
          </div>

          <div class="pt-6 mt-6 border-t border-(--ui-border)">
            <UButton
              v-if="p.isCurrent"
              disabled
              variant="soft"
              color="neutral"
              class="w-full font-bold justify-center"
            >
              Current Active Plan
            </UButton>
            <UButton
              v-else
              :variant="p.hasTrial ? 'solid' : 'outline'"
              color="primary"
              class="w-full font-bold justify-center"
              :class="p.hasTrial ? 'shadow-md shadow-emerald-500/20' : ''"
              :loading="isProcessing"
              @click="handleSubscribe(p.slug, p.hasTrial)"
            >
              <UIcon v-if="p.hasTrial" name="i-lucide-sparkles" class="w-4 h-4 mr-1.5" />
              {{ p.hasTrial ? `Start ${p.trialDurationDays}-Day Free Trial` : (p.price === 0 ? 'Switch to Free Tier' : `Select ${p.name}`) }}
            </UButton>
          </div>
        </div>
      </div>

      <!-- Subscription & Billing History Table Card -->
      <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) p-6 space-y-4 shadow-xs">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-base font-bold text-(--ui-text-highlighted) flex items-center gap-2">
              <UIcon name="i-lucide-receipt" class="w-5 h-5 text-amber-500" />
              Billing & Invoices History
            </h2>
            <p class="text-xs text-(--ui-text-muted) mt-0.5">
              Audit trail of all your subscription activations, plan renewals, and payments.
            </p>
          </div>
          <UButton
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-lucide-refresh-cw"
            :loading="isLoadingHistory"
            @click="loadHistory"
          >
            Refresh
          </UButton>
        </div>

        <!-- Loading State -->
        <div v-if="isLoadingHistory" class="py-12 flex flex-col items-center justify-center gap-3">
          <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-amber-500" />
          <span class="text-xs text-(--ui-text-muted)">Loading billing records...</span>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="subscriptionHistory.length === 0"
          class="py-12 flex flex-col items-center justify-center text-center p-6 border border-dashed border-(--ui-border) rounded-2xl"
        >
          <div class="w-12 h-12 rounded-2xl bg-(--ui-bg-accented) flex items-center justify-center mb-3">
            <UIcon name="i-lucide-file-text" class="w-6 h-6 text-(--ui-text-muted)" />
          </div>
          <h3 class="text-sm font-bold text-(--ui-text-highlighted)">No Invoices or History Yet</h3>
          <p class="text-xs text-(--ui-text-muted) max-w-sm mt-1">
            Your payment references, receipts, and plan change history will appear here once transactions are recorded.
          </p>
        </div>

        <!-- Mobile-First Subscription History Cards List -->
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <div
            v-for="sub in subscriptionHistory"
            :key="sub.subscription_id || sub.id"
            class="p-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) hover:border-amber-500/50 hover:bg-(--ui-bg-accented)/30 transition-all flex flex-col justify-between gap-3 shadow-xs cursor-pointer group"
            @click="openHistoryDetails(sub)"
          >
            <!-- Top Header: Plan Name, Status & Price -->
            <div class="flex items-start justify-between gap-2">
              <div class="space-y-0.5">
                <div class="flex items-center gap-2">
                  <h4 class="font-bold text-sm text-(--ui-text-highlighted) group-hover:text-amber-500 transition">
                    {{ sub.plan_name }}
                  </h4>
                  <span
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
                    :class="[
                      sub.status === 'active'
                        ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                        : sub.status === 'expired'
                        ? 'bg-neutral-500/15 text-neutral-400 border-neutral-500/30'
                        : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                    ]"
                  >
                    {{ sub.status }}
                  </span>
                </div>
                <p class="text-[11px] text-(--ui-text-muted)">
                  {{ new Date(sub.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) }} • {{ new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                </p>
              </div>

              <div class="text-right shrink-0">
                <span class="text-sm font-black font-mono text-(--ui-text-highlighted)">
                  {{ sub.amount === 0 ? 'Free' : `₦${(sub.amount / 100).toLocaleString()}` }}
                </span>
                <div>
                  <span
                    v-if="sub.is_trial"
                    class="inline-flex items-center px-1.5 py-0.2 rounded text-[9px] font-bold bg-purple-500/15 text-purple-400 border border-purple-500/30"
                  >
                    Free Trial
                  </span>
                  <span
                    v-else-if="sub.amount === 0"
                    class="inline-flex items-center px-1.5 py-0.2 rounded text-[9px] font-bold bg-neutral-500/15 text-neutral-400 border border-neutral-500/30"
                  >
                    Free Tier
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  >
                    Paid
                  </span>
                </div>
              </div>
            </div>

            <!-- Description / Note Callout (if present) -->
            <div
              v-if="sub.description"
              class="px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2"
            >
              <UIcon name="i-lucide-message-square" class="w-3.5 h-3.5 mt-0.5 shrink-0 text-amber-500" />
              <div class="min-w-0">
                <span class="text-[10px] uppercase font-bold text-amber-600 dark:text-amber-400 block tracking-wider">Note</span>
                <p class="line-clamp-2 text-[11px] leading-relaxed">{{ sub.description }}</p>
              </div>
            </div>

            <!-- Bottom Row: Copyable ID / Ref & View Details -->
            <div class="pt-2 border-t border-(--ui-border) flex items-center justify-between text-xs gap-2">
              <div class="flex items-center gap-1.5 font-mono text-[11px] text-(--ui-text-muted) min-w-0">
                <span class="text-[10px] text-(--ui-text-dimmed) shrink-0">ID:</span>
                <span class="truncate max-w-[130px] sm:max-w-[170px] select-all">
                  {{ sub.subscription_id || sub.reference || '—' }}
                </span>
                <button
                  v-if="sub.subscription_id || sub.reference"
                  type="button"
                  class="p-1 hover:text-amber-400 text-(--ui-text-muted) transition cursor-pointer rounded"
                  title="Copy Subscription ID"
                  @click.stop="copyToClipboard(sub.subscription_id || sub.reference, 'ID')"
                >
                  <UIcon name="i-lucide-copy" class="w-3.5 h-3.5" />
                </button>
              </div>

              <button
                type="button"
                class="text-[11px] font-bold text-amber-500 hover:text-amber-400 flex items-center gap-0.5 shrink-0"
                @click.stop="openHistoryDetails(sub)"
              >
                Details
                <UIcon name="i-lucide-chevron-right" class="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Subscription History Details Modal -->
    <UModal v-model:open="showHistoryModal" title="Subscription Record Details">
      <template #body>
        <div v-if="selectedHistoryItem" class="p-5 space-y-4">
          <!-- Summary Header -->
          <div class="flex items-center justify-between p-4 rounded-2xl bg-(--ui-bg-accented)/60 border border-(--ui-border)">
            <div>
              <h3 class="text-base font-bold text-(--ui-text-highlighted)">
                {{ selectedHistoryItem.plan_name }}
              </h3>
              <p class="text-xs text-(--ui-text-muted) font-mono">
                Slug: {{ selectedHistoryItem.plan_slug }}
              </p>
            </div>
            <div class="text-right">
              <div class="text-lg font-black font-mono text-(--ui-text-highlighted)">
                {{ selectedHistoryItem.amount === 0 ? 'Free' : `₦${(selectedHistoryItem.amount / 100).toLocaleString()}` }}
              </div>
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
                :class="[
                  selectedHistoryItem.status === 'active'
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : selectedHistoryItem.status === 'expired'
                    ? 'bg-neutral-500/15 text-neutral-400 border-neutral-500/30'
                    : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                ]"
              >
                {{ selectedHistoryItem.status }}
              </span>
            </div>
          </div>

          <!-- Note / Description Highlight -->
          <div v-if="selectedHistoryItem.description" class="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/25 space-y-1">
            <div class="flex items-center gap-1.5 text-xs font-bold text-amber-600 dark:text-amber-400">
              <UIcon name="i-lucide-message-square" class="w-4 h-4" />
              Note / Reference Description
            </div>
            <p class="text-xs text-amber-900 dark:text-amber-200 leading-relaxed">
              {{ selectedHistoryItem.description }}
            </p>
          </div>

          <!-- Details Grid -->
          <div class="space-y-3 text-xs">
            <!-- Full Subscription ID -->
            <div class="p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) flex items-center justify-between gap-3">
              <div class="min-w-0 flex-1">
                <p class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider">Full Subscription ID</p>
                <p class="font-mono text-xs text-(--ui-text-highlighted) select-all break-all mt-0.5">
                  {{ selectedHistoryItem.subscription_id || 'Direct Assignment' }}
                </p>
              </div>
              <UButton
                v-if="selectedHistoryItem.subscription_id"
                size="xs"
                variant="subtle"
                color="neutral"
                icon="i-lucide-copy"
                @click="copyToClipboard(selectedHistoryItem.subscription_id, 'Subscription ID')"
              >
                Copy ID
              </UButton>
            </div>

            <!-- Transaction Reference -->
            <div class="p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) flex items-center justify-between gap-3">
              <div class="min-w-0 flex-1">
                <p class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider">Payment Reference</p>
                <p class="font-mono text-xs text-(--ui-text-highlighted) select-all break-all mt-0.5">
                  {{ selectedHistoryItem.reference || 'None (Direct Activation)' }}
                </p>
              </div>
              <UButton
                v-if="selectedHistoryItem.reference"
                size="xs"
                variant="subtle"
                color="neutral"
                icon="i-lucide-copy"
                @click="copyToClipboard(selectedHistoryItem.reference, 'Payment Reference')"
              >
                Copy Ref
              </UButton>
            </div>

            <!-- 2x2 Key Value Grid -->
            <div class="grid grid-cols-2 gap-3">
              <div class="p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)">
                <p class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider">Plan Type</p>
                <p class="font-bold text-xs text-(--ui-text-highlighted) mt-0.5">
                  {{ selectedHistoryItem.is_trial ? 'Free Trial' : (selectedHistoryItem.amount === 0 ? 'Free Tier' : 'Paid Plan') }}
                </p>
              </div>

              <div class="p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)">
                <p class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider">Payment Channel</p>
                <p class="font-bold text-xs text-(--ui-text-highlighted) mt-0.5 capitalize">
                  {{ selectedHistoryItem.payment_channel || 'System / Auto' }}
                </p>
              </div>

              <div class="p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)">
                <p class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider">Activated Date</p>
                <p class="font-medium text-xs text-(--ui-text-highlighted) mt-0.5">
                  {{ new Date(selectedHistoryItem.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) }}
                </p>
                <p class="text-[10px] text-(--ui-text-muted)">
                  {{ new Date(selectedHistoryItem.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                </p>
              </div>

              <div class="p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)">
                <p class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider">Valid Until / Renewal</p>
                <p class="font-medium text-xs text-(--ui-text-highlighted) mt-0.5">
                  {{ selectedHistoryItem.next_renewal ? new Date(selectedHistoryItem.next_renewal).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Never expires' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template #footer>
        <div class="flex items-center justify-between w-full p-4 border-t border-(--ui-border)">
          <UButton
            variant="ghost"
            color="neutral"
            size="xs"
            @click="showHistoryModal = false"
          >
            Close
          </UButton>
          <UButton
            color="primary"
            variant="soft"
            size="xs"
            icon="i-lucide-clipboard-copy"
            @click="copyFullBillingRecord(selectedHistoryItem)"
          >
            Copy Summary for Support
          </UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
