<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000/api/v1'

useHead({
  title: 'Frequently Asked Questions — Kluda Retail POS',
  meta: [
    {
      name: 'description',
      content: 'Answers to common questions about Kluda POS: offline mode, hardware thermal printing, staff anti-theft controls, and daily/monthly plans.'
    }
  ]
})

interface FAQItem {
  id: number
  question: string
  answer: string
  category: string
  display_order: number
}

const fallbackFaqs: FAQItem[] = [
  {
    id: 1,
    question: 'Can I use Kluda POS when my shop has no internet?',
    answer: 'Yes! Kluda is built with an offline-first mesh engine. Your counter keeps ringing up sales, scanning barcodes, calculating discounts, and issuing thermal receipts even during total internet blackouts. As soon as connectivity returns, all sales sync automatically with the cloud.',
    category: 'offline',
    display_order: 1
  },
  {
    id: 2,
    question: 'Do I need to buy expensive supermarket POS machines?',
    answer: 'Not at all. You can turn the Android phone, iPhone, tablet, or laptop you already own into a fast checkout register. Kluda uses your device camera for instant barcode scanning and pairs wirelessly with budget thermal receipt printers.',
    category: 'hardware',
    display_order: 2
  },
  {
    id: 3,
    question: 'How does Kluda prevent cashier theft and cash pocketing?',
    answer: 'Every single item that leaves your shelf requires a recorded sale, locked to the cashier on duty. Cashiers cannot edit prices, delete past sales, or alter stock counts without manager authorization. At the end of each shift, Kluda reconciles expected cash against actual drawer counts.',
    category: 'general',
    display_order: 3
  },
  {
    id: 4,
    question: 'Can I connect a physical barcode scanner and thermal receipt printer?',
    answer: 'Yes. Kluda supports both handheld USB and Bluetooth barcode scanners. It also integrates directly via WebBluetooth and WebUSB with standard 58mm and 80mm ESC/POS thermal receipt printers (such as GOOJPRT, Xprinter, and Sunmi) with zero drivers needed on Android and PC.',
    category: 'hardware',
    display_order: 4
  },
  {
    id: 5,
    question: 'How does the customer debt and credit ledger work?',
    answer: 'Instead of tracking customer credits in paper notebooks that get torn or misplaced, you can select Debt at checkout. Kluda records the exact balance against the customer profile, logs partial repayments, and shows outstanding debts directly at the counter.',
    category: 'general',
    display_order: 5
  },
  {
    id: 6,
    question: 'Can I pay for Kluda with a daily pass instead of a whole month?',
    answer: 'Yes. We understand cash flow flexibility for retailers. In addition to monthly and annual subscriptions, Kluda offers flexible sachet pricing (such as 24-hour daily passes and weekly plans) so you only pay for what you need.',
    category: 'billing',
    display_order: 6
  },
  {
    id: 7,
    question: 'Is my store sales and customer data safe?',
    answer: 'Absolutely. Kluda guarantees that your sales, product prices, customer records, and financial numbers are 100% private. We NEVER sell, license, or share your store data with advertisers, competitors, or financial lenders.',
    category: 'general',
    display_order: 7
  }
]

const { data: remoteFaqs } = await useAsyncData<FAQItem[]>('public-faqs', async () => {
  try {
    const res = await $fetch<FAQItem[]>(`${apiBase}/faqs`)
    return res && res.length ? res : fallbackFaqs
  } catch {
    return fallbackFaqs
  }
})

const faqs = computed(() => remoteFaqs.value || fallbackFaqs)

const searchQuery = ref('')
const selectedCategory = ref('all')
const activeFaqId = ref<number | null>(faqs.value[0]?.id || 1)

const categories = [
  { label: 'All Questions', value: 'all' },
  { label: 'General & Security', value: 'general' },
  { label: 'Offline Mode', value: 'offline' },
  { label: 'Hardware & Printers', value: 'hardware' },
  { label: 'Pricing & Plans', value: 'billing' }
]

const filteredFaqs = computed(() => {
  return faqs.value.filter((faq) => {
    const matchesCat = selectedCategory.value === 'all' || faq.category === selectedCategory.value
    const q = searchQuery.value.toLowerCase().trim()
    const matchesSearch = !q || faq.question.toLowerCase().includes(q) || faq.answer.toLowerCase().includes(q)
    return matchesCat && matchesSearch
  })
})

function toggleFaq(id: number) {
  activeFaqId.value = activeFaqId.value === id ? null : id
}
</script>

<template>
  <div class="space-y-16 pb-20 overflow-hidden">
    <!-- Hero Header -->
    <section class="relative pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8 text-center max-w-4xl mx-auto space-y-6">
      <div class="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
        <div class="absolute inset-0 bg-[linear-gradient(to_right,#27272a15_1px,transparent_1px),linear-gradient(to_bottom,#27272a15_1px,transparent_1px)] bg-[size:40px_40px]" />
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/10 blur-[100px] rounded-full" />
      </div>

      <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-black tracking-wide uppercase">
        <UIcon name="i-lucide-help-circle" class="w-3.5 h-3.5" />
        <span>Help & Knowledge Center</span>
      </div>

      <h1 class="text-4xl sm:text-5xl font-black text-(--ui-text-highlighted) tracking-tight">
        Frequently Asked Questions
      </h1>

      <p class="text-base sm:text-lg text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
        Everything you need to know about setting up Kluda, running offline, pairing thermal printers, and preventing store loss.
      </p>

      <!-- Search Input -->
      <div class="max-w-xl mx-auto pt-2">
        <div class="relative">
          <UIcon name="i-lucide-search" class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-(--ui-text-dimmed)" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search questions (e.g. offline, printer, pricing, theft)..."
            class="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-(--ui-bg-elevated) border border-(--ui-border) text-sm text-(--ui-text-highlighted) placeholder:text-(--ui-text-dimmed) focus:outline-none focus:border-emerald-500 transition shadow-sm backdrop-blur-md"
          />
        </div>
      </div>

      <!-- Category Filter Pills -->
      <div class="flex flex-wrap items-center justify-center gap-2 pt-2">
        <button
          v-for="cat in categories"
          :key="cat.value"
          type="button"
          class="px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer"
          :class="selectedCategory === cat.value ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20' : 'bg-(--ui-bg-elevated) text-(--ui-text-muted) hover:text-(--ui-text-highlighted) border border-(--ui-border) hover:bg-(--ui-bg-accented)'"
          @click="selectedCategory = cat.value"
        >
          {{ cat.label }}
        </button>
      </div>
    </section>

    <!-- FAQ Accordion List -->
    <section class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
      <div
        v-if="filteredFaqs.length === 0"
        class="text-center py-16 px-4 rounded-3xl border border-dashed border-(--ui-border) bg-(--ui-bg-elevated)/40"
      >
        <UIcon name="i-lucide-search-x" class="size-12 text-(--ui-text-dimmed) mx-auto mb-3" />
        <h3 class="text-base font-bold text-(--ui-text-highlighted)">No matching questions found</h3>
        <p class="text-xs text-(--ui-text-muted) mt-1 max-w-sm mx-auto">
          Try typing different search keywords or switch category filter to "All Questions".
        </p>
      </div>

      <div
        v-for="faq in filteredFaqs"
        :key="faq.id"
        class="rounded-2xl border transition overflow-hidden shadow-xs"
        :class="activeFaqId === faq.id ? 'bg-(--ui-bg-elevated) border-emerald-500/50 shadow-md shadow-emerald-500/10' : 'bg-(--ui-bg-elevated)/70 border-(--ui-border) hover:border-(--ui-border-accented)'"
      >
        <button
          type="button"
          class="w-full px-6 py-5 flex items-center justify-between gap-4 text-left cursor-pointer"
          @click="toggleFaq(faq.id)"
        >
          <span class="text-sm sm:text-base font-bold text-(--ui-text-highlighted) flex items-center gap-3">
            <span class="w-2 h-2 rounded-full shrink-0" :class="activeFaqId === faq.id ? 'bg-emerald-500' : 'bg-(--ui-border-accented)'" />
            {{ faq.question }}
          </span>
          <UIcon
            name="i-lucide-chevron-down"
            class="w-5 h-5 text-(--ui-text-muted) shrink-0 transition-transform duration-200"
            :class="activeFaqId === faq.id ? 'rotate-180 text-emerald-500' : ''"
          />
        </button>

        <div
          v-show="activeFaqId === faq.id"
          class="px-6 pb-6 pt-1 text-sm text-(--ui-text) leading-relaxed border-t border-(--ui-border)/60"
        >
          {{ faq.answer }}
        </div>
      </div>
    </section>

    <!-- Support Help Box -->
    <section class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) dark:bg-gradient-to-tr dark:from-zinc-900 dark:via-zinc-900/80 dark:to-zinc-950 p-8 sm:p-10 text-center space-y-4 shadow-sm">
        <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto text-emerald-600 dark:text-emerald-400">
          <UIcon name="i-lucide-message-square" class="w-6 h-6" />
        </div>
        <h3 class="text-xl font-black text-(--ui-text-highlighted)">Have a specific retail question?</h3>
        <p class="text-sm text-(--ui-text-muted) max-w-lg mx-auto leading-relaxed">
          Need advice on setting up barcode scanners, thermal printers, or running multi-branch inventory? Our retail operations team is available to assist you.
        </p>
        <div class="pt-2">
          <NuxtLink
            to="/contact"
            class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition cursor-pointer"
          >
            <UIcon name="i-lucide-mail" class="w-4 h-4" />
            <span>Contact Support Team</span>
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
