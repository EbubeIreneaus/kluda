<script setup lang="ts">
import IndustrySolutions from '~/components/landing/IndustrySolutions.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

useSeoMeta({
  title: 'Retail Store Solutions | Kluda POS',
  description: 'Explore tailored retail solutions for Supermarkets, Pharmacies, Boutiques, Electronics, and Multi-Branch outlets in Nigeria.'
})

const categories = [
  {
    icon: 'i-lucide-shopping-bag',
    title: 'Supermarkets & Mini-Marts',
    headline: 'Keep selling when network goes down',
    desc: 'Line-busting mobile cashier counters, instant phone camera barcode scanning, and multi-counter live shelf stock sync.',
    to: '/solutions/supermarkets'
  },
  {
    icon: 'i-lucide-pill',
    title: 'Pharmacies & Chemists',
    headline: 'Track customer credit & medicine inventory',
    desc: 'Automated customer debt ledgers, partial payment tracking at checkout, and low-stock alerts on essential medications.',
    to: '/solutions/pharmacies'
  },
  {
    icon: 'i-lucide-shirt',
    title: 'Fashion & Boutiques',
    headline: 'Turn staff smartphones into checkout registers',
    desc: 'Ring up sales right on the shop floor without bulky register computers cluttering your store counter.',
    to: '/solutions/boutiques'
  },
  {
    icon: 'i-lucide-store',
    title: 'Multi-Branch Retailers',
    headline: 'Keep inventory synchronized across locations',
    desc: 'Open and oversee multiple branch locations, monitor live daily sales, and manage cashier staff from one Owner Portal.',
    to: '/solutions/supermarkets'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-4xl mx-auto text-center space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-wider">
          <UIcon name="i-lucide-layout-grid" class="w-3.5 h-3.5" />
          <span>Industry Solutions</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-black text-(--ui-text-highlighted) tracking-tight">
          Tailored For Your<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            Specific Retail Category
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Whether you run a fast-paced mini-mart or a neighborhood pharmacy, Kluda adapts to your daily checkout workflow.
        </p>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <NuxtLink
          v-for="cat in categories"
          :key="cat.title"
          :to="cat.to"
          class="p-8 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 hover:border-emerald-500/40 hover:bg-(--ui-bg-elevated) transition group flex flex-col justify-between"
        >
          <div>
            <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 mb-6 group-hover:scale-110 transition">
              <UIcon :name="cat.icon" class="w-6 h-6" />
            </div>
            <span class="text-xs font-bold uppercase tracking-wider text-emerald-500">{{ cat.title }}</span>
            <h3 class="text-xl font-extrabold text-(--ui-text-highlighted) mt-1 mb-3">
              {{ cat.headline }}
            </h3>
            <p class="text-xs sm:text-sm text-(--ui-text-muted) leading-relaxed">
              {{ cat.desc }}
            </p>
          </div>

          <div class="pt-6 mt-6 border-t border-(--ui-border) flex items-center justify-between text-xs font-bold text-emerald-500">
            <span>Explore {{ cat.title }} Solution</span>
            <UIcon name="i-lucide-arrow-right" class="w-4 h-4 group-hover:translate-x-1 transition" />
          </div>
        </NuxtLink>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <IndustrySolutions />
    </section>

    <CtaSection />
  </div>
</template>
