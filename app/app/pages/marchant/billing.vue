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
  isLoading,
  fetchCurrentSubscription,
  fetchAvailablePlans,
  subscribePlan,
  cancelPlan,
  isOwner
} = useSubscription()

const isProcessing = ref(false)
const billingPeriod = ref<'monthly' | 'yearly'>('monthly')

// Fallback plans if backend plans not populated yet
const defaultPlans = [
  {
    slug: 'starter',
    name: 'Starter Tier',
    price: 0,
    priceMonthly: 'Free',
    priceYearly: 'Free',
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
    priceMonthly: '₦15,000 / mo',
    priceYearly: '₦150,000 / yr',
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
    priceMonthly: '₦45,000 / mo',
    priceYearly: '₦450,000 / yr',
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
  if (availablePlans.value && availablePlans.value.length > 0) {
    return availablePlans.value.map((p) => {
      const isCurrent = currentPlan.value.slug === p.slug
      const priceNaira = p.price / 100
      return {
        slug: p.slug,
        name: p.name,
        price: p.price,
        priceMonthly: p.price === 0 ? 'Free' : `₦${priceNaira.toLocaleString()} / mo`,
        priceYearly: p.price === 0 ? 'Free' : `₦${(priceNaira * 10).toLocaleString()} / yr`,
        badge: isCurrent ? 'Active' : (p.price > 2000000 ? 'Enterprise' : 'Available'),
        description: p.description || 'Retail point-of-sale tier with automated inventory sync.',
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
  }

  return defaultPlans.map(p => ({
    ...p,
    isCurrent: currentPlan.value.slug === p.slug
  }))
})

async function handleSubscribe(planSlug: string) {
  isProcessing.value = true
  try {
    const res = await subscribePlan(planSlug)
    if (res.redirect_url) {
      toast.add({
        title: 'Redirecting to Checkout',
        description: 'Forwarding to Paystack secure payment gateway...',
        color: 'info'
      })
      window.location.href = res.redirect_url
    } else if (res.status === 'active') {
      toast.add({
        title: 'Subscription Updated',
        description: res.message || 'Plan activated successfully.',
        color: 'success'
      })
    }
  } catch (err: any) {
    toast.add({
      title: 'Subscription Error',
      description: err?.data?.detail || err?.message || 'Unable to initialize subscription.',
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

onMounted(async () => {
  await Promise.all([fetchCurrentSubscription(), fetchAvailablePlans()])

  if (route.query.reference) {
    toast.add({
      title: 'Payment Confirmed',
      description: 'Your subscription status has been synced with Paystack.',
      color: 'success'
    })
  }
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
          <span class="text-sm font-bold text-amber-400">Current Subscription</span>
          <span
            :class="[
              'text-[10px] px-2.5 py-0.5 rounded-full font-bold border',
              status === 'ACTIVE'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : (status === 'DUE' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' : 'bg-rose-500/20 text-rose-300 border-rose-500/30')
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

        <div class="flex items-center p-1 bg-(--ui-bg-elevated) border border-(--ui-border) rounded-2xl">
          <button
            type="button"
            class="px-4 py-1.5 rounded-xl text-xs font-bold transition"
            :class="billingPeriod === 'monthly' ? 'bg-amber-500 text-slate-950 shadow-xs' : 'text-(--ui-text-muted)'"
            @click="billingPeriod = 'monthly'"
          >
            Monthly
          </button>
          <button
            type="button"
            class="px-4 py-1.5 rounded-xl text-xs font-bold transition"
            :class="billingPeriod === 'yearly' ? 'bg-amber-500 text-slate-950 shadow-xs' : 'text-(--ui-text-muted)'"
            @click="billingPeriod = 'yearly'"
          >
            Yearly (Save 15%)
          </button>
        </div>
      </div>

      <!-- Plan Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
        <div
          v-for="p in displayPlans"
          :key="p.slug"
          class="rounded-3xl p-6 border bg-(--ui-bg-elevated) flex flex-col justify-between shadow-xs transition relative"
          :class="p.isCurrent ? 'border-amber-500/60 shadow-lg shadow-amber-500/10' : 'border-(--ui-border)'"
        >
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-bold text-(--ui-text-highlighted)">{{ p.name }}</h3>
              <span
                class="text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider"
                :class="p.isCurrent ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-(--ui-bg-accented) text-(--ui-text-muted)'"
              >
                {{ p.badge }}
              </span>
            </div>

            <div class="text-2xl font-black text-(--ui-text-highlighted)">
              {{ billingPeriod === 'monthly' ? p.priceMonthly : p.priceYearly }}
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
              variant="outline"
              color="primary"
              class="w-full font-bold justify-center"
              :loading="isProcessing"
              @click="handleSubscribe(p.slug)"
            >
              {{ p.slug === 'trial' ? 'Start 30-Day Free Trial' : (p.price === 0 ? 'Switch to Free Tier' : `Select ${p.name}`) }}
            </UButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
