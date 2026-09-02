<script setup lang="ts">
const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'
const apiBase = config.public.apiBase || 'http://localhost:8000/api/v1'

const contact = ref({
  email: 'support@kluda.com',
  phone: '+234 800 000 5583',
  whatsapp: '2348000005583',
  address: 'Lagos, Nigeria',
  twitter: 'https://x.com/kluda_app',
  linkedin: 'https://linkedin.com/company/kluda',
  instagram: 'https://instagram.com/kluda.pos'
})

onMounted(async () => {
  try {
    const res = await $fetch<any>(`${apiBase}/auth/contact-info`)
    if (res) {
      contact.value = { ...contact.value, ...res }
    }
  } catch {
    // fallback to defaults
  }
})
</script>

<template>
  <footer class="border-t border-(--ui-border) bg-(--ui-bg-elevated)/40 pt-16 pb-12 transition-colors">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-5 gap-10 mb-12">
        <div class="space-y-4 md:col-span-2">
          <BrandLogo />
          <p class="text-xs text-(--ui-text-muted) leading-relaxed max-w-sm">
            Offline-first retail POS platform that turns any smartphone, tablet, or laptop into a full checkout register with zero expensive machines to buy.
          </p>
          
          <div class="space-y-2 pt-1 text-xs text-(--ui-text-muted)">
            <p class="flex items-center gap-2">
              <UIcon name="i-lucide-mail" class="w-4 h-4 text-emerald-500 shrink-0" />
              <a :href="`mailto:${contact.email}`" class="hover:text-emerald-400 transition">{{ contact.email }}</a>
            </p>
            <p class="flex items-center gap-2">
              <UIcon name="i-lucide-phone" class="w-4 h-4 text-emerald-500 shrink-0" />
              <a :href="`tel:${contact.phone}`" class="hover:text-emerald-400 transition">{{ contact.phone }}</a>
            </p>
            <p class="flex items-center gap-2">
              <UIcon name="i-lucide-map-pin" class="w-4 h-4 text-emerald-500 shrink-0" />
              <span>{{ contact.address }}</span>
            </p>
          </div>

          <!-- Social Handles -->
          <div class="flex items-center gap-3 pt-2">
            <a
              :href="`https://wa.me/${contact.whatsapp}`"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-black flex items-center justify-center transition"
              title="Chat on WhatsApp"
            >
              <UIcon name="i-lucide-message-circle" class="w-4 h-4" />
            </a>
            <a
              :href="contact.twitter"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-zinc-800/60 border border-zinc-700/60 text-zinc-300 hover:text-white hover:bg-zinc-700 flex items-center justify-center transition"
              title="Follow on X"
            >
              <UIcon name="i-lucide-twitter" class="w-4 h-4" />
            </a>
            <a
              :href="contact.linkedin"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-zinc-800/60 border border-zinc-700/60 text-zinc-300 hover:text-white hover:bg-zinc-700 flex items-center justify-center transition"
              title="LinkedIn"
            >
              <UIcon name="i-lucide-linkedin" class="w-4 h-4" />
            </a>
            <a
              :href="contact.instagram"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-zinc-800/60 border border-zinc-700/60 text-zinc-300 hover:text-white hover:bg-zinc-700 flex items-center justify-center transition"
              title="Instagram"
            >
              <UIcon name="i-lucide-instagram" class="w-4 h-4" />
            </a>
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
