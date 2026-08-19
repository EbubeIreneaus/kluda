<script setup lang="ts">
import { ref } from 'vue'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const rememberMe = ref(true)
const isLoading = ref(false)
const errorMsg = ref('')

const toast = useToast()
const ownerStore = useOwnerStore()
const config = useRuntimeConfig()

const activePerkIndex = ref(0)
const perks = [
  {
    icon: 'i-lucide-wifi-off',
    title: '100% Offline Selling Protection',
    description: 'Ring up sales, calculate change, and print receipts even during total internet or power cuts.'
  },
  {
    icon: 'i-lucide-scan-barcode',
    title: 'Zero Scanner Gun Expenses',
    description: 'Use any phone, tablet, or laptop camera to scan barcodes at 60 FPS with instant sound feedback.'
  },
  {
    icon: 'i-lucide-refresh-cw',
    title: 'Real-Time Multi-Counter Sync',
    description: 'Inventory drops instantly across all cashier screens to prevent overselling scarce items.'
  },
  {
    icon: 'i-lucide-book-open',
    title: 'Customer Credit & Debt Ledger',
    description: 'Track customer balances, credit purchases, and partial settlements directly at checkout.'
  }
]

// Auto-rotate perks every 5 seconds
if (import.meta.client) {
  setInterval(() => {
    activePerkIndex.value = (activePerkIndex.value + 1) % perks.length
  }, 5000)
}

async function handleLogin() {
  errorMsg.value = ''
  isLoading.value = true
  try {
    const res = await $fetch<{ access_token?: string, user: any, success: boolean }>(`${config.public.apiBase}/auth/login`, {
      method: 'POST',
      credentials: 'include',
      body: { email: email.value.trim().toLowerCase(), password: password.value }
    })

    ownerStore.setAuth(res.access_token || '', res.user)
    toast.add({ title: 'Welcome back!', description: `Signed in as ${res.user?.fullname || 'Merchant'}`, color: 'success' })
    navigateTo('/dashboard')
  } catch (err: any) {
    errorMsg.value = err?.data?.detail || 'Invalid email or password'
    toast.add({ title: 'Sign in failed', description: errorMsg.value, color: 'error' })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-(--ui-bg) text-(--ui-text) flex flex-col justify-between hero-gradient relative overflow-hidden">
    <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
    <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
    <header class="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between relative z-20">
      <NuxtLink to="/" class="cursor-pointer flex items-center gap-2">
        <BrandLogo />
      </NuxtLink>

      <div class="flex items-center gap-3">
        <UColorModeButton />

        <NuxtLink to="/register">
          <UButton variant="ghost" color="neutral" size="sm" class="text-xs font-semibold">
            Create Store Free
          </UButton>
        </NuxtLink>

        <NuxtLink to="/">
          <UButton variant="outline" color="neutral" size="sm" class="text-xs font-medium">
            <UIcon name="i-lucide-arrow-left" class="w-3.5 h-3.5 mr-1" />
            Home
          </UButton>
        </NuxtLink>
      </div>
    </header>

    <!-- Main Content Container -->
    <main class="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-6 relative z-10">
      <div class="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        <!-- Left Side: Visual Showcase & Benefits (Hidden on mobile, 5 cols on desktop) -->
        <div class="hidden lg:flex lg:col-span-5 flex-col justify-between space-y-8 p-8 rounded-3xl bg-slate-950 text-white border border-emerald-500/30 shadow-2xl relative overflow-hidden">
          <div class="space-y-6">
            <!-- Badge -->
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>Merchant Owner Control Hub</span>
            </div>

            <h2 class="text-2xl sm:text-3xl font-extrabold text-white leading-tight">
              Manage Your Stores & Registers from Anywhere
            </h2>

            <p class="text-xs text-slate-300 leading-relaxed">
              Log in to view live branch revenue, add product stock, provision cashier IDs, and review store performance.
            </p>

            <!-- Dynamic Rotating Perk Card -->
            <div class="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2 transition-all duration-300">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                  <UIcon :name="perks[activePerkIndex].icon" class="w-4 h-4" />
                </div>
                <h4 class="font-bold text-xs text-emerald-300">
                  {{ perks[activePerkIndex].title }}
                </h4>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed pl-11">
                {{ perks[activePerkIndex].description }}
              </p>
            </div>

            <!-- Perks Pagination Dots -->
            <div class="flex items-center justify-center gap-1.5 pt-1">
              <button
                v-for="(_, idx) in perks"
                :key="idx"
                @click="activePerkIndex = idx"
                class="w-2 h-2 rounded-full transition-all cursor-pointer"
                :class="activePerkIndex === idx ? 'w-6 bg-emerald-400' : 'bg-slate-700 hover:bg-slate-600'"
              />
            </div>
          </div>

          <!-- Live Trust Scorecard -->
          <div class="pt-6 border-t border-slate-800/80 space-y-3 text-xs">
            <div class="flex items-center justify-between text-slate-300">
              <span class="flex items-center gap-1.5">
                <UIcon name="i-lucide-shield-check" class="w-4 h-4 text-emerald-400" />
                Session Security:
              </span>
              <span class="font-mono text-emerald-400 font-semibold">13h Encrypted Token</span>
            </div>
            <div class="flex items-center justify-between text-slate-300">
              <span class="flex items-center gap-1.5">
                <UIcon name="i-lucide-activity" class="w-4 h-4 text-emerald-400" />
                Cloud Systems:
              </span>
              <span class="font-mono text-emerald-400 font-semibold">100% Operational</span>
            </div>
          </div>
        </div>

        <!-- Right Side: Interactive Sign-In Form (7 cols) -->
        <div class="lg:col-span-7">
          <div class="glass-panel p-6 sm:p-10 rounded-3xl border border-(--ui-border) shadow-2xl relative">
            <div class="mb-8">
              <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 mb-3">
                <UIcon name="i-lucide-key-round" class="w-3.5 h-3.5" />
                <span>Owner Portal Sign In</span>
              </div>
              <h1 class="text-2xl sm:text-3xl font-extrabold text-(--ui-text-highlighted)">
                Welcome Back, Merchant 👋
              </h1>
              <p class="text-xs sm:text-sm text-(--ui-text-muted) mt-1">
                Enter your business credentials to access your store dashboard.
              </p>
            </div>

            <form class="space-y-5" @submit.prevent="handleLogin">
              <!-- Business Email -->
              <UFormField label="Business Email" required>
                <UInput
                  v-model="email"
                  type="email"
                  placeholder="owner@yourstore.com"
                  icon="i-lucide-mail"
                  size="xl"
                  required
                  autocomplete="email"
                  autofocus
                  class="w-full"
                />
              </UFormField>

              <!-- Password with Eye Toggle -->
              <UFormField label="Password" required>
                <div class="relative">
                  <UInput
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="••••••••"
                    icon="i-lucide-lock"
                    size="xl"
                    required
                    autocomplete="current-password"
                    class="w-full pr-10"
                  />
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-(--ui-text-muted) hover:text-(--ui-text-highlighted) transition p-1 cursor-pointer"
                    aria-label="Toggle password visibility"
                  >
                    <UIcon :name="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'" class="w-4 h-4" />
                  </button>
                </div>
              </UFormField>

              <!-- Remember Me & Forgot Password -->
              <div class="flex items-center justify-between text-xs">
                <label class="flex items-center gap-2 cursor-pointer text-(--ui-text-muted) select-none">
                  <input
                    v-model="rememberMe"
                    type="checkbox"
                    class="rounded border-(--ui-border) text-emerald-500 focus:ring-emerald-500 h-4 w-4"
                  />
                  <span>Remember my login</span>
                </label>

                <NuxtLink to="/register" class="font-medium text-emerald-500 hover:text-emerald-400 transition">
                  Need an account?
                </NuxtLink>
              </div>

              <!-- Error Banner -->
              <div v-if="errorMsg" class="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs flex items-center gap-2.5 animate-fadeIn">
                <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 shrink-0" />
                <span>{{ errorMsg }}</span>
              </div>

              <!-- Submit Button -->
              <UButton
                type="submit"
                block
                size="xl"
                color="primary"
                :loading="isLoading"
                class="font-bold text-xs sm:text-sm py-3.5 shadow-lg shadow-emerald-500/25 cursor-pointer uppercase tracking-wider"
              >
                <UIcon name="i-lucide-log-in" class="w-4 h-4 mr-2" />
                Sign In to Dashboard
              </UButton>
            </form>

            <!-- Bottom Footnote -->
            <div class="mt-8 pt-6 border-t border-(--ui-border) flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-(--ui-text-muted)">
              <span>Don't have a merchant account yet?</span>
              <NuxtLink to="/register">
                <UButton variant="outline" color="neutral" size="sm" class="font-semibold text-xs">
                  <UIcon name="i-lucide-store" class="w-3.5 h-3.5 mr-1.5 text-emerald-500" />
                  Open Free Store
                </UButton>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-center text-xs text-(--ui-text-dimmed) relative z-20">
      © {{ new Date().getFullYear() }} Kluda Platform. Sell Faster, Track Everything.
    </footer>
  </div>
</template>
