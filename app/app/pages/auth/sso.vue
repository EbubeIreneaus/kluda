<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: false })

const route = useRoute()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const auth = useAuthStore()

const statusMessage = ref('Verifying single sign-on ticket...')
const isError = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  const ticket = (route.query.ticket || route.query.sso_ticket) as string

  if (!ticket) {
    isError.value = true
    errorMessage.value = 'No single sign-on ticket provided.'
    return
  }

  try {
    const res = await $fetch<any>(`${apiBase}/auth/sso/exchange`, {
      method: 'POST',
      body: { ticket }
    })

    if (res && res.success && res.access_token) {
      statusMessage.value = 'SSO session verified. Redirecting to POS...'
      
      const primaryStoreId = res.stores?.[0]?.store_id || ''
      const names = (res.user?.fullname || 'Store Owner').split(' ')
      const staffObj = {
        staff_id: res.user?.user_id || 'owner',
        store_id: primaryStoreId,
        first_name: names[0] || 'Store',
        last_name: names.slice(1).join(' ') || 'Owner',
        role: 'owner',
        email: res.user?.email || '',
        permission: ['*'],
        status: 'active',
        created_at: new Date().toISOString()
      }

      auth.setAuth(res.access_token, staffObj, primaryStoreId)

      if (import.meta.client && res.stores) {
        localStorage.setItem('pos_available_stores', JSON.stringify(res.stores))
      }

      setTimeout(() => {
        navigateTo('/')
      }, 400)
    } else {
      isError.value = true
      errorMessage.value = 'Invalid ticket response from server.'
    }
  } catch (err: any) {
    isError.value = true
    errorMessage.value = err?.data?.detail || 'Single sign-on ticket exchange failed or expired.'
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-(--ui-bg) p-4">
    <div class="max-w-md w-full p-8 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-2xl text-center space-y-6">
      <div v-if="!isError" class="space-y-4">
        <div class="relative w-16 h-16 mx-auto flex items-center justify-center">
          <div class="absolute inset-0 rounded-full border-4 border-emerald-500/20 animate-ping" />
          <div class="w-12 h-12 rounded-full border-3 border-emerald-500 border-t-transparent animate-spin" />
        </div>
        <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Kluda Single Sign-On</h2>
        <p class="text-sm text-(--ui-text-muted)">{{ statusMessage }}</p>
      </div>

      <div v-else class="space-y-4">
        <div class="w-12 h-12 mx-auto rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500">
          <UIcon name="i-lucide-alert-circle" class="size-6" />
        </div>
        <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Authentication Failed</h2>
        <p class="text-sm text-red-400">{{ errorMessage }}</p>
        <div class="pt-2">
          <UButton to="/login" variant="solid" color="primary" class="w-full justify-center">
            Go to Login
          </UButton>
        </div>
      </div>
    </div>
  </div>
</template>
