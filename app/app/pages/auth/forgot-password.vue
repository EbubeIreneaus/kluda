<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({ layout: 'auth' })

const config = useRuntimeConfig()
const toast = useToast()

const step = ref<1 | 2 | 3 | 4>(1)
const email = ref('')
const otpCode = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const errorMsg = ref('')

async function handleRequestCode() {
  errorMsg.value = ''
  const cleanEmail = email.value.trim().toLowerCase()
  if (!cleanEmail || !cleanEmail.includes('@')) {
    errorMsg.value = 'Please enter a valid email address'
    return
  }

  isLoading.value = true
  try {
    const res = await $fetch<{ success: boolean, message: string }>(`${config.public.apiBase}/auth/password-reset/request`, {
      method: 'POST',
      body: { email: cleanEmail }
    })
    toast.add({
      title: 'Reset Code Sent',
      description: res.message || 'Check your inbox for your 6-digit reset code.',
      color: 'success'
    })
    step.value = 2
  } catch (err: any) {
    errorMsg.value = err?.data?.detail || 'Failed to request password reset code. Please try again.'
  } finally {
    isLoading.value = false
  }
}

async function handleVerifyCode() {
  errorMsg.value = ''
  const cleanCode = otpCode.value.trim()
  if (!cleanCode || cleanCode.length < 4) {
    errorMsg.value = 'Please enter the verification code sent to your email'
    return
  }

  isLoading.value = true
  try {
    await $fetch<{ success: boolean, message: string }>(`${config.public.apiBase}/auth/password-reset/verify`, {
      method: 'POST',
      body: {
        email: email.value.trim().toLowerCase(),
        code: cleanCode
      }
    })
    step.value = 3
  } catch (err: any) {
    errorMsg.value = err?.data?.detail || 'Invalid or expired verification code.'
  } finally {
    isLoading.value = false
  }
}

async function handleSubmitNewPassword() {
  errorMsg.value = ''
  if (!newPassword.value || newPassword.value.length < 6) {
    errorMsg.value = 'Password must be at least 6 characters long'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = 'Passwords do not match'
    return
  }

  isLoading.value = true
  try {
    const res = await $fetch<{ success: boolean, message: string }>(`${config.public.apiBase}/auth/password-reset/submit`, {
      method: 'POST',
      body: {
        email: email.value.trim().toLowerCase(),
        code: otpCode.value.trim(),
        new_password: newPassword.value
      }
    })
    toast.add({
      title: 'Password Updated',
      description: res.message || 'Your password has been reset successfully.',
      color: 'success'
    })
    step.value = 4
  } catch (err: any) {
    errorMsg.value = err?.data?.detail || 'Failed to update password. Please try again.'
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
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#090d16] border border-emerald-500/40 overflow-hidden mb-4 shadow-xl shadow-emerald-500/25">
          <img src="/kluda_icon.jpg" alt="Kluda" class="w-full h-full object-cover" />
        </div>
        <h1 class="text-3xl font-black tracking-wider text-white">KLUDA</h1>
        <p class="text-emerald-300 font-medium text-xs mt-1 uppercase tracking-wider">Account Recovery & Password Reset</p>
      </div>

      <div class="glass-card rounded-2xl p-8 space-y-6">
        <div v-if="step === 1" class="space-y-5">
          <div>
            <h2 class="text-xl font-semibold text-white">Reset Password</h2>
            <p class="text-xs text-zinc-400 mt-1">Enter your account email to receive a 6-digit verification code.</p>
          </div>

          <form class="space-y-4" @submit.prevent="handleRequestCode">
            <UFormField label="Account Email" class="text-green-100">
              <UInput
                v-model="email"
                type="email"
                placeholder="you@example.com"
                icon="i-lucide-mail"
                size="lg"
                required
                autocomplete="email"
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
              <UIcon name="i-lucide-send" class="w-5 h-5 mr-2" />
              Send Verification Code
            </UButton>
          </form>

          <div class="pt-3 border-t border-white/10 text-center">
            <NuxtLink to="/login" class="text-xs text-emerald-400 hover:text-emerald-300 font-semibold inline-flex items-center gap-1">
              <UIcon name="i-lucide-arrow-left" class="w-3.5 h-3.5" />
              Back to Sign In
            </NuxtLink>
          </div>
        </div>

        <div v-else-if="step === 2" class="space-y-5">
          <div>
            <h2 class="text-xl font-semibold text-white">Enter Verification Code</h2>
            <p class="text-xs text-zinc-400 mt-1">
              We sent a 6-digit code to <span class="text-emerald-400 font-semibold">{{ email }}</span>.
            </p>
          </div>

          <form class="space-y-4" @submit.prevent="handleVerifyCode">
            <UFormField label="6-Digit Reset Code" class="text-green-100">
              <UInput
                v-model="otpCode"
                type="text"
                placeholder="123456"
                icon="i-lucide-key-round"
                size="lg"
                maxlength="8"
                required
                class="font-mono text-center tracking-widest text-lg"
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
              <UIcon name="i-lucide-check-circle" class="w-5 h-5 mr-2" />
              Verify Code
            </UButton>

            <div class="flex items-center justify-between pt-2">
              <button
                type="button"
                class="text-xs text-zinc-400 hover:text-white transition-colors"
                @click="step = 1"
              >
                Change Email
              </button>
              <button
                type="button"
                class="text-xs text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                :disabled="isLoading"
                @click="handleRequestCode"
              >
                Resend Code
              </button>
            </div>
          </form>
        </div>

        <div v-else-if="step === 3" class="space-y-5">
          <div>
            <h2 class="text-xl font-semibold text-white">Set New Password</h2>
            <p class="text-xs text-zinc-400 mt-1">Create a strong new password for your account.</p>
          </div>

          <form class="space-y-4" @submit.prevent="handleSubmitNewPassword">
            <UFormField label="New Password" class="text-green-100">
              <UInput
                v-model="newPassword"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                icon="i-lucide-lock"
                size="lg"
                required
              >
                <template #trailing>
                  <button
                    type="button"
                    class="text-zinc-400 hover:text-white"
                    @click="showPassword = !showPassword"
                  >
                    <UIcon :name="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'" class="w-4 h-4" />
                  </button>
                </template>
              </UInput>
            </UFormField>

            <UFormField label="Confirm New Password" class="text-green-100">
              <UInput
                v-model="confirmPassword"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                icon="i-lucide-shield-check"
                size="lg"
                required
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
              <UIcon name="i-lucide-save" class="w-5 h-5 mr-2" />
              Save New Password
            </UButton>
          </form>
        </div>

        <div v-else-if="step === 4" class="text-center space-y-5 py-4">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <UIcon name="i-lucide-check" class="w-8 h-8" />
          </div>
          <div>
            <h2 class="text-xl font-bold text-white">Password Reset Complete!</h2>
            <p class="text-xs text-zinc-400 mt-1">Your password has been changed. You can now sign into your terminal.</p>
          </div>

          <NuxtLink to="/login" class="block w-full">
            <UButton block size="lg">
              <UIcon name="i-lucide-log-in" class="w-5 h-5 mr-2" />
              Go to Sign In
            </UButton>
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
