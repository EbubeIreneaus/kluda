<script setup lang="ts">
import OfflineFlowDiagram from '~/components/landing/OfflineFlowDiagram.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

useSeoMeta({
  title: 'POS for Pharmacies & Chemists | Kluda',
  description: 'Manage medicine inventory, patient credit ledgers, and fast offline prescription checkout with Kluda for pharmacies and chemists.'
})

const pharmacyBenefits = [
  {
    icon: 'i-lucide-book-open',
    title: 'Customer Credit & Debt Ledger',
    desc: 'Record frequent patient credit sales, track outstanding balances, and record partial repayments directly during checkout.'
  },
  {
    icon: 'i-lucide-pill',
    title: 'Medication Inventory Tracking',
    desc: 'Automatic real-time stock deductions on single packs and wholesale cartons with low-stock warnings before essential drugs run out.'
  },
  {
    icon: 'i-lucide-receipt',
    title: 'Itemized Balance Receipts',
    desc: 'Print customer balance receipts displaying previous debt, current purchase, amount paid, and remaining balance.'
  },
  {
    icon: 'i-lucide-shield-check',
    title: 'Staff Role Permissions',
    desc: 'Prevent unauthorized drug price modifications or discount overrides by configuring manager vs cashier permissions.'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-4xl mx-auto text-center space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-wider">
          <UIcon name="i-lucide-pill" class="w-3.5 h-3.5" />
          <span>Pharmacies & Chemists</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-black text-(--ui-text-highlighted) tracking-tight">
          Track Sales & Patient Credit<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            Without Paper Ledgers
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Say goodbye to lost credit record books. Kluda tracks every customer credit balance, partial repayment, and medicine stock change right at the counter.
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <NuxtLink
            to="/register"
            class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-black text-sm shadow-xl shadow-emerald-500/25 transition active:scale-95"
          >
            <span>Start Selling Free</span>
            <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
          </NuxtLink>
        </div>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
          v-for="b in pharmacyBenefits"
          :key="b.title"
          class="p-6 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 hover:border-emerald-500/30 transition"
        >
          <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 mb-4">
            <UIcon :name="b.icon" class="w-5 h-5" />
          </div>
          <h3 class="text-base font-bold text-(--ui-text-highlighted) mb-2">{{ b.title }}</h3>
          <p class="text-xs text-(--ui-text-muted) leading-relaxed">{{ b.desc }}</p>
        </div>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <OfflineFlowDiagram />
    </section>

    <CtaSection />
  </div>
</template>
