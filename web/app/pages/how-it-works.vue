<script setup lang="ts">
import ArchitectureFlow from '~/components/landing/ArchitectureFlow.vue'
import BarcodeSandbox from '~/components/landing/BarcodeSandbox.vue'
import OfflineFlowDiagram from '~/components/landing/OfflineFlowDiagram.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

useSeoMeta({
  title: 'How Kluda Works | Offline Architecture & Phone Barcode Scanner',
  description: 'Understand how Kluda uses phone camera barcode scanning, browser-local database persistence, and automatic background reconciliation to keep retail checkout running without internet.'
})

const deepDiveFeatures = [
  {
    icon: 'i-lucide-scan-barcode',
    title: 'Phone Camera Barcode Scanning',
    subtitle: 'Zero expensive laser scanner hardware',
    desc: 'Kluda turns your phone or tablet camera into a rapid barcode scanner. With audio confirmation beeps and continuous multi-scan support, cashiers scan FMCG barcodes (EAN-13, UPC, Code 128, QR) directly from the device screen.'
  },
  {
    icon: 'i-lucide-database',
    title: 'Browser-Local Database Persistence',
    subtitle: 'Reliable storage on the device',
    desc: 'When your cashiers open Kluda, your product catalog and price list replicate to high-speed local device storage. Every checkout item, quantity change, and debt entry is written locally with zero server round-trip latency.'
  },
  {
    icon: 'i-lucide-refresh-cw',
    title: 'Automated WebSocket Multi-Register Sync',
    subtitle: 'Real-time multi-counter alignment',
    desc: 'When connected to the internet, registers communicate through encrypted WebSockets. When Counter 1 sells the last 2 units of an item, Counter 2 and Counter 3 reflect the stock reduction instantly.'
  },
  {
    icon: 'i-lucide-book-open',
    title: 'Customer Debt & Credit Ledger',
    subtitle: 'No more lost paper notebooks',
    desc: 'Record frequent customer credit sales directly at the checkout point. Track partial repayments, issue printed balance receipts, and see customer debt summaries in your Owner Portal.'
  },
  {
    icon: 'i-lucide-shield-check',
    title: 'Staff Roles & Cashier Shift Auditing',
    subtitle: 'Granular permissions and accountability',
    desc: 'Assign short staff codes (e.g. STF1001) with dedicated permissions. Control who can edit inventory prices, issue discounts, or view daily revenue totals while keeping your cash registers secure.'
  },
  {
    icon: 'i-lucide-printer',
    title: 'Thermal Receipt Printing',
    subtitle: 'Standard 58mm & 80mm ESC/POS support',
    desc: 'Print professional receipts using standard portable Bluetooth thermal printers, USB desktop receipt printers, or generate instant digital receipts for customers.'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-4xl mx-auto text-center space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-wider">
          <UIcon name="i-lucide-cpu" class="w-3.5 h-3.5" />
          <span>Product Architecture</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-black text-(--ui-text-highlighted) tracking-tight">
          How Kluda Keeps Selling<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            When The Internet Doesn't
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Explore how local browser persistence, phone camera barcode scanning, and silent background cloud reconciliation replace expensive legacy retail POS computers.
        </p>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <OfflineFlowDiagram />
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
          <UIcon name="i-lucide-layers" class="w-3.5 h-3.5" />
          <span>Core Capabilities</span>
        </div>
        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          Engineered for retail resilience
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
            <h3 class="text-lg font-extrabold text-(--ui-text-highlighted) mt-1 mb-3">
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
      <ArchitectureFlow />
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <BarcodeSandbox />
    </section>

    <CtaSection />
  </div>
</template>
