<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: false })

const route = useRoute()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const ownerStore = useOwnerStore()

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
      statusMessage.value = 'SSO session verified. Redirecting to dashboard...'
      ownerStore.setAuth(res.access_token, res.user)
      if (res.stores && Array.isArray(res.stores)) {
        ownerStore.stores = res.stores
        if (res.stores.length > 0 && !ownerStore.selectedStoreId) {
          ownerStore.selectStore(res.stores[0].store_id)
        }
      }
      setTimeout(() => {
        navigateTo('/dashboard')
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
          <div class="absolute inset-0 rounded-full border-4 border-primary/20 animate-ping" />
          <div class="w-12 h-12 rounded-full border-3 border-primary border-t-transparent animate-spin" />
        </div>
        <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Single Sign-On</h2>
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
