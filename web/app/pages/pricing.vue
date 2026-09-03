<script setup lang="ts">
import { ref } from 'vue'
import HardwareComparison from '~/components/landing/HardwareComparison.vue'
import RoiCalculator from '~/components/landing/RoiCalculator.vue'
import CtaSection from '~/components/landing/CtaSection.vue'

definePageMeta({
  layout: 'marketing'
})

const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'

useSeoMeta({
  title: 'Hardware Economics & Pricing | Kluda Retail POS',
  description: 'Zero upfront hardware investment. See how much your retail store saves by using smartphones and tablets with Kluda instead of ₦250,000+ dedicated POS terminal hardware.'
})

const openFaqIndex = ref<number | null>(0)

function toggleFaq(idx: number) {
  openFaqIndex.value = openFaqIndex.value === idx ? null : idx
}

interface PricingFaq {
  q: string
  a: string
}

const defaultFaqs: PricingFaq[] = [
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
    q: 'Are there any hidden hardware or technician fees?',
    a: 'No. Kluda requires zero expensive hardware setups or technician visits. You can turn any existing smartphone, tablet, or PC into a modern checkout register in seconds.'
  }
]

interface SubscriptionPlan {
  id: number
  slug: string
  name: string
  description: string
  price: number
  interval: string
  has_trial: boolean
  trial_duration_days: number
  store_limit: number
  product_limit: number
  sales_limit_per_month: number
  status: string
}

const selectedInterval = ref<string>('monthly')

const { data: rawPlans, pending: isLoadingPlans } = await useAsyncData<SubscriptionPlan[]>('public-subscription-plans', async () => {
  try {
    const apiBase = config.public.apiBase || 'http://localhost:8000/api/v1'
    const res = await $fetch<SubscriptionPlan[]>(`${apiBase}/subscriptions/plans`)
    return res || []
  } catch {
    return []
  }
})

const availableIntervals = computed(() => {
  if (!rawPlans.value || rawPlans.value.length === 0) return ['monthly']
  const clean = rawPlans.value.filter(p => p.slug !== 'trial')
  const ints = Array.from(new Set(clean.map(p => (p.interval || 'monthly').toLowerCase())))
  return ints.length > 0 ? ints : ['monthly']
})

watch(availableIntervals, (ints) => {
  if (ints.length > 0 && ints[0] && !ints.includes(selectedInterval.value)) {
    selectedInterval.value = ints[0]
  }
}, { immediate: true })

const displayPlans = computed(() => {
  if (!rawPlans.value || rawPlans.value.length === 0) return []
  const clean = rawPlans.value.filter(p => p.slug !== 'trial')
  const filtered = clean.filter(p => (p.interval || 'monthly').toLowerCase() === selectedInterval.value.toLowerCase())
  const target = filtered.length > 0 ? filtered : clean

  return target.map(p => {
    const priceNaira = (p.price || 0) / 100
    const inv = (p.interval || 'monthly').toLowerCase()
    const intervalLabel = inv === 'daily' ? 'day' : (inv === 'weekly' ? 'wk' : (inv === 'yearly' ? 'yr' : 'mo'))
    const hasTrial = Boolean(p.has_trial && p.trial_duration_days && p.trial_duration_days > 0)
    
    return {
      slug: p.slug,
      name: p.name,
      description: p.description,
      price: p.price,
      priceFormatted: p.price === 0 ? 'Free' : `₦${priceNaira.toLocaleString()}`,
      intervalLabel: p.price === 0 ? 'forever' : `per ${intervalLabel}`,
      hasTrial,
      trialDays: p.trial_duration_days,
      badge: hasTrial ? `${p.trial_duration_days}-Day Trial` : (p.price > 2000000 ? 'Enterprise' : (p.price === 0 ? 'Free' : 'Popular')),
      features: [
        `${p.store_limit && p.store_limit > 0 ? p.store_limit : 'Unlimited'} Store ${p.store_limit === 1 ? 'Branch' : 'Branches'}`,
        `${p.product_limit && p.product_limit > 0 ? p.product_limit.toLocaleString() : 'Unlimited'} Products`,
        `${p.sales_limit_per_month && p.sales_limit_per_month > 0 ? p.sales_limit_per_month.toLocaleString() : 'Unlimited'} Monthly Sales`,
        '100% Offline Checkout Continuity',
        'Camera Barcode Scanning',
        'Automated Thermal Receipts'
      ]
    }
  })
})

const { data: dynamicFaqs } = await useAsyncData<PricingFaq[]>('pricing-faqs', async () => {
  try {
    const apiBase = config.public.apiBase || 'http://localhost:8000/api/v1'
    const res = await $fetch<any[]>(`${apiBase}/faqs`)
    if (res && res.length) {
      return res.map(f => ({ q: f.question, a: f.answer }))
    }
  } catch {}
  return defaultFaqs
})

const displayFaqs = computed(() => dynamicFaqs.value || defaultFaqs)
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
            Transparent Subscription Plans.
          </span>
        </h1>

        <p class="text-base sm:text-xl text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Stop paying ₦250,000+ for bulky desktop terminal towers. Turn the devices your staff already carry into modern retail cash registers.
        </p>

        <!-- Dynamic Interval Selector -->
        <div v-if="availableIntervals.length > 1" class="pt-4 flex justify-center">
          <div class="inline-flex items-center p-1.5 bg-(--ui-bg-elevated) border border-(--ui-border) rounded-2xl shadow-sm">
            <button
              v-for="inv in availableIntervals"
              :key="inv"
              type="button"
              class="px-5 py-2 rounded-xl text-xs font-black transition capitalize cursor-pointer"
              :class="selectedInterval === inv ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20' : 'text-(--ui-text-muted) hover:text-(--ui-text-highlighted)'"
              @click="selectedInterval = inv"
            >
              {{ inv === 'yearly' ? 'Yearly (Save 15%)' : (inv === 'daily' ? 'Daily Pass' : inv) }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Dynamic Plans Grid -->
    <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div v-if="displayPlans.length > 0" class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div
          v-for="plan in displayPlans"
          :key="plan.slug"
          class="rounded-3xl border border-(--ui-border) bg-gradient-to-b from-(--ui-bg-elevated) to-(--ui-bg) p-8 shadow-xl flex flex-col justify-between relative transition-all duration-300 hover:border-emerald-500/40 hover:-translate-y-1"
        >
          <div class="space-y-6">
            <div class="flex items-center justify-between">
              <h3 class="text-xl font-black text-(--ui-text-highlighted)">{{ plan.name }}</h3>
              <span class="text-[10px] px-3 py-1 rounded-full font-black uppercase tracking-wider bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                {{ plan.badge }}
              </span>
            </div>

            <p class="text-xs text-(--ui-text-muted) min-h-[36px]">{{ plan.description }}</p>

            <div class="pt-2">
              <div class="flex items-baseline gap-2">
                <span class="text-4xl font-black text-(--ui-text-highlighted)">{{ plan.priceFormatted }}</span>
                <span class="text-xs font-bold text-(--ui-text-muted)">/ {{ plan.intervalLabel }}</span>
              </div>
            </div>

            <div class="pt-6 border-t border-(--ui-border) space-y-3 text-xs">
              <div v-for="feat in plan.features" :key="feat" class="flex items-center gap-2 text-(--ui-text-highlighted)">
                <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{{ feat }}</span>
              </div>
            </div>
          </div>

          <div class="pt-8 mt-8 border-t border-(--ui-border)">
            <a
              :href="`${posUrl}/auth/register?plan=${plan.slug}`"
              class="w-full inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl font-black text-xs shadow-lg transition active:scale-95"
              :class="plan.hasTrial || plan.price > 0 ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black shadow-emerald-500/20' : 'bg-(--ui-bg-accented) text-(--ui-text-highlighted) hover:bg-(--ui-border)'"
            >
              <UIcon v-if="plan.hasTrial" name="i-lucide-sparkles" class="w-4 h-4" />
              <span>{{ plan.hasTrial ? `Start ${plan.trialDays}-Day Free Trial` : (plan.price === 0 ? 'Start Selling Free' : 'Get Started') }}</span>
              <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>

      <!-- Fallback if database has no active plans yet -->
      <div v-else class="rounded-3xl border-2 border-emerald-500/40 bg-gradient-to-b from-emerald-950/30 via-(--ui-bg-elevated) to-(--ui-bg-elevated) p-8 sm:p-12 shadow-2xl relative overflow-hidden text-center max-w-4xl mx-auto">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500 text-black text-xs font-black uppercase tracking-wider mb-6">
          <span>Starter Retail Tier</span>
        </div>

        <h2 class="text-3xl sm:text-4xl font-black text-(--ui-text-highlighted) tracking-tight">
          Start Free Today
        </h2>
        <p class="text-sm text-(--ui-text-muted) mt-2 max-w-lg mx-auto">
          Full platform access with camera barcode scanning and offline sales continuity.
        </p>

        <div class="py-6">
          <span class="text-5xl sm:text-6xl font-black text-emerald-400">₦0</span>
          <span class="text-sm font-semibold text-(--ui-text-muted)"> / free starter access</span>
        </div>

        <a
          :href="`${posUrl}/auth/register`"
          class="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-black text-sm shadow-xl shadow-emerald-500/25 transition active:scale-95"
        >
          <span>Start Selling Free</span>
          <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
        </a>
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
          v-for="(faq, idx) in displayFaqs"
          :key="faq.q"
          class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 overflow-hidden transition"
        >
          <button
            @click="toggleFaq(idx)"
            class="w-full p-5 sm:p-6 text-left flex items-center justify-between gap-4 font-bold text-sm sm:text-base text-(--ui-text-highlighted) cursor-pointer"
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

      <div class="text-center pt-8">
        <NuxtLink
          to="/faq"
          class="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) hover:bg-(--ui-bg-accented) text-xs font-bold text-emerald-700 dark:text-emerald-400 shadow-xs transition cursor-pointer"
        >
          <span>View All Frequently Asked Questions</span>
          <UIcon name="i-lucide-arrow-right" class="w-3.5 h-3.5" />
        </NuxtLink>
      </div>
    </section>

    <CtaSection />
  </div>
</template>
