<script setup lang="ts">
import OfflineFlowDiagram from '~/components/landing/OfflineFlowDiagram.vue'
import InteractivePosDemo from '~/components/landing/InteractivePosDemo.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

useSeoMeta({
  title: 'POS for Supermarkets & Mini-Marts | Kluda',
  description: 'Fast, line-busting retail POS for supermarkets and grocery stores. Scan barcodes with phone cameras and keep checking out queues even during internet outages.'
})

const benefits = [
  {
    icon: 'i-lucide-users',
    title: 'Line-Busting Mobile Cashiers',
    desc: 'Deploy extra cashier counters on staff smartphones instantly during peak morning and evening rushes to eliminate long queues.'
  },
  {
    icon: 'i-lucide-scan-barcode',
    title: 'Phone Camera Barcode Scanning',
    desc: 'Scan EAN-13 packaged goods with continuous audio beep confirmation without purchasing dedicated handheld barcode scanners.'
  },
  {
    icon: 'i-lucide-refresh-cw',
    title: 'Multi-Counter Synchronized Stock',
    desc: 'When Counter 1 sells an item, shelf stock updates across all other cashier registers in real time to prevent overselling.'
  },
  {
    icon: 'i-lucide-printer',
    title: 'Instant Thermal Receipts',
    desc: 'Connect standard 58mm or 80mm ESC/POS Bluetooth and USB thermal printers for instant customer checkout receipts.'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-4xl mx-auto text-center space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-wider">
          <UIcon name="i-lucide-shopping-bag" class="w-3.5 h-3.5" />
          <span>Supermarkets & Mini-Marts</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-black text-(--ui-text-highlighted) tracking-tight">
          Keep Checkout Queues Moving<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            Even When Network Drops
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Never let a network glitch slow down your grocery checkout. Equip your cashiers with high-speed camera scanning on the phones they already have.
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
          v-for="b in benefits"
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

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <InteractivePosDemo />
    </section>

    <CtaSection />
  </div>
</template>
