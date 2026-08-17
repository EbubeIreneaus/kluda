<script setup lang="ts">
import { ref } from 'vue'
import InteractivePosDemo from '~/components/landing/InteractivePosDemo.vue'
import RoiCalculator from '~/components/landing/RoiCalculator.vue'
import ArchitectureFlow from '~/components/landing/ArchitectureFlow.vue'
import IndustrySolutions from '~/components/landing/IndustrySolutions.vue'
import BarcodeSandbox from '~/components/landing/BarcodeSandbox.vue'

const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'

const activeFeatureTab = ref('offline')
const openFaqIndex = ref<number | null>(0)
const isMobileMenuOpen = ref(false)

const navLinks = [
  { label: 'Core Features', href: '#features', icon: 'i-lucide-sparkles' },
  { label: 'Register Live Demo', href: '#demo', icon: 'i-lucide-scan-barcode' },
  { label: 'How It Works', href: '#architecture', icon: 'i-lucide-activity' },
  { label: 'Store Savings Calculator', href: '#calculator', icon: 'i-lucide-calculator' },
  { label: 'Tailored Store Solutions', href: '#use-cases', icon: 'i-lucide-layout-grid' },
  { label: 'Barcode Sandbox Tool', href: '#sandbox', icon: 'i-lucide-scan-line' },
  { label: 'Why RetailPOS', href: '#comparison', icon: 'i-lucide-check-circle' },
  { label: 'Free Beta Testing Access', href: '#pricing', icon: 'i-lucide-gift' },
  { label: 'Merchant FAQ', href: '#faq', icon: 'i-lucide-help-circle' }
]

function toggleFaq(idx: number) {
  openFaqIndex.value = openFaqIndex.value === idx ? null : idx
}

const features = [
  {
    id: 'offline',
    title: 'Offline-First Selling',
    icon: 'i-lucide-wifi-off',
    tagline: 'Never lose a sale during power or internet outages',
    description: 'Every sale is saved instantly on your device with complete reliability. When internet connectivity returns, sales sync to your cloud account automatically in the background without staff needing to do anything.',
    highlights: ['Instant 0.1-second checkout speed', 'Automatic background sync when online', 'Zero lost sales during internet cuts']
  },
  {
    id: 'scanner',
    title: 'Phone Camera Barcode Scan',
    icon: 'i-lucide-scan-barcode',
    tagline: 'Zero scanner guns or hardware required',
    description: 'Use the built-in camera of any smartphone, tablet, or laptop to scan product barcodes at lightning speed with instant sound confirmation. No extra accessories or cables required.',
    highlights: ['Saves ₦20,000+ per scanner gun', 'Instant continuous scan mode with audio beep', 'Custom barcode generator for loose items']
  },
  {
    id: 'mesh',
    title: 'Real-Time Multi-Counter Sync',
    icon: 'i-lucide-refresh-cw',
    tagline: 'Synchronize inventory across all registers',
    description: 'Run multiple cashier counters simultaneously. When one counter sells an item, remaining shelf stock updates immediately across all other cashier screens to prevent overselling.',
    highlights: ['Instant live updates across all counters', 'Prevents overselling scarce items', 'Store-wide live sales tracking']
  },
  {
    id: 'debts',
    title: 'Customer Debt & Credit Ledger',
    icon: 'i-lucide-book-open',
    tagline: 'Track customer balances and credit sales',
    description: 'Manage frequent customers, record credit sales, track unpaid balances, and record partial repayments directly during checkout without leaving the cashier register.',
    highlights: ['Detailed customer purchase history', 'Instant 1-tap debt repayment recording', 'Automated balance receipts on thermal printer']
  },
  {
    id: 'multistore',
    title: 'Multi-Branch Store Hub',
    icon: 'i-lucide-store',
    tagline: 'Centralized multi-location control',
    description: 'Open new store locations in seconds. Manage inventories, monitor live branch revenue, and generate cashier logins for all your outlets from one single Merchant Portal.',
    highlights: ['1-click branch store creation', 'Individual product catalogs per location', 'Global owner revenue dashboard']
  },
  {
    id: 'security',
    title: 'Staff Roles & Permissions',
    icon: 'i-lucide-shield-check',
    tagline: 'Protect profits and cashier accountability',
    description: 'Create dedicated Staff IDs for cashiers and managers. Choose who can view revenue analytics, edit product prices, or only process checkout sales, keeping your financial data secure.',
    highlights: ['Staff ID generation (e.g. STF1001)', 'Custom permission control per cashier', 'Full shift and transaction audit history']
  }
]

const comparisonItems = [
  { feature: 'Initial Hardware Cost', traditional: '₦250,000+ per terminal', cloudPos: '₦120,000+ per iPad/stand', retailPos: '₦0 (Use any phone, tablet, or PC)', win: true },
  { feature: 'Barcode Scanner Gun', traditional: '₦20,000 - ₦35,000 extra', cloudPos: '₦45,000 Bluetooth scanner', retailPos: 'Included (Built-in Camera Scanner)', win: true },
  { feature: 'Works Without Internet', traditional: '❌ Freezes or crashes', cloudPos: '⚠️ Limited offline mode', retailPos: '✅ 100% Offline Capability (Never Stalls)', win: true },
  { feature: 'Multi-Counter Live Sync', traditional: '❌ Costly local server needed', cloudPos: '❌ Requires fast constant internet', retailPos: '✅ Instant Real-Time Counter Sync', win: true },
  { feature: 'Customer Debt Ledger', traditional: '❌ Separate paper notebook', cloudPos: '❌ Paid third-party app plugin', retailPos: '✅ Built-in In-Register Debt Tracking', win: true },
  { feature: 'Setup Time', traditional: '3 - 7 days on-site technician', cloudPos: '2 - 4 hours configuration', retailPos: '⚡ Under 60 seconds (Instant Browser App)', win: true },
  { feature: 'Thermal Receipt Printing', traditional: 'Proprietary printer only', cloudPos: 'Select expensive AirPrint printers', retailPos: '✅ Standard 58mm/80mm Bluetooth & USB', win: true },
  { feature: 'Monthly Fee During Beta', traditional: '₦15,000+ monthly maintenance', cloudPos: '$29 - $89 / month', retailPos: '🎉 ₦0 (100% Free Public Testing)', win: true }
]

const testimonials = [
  {
    quote: "We run a busy supermarket in Ikeja, and whenever heavy rain cuts our fiber line, other POS apps crash and customers abandon their carts. With RetailPOS, our cashiers don't even notice the outage. Everything rings up instantly and auto-syncs the moment network returns.",
    author: 'Emmanuel Adeleke',
    role: 'Supermarket Operations Manager',
    location: 'Lagos, Nigeria',
    badge: 'Verified Merchant',
    metric: '₦480,000 Saved in Hardware'
  },
  {
    quote: "The built-in camera barcode scanning completely eliminated the need for barcode scanner guns across our 3 pharmacy branches. The customer credit ledger also stopped credit leakages for our chronic patients.",
    author: 'Dr. Fatima Bello',
    role: 'Managing Pharmacist',
    location: 'Abuja, Nigeria',
    badge: 'Verified Merchant',
    metric: '100% Zero Debt Leakage'
  },
  {
    quote: "I opened two new boutique kiosks at a weekend lifestyle fair. I didn't need to rent POS terminals or buy Wi-Fi routers. My staff simply opened RetailPOS on their Android phones and printed receipts via Bluetooth.",
    author: 'Chidinma Okafor',
    role: 'Founder & Retail Director',
    location: 'Port Harcourt, Nigeria',
    badge: 'Verified Merchant',
    metric: '100% Mobile Operations'
  }
]

const faqs = [
  {
    q: 'Does RetailPOS really work without an active internet connection?',
    a: 'Yes! RetailPOS is built so your store never stops. Your entire product catalog, prices, and customer balances live safely on your device. Cashiers can ring up items, apply discounts, and print thermal receipts with zero internet connection. The moment network or Wi-Fi reconnects, all pending sales sync automatically to your store cloud.'
  },
  {
    q: 'Do I need to buy expensive barcode scanner guns or POS machines?',
    a: 'No! RetailPOS turns any smartphone, tablet, laptop, or existing desktop computer into a full POS register. It uses the built-in device camera to scan standard barcodes (EAN-13, UPC-A, Code-128) with instant sound feedback. If you already own USB or Bluetooth scanner guns, RetailPOS supports them out of the box.'
  },
  {
    q: 'How much does RetailPOS cost right now?',
    a: 'RetailPOS is currently in open Public Testing / Community Beta and is 100% FREE for all participating merchants. You get unrestricted access to unlimited store branches, unlimited cashier accounts, offline selling, customer debt ledgers, and analytics with no credit card required.'
  },
  {
    q: 'How does real-time multi-counter sync work?',
    a: 'When multiple cashiers are ringing up sales at different counters in the same store, inventory deductions update across all screens in real time. If Counter 1 sells the last unit of a product, Counter 2 immediately reflects the updated stock so your staff never oversell items.'
  },
  {
    q: 'Can I print receipts to thermal printers?',
    a: 'Yes! RetailPOS supports standard 58mm and 80mm thermal receipt printers via Bluetooth, USB, or the standard print dialog. Receipts include your store name, address, cashier ID, itemized products, payment method, customer balance, and customizable footer notes.'
  },
  {
    q: 'Can I track customer credits, debts, and partial payments?',
    a: 'Absolutely. RetailPOS features a built-in Customer Debt Ledger. During checkout, cashiers can assign a sale to a registered customer. If the customer pays a partial amount, the remaining balance is automatically saved as debt with optional timestamped notes. When the customer pays later, you can settle it with a single tap.'
  },
  {
    q: 'How do I add staff cashiers and assign permissions?',
    a: 'From the Store Owner Portal, go to the Staff section. You can create staff profiles, generate custom Staff IDs (e.g. STF1001), set passwords, and check off specific permissions (e.g., Record Sales, View Products, Manage Products, View Analytics, Manage Staff).'
  },
  {
    q: 'Can I use RetailPOS on multiple store branches?',
    a: 'Yes! Store owners can create multiple distinct store branches (e.g., "Main Supermarket", "Branch 2 - Express"). Each branch has its own isolated staff, products, and sales logs, while the owner dashboard aggregates analytics across all locations.'
  }
]
</script>

<template>
  <div class="min-h-screen bg-(--ui-bg) text-(--ui-text)">
    <!-- Sticky Navigation Header -->
    <header class="sticky top-0 z-50 backdrop-blur-xl bg-(--ui-bg)/85 border-b border-(--ui-border) transition-all duration-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <NuxtLink to="/" class="cursor-pointer flex items-center gap-2">
          <BrandLogo />
        </NuxtLink>

        <!-- Desktop Navigation Links (Visible on Large Screens lg:) -->
        <nav class="hidden lg:flex items-center gap-7 text-xs font-semibold text-(--ui-text-muted)">
          <a href="#features" class="hover:text-emerald-500 transition">Features</a>
          <a href="#demo" class="hover:text-emerald-500 transition">Live Demo</a>
          <a href="#architecture" class="hover:text-emerald-500 transition">How It Works</a>
          <a href="#calculator" class="hover:text-emerald-500 transition">Savings Calculator</a>
          <a href="#use-cases" class="hover:text-emerald-500 transition">Store Types</a>
          <a href="#comparison" class="hover:text-emerald-500 transition">Why RetailPOS</a>
          <a href="#pricing" class="hover:text-emerald-500 transition">Free Access</a>
          <a href="#faq" class="hover:text-emerald-500 transition">FAQ</a>
        </nav>

        <!-- Right Action Controls -->
        <div class="flex items-center gap-2 sm:gap-3">
          <!-- Color mode button (Always visible on mobile, tablet & desktop) -->
          <UColorModeButton />

          <!-- Sign In (Hidden on small mobile, visible on iPad/Tablet sm: and Desktop) -->
          <NuxtLink to="/login" class="hidden sm:inline-flex">
            <UButton variant="ghost" color="neutral" size="sm" class="font-medium text-xs">
              Sign In
            </UButton>
          </NuxtLink>

          <!-- Open Free Store (Hidden on small mobile, visible on iPad/Tablet sm: and Desktop) -->
          <NuxtLink to="/register" class="hidden sm:inline-flex">
            <UButton color="primary" size="sm" class="font-bold text-xs shadow-sm shadow-emerald-500/20">
              <UIcon name="i-lucide-store" class="w-3.5 h-3.5 mr-1" />
              Open Free Store
            </UButton>
          </NuxtLink>

          <!-- Hamburger Menu Button (Visible on Mobile and iPad/Tablet, Hidden on Desktop lg:) -->
          <button
            @click="isMobileMenuOpen = !isMobileMenuOpen"
            class="lg:hidden p-2 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)/60 hover:bg-(--ui-bg-muted) text-(--ui-text-highlighted) transition cursor-pointer flex items-center justify-center"
            aria-label="Toggle navigation menu"
          >
            <UIcon :name="isMobileMenuOpen ? 'i-lucide-x' : 'i-lucide-menu'" class="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>

    <!-- Mobile & Tablet Slideover Navigation Menu -->
    <USlideover v-model:open="isMobileMenuOpen" side="right" title="Navigation">
      <template #body>
        <div class="flex flex-col justify-between h-full space-y-6 py-2">
          <!-- Section Navigation Links -->
          <div class="space-y-1">
            <span class="text-[11px] font-mono uppercase tracking-wider text-(--ui-text-dimmed) font-bold px-3 block mb-2">
              Explore Platform
            </span>
            <a
              v-for="link in navLinks"
              :key="link.href"
              :href="link.href"
              @click="isMobileMenuOpen = false"
              class="flex items-center justify-between p-3 rounded-xl text-sm font-semibold text-(--ui-text-muted) hover:text-emerald-500 hover:bg-emerald-500/10 transition"
            >
              <div class="flex items-center gap-3">
                <UIcon :name="link.icon" class="w-4 h-4 text-emerald-500" />
                <span>{{ link.label }}</span>
              </div>
              <UIcon name="i-lucide-chevron-right" class="w-4 h-4 opacity-40" />
            </a>
          </div>

          <!-- Bottom Actions inside drawer -->
          <div class="space-y-3 pt-6 border-t border-(--ui-border)">
            <a :href="posUrl" target="_blank" @click="isMobileMenuOpen = false" class="block">
              <UButton block variant="outline" color="neutral" size="lg" class="font-semibold text-xs">
                <UIcon name="i-lucide-scan-barcode" class="w-4 h-4 mr-2 text-emerald-500" />
                Launch POS Cashier Terminal
              </UButton>
            </a>

            <NuxtLink to="/register" @click="isMobileMenuOpen = false" class="block">
              <UButton block color="primary" size="lg" class="font-bold text-xs shadow-md shadow-emerald-500/20">
                <UIcon name="i-lucide-store" class="w-4 h-4 mr-2" />
                Create Free Merchant Account
              </UButton>
            </NuxtLink>

            <NuxtLink to="/login" @click="isMobileMenuOpen = false" class="block">
              <UButton block variant="ghost" color="neutral" size="lg" class="font-medium text-xs">
                Merchant Owner Sign In
              </UButton>
            </NuxtLink>
          </div>
        </div>
      </template>
    </USlideover>

    <!-- Hero Section -->
    <section class="relative pt-12 pb-20 overflow-hidden hero-gradient">
      <!-- Glow background spheres -->
      <div class="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[650px] bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div class="absolute top-1/3 right-10 w-[450px] h-[450px] bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div class="text-center max-w-3xl mx-auto mb-10">
          <!-- Announcement badge -->
          <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 mb-6 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span>⚡ Public Beta 2.0 • 100% Free For All Testing Merchants</span>
          </div>

          <!-- Main Headline -->
          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.12] text-(--ui-text-highlighted) mb-6">
            Turn Any Device Into An <br class="hidden sm:inline" />
            <span class="text-gradient">Ultra-Fast, Offline Retail POS</span>
          </h1>

          <!-- Subheadline -->
          <p class="text-base sm:text-lg text-(--ui-text-muted) leading-relaxed mb-8">
            Replace expensive cash registers with phone-camera barcode scanning, instant offline transaction reconciliation, customer credit ledgers, and real-time multi-counter sync.
          </p>

          <!-- CTAs -->
          <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
            <NuxtLink to="/register" class="w-full sm:w-auto">
              <UButton size="xl" color="primary" class="w-full sm:w-auto px-8 py-3.5 font-bold shadow-lg shadow-emerald-500/30">
                <UIcon name="i-lucide-rocket" class="w-5 h-5 mr-2" />
                Create Free Merchant Account
              </UButton>
            </NuxtLink>

            <a :href="posUrl" target="_blank" class="w-full sm:w-auto">
              <UButton size="xl" variant="outline" color="neutral" class="w-full sm:w-auto px-6 py-3.5 font-semibold">
                <UIcon name="i-lucide-scan-barcode" class="w-5 h-5 mr-2 text-emerald-500" />
                Launch POS Register App
              </UButton>
            </a>
          </div>

          <!-- Trust points -->
          <div class="flex flex-wrap items-center justify-center gap-6 mt-8 text-xs font-medium text-(--ui-text-dimmed)">
            <span class="flex items-center gap-1.5">
              <UIcon name="i-lucide-check-circle-2" class="w-4 h-4 text-emerald-500" /> 100% Offline Capable
            </span>
            <span class="flex items-center gap-1.5">
              <UIcon name="i-lucide-check-circle-2" class="w-4 h-4 text-emerald-500" /> Zero Scanner Gun Needed
            </span>
            <span class="flex items-center gap-1.5">
              <UIcon name="i-lucide-check-circle-2" class="w-4 h-4 text-emerald-500" /> Free Public Beta
            </span>
            <span class="flex items-center gap-1.5">
              <UIcon name="i-lucide-check-circle-2" class="w-4 h-4 text-emerald-500" /> No Credit Card Required
            </span>
          </div>
        </div>

        <!-- Interactive POS Register Live Demo -->
        <div id="demo" class="mt-8">
          <div class="text-center mb-3">
            <span class="text-xs font-semibold uppercase tracking-wider text-emerald-500">Interactive Demo Simulator</span>
          </div>
          <InteractivePosDemo />
        </div>
      </div>
    </section>

    <!-- Superpower Metrics Strip -->
    <section class="py-12 border-y border-(--ui-border) bg-(--ui-bg-elevated)/60">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 md:grid-cols-5 gap-6 text-center">
          <div class="p-4 rounded-2xl bg-(--ui-bg) border border-(--ui-border)">
            <div class="text-2xl sm:text-3xl font-extrabold text-emerald-500 font-mono">0.1s</div>
            <div class="text-xs font-semibold text-(--ui-text-highlighted) mt-1">Instant Checkout Speed</div>
            <div class="text-[11px] text-(--ui-text-dimmed) mt-0.5">Zero waiting for slow internet</div>
          </div>
          <div class="p-4 rounded-2xl bg-(--ui-bg) border border-(--ui-border)">
            <div class="text-2xl sm:text-3xl font-extrabold text-emerald-500 font-mono">100%</div>
            <div class="text-xs font-semibold text-(--ui-text-highlighted) mt-1">Offline Selling Uptime</div>
            <div class="text-[11px] text-(--ui-text-dimmed) mt-0.5">Never lose a sale to outages</div>
          </div>
          <div class="p-4 rounded-2xl bg-(--ui-bg) border border-(--ui-border)">
            <div class="text-2xl sm:text-3xl font-extrabold text-emerald-500 font-mono">₦0</div>
            <div class="text-xs font-semibold text-(--ui-text-highlighted) mt-1">Scanner Gun Budget</div>
            <div class="text-[11px] text-(--ui-text-dimmed) mt-0.5">Built-in phone camera scan</div>
          </div>
          <div class="p-4 rounded-2xl bg-(--ui-bg) border border-(--ui-border)">
            <div class="text-2xl sm:text-3xl font-extrabold text-emerald-500 font-mono">60 FPS</div>
            <div class="text-xs font-semibold text-(--ui-text-highlighted) mt-1">Camera Barcode Engine</div>
            <div class="text-[11px] text-(--ui-text-dimmed) mt-0.5">EAN-13, UPC-A, Code-128</div>
          </div>
          <div class="p-4 rounded-2xl bg-(--ui-bg) border border-(--ui-border) col-span-2 md:col-span-1">
            <div class="text-2xl sm:text-3xl font-extrabold text-emerald-500 font-mono">Real-Time</div>
            <div class="text-xs font-semibold text-(--ui-text-highlighted) mt-1">Multi-Counter Sync</div>
            <div class="text-[11px] text-(--ui-text-dimmed) mt-0.5">Automatic inventory updates</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Key Feature Highlights (Interactive Tabs) -->
    <section id="features" class="py-20 border-b border-(--ui-border) bg-(--ui-bg)">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-16">
          <h2 class="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-2">Built for Modern Retail</h2>
          <h3 class="text-3xl sm:text-4xl font-extrabold text-(--ui-text-highlighted)">
            Everything your store needs to sell at lightspeed
          </h3>
          <p class="text-sm text-(--ui-text-muted) mt-2">
            Engineered to eliminate checkout lines, reduce cashier hardware costs, and guarantee zero downtime.
          </p>
        </div>

        <!-- Interactive feature tabs -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <!-- Left: Tab Buttons (5 cols) -->
          <div class="lg:col-span-5 space-y-3">
            <button
              v-for="feat in features"
              :key="feat.id"
              @click="activeFeatureTab = feat.id"
              class="w-full text-left p-4 sm:p-5 rounded-2xl transition-all duration-200 border cursor-pointer"
              :class="activeFeatureTab === feat.id ? 'bg-(--ui-bg) border-emerald-500 shadow-md shadow-emerald-500/10 ring-1 ring-emerald-500/30' : 'bg-(--ui-bg-elevated)/40 border-transparent hover:border-(--ui-border)'"
            >
              <div class="flex items-start gap-4">
                <div
                  class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition"
                  :class="activeFeatureTab === feat.id ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/30' : 'bg-(--ui-bg-muted) text-(--ui-text-muted)'"
                >
                  <UIcon :name="feat.icon" class="w-5 h-5" />
                </div>
                <div>
                  <h4 class="font-bold text-sm sm:text-base text-(--ui-text-highlighted)">{{ feat.title }}</h4>
                  <p class="text-xs text-(--ui-text-muted) mt-0.5">{{ feat.tagline }}</p>
                </div>
              </div>
            </button>
          </div>

          <!-- Right: Active Feature Details Showcase (7 cols) -->
          <div class="lg:col-span-7">
            <div class="glass-panel rounded-3xl p-8 border border-(--ui-border) relative overflow-hidden">
              <template v-for="feat in features" :key="feat.id">
                <div v-if="activeFeatureTab === feat.id" class="space-y-6 animate-fadeIn">
                  <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                    <UIcon :name="feat.icon" class="w-4 h-4" />
                    <span>Feature Highlights</span>
                  </div>

                  <h3 class="text-2xl font-bold text-(--ui-text-highlighted)">{{ feat.tagline }}</h3>
                  <p class="text-(--ui-text-muted) leading-relaxed text-sm sm:text-base">{{ feat.description }}</p>

                  <div class="space-y-3 pt-4 border-t border-(--ui-border)">
                    <div v-for="hl in feat.highlights" :key="hl" class="flex items-center gap-3 text-xs sm:text-sm font-medium text-(--ui-text)">
                      <div class="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center shrink-0">
                        <UIcon name="i-lucide-check" class="w-3.5 h-3.5" />
                      </div>
                      <span>{{ hl }}</span>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Architecture & How It Works Flow -->
    <section id="architecture" class="py-20 border-b border-(--ui-border) bg-(--ui-bg-elevated)/40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ArchitectureFlow />
      </div>
    </section>

    <!-- Interactive ROI / Cost Calculator -->
    <section id="calculator" class="py-20 border-b border-(--ui-border) bg-(--ui-bg)">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <RoiCalculator />
      </div>
    </section>

    <!-- Tailored Industry Solutions -->
    <section id="use-cases" class="py-20 border-b border-(--ui-border) bg-(--ui-bg-elevated)/40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <IndustrySolutions />
      </div>
    </section>

    <!-- Live Barcode Sandbox Tool -->
    <section id="sandbox" class="py-20 border-b border-(--ui-border) bg-(--ui-bg)">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <BarcodeSandbox />
      </div>
    </section>

    <!-- Traditional vs Cloud vs RetailPOS Comparison -->
    <section id="comparison" class="py-20 border-b border-(--ui-border) bg-(--ui-bg-elevated)/40">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-14">
          <h2 class="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-2">Cost & Capability</h2>
          <h3 class="text-3xl sm:text-4xl font-extrabold text-(--ui-text-highlighted)">
            Why Modern Merchants Choose RetailPOS
          </h3>
          <p class="text-sm text-(--ui-text-muted) mt-2">
            See how RetailPOS compares against legacy hardware registers and generic cloud POS systems.
          </p>
        </div>

        <div class="overflow-x-auto rounded-3xl border border-(--ui-border) glass-panel">
          <table class="w-full text-left border-collapse min-w-[600px]">
            <thead>
              <tr class="border-b border-(--ui-border) bg-(--ui-bg-elevated)">
                <th class="p-4 sm:p-5 text-xs sm:text-sm font-bold text-(--ui-text-highlighted)">Feature / Metric</th>
                <th class="p-4 sm:p-5 text-xs sm:text-sm font-semibold text-rose-500">Legacy Hardware POS</th>
                <th class="p-4 sm:p-5 text-xs sm:text-sm font-semibold text-amber-500">Generic Cloud POS</th>
                <th class="p-4 sm:p-5 text-xs sm:text-sm font-bold text-emerald-500 bg-emerald-500/10">RetailPOS</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-(--ui-border) text-xs sm:text-sm">
              <tr v-for="item in comparisonItems" :key="item.feature" class="hover:bg-(--ui-bg-muted)/40 transition">
                <td class="p-4 sm:p-5 font-medium text-(--ui-text-highlighted)">{{ item.feature }}</td>
                <td class="p-4 sm:p-5 text-(--ui-text-muted)">{{ item.traditional }}</td>
                <td class="p-4 sm:p-5 text-(--ui-text-muted)">{{ item.cloudPos }}</td>
                <td class="p-4 sm:p-5 font-bold text-emerald-500 bg-emerald-500/10">{{ item.retailPos }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Early Adopter Testimonials -->
    <section id="testimonials" class="py-20 border-b border-(--ui-border) bg-(--ui-bg)">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-14">
          <h2 class="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-2">Proven in the Field</h2>
          <h3 class="text-3xl sm:text-4xl font-extrabold text-(--ui-text-highlighted)">
            Loved by Early Adopter Retailers
          </h3>
          <p class="text-sm text-(--ui-text-muted) mt-2">
            Real feedback from supermarket owners, pharmacy managers, and boutique directors.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            v-for="t in testimonials"
            :key="t.author"
            class="p-6 sm:p-8 rounded-3xl border border-(--ui-border) glass-panel flex flex-col justify-between"
          >
            <div>
              <div class="flex items-center justify-between mb-4">
                <div class="flex gap-1 text-amber-400">
                  <UIcon v-for="i in 5" :key="i" name="i-lucide-star" class="w-4 h-4 fill-amber-400" />
                </div>
                <span class="text-[11px] font-semibold text-emerald-500 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                  {{ t.badge }}
                </span>
              </div>
              <p class="text-xs sm:text-sm text-(--ui-text) leading-relaxed italic">
                "{{ t.quote }}"
              </p>
            </div>

            <div class="pt-6 border-t border-(--ui-border) mt-6 flex items-center justify-between">
              <div>
                <h4 class="font-bold text-xs sm:text-sm text-(--ui-text-highlighted)">{{ t.author }}</h4>
                <p class="text-[11px] text-(--ui-text-muted)">{{ t.role }} • {{ t.location }}</p>
              </div>
              <span class="font-mono text-xs font-bold text-emerald-500">
                {{ t.metric }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Public Testing Free Tier Pricing Section -->
    <section id="pricing" class="py-20 border-b border-(--ui-border) bg-(--ui-bg-elevated)/40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-14">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 mb-3">
            <UIcon name="i-lucide-gift" class="w-4 h-4" />
            <span>Public Beta Testing Period</span>
          </div>
          <h3 class="text-3xl sm:text-4xl font-extrabold text-(--ui-text-highlighted)">
            100% Free During Public Beta
          </h3>
          <p class="text-sm text-(--ui-text-muted) mt-2">
            No subscriptions, no hidden fees, and no credit card required. Test all enterprise features with your store.
          </p>
        </div>

        <div class="max-w-4xl mx-auto">
          <!-- Featured Community Testing Card -->
          <div class="rounded-3xl p-8 sm:p-12 border-2 border-emerald-500 bg-(--ui-bg) relative shadow-2xl shadow-emerald-500/10 overflow-hidden">
            <div class="absolute -top-3 right-8 px-4 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500 text-slate-950 shadow-md">
              Full Access Included
            </div>

            <div class="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
              <div class="md:col-span-7 space-y-4">
                <h4 class="text-2xl font-extrabold text-(--ui-text-highlighted)">
                  Community Beta & Testing Tier
                </h4>
                <p class="text-sm text-(--ui-text-muted) leading-relaxed">
                  Join our merchant testing program and ring up transactions without paying a single kobo. Help us shape the future of offline-first retail.
                </p>

                <div class="py-4">
                  <div class="flex items-baseline gap-2">
                    <span class="text-4xl sm:text-5xl font-extrabold text-emerald-500 font-mono">₦0</span>
                    <span class="text-xs sm:text-sm text-(--ui-text-muted)">/ free testing access</span>
                  </div>
                  <span class="text-xs text-emerald-600 dark:text-emerald-400 font-semibold block mt-1">
                    ✓ No credit card required • Instant automated setup
                  </span>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                  <div class="flex items-center gap-2 text-xs font-medium text-(--ui-text)">
                    <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>Unlimited Store Branches</span>
                  </div>
                  <div class="flex items-center gap-2 text-xs font-medium text-(--ui-text)">
                    <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>Unlimited Cashier Accounts</span>
                  </div>
                  <div class="flex items-center gap-2 text-xs font-medium text-(--ui-text)">
                    <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>100% Offline Selling Capability</span>
                  </div>
                  <div class="flex items-center gap-2 text-xs font-medium text-(--ui-text)">
                    <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>Phone Camera Barcode Scanning</span>
                  </div>
                  <div class="flex items-center gap-2 text-xs font-medium text-(--ui-text)">
                    <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>Customer Debt & Credit Ledger</span>
                  </div>
                  <div class="flex items-center gap-2 text-xs font-medium text-(--ui-text)">
                    <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>Thermal Receipt Printing</span>
                  </div>
                </div>
              </div>

              <div class="md:col-span-5 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 p-6 rounded-2xl border border-slate-800 text-white text-center space-y-4">
                <div class="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                  <UIcon name="i-lucide-shield-check" class="w-6 h-6" />
                </div>
                <h5 class="text-base font-bold text-white">Start Testing Today</h5>
                <p class="text-xs text-slate-400">
                  Open your owner portal, add your store branch, provision your first cashier, and experience instant checkout speed.
                </p>

                <NuxtLink to="/register" class="block">
                  <button class="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 cursor-pointer">
                    <UIcon name="i-lucide-sparkles" class="w-4 h-4" />
                    Create Free Store Account
                  </button>
                </NuxtLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Interactive FAQ Section -->
    <section id="faq" class="py-20 border-b border-(--ui-border) bg-(--ui-bg)">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-14">
          <h2 class="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-2">Got Questions?</h2>
          <h3 class="text-3xl font-extrabold text-(--ui-text-highlighted)">Frequently Asked Questions</h3>
          <p class="text-sm text-(--ui-text-muted) mt-2">
            Everything you need to know about offline selling, hardware compatibility, and cashier permissions.
          </p>
        </div>

        <div class="space-y-3">
          <div
            v-for="(faq, idx) in faqs"
            :key="faq.q"
            class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)/40 overflow-hidden transition-all"
          >
            <button
              @click="toggleFaq(idx)"
              class="w-full p-5 sm:p-6 text-left flex items-center justify-between gap-4 cursor-pointer hover:bg-(--ui-bg-muted)/30 transition"
            >
              <h4 class="font-bold text-sm sm:text-base text-(--ui-text-highlighted)">{{ faq.q }}</h4>
              <UIcon
                name="i-lucide-chevron-down"
                class="w-5 h-5 text-(--ui-text-muted) transition-transform duration-200 shrink-0"
                :class="openFaqIndex === idx ? 'rotate-180 text-emerald-500' : ''"
              />
            </button>

            <div
              v-if="openFaqIndex === idx"
              class="px-5 sm:px-6 pb-6 text-xs sm:text-sm text-(--ui-text-muted) leading-relaxed border-t border-(--ui-border) pt-4 animate-fadeIn"
            >
              {{ faq.a }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- High-Impact Bottom Call to Action -->
    <section class="py-20 bg-gradient-to-tr from-emerald-950/50 via-(--ui-bg) to-teal-950/40 relative overflow-hidden">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-500/10 via-transparent to-transparent pointer-events-none" />

      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <div class="w-14 h-14 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-emerald-500/10">
          <UIcon name="i-lucide-shopping-bag" class="w-7 h-7" />
        </div>

        <h3 class="text-3xl sm:text-5xl font-extrabold text-(--ui-text-highlighted) tracking-tight mb-4">
          Ready to Supercharge Your Retail Store?
        </h3>
        <p class="text-sm sm:text-base text-(--ui-text-muted) max-w-xl mx-auto mb-8 leading-relaxed">
          Join forward-thinking merchants ringing up sales offline with zero hardware baggage and instant checkout speed.
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
          <NuxtLink to="/register" class="w-full sm:w-auto">
            <UButton size="xl" color="primary" class="w-full sm:w-auto px-8 py-3.5 font-bold shadow-xl shadow-emerald-500/25">
              <UIcon name="i-lucide-rocket" class="w-5 h-5 mr-2" />
              Open Your Free Store in 60s
            </UButton>
          </NuxtLink>

          <a :href="posUrl" target="_blank" class="w-full sm:w-auto">
            <UButton size="xl" variant="outline" color="neutral" class="w-full sm:w-auto px-6 py-3.5 font-semibold">
              <UIcon name="i-lucide-scan-barcode" class="w-5 h-5 mr-2 text-emerald-500" />
              Test POS Terminal App
            </UButton>
          </a>
        </div>
      </div>
    </section>

    <!-- Rich Multi-Column Footer with Responsive Mobile Grid -->
    <footer class="py-14 border-t border-(--ui-border) bg-(--ui-bg)">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- 2-Column Grid on Mobile, 12-Column Grid on Desktop -->
        <div class="grid grid-cols-2 md:grid-cols-12 gap-8 gap-y-10 pb-12 border-b border-(--ui-border)">
          <!-- Col 1: Brand (Spans full 2 columns on mobile, 4 cols on desktop) -->
          <div class="col-span-2 md:col-span-4 space-y-4">
            <BrandLogo />
            <p class="text-xs text-(--ui-text-muted) leading-relaxed max-w-sm">
              The next-generation offline-first multi-store retail POS platform. Ring up sales anywhere, anytime, with zero hardware dependencies.
            </p>
            <div class="flex items-center gap-3 text-xs text-(--ui-text-dimmed)">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500 font-mono font-semibold">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                Network Systems Operational
              </span>
            </div>
          </div>

          <!-- Col 2: Product (1 col on mobile, 2 cols on desktop) -->
          <div class="col-span-1 md:col-span-2 space-y-3">
            <h5 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-highlighted)">Product</h5>
            <ul class="space-y-2 text-xs text-(--ui-text-muted)">
              <li><a href="#features" class="hover:text-emerald-500 transition">Core Features</a></li>
              <li><a href="#demo" class="hover:text-emerald-500 transition">Register Demo</a></li>
              <li><a href="#architecture" class="hover:text-emerald-500 transition">How It Works</a></li>
              <li><a href="#calculator" class="hover:text-emerald-500 transition">ROI Calculator</a></li>
              <li><a href="#sandbox" class="hover:text-emerald-500 transition">Barcode Sandbox</a></li>
            </ul>
          </div>

          <!-- Col 3: Retail Solutions (1 col on mobile, 3 cols on desktop) -->
          <div class="col-span-1 md:col-span-3 space-y-3">
            <h5 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-highlighted)">Solutions</h5>
            <ul class="space-y-2 text-xs text-(--ui-text-muted)">
              <li><a href="#use-cases" class="hover:text-emerald-500 transition">Supermarkets & Groceries</a></li>
              <li><a href="#use-cases" class="hover:text-emerald-500 transition">Pharmacies & Chemists</a></li>
              <li><a href="#use-cases" class="hover:text-emerald-500 transition">Fashion Boutiques</a></li>
              <li><a href="#use-cases" class="hover:text-emerald-500 transition">Electronics & Hardware</a></li>
              <li><a href="#use-cases" class="hover:text-emerald-500 transition">Food Trucks & Pop-ups</a></li>
            </ul>
          </div>

          <!-- Col 4: Portals & Access (Spans 2 cols on mobile or nicely placed, 3 cols on desktop) -->
          <div class="col-span-2 sm:col-span-1 md:col-span-3 space-y-3">
            <h5 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-highlighted)">Portals & Access</h5>
            <ul class="space-y-2 text-xs text-(--ui-text-muted)">
              <li><NuxtLink to="/register" class="hover:text-emerald-500 transition">Open Free Store</NuxtLink></li>
              <li><NuxtLink to="/login" class="hover:text-emerald-500 transition">Merchant Owner Sign In</NuxtLink></li>
              <li><a :href="posUrl" target="_blank" class="hover:text-emerald-500 transition">Cashier POS Terminal</a></li>
              <li><a href="#pricing" class="hover:text-emerald-500 transition">Public Beta Program</a></li>
              <li><a href="#faq" class="hover:text-emerald-500 transition">Merchant FAQ</a></li>
            </ul>
          </div>
        </div>

        <!-- Bottom Copyright & Badges -->
        <div class="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-(--ui-text-muted)">
          <p>© {{ new Date().getFullYear() }} RetailPOS Platform. All rights reserved.</p>
          <div class="flex flex-wrap items-center gap-4 text-xs text-(--ui-text-dimmed)">
            <span class="text-emerald-500 font-semibold">100% Offline-Ready POS</span>
            <span>•</span>
            <span>Bank-Grade Cloud Backup</span>
            <span>•</span>
            <span>Multi-Counter Live Sync</span>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>
