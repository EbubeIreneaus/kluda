<script setup lang="ts">
import { ref, computed } from 'vue'

const showPassword = ref(false)

const agreeTerms = ref(true)

const {form: userForm, reset:restUserForm} = useForm({
  fullname: "",
  email: "",
  phone: "",
  password: ""
})

const {form: storeForm, reset: resetStoreForm} = useForm(
  {
    name: "",
    category: "",
    website: ""
  }
)

const isLoading = ref(false)
const errorMsg = ref('')

const toast = useToast()
const ownerStore = useOwnerStore()
const config = useRuntimeConfig()

const categories = [
  { label: 'General Retail', icon: 'i-lucide-shopping-bag' },
  { label: 'Supermarket & Grocery', icon: 'i-lucide-store' },
  { label: 'Pharmacy & Chemist', icon: 'i-lucide-pill' },
  { label: 'Fashion Boutique & Apparel', icon: 'i-lucide-sparkles' },
  { label: 'Electronics, Phone & Gadgets', icon: 'i-lucide-wrench' },
  { label: 'Restaurant, Bakery & Cafe', icon: 'i-lucide-coffee' },
  { label: 'Cosmetics & Beauty', icon: 'i-lucide-heart' }
]

const passwordStrength = computed(() => {
  const password = userForm.value.password
  if (!password) return 0
  let score = 0
  if (password.length >= 6) score += 33
  if (password.length >= 8) score += 33
  if (/[0-9]/.test(password) || /[^A-Za-z0-9]/.test(password)) score += 34
  return Math.min(100, score)
})

const passwordStrengthLabel = computed(() => {
  if (passwordStrength.value === 0) return ''
  if (passwordStrength.value < 50) return 'Weak password'
  if (passwordStrength.value < 80) return 'Medium password'
  return 'Strong password'
})

const passwordStrengthColor = computed(() => {
  if (passwordStrength.value < 50) return 'bg-rose-500'
  if (passwordStrength.value < 80) return 'bg-amber-500'
  return 'bg-emerald-500'
})

async function handleRegister() {
  if (!userForm.value.fullname || !userForm.value.email || !userForm.value.password) {
    toast.add({ title: 'Please fill all required fields', color: 'warning' })
    return
  }

  if (!agreeTerms.value) {
    toast.add({ title: 'Please accept the terms to proceed', color: 'warning' })
    return
  }

  errorMsg.value = ''
  isLoading.value = true

  try {
    const regRes = await $fetch<{ access_token?: string, user: any, success: boolean }>(`${config.public.apiBase}/auth/register`, {
      method: 'POST',
      credentials: 'include',
      body: userForm.value
    })

    toast.add({
      title: 'Account Created!',
      description: `Welcome to RetailPOS, ${regRes.user?.fullname || 'Merchant'}!`,
      color: 'success'
    })

    await navigateTo('/login')
  } catch (err: any) {
    errorMsg.value = err?.data?.detail || 'Registration failed. Please check your details.'
    toast.add({ title: 'Sign up failed', description: errorMsg.value, color: 'error' })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-(--ui-bg) text-(--ui-text) flex flex-col justify-between hero-gradient relative overflow-hidden">
    <!-- Ambient glow spheres -->
    <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
    <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

    <!-- Top Bar Navigation -->
    <header class="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between relative z-20">
      <NuxtLink to="/" class="cursor-pointer flex items-center gap-2">
        <BrandLogo />
      </NuxtLink>

      <div class="flex items-center gap-3">
        <UColorModeButton />

        <NuxtLink to="/login">
          <UButton variant="ghost" color="neutral" size="sm" class="text-xs font-semibold">
            Sign In
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

    <!-- Main Registration Container -->
    <main class="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-6 relative z-10">
      <div class="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        <!-- Left Side: Onboarding Roadmap & Value (Hidden on mobile, 5 cols on desktop) -->
        <div class="hidden lg:flex lg:col-span-5 flex-col justify-between space-y-8 p-8 rounded-3xl bg-slate-950 text-white border border-emerald-500/30 shadow-2xl relative overflow-hidden">
          <div class="space-y-6">
            <!-- Badge -->
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <UIcon name="i-lucide-sparkles" class="w-4 h-4" />
              <span>Instant Store Activation</span>
            </div>

            <h2 class="text-2xl sm:text-3xl font-extrabold text-white leading-tight">
              Open Your Retail Store in Under 60 Seconds
            </h2>

            <p class="text-xs text-slate-300 leading-relaxed">
              No hardware purchases, no credit card, and no setup fees. Get instant access to full offline selling and multi-store management.
            </p>

            <!-- 3-Step Visual Roadmap -->
            <div class="space-y-3 pt-2">
              <div class="flex items-start gap-3 p-3 rounded-xl bg-slate-900/90 border border-emerald-500/30">
                <div class="w-6 h-6 rounded-full bg-emerald-500 text-slate-950 font-bold text-xs flex items-center justify-center shrink-0">
                  1
                </div>
                <div>
                  <h4 class="font-bold text-xs text-white">Create Owner Account</h4>
                  <p class="text-[11px] text-slate-400">Set up your business credentials</p>
                </div>
              </div>

              <div class="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <div class="w-6 h-6 rounded-full bg-slate-800 text-slate-300 font-bold text-xs flex items-center justify-center shrink-0">
                  2
                </div>
                <div>
                  <h4 class="font-bold text-xs text-slate-200">Add Store Branch</h4>
                  <p class="text-[11px] text-slate-400">Provision your store catalog & stock</p>
                </div>
              </div>

              <div class="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <div class="w-6 h-6 rounded-full bg-slate-800 text-slate-300 font-bold text-xs flex items-center justify-center shrink-0">
                  3
                </div>
                <div>
                  <h4 class="font-bold text-xs text-slate-200">Launch Register on Any Phone</h4>
                  <p class="text-[11px] text-slate-400">Scan barcodes & ring up sales offline</p>
                </div>
              </div>
            </div>
          </div>

          <div class="pt-6 border-t border-slate-800/80 space-y-2 text-xs">
            <div class="flex items-center justify-between text-slate-300">
              <span class="flex items-center gap-1.5">
                <UIcon name="i-lucide-gift" class="w-4 h-4 text-emerald-400" />
                Testing Access:
              </span>
              <span class="font-mono text-emerald-400 font-bold">100% Free Forever</span>
            </div>
            <div class="flex items-center justify-between text-slate-300">
              <span class="flex items-center gap-1.5">
                <UIcon name="i-lucide-credit-card" class="w-4 h-4 text-emerald-400" />
                Billing Details:
              </span>
              <span class="font-mono text-emerald-400 font-bold">No Credit Card Needed</span>
            </div>
          </div>
        </div>

        <div class="lg:col-span-7">
          <div class="glass-panel p-6 sm:p-10 rounded-3xl border border-(--ui-border) shadow-2xl relative">
            <div class="mb-6">
              <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 mb-3">
                <UIcon name="i-lucide-store" class="w-3.5 h-3.5" />
                <span>Free Merchant Registration</span>
              </div>
              <h1 class="text-2xl sm:text-3xl font-extrabold text-(--ui-text-highlighted)">
                Open Your Store Account 🚀
              </h1>
              <p class="text-xs sm:text-sm text-(--ui-text-muted) mt-1">
                Fill in your details below to activate your merchant workspace.
              </p>
            </div>

            <form class="space-y-4" @submit.prevent="handleRegister">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField label="Your Full Name" required>
                  <UInput
                    v-model="userForm.fullname"
                    placeholder="e.g. Chukwuma Adeleke"
                    icon="i-lucide-user"
                    size="lg"
                    required
                    autocomplete="name"
                    autofocus
                    class="w-full"
                  />
                </UFormField>

                <UFormField label="Business Email" required>
                  <UInput
                    v-model="userForm.email"
                    type="email"
                    placeholder="owner@yourstore.com"
                    icon="i-lucide-mail"
                    size="lg"
                    required
                    autocomplete="email"
                    class="w-full"
                  />
                </UFormField>
              </div>

              <UFormField label="Phone Number (Optional)">
                <UInput
                  v-model="userForm.phone"
                  type="tel"
                  placeholder="0801 234 5678"
                  icon="i-lucide-phone"
                  size="lg"
                  autocomplete="tel"
                  class="w-full"
                />
              </UFormField>

              <UFormField label="Create Password" required>
                <div class="relative">
                  <UInput
                    v-model="userForm.password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="At least 6 characters"
                    icon="i-lucide-lock"
                    size="lg"
                    required
                    autocomplete="new-password"
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

                <div v-if="userForm.password" class="mt-2 space-y-1">
                  <div class="w-full h-1.5 bg-(--ui-bg-muted) rounded-full overflow-hidden">
                    <div
                      class="h-full transition-all duration-300"
                      :class="passwordStrengthColor"
                      :style="{ width: `${passwordStrength}%` }"
                    />
                  </div>
                  <span class="text-[11px] text-(--ui-text-dimmed) block">
                    {{ passwordStrengthLabel }}
                  </span>
                </div>
              </UFormField>

              <div class="flex items-start gap-2.5 text-xs text-(--ui-text-muted) pt-1">
                <input
                  v-model="agreeTerms"
                  type="checkbox"
                  id="agree-terms"
                  class="mt-0.5 rounded border-(--ui-border) text-emerald-500 focus:ring-emerald-500 h-4 w-4 shrink-0"
                />
                <label for="agree-terms" class="cursor-pointer select-none">
                  I agree to the Free Public Beta testing terms and acknowledge that RetailPOS stores data locally with cloud synchronization.
                </label>
              </div>

              <div v-if="errorMsg" class="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs flex items-center gap-2.5 animate-fadeIn">
                <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 shrink-0" />
                <span>{{ errorMsg }}</span>
              </div>

              <UButton
                type="submit"
                block
                size="xl"
                color="primary"
                :loading="isLoading"
                class="font-bold text-xs sm:text-sm py-3.5 shadow-lg shadow-emerald-500/25 cursor-pointer uppercase tracking-wider mt-2"
              >
                <UIcon name="i-lucide-rocket" class="w-4 h-4 mr-2" />
                Launch My Free Store Account
              </UButton>
            </form>

            <div class="mt-6 pt-4 border-t border-(--ui-border) flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-(--ui-text-muted)">
              <span>Already have an owner account?</span>
              <NuxtLink to="/login">
                <UButton variant="outline" color="neutral" size="sm" class="font-semibold text-xs">
                  <UIcon name="i-lucide-log-in" class="w-3.5 h-3.5 mr-1.5 text-emerald-500" />
                  Sign In to Dashboard
                </UButton>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-center text-xs text-(--ui-text-dimmed) relative z-20">
      © {{ new Date().getFullYear() }} RetailPOS Platform. Free Public Beta.
    </footer>
  </div>
</template>
