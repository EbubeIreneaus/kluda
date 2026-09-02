<script setup lang="ts">
import { ref } from 'vue'

const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'

const activeIndustry = ref('supermarket')

const industries = [
  {
    id: 'supermarket',
    name: 'Supermarkets & Groceries',
    icon: 'i-lucide-shopping-bag',
    headline: 'Eliminate Long Checkout Queues & Hardware Failure',
    description: 'During peak morning and evening rushes, system lag costs customers. Kluda allows cashiers to scan products rapidly directly from their tablets or smartphones with zero checkout delay.',
    benefits: [
      'Line-busting: Deploy mobile cashiers anywhere in the store',
      'Barcode generator for loose produce and packed goods',
      'Multi-counter synchronized stock counts',
      'Instant thermal receipt printing via Bluetooth or USB'
    ],
    metric: 'Fast Mobile Checkout'
  },
  {
    id: 'pharmacy',
    name: 'Pharmacies & Chemists',
    icon: 'i-lucide-pill',
    headline: 'Track Prescriptions, Frequent Patients & Customer Balances',
    description: 'Provide exceptional patient care with instant customer profile lookups, automated credit and debt ledgers, and real-time inventory deductions for high-value medication.',
    benefits: [
      'Customer debt ledger with automated balance tracking',
      'Partial payments & installment settlements during checkout',
      'Low-stock alerts before essential medicines run out',
      'Staff permission controls to prevent unauthorized price changes'
    ],
    metric: '100% Debt Accountability'
  },
  {
    id: 'boutique',
    name: 'Fashion & Boutiques',
    icon: 'i-lucide-sparkles',
    headline: 'Modern Mobile POS for Elegant Retail Spaces',
    description: 'No bulky cash registers cluttering your aesthetic counters. Walk around the sales floor, help customers try on outfits, and ring up sales directly from your phone.',
    benefits: [
      'Sleek mobile cashier experience on iPhones, Androids, or iPads',
      'Customer purchase histories for loyalty recommendations',
      'Multi-branch stock visibility across your boutique locations',
      'Custom branding on digital and thermal receipts'
    ],
    metric: '₦0 Heavy Register Clutter'
  },
  {
    id: 'hardware',
    name: 'Electronics & Hardware',
    icon: 'i-lucide-wrench',
    headline: 'Manage Complex Catalogs & Trade Credits',
    description: 'Handle thousands of SKUs, spare parts, and contractor accounts with flexible customer ledgers and instant barcode recognition.',
    benefits: [
      'Fast search across local inventory items',
      'Credit ledger for contractors and frequent trade buyers',
      'Itemized invoices and receipt reprint history',
      'Role-based access locks margins from junior clerks'
    ],
    metric: 'Instant SKU Search'
  },
  {
    id: 'kiosk',
    name: 'Pop-ups & Food Trucks',
    icon: 'i-lucide-store',
    headline: 'Full POS Capabilities Where Wi-Fi Does Not Reach',
    description: 'Selling at weekend trade fairs, festivals, or pop-up markets? Kluda operates offline from battery-powered phones and auto-syncs when you reconnect.',
    benefits: [
      'No Wi-Fi or cellular network required during the event',
      'Runs on standard mobile batteries all day long',
      'Quick cash, transfer, and split payment recording',
      'Automatic end-of-day sales reconciliation'
    ],
    metric: '100% Battery-Powered Operation'
  }
]
</script>

<template>
  <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/60 p-6 sm:p-10 shadow-2xl backdrop-blur-xl">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 mb-3">
        <UIcon name="i-lucide-layout-grid" class="w-4 h-4" />
        <span>Tailored For Every Retail Model</span>
      </div>
      <h3 class="text-2xl sm:text-3xl font-extrabold text-(--ui-text-highlighted) tracking-tight">
        Built for Your Specific Retail Workflow
      </h3>
      <p class="text-sm text-(--ui-text-muted) mt-2">
        Whether you manage a high-volume supermarket or a single boutique kiosk, Kluda adapts to your counter.
      </p>
    </div>

    <div class="flex flex-wrap items-center justify-center gap-2 mb-8">
      <button
        v-for="ind in industries"
        :key="ind.id"
        @click="activeIndustry = ind.id"
        class="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer border"
        :class="activeIndustry === ind.id ? 'bg-emerald-500 text-slate-950 border-emerald-500 shadow-md shadow-emerald-500/20' : 'bg-(--ui-bg-elevated) text-(--ui-text-muted) border-(--ui-border) hover:text-(--ui-text-highlighted)'"
      >
        <UIcon :name="ind.icon" class="w-4 h-4" />
        <span>{{ ind.name }}</span>
      </button>
    </div>

    <template v-for="ind in industries" :key="ind.id">
      <div
        v-if="activeIndustry === ind.id"
        class="grid grid-cols-1 lg:grid-cols-12 gap-8 p-6 sm:p-8 rounded-2xl bg-(--ui-bg)/80 border border-(--ui-border) items-center"
      >
        <div class="lg:col-span-7 space-y-4">
          <div class="inline-block px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-500 font-mono text-xs font-bold">
            {{ ind.metric }}
          </div>
          <h4 class="text-xl sm:text-2xl font-bold text-(--ui-text-highlighted)">
            {{ ind.headline }}
          </h4>
          <p class="text-sm text-(--ui-text-muted) leading-relaxed">
            {{ ind.description }}
          </p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4 border-t border-(--ui-border)">
            <div v-for="b in ind.benefits" :key="b" class="flex items-start gap-2 text-xs font-medium text-(--ui-text)">
              <UIcon name="i-lucide-check-circle-2" class="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              <span>{{ b }}</span>
            </div>
          </div>
        </div>

        <div class="lg:col-span-5 bg-gradient-to-br from-emerald-950/60 to-slate-950 p-6 rounded-2xl border border-emerald-500/20 text-white flex flex-col justify-between min-h-[220px]">
          <div>
            <div class="flex items-center gap-2 text-emerald-400 text-xs font-mono mb-2">
              <UIcon name="i-lucide-store" class="w-4 h-4" />
              <span>Ready for immediate deployment</span>
            </div>
            <h5 class="text-base font-bold text-white mb-2">Set up in under 60 seconds</h5>
            <p class="text-xs text-slate-400">
              No hardware technician needed. Open the web link on your phone or PC, log in your cashier, and start ringing up transactions immediately.
            </p>
          </div>

          <a :href="`${posUrl}/auth/register`" class="mt-6">
            <button class="w-full py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition flex items-center justify-center gap-2 cursor-pointer shadow-md shadow-emerald-500/20">
              <UIcon name="i-lucide-rocket" class="w-4 h-4" />
              Start Free for {{ ind.name }}
            </button>
          </a>
        </div>
      </div>
    </template>
  </div>
</template>
