<script setup lang="ts">
import OfflineFlowDiagram from '~/components/landing/OfflineFlowDiagram.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

useSeoMeta({
  title: 'Why Kluda | Stop Money Theft & Take Control of Your Store',
  description: 'Discover why Kluda was built: to eliminate employee cash theft, automate stock tracking, and manage customer debts without buying expensive supermarket POS machines.'
})

const manifestoPoints = [
  {
    icon: 'i-lucide-shield-check',
    title: 'Stop Staff Theft & Pocketed Cash',
    desc: 'When sales are recorded only on paper, staff can easily under-report sales and pocket cash. Kluda locks every checkout to a cashier shift and digital receipt.'
  },
  {
    icon: 'i-lucide-boxes',
    title: 'Live Stock Control Without Manual Counts',
    desc: 'Never wonder where your cartons or items disappeared to. Every sale automatically deducts shelf stock in real-time, giving you accurate inventory at all times.'
  },
  {
    icon: 'i-lucide-book-open',
    title: 'Zero Lost Customer Debts',
    desc: 'Say goodbye to torn, coffee-stained exercise books. Log customer credit in two taps, track partial repayments, and keep your loyal customers happy without losing money.'
  },
  {
    icon: 'i-lucide-smartphone',
    title: 'No ₦300,000 Supermarket Machines Needed',
    desc: 'You do not need to buy heavy computer towers or dedicated hardware. The phone, tablet, or laptop you already own has everything needed to run a world-class register.'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-4xl mx-auto text-center space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-wider">
          <UIcon name="i-lucide-shield-alert" class="w-3.5 h-3.5" />
          <span>Our Store Protection Mission</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-black text-(--ui-text-highlighted) tracking-tight leading-tight">
          Stop Leaving Your Store Revenue<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            To Paper Books & Guesswork.
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Every day, retail store owners bleed profit through untracked cash sales, employee theft, missing inventory, and forgotten customer debts. Kluda puts an end to that.
        </p>
      </div>
    </section>

    <section class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="p-8 sm:p-12 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 space-y-8 leading-relaxed text-sm sm:text-base text-(--ui-text-muted)">
        <h2 class="text-2xl sm:text-3xl font-black text-(--ui-text-highlighted)">
          The Paper Exercise Book Is Where Profits Disappear
        </h2>

        <p>
          In retail shops, mini-marts, boutiques, and pharmacies across the country, store owners struggle with the same painful realities: sales girls and sales boys claiming "market was slow" while pocketing cash, cartons of stock disappearing without explanation, and customer credit scribbled in books that get lost or disputed.
        </p>

        <p>
          Many store owners believe that the only way to stop this is to spend ₦300,000 to ₦500,000 on bulky supermarket computer towers, barcode scanners, and complicated enterprise software.
        </p>

        <div class="p-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-(--ui-text-highlighted) font-semibold text-base">
          "We built Kluda to give every retail store owner the exact same inventory control, theft protection, and sales auditing that giant supermarket chains enjoy — directly on the smartphone in their pocket."
        </div>

        <p>
          With Kluda, your counter register is fast, accurate, and completely theft-proof. Even during power blackouts or network drops, your staff can ring up customers seamlessly while you track your store revenue from anywhere in the world.
        </p>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          The 4 Pillars of Kluda Store Management
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

    <CtaSection />
  </div>
</template>
