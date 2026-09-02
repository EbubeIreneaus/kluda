<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: 'marchant' })

const auth = useAuthStore()
const toast = useToast()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isChangingPassword = ref(false)

const terminalSound = ref(true)
const offlineAlerts = ref(true)
const autoSync = ref(true)

onMounted(() => {
  if (import.meta.client) {
    terminalSound.value = localStorage.getItem('pos_sound') !== 'false'
    offlineAlerts.value = localStorage.getItem('pos_offline_alerts') !== 'false'
    autoSync.value = localStorage.getItem('pos_auto_sync') !== 'false'
  }
})

function saveNotificationPreferences() {
  if (import.meta.client) {
    localStorage.setItem('pos_sound', String(terminalSound.value))
    localStorage.setItem('pos_offline_alerts', String(offlineAlerts.value))
    localStorage.setItem('pos_auto_sync', String(autoSync.value))
  }
  toast.add({
    title: 'Preferences Saved',
    description: 'Terminal and notification preferences updated.',
    color: 'success'
  })
}

async function handleChangePassword() {
  if (!oldPassword.value || !newPassword.value) {
    toast.add({ title: 'Please fill in both old and new password', color: 'warning' })
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    toast.add({ title: 'New passwords do not match', color: 'error' })
    return
  }

  if (newPassword.value.length < 6) {
    toast.add({ title: 'New password must be at least 6 characters', color: 'warning' })
    return
  }

  isChangingPassword.value = true
  try {
    const res = await $fetch<{ message: string }>(`${apiBase}/auth/change-password`, {
      method: 'POST',
      credentials: 'include',
      headers: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
      body: {
        old_password: oldPassword.value,
        new_password: newPassword.value
      }
    })

    toast.add({
      title: 'Password Changed',
      description: res.message || 'Please log in again with your new password.',
      color: 'success'
    })

    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''

    await auth.logout(true)
  } catch (err: any) {
    toast.add({
      title: 'Password change failed',
      description: err?.data?.detail || 'Incorrect current password or server error',
      color: 'error'
    })
  } finally {
    isChangingPassword.value = false
  }
}
</script>

<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <div>
      <h1 class="text-2xl font-black tracking-tight text-(--ui-text-highlighted)">
        Account & Security
      </h1>
      <p class="text-sm text-(--ui-text-muted) mt-1">
        Manage your owner account profile, credentials, security, and subscription.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <div class="p-6 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-5 shadow-xs">
          <div class="flex items-center gap-4">
            <UAvatar :text="auth.initials" size="xl" class="bg-amber-500/20 text-amber-400 font-black border border-amber-500/30" />
            <div>
              <h3 class="text-lg font-bold text-(--ui-text-highlighted)">{{ auth.fullName || auth.user?.fullname }}</h3>
              <p class="text-xs text-(--ui-text-muted)">Store Owner & Merchant Account</p>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-(--ui-border) text-sm">
            <div class="p-3.5 rounded-2xl bg-(--ui-bg-accented)/30 border border-(--ui-border)">
              <span class="text-xs text-(--ui-text-muted)">Email Address</span>
              <p class="font-bold text-(--ui-text-highlighted) mt-0.5">{{ auth.staff?.email || auth.user?.email }}</p>
            </div>
            <div class="p-3.5 rounded-2xl bg-(--ui-bg-accented)/30 border border-(--ui-border)">
              <span class="text-xs text-(--ui-text-muted)">Phone Number</span>
              <p class="font-bold text-(--ui-text-highlighted) mt-0.5">{{ auth.staff?.phone || auth.user?.phone || 'Not provided' }}</p>
            </div>
            <div class="p-3.5 rounded-2xl bg-(--ui-bg-accented)/30 border border-(--ui-border)">
              <span class="text-xs text-(--ui-text-muted)">User ID</span>
              <p class="font-mono text-xs font-bold text-emerald-400 mt-0.5">{{ auth.staff?.staff_id || auth.user?.user_id }}</p>
            </div>
            <div class="p-3.5 rounded-2xl bg-(--ui-bg-accented)/30 border border-(--ui-border)">
              <span class="text-xs text-(--ui-text-muted)">Total Store Branches</span>
              <p class="font-bold text-(--ui-text-highlighted) mt-0.5">{{ auth.stores.length }} Branches</p>
            </div>
          </div>
        </div>

        <div class="p-6 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-4 shadow-xs">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-lock" class="w-5 h-5 text-amber-500" />
            <h3 class="text-base font-bold text-(--ui-text-highlighted)">Change Password</h3>
          </div>
          <p class="text-xs text-(--ui-text-muted)">Update your master merchant password. All active sessions will be refreshed.</p>

          <form class="space-y-4 pt-2" @submit.prevent="handleChangePassword">
            <div class="space-y-1">
              <label class="text-xs font-bold text-(--ui-text-highlighted)">Current Password</label>
              <input
                v-model="oldPassword"
                type="password"
                required
                class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-emerald-500"
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-xs font-bold text-(--ui-text-highlighted)">New Password</label>
                <input
                  v-model="newPassword"
                  type="password"
                  required
                  minlength="6"
                  class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-emerald-500"
                />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-(--ui-text-highlighted)">Confirm New Password</label>
                <input
                  v-model="confirmPassword"
                  type="password"
                  required
                  minlength="6"
                  class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div class="pt-2">
              <UButton
                type="submit"
                color="primary"
                :loading="isChangingPassword"
                class="font-bold px-5 py-2.5"
              >
                Update Password
              </UButton>
            </div>
          </form>
        </div>
      </div>

      <div class="space-y-6">
        <div class="p-6 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-4 shadow-xs">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-credit-card" class="w-5 h-5 text-amber-500" />
            <h3 class="text-base font-bold text-(--ui-text-highlighted)">Plan & Billing</h3>
          </div>

          <div class="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-400">Merchant Growth Plan</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-500/20 text-amber-300">Active</span>
            </div>
            <p class="text-xs text-(--ui-text-muted)">Multi-store POS with unlimited offline caching and automatic cloud sync.</p>
          </div>

          <div class="space-y-2 text-xs text-(--ui-text-muted) pt-2">
            <div class="flex items-center justify-between">
              <span>Stores Limit</span>
              <span class="font-bold text-(--ui-text-highlighted)">Unlimited</span>
            </div>
            <div class="flex items-center justify-between">
              <span>Staff Cashiers</span>
              <span class="font-bold text-(--ui-text-highlighted)">Unlimited</span>
            </div>
            <div class="flex items-center justify-between">
              <span>Billing Cycle</span>
              <span class="font-bold text-(--ui-text-highlighted)">Standard Early Access</span>
            </div>
          </div>
        </div>

        <div class="p-6 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-4 shadow-xs">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-bell" class="w-5 h-5 text-emerald-500" />
            <h3 class="text-base font-bold text-(--ui-text-highlighted)">Terminal Preferences</h3>
          </div>

          <div class="space-y-3 pt-2">
            <label class="flex items-center justify-between p-3 rounded-2xl bg-(--ui-bg-accented)/20 border border-(--ui-border) cursor-pointer">
              <div class="pr-2">
                <p class="text-xs font-bold text-(--ui-text-highlighted)">Barcode Audio Chime</p>
                <p class="text-[11px] text-(--ui-text-muted)">Play sound on barcode scan</p>
              </div>
              <input v-model="terminalSound" type="checkbox" class="rounded text-emerald-500 focus:ring-0" @change="saveNotificationPreferences" />
            </label>

            <label class="flex items-center justify-between p-3 rounded-2xl bg-(--ui-bg-accented)/20 border border-(--ui-border) cursor-pointer">
              <div class="pr-2">
                <p class="text-xs font-bold text-(--ui-text-highlighted)">Offline Sync Toast</p>
                <p class="text-[11px] text-(--ui-text-muted)">Alert when sync queue empties</p>
              </div>
              <input v-model="offlineAlerts" type="checkbox" class="rounded text-emerald-500 focus:ring-0" @change="saveNotificationPreferences" />
            </label>

            <label class="flex items-center justify-between p-3 rounded-2xl bg-(--ui-bg-accented)/20 border border-(--ui-border) cursor-pointer">
              <div class="pr-2">
                <p class="text-xs font-bold text-(--ui-text-highlighted)">Background Auto-Sync</p>
                <p class="text-[11px] text-(--ui-text-muted)">Sync IndexedDB sales silently</p>
              </div>
              <input v-model="autoSync" type="checkbox" class="rounded text-emerald-500 focus:ring-0" @change="saveNotificationPreferences" />
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
