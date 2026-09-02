<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({ layout: 'marchant' })

const auth = useAuthStore()
const toast = useToast()

const billingPeriod = ref<'monthly' | 'yearly'>('monthly')

const plans = [
  {
    name: 'Starter Tier',
    priceMonthly: 'Free',
    priceYearly: 'Free',
    badge: 'Basic',
    description: 'Essential POS counter for single-terminal retail operations.',
    features: [
      '1 Store Branch',
      'Up to 2 Cashier Accounts',
      'Offline Barcode Scanning & Sales',
      'Standard Thermal Receipts',
      'Local IndexedDB Caching'
    ],
    isCurrent: false,
    color: 'neutral'
  },
  {
    name: 'Merchant Growth',
    priceMonthly: '₦15,000 / mo',
    priceYearly: '₦150,000 / yr',
    badge: 'Active Early Access',
    description: 'Full multi-branch retail suite with real-time cloud synchronization.',
    features: [
      'Unlimited Store Branches',
      'Unlimited Cashiers & Managers',
      'Offline Multi-Store IndexedDB Isolation',
      'Real-time Multi-Device WebSocket Sync',
      'Customer Debt & Credit Ledger',
      'Full Sales Analytics & Reports',
      'Direct WhatsApp & Web Push Notifications'
    ],
    isCurrent: true,
    color: 'amber'
  },
  {
    name: 'Enterprise Mesh',
    priceMonthly: '₦45,000 / mo',
    priceYearly: '₦450,000 / yr',
    badge: 'Custom',
    description: 'High-throughput retail chains with automated inventory reconciliation.',
    features: [
      'Everything in Merchant Growth',
      'Dedicated Cloud Cluster & SLA',
      'Multi-Warehouse Inventory Transfers',
      'Custom ERP & Accounting Connectors',
      'Priority 24/7 Support Escalation'
    ],
    isCurrent: false,
    color: 'emerald'
  }
]

function handleUpgrade(planName: string) {
  toast.add({
    title: `${planName} Selected`,
    description: 'Payment gateway integration is ready for deployment.',
    color: 'success'
  })
}
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

    <div class="p-6 rounded-3xl border border-amber-500/30 bg-amber-500/5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="space-y-1">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold text-amber-400">Current Subscription</span>
          <span class="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            Active Early Access
          </span>
        </div>
        <h3 class="text-xl font-extrabold text-(--ui-text-highlighted)">Merchant Growth Plan</h3>
        <p class="text-xs text-(--ui-text-muted)">
          Includes unlimited retail branches, staff cashier accounts, offline sync, and real-time ledger.
        </p>
      </div>

      <div class="flex items-center gap-2 self-start sm:self-auto">
        <div class="text-right hidden md:block pr-2">
          <p class="text-xs text-(--ui-text-dimmed)">Next Renewal</p>
          <p class="text-xs font-bold text-(--ui-text-highlighted)">Standard Early Access</p>
        </div>
      </div>
    </div>

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

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
        <div
          v-for="plan in plans"
          :key="plan.name"
          class="rounded-3xl p-6 border bg-(--ui-bg-elevated) flex flex-col justify-between shadow-xs transition"
          :class="plan.isCurrent ? 'border-amber-500/60 shadow-lg shadow-amber-500/10' : 'border-(--ui-border)'"
        >
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-bold text-(--ui-text-highlighted)">{{ plan.name }}</h3>
              <span
                class="text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider"
                :class="plan.isCurrent ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-(--ui-bg-accented) text-(--ui-text-muted)'"
              >
                {{ plan.badge }}
              </span>
            </div>

            <div class="text-2xl font-black text-(--ui-text-highlighted)">
              {{ billingPeriod === 'monthly' ? plan.priceMonthly : plan.priceYearly }}
            </div>

            <p class="text-xs text-(--ui-text-muted)">{{ plan.description }}</p>

            <div class="pt-3 border-t border-(--ui-border) space-y-2.5 text-xs">
              <div v-for="feat in plan.features" :key="feat" class="flex items-center gap-2 text-(--ui-text-highlighted)">
                <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{{ feat }}</span>
              </div>
            </div>
          </div>

          <div class="pt-6 mt-6 border-t border-(--ui-border)">
            <UButton
              v-if="plan.isCurrent"
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
              @click="handleUpgrade(plan.name)"
            >
              Select {{ plan.name }}
            </UButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
