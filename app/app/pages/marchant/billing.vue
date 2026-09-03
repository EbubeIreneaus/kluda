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

// Dynamically extract unique intervals present in availablePlans (excluding standalone trial)
const availableIntervals = computed(() => {
  if (!availablePlans.value || availablePlans.value.length === 0) {
    return ['monthly', 'yearly']
  }
  const cleanPlans = availablePlans.value.filter((p: any) => p.slug !== 'trial')
  const intervals = Array.from(new Set(cleanPlans.map((p: any) => p.interval || 'monthly')))
  return intervals.length > 0 ? intervals : ['monthly']
})

// Auto-select first available interval if selectedInterval is not in list
watch(availableIntervals, (intervals) => {
  if (intervals.length > 0 && !intervals.includes(selectedInterval.value)) {
    selectedInterval.value = intervals[0]
  }
}, { immediate: true })

// Fallback plans if backend plans not populated yet
const defaultPlans = [
  {
    slug: 'starter',
    name: 'Starter Tier',
    price: 0,
    interval: 'monthly',
    has_trial: false,
    trial_duration_days: 0,
    badge: 'Basic',
    description: 'Essential POS counter for single-terminal retail operations.',
    features: [
      '1 Store Branch',
      'Up to 100 Products',
      '500 Monthly Sales',
      'Offline Barcode Scanning & Sales',
      'Standard Thermal Receipts'
    ]
  },
  {
    slug: 'growth',
    name: 'Merchant Growth',
    price: 1500000, // 15,000 NGN in kobo
    interval: 'monthly',
    has_trial: true,
    trial_duration_days: 14,
    badge: 'Popular',
    description: 'Full multi-branch retail suite with real-time cloud synchronization.',
    features: [
      '3 Store Branches',
      'Up to 2,000 Products',
      '10,000 Monthly Sales',
      'Real-time Multi-Device WebSocket Sync',
      'Customer Debt & Credit Ledger',
      'Full Sales Analytics & Reports',
      'Web Push Notifications'
    ]
  },
  {
    slug: 'enterprise',
    name: 'Enterprise Mesh',
    price: 4500000, // 45,000 NGN in kobo
    interval: 'monthly',
    has_trial: false,
    trial_duration_days: 0,
    badge: 'Custom',
    description: 'High-throughput retail chains with automated inventory reconciliation.',
    features: [
      'Unlimited Store Branches',
      'Unlimited Products',
      'Unlimited Monthly Sales',
      'Dedicated Cloud Cluster & SLA',
      'Multi-Warehouse Inventory Transfers',
      'Priority 24/7 Support Escalation'
    ]
  }
]

const displayPlans = computed(() => {
  const rawList = (availablePlans.value && availablePlans.value.length > 0) ? availablePlans.value : defaultPlans
  // Standalone trial is NEVER shown
  const plans = rawList.filter((p: any) => p.slug !== 'trial')
  
  // Filter by selectedInterval if availableIntervals has multiple
  const filtered = plans.filter((p: any) => {
    const planInterval = (p.interval || 'monthly').toLowerCase()
    return planInterval === selectedInterval.value.toLowerCase()
  })

  const targetPlans = filtered.length > 0 ? filtered : plans

  return targetPlans.map((p: any) => {
    const isCurrent = currentPlan.value.slug === p.slug
    const priceNaira = p.price / 100
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

      <!-- Plan Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
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

        <!-- History Table -->
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="border-b border-(--ui-border) text-(--ui-text-muted) font-semibold">
                <th class="py-3 px-3">Date</th>
                <th class="py-3 px-3">Plan</th>
                <th class="py-3 px-3">Type</th>
                <th class="py-3 px-3">Amount</th>
                <th class="py-3 px-3">Status</th>
                <th class="py-3 px-3">Reference</th>
                <th class="py-3 px-3">Valid Until</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-(--ui-border)">
              <tr
                v-for="sub in subscriptionHistory"
                :key="sub.subscription_id || sub.id"
                class="hover:bg-(--ui-bg-accented)/50 transition"
              >
                <td class="py-3 px-3 font-medium text-(--ui-text-highlighted) whitespace-nowrap">
                  {{ new Date(sub.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) }}
                  <div class="text-[10px] text-(--ui-text-muted)">
                    {{ new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                  </div>
                </td>
                <td class="py-3 px-3 font-bold text-(--ui-text-highlighted) whitespace-nowrap">
                  {{ sub.plan_name }}
                </td>
                <td class="py-3 px-3 whitespace-nowrap">
                  <span
                    v-if="sub.is_trial"
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/15 text-purple-400 border border-purple-500/30"
                  >
                    Free Trial
                  </span>
                  <span
                    v-else-if="sub.amount === 0"
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-neutral-500/15 text-neutral-400 border border-neutral-500/30"
                  >
                    Free Tier
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  >
                    Paid Plan
                  </span>
                </td>
                <td class="py-3 px-3 font-bold text-(--ui-text-highlighted) whitespace-nowrap">
                  {{ sub.amount === 0 ? 'Free' : `₦${(sub.amount / 100).toLocaleString()}` }}
                </td>
                <td class="py-3 px-3 whitespace-nowrap">
                  <span
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                    :class="[
                      sub.status === 'active'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : sub.status === 'expired'
                        ? 'bg-neutral-500/15 text-neutral-400 border border-neutral-500/30'
                        : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                    ]"
                  >
                    {{ sub.status }}
                  </span>
                </td>
                <td class="py-3 px-3 font-mono text-[11px] text-(--ui-text-muted) whitespace-nowrap">
                  {{ sub.reference || (sub.subscription_id ? String(sub.subscription_id).slice(0, 12) + '...' : '—') }}
                </td>
                <td class="py-3 px-3 text-(--ui-text-muted) whitespace-nowrap">
                  {{ sub.next_renewal ? new Date(sub.next_renewal).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
