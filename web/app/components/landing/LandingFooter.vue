<script setup lang="ts">
const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'
</script>

<template>
  <footer class="border-t border-(--ui-border) bg-(--ui-bg-elevated)/40 pt-16 pb-12 transition-colors">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
        <div class="space-y-4 md:col-span-1">
          <BrandLogo />
          <p class="text-xs text-(--ui-text-muted) leading-relaxed">
            Offline-first retail POS platform that turns any smartphone, tablet, or laptop into a full checkout register with zero hardware costs.
          </p>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-[11px] font-bold">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Public Beta Testing</span>
          </div>
        </div>

        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-highlighted) mb-4">Product</h4>
          <ul class="space-y-2.5 text-xs text-(--ui-text-muted)">
            <li><NuxtLink to="/how-it-works" class="hover:text-emerald-500 transition">How It Works</NuxtLink></li>
            <li><NuxtLink to="/pricing" class="hover:text-emerald-500 transition">Hardware Economics</NuxtLink></li>
            <li><NuxtLink to="/pricing#calculator" class="hover:text-emerald-500 transition">Savings Calculator</NuxtLink></li>
            <li><NuxtLink to="/why-kluda" class="hover:text-emerald-500 transition">Why Kluda</NuxtLink></li>
            <li><a :href="posUrl" target="_blank" class="hover:text-emerald-500 transition flex items-center gap-1"><span>Cashier Terminal App</span><UIcon name="i-lucide-external-link" class="w-3 h-3" /></a></li>
          </ul>
        </div>

        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-highlighted) mb-4">Store Solutions</h4>
          <ul class="space-y-2.5 text-xs text-(--ui-text-muted)">
            <li><NuxtLink to="/solutions/supermarkets" class="hover:text-emerald-500 transition">Supermarkets & Mini-Marts</NuxtLink></li>
            <li><NuxtLink to="/solutions/pharmacies" class="hover:text-emerald-500 transition">Pharmacies & Chemists</NuxtLink></li>
            <li><NuxtLink to="/solutions/boutiques" class="hover:text-emerald-500 transition">Fashion & Boutiques</NuxtLink></li>
            <li><NuxtLink to="/solutions" class="hover:text-emerald-500 transition">All Store Types</NuxtLink></li>
          </ul>
        </div>

        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-(--ui-text-highlighted) mb-4">Merchant Portal</h4>
          <ul class="space-y-2.5 text-xs text-(--ui-text-muted)">
            <li><a :href="`${posUrl}/auth/register`" class="hover:text-emerald-500 transition">Create Merchant Account</a></li>
            <li><a :href="`${posUrl}/auth/login`" class="hover:text-emerald-500 transition">Owner Sign In</a></li>
            <li><NuxtLink to="/pricing#faq" class="hover:text-emerald-500 transition">Retailer FAQ</NuxtLink></li>
          </ul>
        </div>
      </div>

      <div class="pt-8 border-t border-(--ui-border) flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-(--ui-text-dimmed)">
        <p>© {{ new Date().getFullYear() }} Kluda Retail Platform. Built for retailers where internet isn't guaranteed.</p>
        <div class="flex items-center gap-6">
          <NuxtLink to="/pricing" class="hover:text-(--ui-text-muted) transition">Hardware & Pricing</NuxtLink>
          <NuxtLink to="/why-kluda" class="hover:text-(--ui-text-muted) transition">Manifesto</NuxtLink>
          <a :href="`${posUrl}/auth/login`" class="hover:text-(--ui-text-muted) transition">Portal Access</a>
        </div>
      </div>
    </div>
  </footer>
</template>
