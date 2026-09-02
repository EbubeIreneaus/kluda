<script setup lang="ts">
import InteractivePosDemo from '~/components/landing/InteractivePosDemo.vue'
import RoiCalculator from '~/components/landing/RoiCalculator.vue'
import OfflineFlowDiagram from '~/components/landing/OfflineFlowDiagram.vue'
import HardwareComparison from '~/components/landing/HardwareComparison.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'

useSeoMeta({
  title: 'Kluda | Retail POS That Works Offline Without Dedicated Hardware',
  description: 'Kluda lets small businesses and retailers sell, scan barcodes, and track every transaction even when the internet is down — using the phone or tablet you already own.'
})

const outcomes = [
  {
    title: 'Sell without interruption',
    headline: 'Internet goes down? Keep selling.',
    desc: 'Never stop ringing up customer carts or scanning barcodes when network drops. Transactions store locally and sync automatically when connection returns.',
    icon: 'i-lucide-wifi-off',
    link: '/how-it-works'
  },
  {
    title: 'Know what you sold',
    headline: 'Every transaction recorded & tracked.',
    desc: 'Real-time sales insights, inventory deductions, discount controls, and printed thermal receipts without manual book-keeping or lost paper slips.',
    icon: 'i-lucide-receipt',
    link: '/how-it-works'
  },
  {
    title: 'Run your store from your phone',
    headline: 'No dedicated POS machine required.',
    desc: 'Turn any Android smartphone, iPhone, iPad, tablet, or existing laptop into a full checkout counter with instant camera barcode scanning.',
    icon: 'i-lucide-smartphone',
    link: '/pricing'
  },
  {
    title: 'Stay in sync across counters',
    headline: 'Multiple registers and branches aligned.',
    desc: 'Manage inventory across multiple cashiers and store branches in real-time to prevent overselling scarce items.',
    icon: 'i-lucide-refresh-cw',
    link: '/solutions'
  }
]

const storeUseCases = [
  {
    icon: 'i-lucide-shopping-bag',
    title: 'Supermarkets & Mini-Marts',
    desc: 'Keep checking out long queues when internet cuts during peak hours.',
    to: '/solutions/supermarkets'
  },
  {
    icon: 'i-lucide-pill',
    title: 'Pharmacies & Chemists',
    desc: 'Track frequent customer credit balances and inventory without paper ledgers.',
    to: '/solutions/pharmacies'
  },
  {
    icon: 'i-lucide-shirt',
    title: 'Fashion & Boutiques',
    desc: 'Turn your sales staff smartphones into mobile checkout registers.',
    to: '/solutions/boutiques'
  },
  {
    icon: 'i-lucide-store',
    title: 'Multi-Branch Retailers',
    desc: 'Monitor live branch revenue and stock levels from a single owner portal.',
    to: '/solutions'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="relative pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="absolute inset-0 -z-10 flex items-center justify-center">
        <div class="w-[600px] h-[600px] rounded-full bg-emerald-500/10 blur-[120px] pointer-events-none" />
        <div class="w-[450px] h-[450px] rounded-full bg-teal-500/10 blur-[100px] pointer-events-none -translate-y-24" />
      </div>

      <div data-aos="fade-up" data-aos-duration="600" class="max-w-5xl mx-auto text-center space-y-8">
        <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-black tracking-wide uppercase">
          <UIcon name="i-lucide-zap" class="w-3.5 h-3.5" />
          <span>Offline-First Retail Platform</span>
        </div>

        <h1 class="text-4xl sm:text-6xl lg:text-7xl font-black text-(--ui-text-highlighted) tracking-tight leading-[1.08]">
          SELL. TRACK.<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            EVEN WHEN YOU'RE OFFLINE.
          </span>
        </h1>

        <p class="text-lg sm:text-2xl text-(--ui-text-muted) max-w-3xl mx-auto font-normal leading-relaxed">
          Kluda keeps your retail business running when the internet doesn't — using the phone, tablet or PC you already have.
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <a
            :href="`${posUrl}/auth/register`"
            class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-black text-sm shadow-xl shadow-emerald-500/25 transition active:scale-95"
          >
            <span>Start Selling Free</span>
            <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
          </a>

          <NuxtLink
            to="/how-it-works"
            class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)/60 hover:bg-(--ui-bg-accented) text-(--ui-text-highlighted) font-bold text-sm transition"
          >
            <UIcon name="i-lucide-play-circle" class="w-4 h-4 text-emerald-500" />
            <span>See How It Works</span>
          </NuxtLink>
        </div>

        <div class="pt-4 flex flex-wrap items-center justify-center gap-4 sm:gap-8 text-xs font-semibold text-(--ui-text-muted)">
          <div class="flex items-center gap-1.5">
            <UIcon name="i-lucide-check-circle-2" class="w-4 h-4 text-emerald-500" />
            <span>No expensive POS hardware</span>
          </div>
          <div class="flex items-center gap-1.5">
            <UIcon name="i-lucide-check-circle-2" class="w-4 h-4 text-emerald-500" />
            <span>Works 100% offline</span>
          </div>
          <div class="flex items-center gap-1.5">
            <UIcon name="i-lucide-check-circle-2" class="w-4 h-4 text-emerald-500" />
            <span>Syncs automatically when online</span>
          </div>
        </div>
      </div>
    </section>

    <section data-aos="fade-up" data-aos-duration="600" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <HardwareComparison />
    </section>

    <section data-aos="fade-up" data-aos-duration="600" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <OfflineFlowDiagram />
    </section>

    <section data-aos="fade-up" data-aos-duration="600" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
          <UIcon name="i-lucide-target" class="w-3.5 h-3.5" />
          <span>Merchant Outcomes</span>
        </div>
        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          Built around what your store needs
        </h2>
        <p class="text-sm text-(--ui-text-muted) mt-2">
          Software designed to solve real operational retail challenges.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div
          v-for="(outcome, idx) in outcomes"
          :key="outcome.title"
          data-aos="fade-up"
          :data-aos-delay="idx * 100"
          data-aos-duration="600"
          class="p-8 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 hover:border-emerald-500/30 transition flex flex-col justify-between group"
        >
          <div>
            <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 mb-6 group-hover:scale-110 transition">
              <UIcon :name="outcome.icon" class="w-6 h-6" />
            </div>
            <span class="text-xs font-bold uppercase tracking-wider text-emerald-500">{{ outcome.title }}</span>
            <h3 class="text-xl font-extrabold text-(--ui-text-highlighted) mt-1 mb-3">
              {{ outcome.headline }}
            </h3>
            <p class="text-xs sm:text-sm text-(--ui-text-muted) leading-relaxed">
              {{ outcome.desc }}
            </p>
          </div>

          <div class="pt-6 mt-6 border-t border-(--ui-border) flex items-center justify-between">
            <NuxtLink :to="outcome.link" class="text-xs font-bold text-emerald-500 hover:text-emerald-400 flex items-center gap-1.5 transition">
              <span>Explore details</span>
              <UIcon name="i-lucide-arrow-right" class="w-3.5 h-3.5" />
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <section data-aos="fade-up" data-aos-duration="600" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-10">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
          <UIcon name="i-lucide-scan-barcode" class="w-3.5 h-3.5" />
          <span>Try The Cashier Interface</span>
        </div>
        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          Test the checkout register right now
        </h2>
        <p class="text-sm text-(--ui-text-muted) mt-2">
          Toggle the offline switch below to see how carts checkout and queue transactions without internet.
        </p>
      </div>

      <InteractivePosDemo />
    </section>

    <section data-aos="fade-up" data-aos-duration="600" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-10">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
          <UIcon name="i-lucide-layout-grid" class="w-3.5 h-3.5" />
          <span>Tailored For Your Retail Category</span>
        </div>
        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          Designed for your store type
        </h2>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <NuxtLink
          v-for="(store, idx) in storeUseCases"
          :key="store.title"
          :to="store.to"
          data-aos="fade-up"
          :data-aos-delay="idx * 80"
          data-aos-duration="600"
          class="p-6 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 hover:border-emerald-500/40 hover:bg-(--ui-bg-elevated) transition group flex flex-col justify-between"
        >
          <div>
            <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 mb-4 group-hover:scale-110 transition">
              <UIcon :name="store.icon" class="w-5 h-5" />
            </div>
            <h3 class="text-base font-bold text-(--ui-text-highlighted) mb-2">{{ store.title }}</h3>
            <p class="text-xs text-(--ui-text-muted) leading-relaxed">{{ store.desc }}</p>
          </div>
          <div class="mt-4 pt-3 border-t border-(--ui-border) flex items-center gap-1 text-xs font-bold text-emerald-500">
            <span>Learn more</span>
            <UIcon name="i-lucide-chevron-right" class="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
          </div>
        </NuxtLink>
      </div>
    </section>

    <section data-aos="fade-up" data-aos-duration="600" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <RoiCalculator />
    </section>

    <CtaSection />
  </div>
</template>
