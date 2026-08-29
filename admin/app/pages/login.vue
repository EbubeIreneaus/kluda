<script setup lang="ts">
definePageMeta({
  layout: 'auth'
})

const { login } = useAdminAuth()
const identifier = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!identifier.value || !password.value) {
    errorMessage.value = 'Please enter your email and password'
    return
  }
  isLoading.value = true
  errorMessage.value = ''

  try {
    const ok = await login(identifier.value, password.value)
    if (ok) {
      navigateTo('/')
    } else {
      errorMessage.value = 'Invalid login credentials'
    }
  } catch (err: any) {
    errorMessage.value = err?.data?.detail || 'Login failed. Please check your credentials.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="bg-zinc-900/80 border border-zinc-800 p-8 rounded-2xl shadow-2xl backdrop-blur-xl flex flex-col gap-6">
    <div class="flex flex-col items-center text-center gap-2">
      <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center font-black text-zinc-950 text-2xl shadow-lg shadow-emerald-500/20 mb-1">
        K
      </div>
      <h1 class="text-xl font-bold tracking-tight text-white">Kluda Administration</h1>
      <p class="text-xs text-zinc-400">Enter your company or personal email to access control center</p>
    </div>

    <div v-if="errorMessage" class="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-xl text-xs flex items-center gap-2">
      <UIcon name="i-lucide-alert-circle" class="w-4 h-4 shrink-0" />
      <span>{{ errorMessage }}</span>
    </div>

    <form class="flex flex-col gap-4" @submit.prevent="handleLogin">
      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-300">Email</label>
        <UInput
          v-model="identifier"
          placeholder="Email"
          icon="i-lucide-mail"
          size="md"
          autocomplete="username"
          required
        />
      </div>

      <div class="flex flex-col gap-1.5">
        <div class="flex items-center justify-between">
          <label class="text-xs font-medium text-zinc-300">Password</label>
          <NuxtLink to="/forgot-password" class="text-xs text-emerald-400 hover:underline">Forgot password?</NuxtLink>
        </div>
        <UInput
          v-model="password"
          type="password"
          placeholder="••••••••••••"
          icon="i-lucide-lock"
          size="md"
          autocomplete="current-password"
          required
        />
      </div>

      <UButton
        type="submit"
        label="Sign In to Admin Portal"
        icon="i-lucide-arrow-right"
        trailing
        color="primary"
        block
        size="md"
        :loading="isLoading"
        class="mt-2"
      />
    </form>

    <div class="text-center text-[11px] text-zinc-400">
      Authorized personnel only. All access attempts are logged.
    </div>
  </div>
</template>
