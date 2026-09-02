<script setup lang="ts">
import ArchitectureFlow from '~/components/landing/ArchitectureFlow.vue'
import BarcodeSandbox from '~/components/landing/BarcodeSandbox.vue'
import OfflineFlowDiagram from '~/components/landing/OfflineFlowDiagram.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

useSeoMeta({
  title: 'How Kluda Works | Simple Store Management, Stock Tracking & Anti-Theft',
  description: 'Learn how Kluda protects your retail profit, tracks inventory in real time, manages customer debts, and turns your phone into a complete checkout counter.'
})

const deepDiveFeatures = [
  {
    icon: 'i-lucide-shield-check',
    title: 'Cashier Shift Auditing & Anti-Theft',
    subtitle: 'Every sale tied to a cashier',
    desc: 'Assign short staff codes (e.g. STF1001) with dedicated permissions. Control who can issue discounts or view profit totals, and reconcile cash collected at the end of each shift.'
  },
  {
    icon: 'i-lucide-boxes',
    title: 'Live Stock & Inventory Tracking',
    subtitle: 'Automatic deduction on every sale',
    desc: 'When an item sells, stock drops instantly across the system. Know your fast-moving items, remaining cartons, and low-stock alerts before your shelf goes empty.'
  },
  {
    icon: 'i-lucide-book-open',
    title: 'Customer Debt & Credit Ledger',
    subtitle: 'No more lost paper notebooks',
    desc: 'Record customer credit sales directly at checkout in two taps. Track partial repayments, issue printed balance receipts, and see total outstanding debts in your Owner Portal.'
  },
  {
    icon: 'i-lucide-scan-barcode',
    title: 'Phone Camera Barcode Scanning',
    subtitle: 'Zero expensive laser scanner hardware',
    desc: 'Kluda turns your phone or tablet camera into a rapid barcode scanner. With audio confirmation beeps and continuous multi-scan support, cashiers scan FMCG barcodes directly from the device screen.'
  },
  {
    icon: 'i-lucide-printer',
    title: 'Thermal Receipt Printing',
    subtitle: 'Standard 58mm & 80mm ESC/POS support',
    desc: 'Print professional receipts using standard portable Bluetooth thermal printers, USB desktop receipt printers, or generate instant digital receipts for customers.'
  },
  {
    icon: 'i-lucide-database',
    title: '100% Reliable Local Engine',
    subtitle: 'Instant speed under any network conditions',
    desc: 'Kluda stores your catalog locally on the device. Checkout is instant and never freezes, and all sales records sync silently to the cloud whenever internet is available.'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-4xl mx-auto text-center space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-wider">
          <UIcon name="i-lucide-cpu" class="w-3.5 h-3.5" />
          <span>How It Works</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-black text-(--ui-text-highlighted) tracking-tight">
          Supermarket Control In Your Pocket.<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            Simple. Theft-Proof. Complete.
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          See how Kluda replaces messy paper books and expensive computer hardware with a modern sales register that protects your profits every day.
        </p>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
          <UIcon name="i-lucide-layers" class="w-3.5 h-3.5" />
          <span>Core Capabilities</span>
        </div>
        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          Everything your retail store needs to thrive
        </h2>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div
          v-for="feat in deepDiveFeatures"
          :key="feat.title"
          class="p-8 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 hover:border-emerald-500/30 transition group flex flex-col justify-between"
        >
          <div>
            <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 mb-6 group-hover:scale-110 transition">
              <UIcon :name="feat.icon" class="w-6 h-6" />
            </div>
            <span class="text-xs font-bold uppercase tracking-wider text-emerald-500">{{ feat.subtitle }}</span>
            <h3 class="text-xl font-extrabold text-(--ui-text-highlighted) mt-1 mb-3">
              {{ feat.title }}
            </h3>
            <p class="text-xs sm:text-sm text-(--ui-text-muted) leading-relaxed">
              {{ feat.desc }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <OfflineFlowDiagram />
    </section>

    <CtaSection />
  </div>
</template>
