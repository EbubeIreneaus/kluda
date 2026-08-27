<script setup lang="ts">
import { ref } from 'vue'

const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'
const route = useRoute()
const isMobileMenuOpen = ref(false)
const colorMode = useColorMode()

const navLinks = [
  { label: 'How It Works', to: '/how-it-works', icon: 'i-lucide-activity' },
  { label: 'Solutions', to: '/solutions', icon: 'i-lucide-layout-grid' },
  { label: 'Hardware & Pricing', to: '/pricing', icon: 'i-lucide-calculator' },
  { label: 'Why Kluda', to: '/why-kluda', icon: 'i-lucide-shield-check' }
]

function toggleColorMode() {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <header class="sticky top-0 z-50 w-full border-b border-(--ui-border) bg-(--ui-bg)/80 backdrop-blur-xl transition-colors">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <NuxtLink to="/" class="flex items-center gap-3">
        <BrandLogo />
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-1 bg-(--ui-bg-elevated)/60 border border-(--ui-border) px-3 py-1.5 rounded-full shadow-sm">
        <NuxtLink
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="px-4 py-2 rounded-full text-xs font-semibold transition flex items-center gap-2"
          :class="isActive(link.to) ? 'bg-emerald-500/15 text-emerald-500' : 'text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented)'"
        >
          <UIcon :name="link.icon" class="w-3.5 h-3.5" />
          <span>{{ link.label }}</span>
        </NuxtLink>
      </nav>

      <div class="hidden md:flex items-center gap-3">
        <button
          @click="toggleColorMode"
          class="p-2 rounded-xl border border-(--ui-border) text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented) transition"
          aria-label="Toggle Theme"
        >
          <UIcon :name="colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon'" class="w-4 h-4" />
        </button>

        <a
          :href="posUrl"
          target="_blank"
          class="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold border border-emerald-500/30 bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition"
        >
          <UIcon name="i-lucide-scan-barcode" class="w-4 h-4" />
          <span>POS Terminal</span>
        </a>

        <NuxtLink
          to="/login"
          class="text-xs font-bold text-(--ui-text-muted) hover:text-(--ui-text-highlighted) px-3 py-2 transition"
        >
          Sign In
        </NuxtLink>

        <NuxtLink
          to="/register"
          class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-extrabold text-xs shadow-lg shadow-emerald-500/25 transition active:scale-95"
        >
          <span>Start Selling Free</span>
          <UIcon name="i-lucide-arrow-right" class="w-3.5 h-3.5" />
        </NuxtLink>
      </div>

      <div class="flex md:hidden items-center gap-2">
        <button
          @click="toggleColorMode"
          class="p-2 rounded-xl border border-(--ui-border) text-(--ui-text-muted)"
          aria-label="Toggle Theme"
        >
          <UIcon :name="colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon'" class="w-4 h-4" />
        </button>

        <button
          @click="isMobileMenuOpen = !isMobileMenuOpen"
          class="p-2 rounded-xl border border-(--ui-border) text-(--ui-text-muted)"
          aria-label="Open Menu"
        >
          <UIcon :name="isMobileMenuOpen ? 'i-lucide-x' : 'i-lucide-menu'" class="w-5 h-5" />
        </button>
      </div>
    </div>

    <div v-if="isMobileMenuOpen" class="md:hidden border-t border-(--ui-border) bg-(--ui-bg-elevated) px-4 pt-3 pb-6 space-y-3">
      <div class="space-y-1">
        <NuxtLink
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          @click="isMobileMenuOpen = false"
          class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition"
          :class="isActive(link.to) ? 'bg-emerald-500/15 text-emerald-500 font-bold' : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented)'"
        >
          <UIcon :name="link.icon" class="w-4 h-4" />
          <span>{{ link.label }}</span>
        </NuxtLink>
      </div>

      <div class="pt-3 border-t border-(--ui-border) space-y-2">
        <a
          :href="posUrl"
          target="_blank"
          class="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-xs font-bold border border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
        >
          <UIcon name="i-lucide-scan-barcode" class="w-4 h-4" />
          <span>Launch POS Terminal</span>
        </a>

        <div class="grid grid-cols-2 gap-2">
          <NuxtLink
            to="/login"
            @click="isMobileMenuOpen = false"
            class="flex items-center justify-center py-2.5 rounded-xl text-xs font-bold border border-(--ui-border) text-(--ui-text-highlighted)"
          >
            Sign In
          </NuxtLink>

          <NuxtLink
            to="/register"
            @click="isMobileMenuOpen = false"
            class="flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-black font-extrabold text-xs shadow-md"
          >
            <span>Start Free</span>
            <UIcon name="i-lucide-arrow-right" class="w-3.5 h-3.5" />
          </NuxtLink>
        </div>
      </div>
    </div>
  </header>
</template>
