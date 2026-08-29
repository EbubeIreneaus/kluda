<script setup lang="ts">
definePageMeta({
  layout: 'auth'
})

const { apiFetch } = useAdminApi()
const step = ref<'email' | 'otp' | 'password'>('email')
const email = ref('')
const otp = ref('')
const newPassword = ref('')
const isLoading = ref(false)
const isResending = ref(false)
const message = ref('')
const error = ref('')
const cooldown = ref(0)
let timer: any = null

function startCooldown(sec = 60) {
  cooldown.value = sec
  clearInterval(timer)
  timer = setInterval(() => {
    if (cooldown.value > 0) {
      cooldown.value--
    } else {
      clearInterval(timer)
    }
  }, 1000)
}

onBeforeUnmount(() => {
  clearInterval(timer)
})

async function handleRequestOTP() {
  if (!email.value) return
  isLoading.value = true
  error.value = ''
  try {
    await apiFetch('/admin/auth/forgot-password', {
      method: 'POST',
      body: { email: email.value }
    })
    step.value = 'otp'
    message.value = 'A 6-digit verification code has been dispatched to your email.'
    startCooldown(60)
  } catch (err: any) {
    error.value = err?.data?.detail || 'Failed to request OTP'
  } finally {
    isLoading.value = false
  }
}

async function handleResendOTP() {
  if (!email.value || cooldown.value > 0) return
  isResending.value = true
  error.value = ''
  try {
    await apiFetch('/admin/auth/forgot-password', {
      method: 'POST',
      body: { email: email.value }
    })
    message.value = 'A fresh verification code has been sent to your email.'
    startCooldown(60)
  } catch (err: any) {
    error.value = err?.data?.detail || 'Failed to resend code'
  } finally {
    isResending.value = false
  }
}

async function handleVerifyOTP() {
  if (!otp.value) return
  isLoading.value = true
  error.value = ''
  try {
    await apiFetch('/admin/auth/verify-otp', {
      method: 'POST',
      body: { email: email.value, otp: otp.value }
    })
    step.value = 'password'
    message.value = 'Code verified! Enter your new password below.'
  } catch (err: any) {
    error.value = err?.data?.detail || 'Invalid or expired OTP'
  } finally {
    isLoading.value = false
  }
}

async function handleResetPassword() {
  if (!newPassword.value) return
  isLoading.value = true
  error.value = ''
  try {
    await apiFetch('/admin/auth/reset-password', {
      method: 'POST',
      body: { email: email.value, otp: otp.value, new_password: newPassword.value }
    })
    navigateTo('/login')
  } catch (err: any) {
    error.value = err?.data?.detail || 'Failed to reset password'
  } finally {
    isLoading.value = false
  }
}

function resetToEmailStep() {
  step.value = 'email'
  otp.value = ''
  error.value = ''
  message.value = ''
}
</script>

<template>
  <div class="bg-zinc-900/80 border border-zinc-800 p-8 rounded-2xl shadow-2xl backdrop-blur-xl flex flex-col gap-6">
    <div class="flex flex-col items-center text-center gap-2">
      <div class="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xl mb-1">
        <UIcon name="i-lucide-key-round" class="w-6 h-6" />
      </div>
      <h1 class="text-xl font-bold tracking-tight text-white">Reset Admin Password</h1>
      <p class="text-xs text-zinc-400">Recover your account using your personal or company email</p>
    </div>

    <div v-if="message" class="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-3 rounded-xl text-xs flex items-center gap-2">
      <UIcon name="i-lucide-check-circle" class="w-4 h-4 shrink-0" />
      <span>{{ message }}</span>
    </div>

    <div v-if="error" class="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-xl text-xs flex items-center gap-2">
      <UIcon name="i-lucide-alert-circle" class="w-4 h-4 shrink-0" />
      <span>{{ error }}</span>
    </div>

    <form v-if="step === 'email'" class="flex flex-col gap-4" @submit.prevent="handleRequestOTP">
      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-300">Admin Email</label>
        <UInput
          v-model="email"
          placeholder="your.email@example.com"
          icon="i-lucide-mail"
          size="md"
          required
        />
      </div>
      <UButton
        type="submit"
        label="Send Verification Code"
        color="primary"
        block
        size="md"
        :loading="isLoading"
      />
    </form>

    <div v-else-if="step === 'otp'" class="flex flex-col gap-4">
      <div class="flex items-center justify-between text-xs px-1">
        <span class="text-zinc-400 font-mono">{{ email }}</span>
        <button
          type="button"
          class="text-emerald-400 hover:underline text-xs"
          @click="resetToEmailStep"
        >
          Change email
        </button>
      </div>

      <form class="flex flex-col gap-4" @submit.prevent="handleVerifyOTP">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">6-Digit OTP Code</label>
          <UInput
            v-model="otp"
            placeholder="123456"
            icon="i-lucide-shield"
            size="md"
            maxlength="6"
            required
          />
        </div>
        <UButton
          type="submit"
          label="Verify Code"
          color="primary"
          block
          size="md"
          :loading="isLoading"
        />
      </form>

      <div class="flex items-center justify-between text-xs pt-1 border-t border-zinc-800/80">
        <span class="text-zinc-400">Didn't receive code?</span>
        <button
          type="button"
          :disabled="cooldown > 0 || isResending"
          class="font-semibold text-xs transition-colors"
          :class="cooldown > 0 ? 'text-zinc-500 cursor-not-allowed' : 'text-emerald-400 hover:underline cursor-pointer'"
          @click="handleResendOTP"
        >
          <span v-if="cooldown > 0">Resend in {{ cooldown }}s</span>
          <span v-else>{{ isResending ? 'Sending...' : 'Resend Code' }}</span>
        </button>
      </div>
    </div>

    <form v-else class="flex flex-col gap-4" @submit.prevent="handleResetPassword">
      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-300">New Password</label>
        <UInput
          v-model="newPassword"
          type="password"
          placeholder="••••••••••••"
          icon="i-lucide-lock"
          size="md"
          required
        />
      </div>
      <UButton
        type="submit"
        label="Set New Password"
        color="primary"
        block
        size="md"
        :loading="isLoading"
      />
    </form>

    <div class="text-center">
      <NuxtLink to="/login" class="text-xs text-zinc-400 hover:text-emerald-400 transition-colors inline-flex items-center gap-1.5">
        <UIcon name="i-lucide-arrow-left" class="w-3.5 h-3.5" />
        Back to Sign In
      </NuxtLink>
    </div>
  </div>
</template>
