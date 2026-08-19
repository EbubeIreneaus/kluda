<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({ layout: 'default' })

const staffId = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMsg = ref('')
const toast = useToast()
const auth = useAuthStore()

const availableStores = ref<any[]>([])
const pendingLoginData = ref<any>(null)
const showStorePicker = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  isLoading.value = true
  const identifier = staffId.value.trim()
  const formattedId = identifier.includes('@') ? identifier : identifier.toUpperCase()

  try {
    const config = useRuntimeConfig()
    const data = await $fetch<{ access_token?: string, staff: any, store_id?: string, stores?: any[], success: boolean }>(`${config.public.apiBase}/staff/auth/login`, {
      method: 'POST',
      credentials: 'include',
      body: { staff_id: formattedId, password: password.value }
    })

    if (data.stores && data.stores.length > 1) {
      pendingLoginData.value = data
      availableStores.value = data.stores
      showStorePicker.value = true
      return
    }

    auth.setAuth(data.access_token || '', data.staff, data.store_id)
    toast.add({ title: 'Welcome back!', description: `Logged in as ${data.staff?.first_name || 'User'}`, color: 'success' })
    await navigateTo('/')
  } catch (err: any) {
    errorMsg.value = err?.data?.detail || 'Invalid login identifier or password'
    toast.add({ title: 'Login failed', description: errorMsg.value, color: 'error' })
  } finally {
    isLoading.value = false
  }
}

async function selectStoreAndProceed(store: any) {
  if (!pendingLoginData.value) return
  auth.setAuth(pendingLoginData.value.access_token || '', {
    ...pendingLoginData.value.staff,
    store_id: store.store_id
  }, store.store_id)
  toast.add({ title: 'Terminal Ready', description: `Connected to ${store.name}`, color: 'success' })
  showStorePicker.value = false
  await navigateTo('/')
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
        <p class="text-emerald-300 font-medium text-xs mt-1 uppercase tracking-wider">Sell Faster, Track Everything</p>
      </div>

      <div class="glass-card rounded-2xl p-8">
        <h2 class="text-xl font-semibold text-white mb-6">Sign In</h2>

        <form class="space-y-5" @submit.prevent="handleLogin">
          <UFormField label="Staff ID or Owner Email" class="text-green-100">
            <UInput
              v-model="staffId"
              type="text"
              placeholder="e.g. STF1001 or owner@example.com"
              icon="i-lucide-user"
              size="lg"
              required
              autocomplete="username"
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
          Universal Authentication • Staff & Store Owners
        </p>
      </div>
    </div>

    <UModal v-model:open="showStorePicker" title="Select Store Terminal">
      <template #body>
        <div class="p-5 space-y-4">
          <p class="text-sm text-(--ui-text-muted)">Your owner account has multiple stores. Select which store you want to open in this POS terminal:</p>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <button
              v-for="store in availableStores"
              :key="store.store_id"
              type="button"
              class="w-full p-4 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/30 hover:bg-(--ui-bg-accented) flex items-center justify-between text-left transition"
              @click="selectStoreAndProceed(store)"
            >
              <div>
                <p class="font-semibold text-(--ui-text-highlighted)">{{ store.name }}</p>
                <p class="text-xs text-(--ui-text-muted)">{{ store.category }} • {{ store.address || 'Main Branch' }}</p>
              </div>
              <UIcon name="i-lucide-chevron-right" class="size-5 text-(--ui-text-dimmed)" />
            </button>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
