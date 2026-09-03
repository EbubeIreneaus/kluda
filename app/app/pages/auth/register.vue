<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({ layout: 'auth' })

const auth = useAuthStore()
const config = useRuntimeConfig()
const toast = useToast()
const route = useRoute()
const { getSavedReferralCode, getSavedPlan, getSavedTrial, clearSavedOnboardingParams } = useOnboardingParams()
const marketingWebUrl = computed(() => (config.public as any).webDashboardUrl || 'https://kluda.app')

const step = ref<1 | 2>(1)
const isLoading = ref(false)
const errorMsg = ref('')
const agreeTerms = ref(false)
const selectedPlan = ref('')
const hasTrialIntent = ref(false)

const form = ref({
  fullname: '',
  email: '',
  phone: '',
  password: '',
  store_name: '',
  store_category: 'Supermarket & Grocery',
  store_address: '',
  referral_code: ''
})

onMounted(() => {
  form.value.referral_code = getSavedReferralCode()
  selectedPlan.value = getSavedPlan()
  hasTrialIntent.value = getSavedTrial()
})

const categories = [
  'Supermarket & Grocery',
  'Fashion, Shoes & Boutique',
  'Pharmacy & Health',
  'Electronics & Gadgets',
  'Restaurant, Bar & Cafe',
  'Beauty, Cosmetics & Salon',
  'Hardware & Building Materials',
  'General Retail & Provisions'
]

function nextStep() {
  errorMsg.value = ''
  if (!form.value.fullname.trim() || !form.value.email.trim() || !form.value.password.trim()) {
    errorMsg.value = 'Please fill in all required fields'
    return
  }
  if (form.value.password.length < 6) {
    errorMsg.value = 'Password must be at least 6 characters'
    return
  }
  step.value = 2
}

async function handleRegister() {
  errorMsg.value = ''
  if (!form.value.store_name.trim()) {
    errorMsg.value = 'Please provide a name for your store branch'
    return
  }

  if (!agreeTerms.value) {
    errorMsg.value = 'You must agree to the Terms of Service and Privacy Policy to continue.'
    return
  }

  isLoading.value = true
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/auth/register`, {
      method: 'POST',
      credentials: 'include',
      body: form.value
    })

    if (data.user_access_token) {
      const primaryStore = data.stores?.[0]
      const nameParts = (data.user?.fullname || form.value.fullname).split(' ')
      const staffObj = {
        staff_id: 'OWNER',
        first_name: nameParts[0] || 'Store',
        last_name: nameParts.slice(1).join(' ') || 'Owner',
        role: 'owner',
        email: data.user?.email || form.value.email,
        store_id: primaryStore?.store_id || '',
        permission: ['manage:all', 'record:sales', 'view:product', 'manage:product'],
        status: 'active',
        has_pin: false,
        created_at: new Date().toISOString()
      }

      auth.setAuth(data.user_access_token, staffObj, primaryStore?.store_id, data.user_refresh_token)
      if (import.meta.client) {
        localStorage.setItem('has_completed_onboarding', 'true')
      }

      const planToNavigate = selectedPlan.value || getSavedPlan()
      clearSavedOnboardingParams()

      toast.add({
        title: 'Account & Store Created!',
        description: `Welcome to Kluda. Your store "${form.value.store_name}" is ready.`,
        color: 'success'
      })

      if (planToNavigate && planToNavigate !== 'free') {
        await navigateTo(`/marchant/billing#${planToNavigate}`)
      } else {
        await navigateTo('/')
      }
    } else {
      toast.add({
        title: 'Registration Successful',
        description: 'Please sign in to access your terminal.',
        color: 'success'
      })
      await navigateTo('/auth/login')
    }
  } catch (err: any) {
    errorMsg.value = err?.data?.detail || 'Failed to complete registration. Please try again.'
    toast.add({
      title: 'Registration Failed',
      description: errorMsg.value,
      color: 'error'
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="gradient-bg min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-(--ui-bg-elevated) border border-emerald-500/40 text-emerald-500 shadow-xl shadow-emerald-500/10 mb-4">
          <UIcon name="i-lucide-store" class="w-8 h-8" />
        </div>
        <h1 class="text-2xl font-extrabold tracking-tight text-(--ui-text-highlighted)">
          {{ step === 1 ? 'Create Your Account' : 'Set Up Your Store' }}
        </h1>
        <p class="text-xs text-(--ui-text-muted) mt-1">
          {{ step === 1 ? 'Step 1 of 2: Owner profile credentials' : 'Step 2 of 2: First store & register details' }}
        </p>

        <div class="flex items-center justify-center gap-2 mt-4">
          <div class="h-1.5 w-12 rounded-full transition-all duration-300" :class="step >= 1 ? 'bg-emerald-500' : 'bg-(--ui-bg-muted)'" />
          <div class="h-1.5 w-12 rounded-full transition-all duration-300" :class="step >= 2 ? 'bg-emerald-500' : 'bg-(--ui-bg-muted)'" />
        </div>
      </div>

      <div class="glass-panel p-6 sm:p-8 rounded-3xl border border-(--ui-border) shadow-2xl relative overflow-hidden">
        <div v-if="errorMsg" class="mb-5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs flex items-center gap-2.5">
          <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 shrink-0" />
          <span>{{ errorMsg }}</span>
        </div>

        <form v-if="step === 1" @submit.prevent="nextStep" class="space-y-4">
          <UFormField label="Full Name" required>
            <UInput
              v-model="form.fullname"
              placeholder="e.g. Chidinma Okonkwo"
              size="md"
              icon="i-lucide-user"
              required
            />
          </UFormField>

          <UFormField label="Email Address" required>
            <UInput
              v-model="form.email"
              type="email"
              placeholder="owner@mybusiness.com"
              size="md"
              icon="i-lucide-mail"
              required
            />
          </UFormField>

          <UFormField label="Phone Number (Optional)">
            <UInput
              v-model="form.phone"
              type="tel"
              placeholder="08012345678"
              size="md"
              icon="i-lucide-phone"
            />
          </UFormField>

          <UFormField label="Password" required>
            <UInput
              v-model="form.password"
              type="password"
              placeholder="••••••••"
              size="md"
              icon="i-lucide-lock"
              required
            />
          </UFormField>

          <UButton
            type="submit"
            block
            size="md"
            color="primary"
            class="font-bold py-3 mt-6 shadow-lg shadow-emerald-500/20 cursor-pointer"
          >
            <span>Continue to Store Setup</span>
            <UIcon name="i-lucide-arrow-right" class="w-4 h-4 ml-1.5" />
          </UButton>
        </form>

        <form v-else @submit.prevent="handleRegister" class="space-y-4">
          <UFormField label="Store / Business Name" required>
            <UInput
              v-model="form.store_name"
              placeholder="e.g. Chidinma Supermarket"
              size="md"
              icon="i-lucide-shopping-bag"
              required
            />
          </UFormField>

          <UFormField label="Business Category" required>
            <USelect
              v-model="form.store_category"
              :items="categories"
              size="md"
            />
          </UFormField>

          <UFormField label="Store Address (Optional)">
            <UInput
              v-model="form.store_address"
              placeholder="e.g. 14 Allen Avenue, Ikeja"
              size="md"
              icon="i-lucide-map-pin"
            />
          </UFormField>

          <UFormField label="Referral Code (Optional)">
            <UInput
              v-model="form.referral_code"
              placeholder="e.g. CHIDINMA-A1B2"
              size="md"
              icon="i-lucide-gift"
            />
          </UFormField>

          <!-- Terms & Privacy Agreement Checkbox -->
          <div class="pt-2">
            <label class="flex items-start gap-2.5 text-xs text-(--ui-text-muted) cursor-pointer select-none">
              <input
                v-model="agreeTerms"
                type="checkbox"
                required
                class="w-4 h-4 rounded border-neutral-700 bg-neutral-900 text-emerald-500 focus:ring-0 cursor-pointer mt-0.5"
              />
              <span class="leading-relaxed">
                I agree to Kluda's
                <a :href="`${marketingWebUrl}/terms`" target="_blank" rel="noopener noreferrer" class="text-emerald-400 font-semibold underline hover:text-emerald-300">Terms of Service</a>
                and
                <a :href="`${marketingWebUrl}/privacy`" target="_blank" rel="noopener noreferrer" class="text-emerald-400 font-semibold underline hover:text-emerald-300">Privacy Policy</a>.
              </span>
            </label>
          </div>

          <div class="flex items-center gap-3 pt-4">
            <UButton
              type="button"
              variant="outline"
              color="neutral"
              size="md"
              class="font-semibold px-4 py-2.5"
              @click="step = 1"
            >
              Back
            </UButton>

            <UButton
              type="submit"
              block
              size="md"
              color="primary"
              :disabled="!agreeTerms || isLoading"
              :loading="isLoading"
              class="font-bold flex-1 py-2.5 shadow-lg shadow-emerald-500/20 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <UIcon name="i-lucide-check-circle" class="w-4 h-4 mr-1.5" />
              Launch Store & Register
            </UButton>
          </div>
        </form>

        <div class="mt-6 pt-5 border-t border-(--ui-border) text-center text-xs text-(--ui-text-muted)">
          <span>Already have an account?</span>
          <NuxtLink to="/auth/login" class="text-emerald-500 font-semibold ml-1.5 hover:underline">
            Sign In
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
