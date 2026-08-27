<script setup lang="ts">
import { ref } from 'vue'
import HardwareComparison from '~/components/landing/HardwareComparison.vue'
import RoiCalculator from '~/components/landing/RoiCalculator.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

useSeoMeta({
  title: 'Hardware Economics & Pricing | Kluda Retail POS',
  description: 'Zero upfront hardware investment. See how much your retail store saves by using smartphones and tablets with Kluda instead of ₦250,000+ dedicated POS terminal hardware.'
})

const openFaqIndex = ref<number | null>(0)

function toggleFaq(idx: number) {
  openFaqIndex.value = openFaqIndex.value === idx ? null : idx
}

const faqs = [
  {
    q: 'Do I need to buy any dedicated POS hardware to use Kluda?',
    a: 'No. Kluda is designed to run directly in the modern web browser on Android phones, iPhones, iPads, Android tablets, and existing laptops/PCs. You use the camera you already own for barcode scanning.'
  },
  {
    q: 'How does Kluda work when internet connection drops completely?',
    a: 'Your store catalog and price list reside directly in local browser storage. When internet goes offline, cashiers continue scanning barcodes, adjusting cart quantities, applying discounts, and completing sales. When connection returns, everything reconciles silently with the cloud.'
  },
  {
    q: 'Can I print receipts to standard thermal printers?',
    a: 'Yes. Kluda supports standard 58mm and 80mm ESC/POS thermal printers via Bluetooth, USB, or WiFi network connection.'
  },
  {
    q: 'Can I use an external USB or Bluetooth barcode scanner if I already own one?',
    a: 'Yes. While Kluda has a built-in phone camera barcode scanner, it also works natively with all standard USB laser guns and Bluetooth handheld barcode scanners.'
  },
  {
    q: 'How much does Kluda cost during the Public Beta?',
    a: 'Kluda is 100% free during our Public Beta while we build and refine features with early retailers. There are no credit card requirements and no hidden fees.'
  },
  {
    q: 'Can I track customer debt and credit purchases?',
    a: 'Yes. Kluda includes a built-in Customer Credit Ledger. You can record credit sales, monitor unpaid balances, accept partial repayments, and issue debt statement receipts directly at checkout.'
  }
]
</script>

<template>
  <div class="space-y-24 sm:space-y-32 pb-16 overflow-hidden">
    <section class="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-4xl mx-auto text-center space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-wider">
          <UIcon name="i-lucide-coins" class="w-3.5 h-3.5" />
          <span>Simple, Transparent Economics</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-black text-(--ui-text-highlighted) tracking-tight">
          Zero Hardware Cost.<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            Free While We Build Together.
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Stop paying ₦250,000+ for bulky desktop terminal towers. Turn the devices your staff already carry into modern retail cash registers.
        </p>
      </div>
    </section>

    <section class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="rounded-3xl border-2 border-emerald-500/40 bg-gradient-to-b from-emerald-950/30 via-(--ui-bg-elevated) to-(--ui-bg-elevated) p-8 sm:p-12 shadow-2xl relative overflow-hidden text-center">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500 text-black text-xs font-black uppercase tracking-wider mb-6">
          <span>Early Retailer Public Beta</span>
        </div>

        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          Public Beta Access
        </h2>
        <p class="text-sm text-(--ui-text-muted) mt-2 max-w-lg mx-auto">
          Full platform access while we partner with early store owners across Nigeria.
        </p>

        <div class="py-8">
          <div class="flex items-baseline justify-center gap-2">
            <span class="text-5xl sm:text-6xl font-black text-emerald-400">₦0</span>
            <span class="text-sm font-semibold text-(--ui-text-muted)">/ free during beta testing</span>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl mx-auto text-left text-xs text-(--ui-text-muted) mb-8">
          <div class="flex items-center gap-2.5 p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Unlimited products & inventory</span>
          </div>
          <div class="flex items-center gap-2.5 p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Unlimited cashier registers & counters</span>
          </div>
          <div class="flex items-center gap-2.5 p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Built-in phone camera barcode scanner</span>
          </div>
          <div class="flex items-center gap-2.5 p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500 shrink-0" />
            <span>100% offline checkout continuity</span>
          </div>
          <div class="flex items-center gap-2.5 p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Customer credit & debt ledger</span>
          </div>
          <div class="flex items-center gap-2.5 p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Owner revenue & analytics portal</span>
          </div>
        </div>

        <NuxtLink
          to="/register"
          class="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-black text-sm shadow-xl shadow-emerald-500/25 transition active:scale-95"
        >
          <span>Start Selling Free</span>
          <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
        </NuxtLink>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <HardwareComparison />
    </section>

    <section id="calculator" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <RoiCalculator />
    </section>

    <section id="faq" class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
          <UIcon name="i-lucide-help-circle" class="w-3.5 h-3.5" />
          <span>Frequently Asked Questions</span>
        </div>
        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          Questions retailers ask us
        </h2>
      </div>

      <div class="space-y-4">
        <div
          v-for="(faq, idx) in faqs"
          :key="faq.q"
          class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 overflow-hidden transition"
        >
          <button
            @click="toggleFaq(idx)"
            class="w-full p-5 sm:p-6 text-left flex items-center justify-between gap-4 font-bold text-sm sm:text-base text-(--ui-text-highlighted)"
          >
            <span>{{ faq.q }}</span>
            <UIcon
              name="i-lucide-chevron-down"
              class="w-4 h-4 text-emerald-500 transition-transform shrink-0"
              :class="openFaqIndex === idx ? 'rotate-180' : ''"
            />
          </button>

          <div v-if="openFaqIndex === idx" class="px-5 sm:px-6 pb-6 pt-0 text-xs sm:text-sm text-(--ui-text-muted) leading-relaxed border-t border-(--ui-border)/40">
            {{ faq.a }}
          </div>
        </div>
      </div>
    </section>

    <CtaSection />
  </div>
</template>
