<script setup lang="ts">
import OfflineFlowDiagram from '~/components/landing/OfflineFlowDiagram.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

useSeoMeta({
  title: 'Why Kluda | Retail Shouldn’t Stop Because The Internet Did',
  description: 'Kluda is built around the realities of retail in emerging markets. Discover our mission to eliminate expensive POS hardware and give every store continuous offline sales power.'
})

const manifestoPoints = [
  {
    icon: 'i-lucide-smartphone',
    title: 'Your device becomes the terminal',
    desc: 'You already carry a powerful computer with a high-resolution camera in your pocket. There is no reason to spend ₦250,000+ on dedicated plastic checkout hardware.'
  },
  {
    icon: 'i-lucide-wifi-off',
    title: 'Your store keeps selling offline',
    desc: 'Network outages should never decide whether your retail store makes money today. Kluda writes every sale locally to your device browser so checkout queues never halt.'
  },
  {
    icon: 'i-lucide-receipt',
    title: 'Your sales stay tracked',
    desc: 'Say goodbye to messy paper ledger books and unrecorded credit sales. Every transaction, discount, customer debt, and cashier shift is audited with crystal clarity.'
  },
  {
    icon: 'i-lucide-refresh-cw',
    title: 'Your data syncs when you’re online',
    desc: 'The exact moment internet connectivity returns, your records back up silently to your secure cloud database without staff needing to touch a single button.'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-4xl mx-auto text-center space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-wider">
          <UIcon name="i-lucide-shield-alert" class="w-3.5 h-3.5" />
          <span>Our Manifesto</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-black text-(--ui-text-highlighted) tracking-tight leading-tight">
          Retail Shouldn't Stop<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            Because The Internet Did.
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Traditional retail software was designed for countries with guaranteed 24/7 internet and stable power. Kluda is built around the real world.
        </p>
      </div>
    </section>

    <section class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="p-8 sm:p-12 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 space-y-8 leading-relaxed text-sm sm:text-base text-(--ui-text-muted)">
        <h2 class="text-2xl sm:text-3xl font-black text-(--ui-text-highlighted)">
          Designed for reality, not assumptions
        </h2>

        <p>
          In retail stores across Lagos, Abuja, Port Harcourt, and emerging markets worldwide, store managers face the same daily headaches: mobile network drops, internet line cuts, sudden power outages, and prohibitive hardware setup fees.
        </p>

        <p>
          When traditional cloud POS software loses internet connection, the screen freezes, cashier registers lock up, and customers leave items sitting on the counter.
        </p>

        <div class="p-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-(--ui-text-highlighted) font-semibold text-base">
          "We founded Kluda on a simple thesis: retail checkout software must be offline-first by default, operate on device battery power, and require zero proprietary hardware purchases."
        </div>

        <p>
          By storing your store catalog in local browser persistence and utilizing your phone camera as a high-speed barcode reader, your cashiers can ring up 100 customers during a 2-hour internet outage without dropping a single sale.
        </p>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          The 4 Pillars of Kluda
        </h2>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div
          v-for="pillar in manifestoPoints"
          :key="pillar.title"
          class="p-8 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 hover:border-emerald-500/30 transition group"
        >
          <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 mb-6 group-hover:scale-110 transition">
            <UIcon :name="pillar.icon" class="w-6 h-6" />
          </div>
          <h3 class="text-xl font-extrabold text-(--ui-text-highlighted) mb-3">
            {{ pillar.title }}
          </h3>
          <p class="text-xs sm:text-sm text-(--ui-text-muted) leading-relaxed">
            {{ pillar.desc }}
          </p>
        </div>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <OfflineFlowDiagram />
    </section>

    <CtaSection />
  </div>
</template>
