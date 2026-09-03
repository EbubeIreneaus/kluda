<script setup lang="ts">
const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'
const apiBase = config.public.apiBase || 'http://localhost:8000/api/v1'

const contact = ref<Record<string, any>>({})

onMounted(async () => {
  try {
    const res = await $fetch<any>(`${apiBase}/auth/contact-info`)
    if (res && typeof res === 'object') {
      contact.value = res
    }
  } catch {
    // keep empty if fetch fails
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
          
          <div v-if="contact.email || contact.phone || contact.address || contact.hours" class="space-y-2 pt-1 text-xs text-(--ui-text-muted)">
            <p v-if="contact.email" class="flex items-center gap-2">
              <UIcon name="i-lucide-mail" class="w-4 h-4 text-emerald-500 shrink-0" />
              <a :href="`mailto:${contact.email}`" class="hover:text-emerald-400 transition">{{ contact.email }}</a>
            </p>
            <p v-if="contact.phone" class="flex items-center gap-2">
              <UIcon name="i-lucide-phone" class="w-4 h-4 text-emerald-500 shrink-0" />
              <a :href="`tel:${contact.phone}`" class="hover:text-emerald-400 transition">{{ contact.phone }}</a>
            </p>
            <p v-if="contact.address" class="flex items-center gap-2">
              <UIcon name="i-lucide-map-pin" class="w-4 h-4 text-emerald-500 shrink-0" />
              <span>{{ contact.address }}</span>
            </p>
            <p v-if="contact.hours" class="flex items-center gap-2">
              <UIcon name="i-lucide-clock" class="w-4 h-4 text-emerald-500 shrink-0" />
              <span>{{ contact.hours }}</span>
            </p>
          </div>

          <!-- Social Handles -->
          <div
            v-if="contact.whatsapp || contact.facebook || contact.twitter || contact.linkedin || contact.instagram"
            class="flex items-center gap-3 pt-2"
          >
            <a
              v-if="contact.whatsapp"
              :href="`https://wa.me/${contact.whatsapp}`"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-black flex items-center justify-center transition"
              title="Chat on WhatsApp"
            >
              <UIcon name="i-lucide-message-circle" class="w-4 h-4" />
            </a>
            <a
              v-if="contact.facebook"
              :href="contact.facebook"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented) flex items-center justify-center transition shadow-xs"
              title="Follow on Facebook"
            >
              <UIcon name="i-lucide-facebook" class="w-4 h-4" />
            </a>
            <a
              v-if="contact.twitter"
              :href="contact.twitter"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented) flex items-center justify-center transition shadow-xs"
              title="Follow on X"
            >
              <UIcon name="i-lucide-twitter" class="w-4 h-4" />
            </a>
            <a
              v-if="contact.instagram"
              :href="contact.instagram"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented) flex items-center justify-center transition shadow-xs"
              title="Instagram"
            >
              <UIcon name="i-lucide-instagram" class="w-4 h-4" />
            </a>
            <a
              v-if="contact.linkedin"
              :href="contact.linkedin"
              target="_blank"
              rel="noopener noreferrer"
              class="w-8 h-8 rounded-xl bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented) flex items-center justify-center transition shadow-xs"
              title="LinkedIn"
            >
              <UIcon name="i-lucide-linkedin" class="w-4 h-4" />
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
            <li><NuxtLink to="/faq" class="hover:text-emerald-500 transition">Retailer FAQ & Help</NuxtLink></li>
            <li><NuxtLink to="/terms" class="hover:text-emerald-500 transition">Terms of Service</NuxtLink></li>
            <li><NuxtLink to="/privacy" class="hover:text-emerald-500 transition">Privacy Policy</NuxtLink></li>
          </ul>
        </div>
      </div>

      <div class="pt-8 border-t border-(--ui-border) flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-(--ui-text-dimmed)">
        <p>© {{ new Date().getFullYear() }} Kluda Retail Platform. Built for retailers where internet isn't guaranteed.</p>
        <div class="flex flex-wrap items-center gap-4 sm:gap-6">
          <NuxtLink to="/faq" class="hover:text-emerald-400 transition">FAQ</NuxtLink>
          <NuxtLink to="/terms" class="hover:text-emerald-400 transition">Terms of Service</NuxtLink>
          <NuxtLink to="/privacy" class="hover:text-emerald-400 transition">Privacy Policy</NuxtLink>
          <NuxtLink to="/pricing" class="hover:text-emerald-400 transition">Hardware & Pricing</NuxtLink>
        </div>
      </div>
    </div>
  </footer>
</template>
