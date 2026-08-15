<script setup lang="ts">
definePageMeta({ layout: 'default' })

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMsg = ref('')
const toast = useToast()
const auth = useAuthStore()


async function handleLogin() {
  errorMsg.value = ''
  isLoading.value = true
  try {
    const config = useRuntimeConfig()
    const data = await $fetch<{ access_token?: string, staff: any, success: boolean }>(`${config.public.apiBase}/auth/login`, {
      method: 'POST',
      credentials: 'include',
      body: { email: email.value, password: password.value }
    })
    auth.setAuth(data.access_token || '', data.staff)
    toast.add({ title: 'Welcome back!', description: `Logged in as ${data.staff.first_name}`, color: 'success' })
    navigateTo('/dashboard')
  } catch (err: any) {
    errorMsg.value = err?.data?.detail || 'Invalid email or password'
    toast.add({ title: 'Login failed', description: errorMsg.value, color: 'error' })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="gradient-bg min-h-screen flex items-center justify-center p-4">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute w-72 h-72 bg-green-400/10 rounded-full -top-20 -left-20 blur-3xl" />
      <div class="absolute w-96 h-96 bg-emerald-400/8 rounded-full -bottom-32 -right-32 blur-3xl" />
      <div class="absolute w-48 h-48 bg-teal-300/10 rounded-full top-1/3 right-1/4 blur-2xl" />
    </div>

    <div class="w-full max-w-md relative z-10">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-green-500 text-white font-bold text-2xl mb-4 shadow-lg shadow-green-500/30">
          RP
        </div>
        <h1 class="text-3xl font-bold text-white">RetailPOS</h1>
        <p class="text-green-200/70 mt-2">Next-generation point of sale</p>
      </div>

      <div class="glass-card rounded-2xl p-8">
        <h2 class="text-xl font-semibold text-white mb-6">Sign in to your account</h2>

        <form class="space-y-5" @submit.prevent="handleLogin">
          <UFormField label="Email" class="text-green-100">
            <UInput
              v-model="email"
              type="email"
              placeholder="admin@hello.com"
              icon="i-lucide-mail"
              size="lg"
              required
              autocomplete="email"
            />
          </UFormField>

          <UFormField label="Password" class="text-green-100">
            <UInput
              v-model="password"
              type="password"
              placeholder="••••••••"
              icon="i-lucide-lock"
              size="lg"
              required
              autocomplete="current-password"
            />
          </UFormField>

          <div v-if="errorMsg" class="text-red-400 text-sm flex items-center gap-2">
            <UIcon name="i-lucide-alert-circle" class="w-4 h-4 shrink-0" />
            {{ errorMsg }}
          </div>

          <UButton
            type="submit"
            block
            size="lg"
            :loading="isLoading"
            class="mt-2"
          >
            <UIcon name="i-lucide-log-in" class="w-5 h-5 mr-2" />
            Sign In
          </UButton>
        </form>

        <p class="text-center text-green-200/50 text-xs mt-6">
          Secured session • 13-hour token expiry • Device-locked
        </p>
      </div>
    </div>
  </div>
</template>
