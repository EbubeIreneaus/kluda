<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: 'dashboard' })

const auth = useAuthStore()
const toast = useToast()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const { isSupported, isSubscribed, isLoading: isPushLoading, checkSupportAndStatus, subscribe, unsubscribe } = usePushNotification()

const permissionState = ref<NotificationPermission>('default')

function updatePermissionState() {
  if (import.meta.client && 'Notification' in window) {
    permissionState.value = Notification.permission
  }
}

async function handleTogglePush(val: boolean) {
  if (val) {
    const ok = await subscribe()
    updatePermissionState()
    if (ok) {
      toast.add({
        title: 'Notifications Enabled',
        description: 'This terminal is now registered for store announcements and stock alerts.',
        color: 'success',
      })
    } else if (permissionState.value === 'denied') {
      toast.add({
        title: 'Notifications Blocked',
        description: 'Please enable notifications in your browser site settings.',
        color: 'error',
      })
    }
  } else {
    const ok = await unsubscribe()
    updatePermissionState()
    if (ok) {
      toast.add({
        title: 'Notifications Disabled',
        description: 'This terminal has been unsubscribed from push notifications.',
        color: 'neutral',
      })
    }
  }
}

const isChangingPassword = ref(false)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

async function handleChangePassword() {
  if (!passwordForm.value.old_password || !passwordForm.value.new_password) {
    toast.add({
      title: 'Missing Fields',
      description: 'Please fill in all password fields.',
      color: 'warning',
    })
    return
  }

  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    toast.add({
      title: 'Password Mismatch',
      description: 'New password and confirm password do not match.',
      color: 'error',
    })
    return
  }

  if (passwordForm.value.new_password.length < 6) {
    toast.add({
      title: 'Weak Password',
      description: 'New password must be at least 6 characters.',
      color: 'warning',
    })
    return
  }

  isChangingPassword.value = true
  try {
    const res = await $fetch<{ message: string }>(`${apiBase}/auth/change-password`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.token ?? ''}`,
      },
      body: {
        old_password: passwordForm.value.old_password,
        new_password: passwordForm.value.new_password,
      },
    })

    toast.add({
      title: 'Success',
      description: res.message || 'Password changed successfully. Please log in again.',
      color: 'success',
    })

    passwordForm.value = {
      old_password: '',
      new_password: '',
      confirm_password: '',
    }

    setTimeout(() => {
      auth.logout()
      navigateTo('/login')
    }, 1500)
  } catch (err: any) {
    toast.add({
      title: 'Failed to Change Password',
      description: err?.data?.detail || 'Incorrect current password or server error.',
      color: 'error',
    })
  } finally {
    isChangingPassword.value = false
  }
}

onMounted(async () => {
  await checkSupportAndStatus()
  updatePermissionState()
})
</script>

<template>
  <div class="max-w-4xl space-y-6">
    <div>
      <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Account Settings</h2>
      <p class="text-sm text-(--ui-text-muted)">View your staff profile, terminal preferences, and security credentials.</p>
    </div>

    <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-6 space-y-6">
      <div class="flex items-center gap-4">
        <UAvatar :text="auth.initials" size="xl" />
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-bold text-(--ui-text-highlighted)">{{ auth.fullName }}</h3>
            <UBadge color="primary" variant="subtle" size="xs" class="capitalize">
              {{ auth.staff?.role?.replace('_', ' ') || 'Staff' }}
            </UBadge>
            <UBadge
              :color="auth.staff?.status === 'active' ? 'success' : 'warning'"
              variant="subtle"
              size="xs"
              class="capitalize"
            >
              {{ auth.staff?.status || 'Active' }}
            </UBadge>
          </div>
          <p class="text-xs text-(--ui-text-dimmed)">Staff ID: {{ auth.staff?.staff_id }}</p>
        </div>
      </div>

      <div class="border-t border-(--ui-border) pt-4">
        <h4 class="text-xs font-semibold text-(--ui-text-dimmed) uppercase tracking-wider mb-4">
          Profile Information (Managed by Admin)
        </h4>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-xs text-(--ui-text-dimmed) block">Email Address</span>
            <span class="font-medium text-(--ui-text-highlighted)">{{ auth.staff?.email || '—' }}</span>
          </div>
          <div>
            <span class="text-xs text-(--ui-text-dimmed) block">Phone Number</span>
            <span class="font-medium text-(--ui-text-highlighted)">{{ auth.staff?.phone || 'Not Provided' }}</span>
          </div>
          <div>
            <span class="text-xs text-(--ui-text-dimmed) block">Assigned Permissions</span>
            <div class="flex flex-wrap gap-1.5 mt-1">
              <UBadge
                v-for="perm in (auth.staff?.permission || [])"
                :key="typeof perm === 'string' ? perm : ((perm as any)?.value || String(perm))"
                :color="(typeof perm === 'string' ? perm : ((perm as any)?.value || String(perm))) === 'manage:all' ? 'error' : 'info'"
                variant="subtle"
                size="xs"
              >
                {{ typeof perm === 'string' ? perm : ((perm as any)?.value || String(perm)) }}
              </UBadge>
              <span v-if="!auth.staff?.permission?.length" class="text-xs text-(--ui-text-dimmed)">No permissions assigned</span>
            </div>
          </div>
          <div>
            <span class="text-xs text-(--ui-text-dimmed) block">Last Login</span>
            <span class="font-medium text-(--ui-text-highlighted)">{{ auth.staff?.last_login ? new Date(auth.staff.last_login).toLocaleString() : 'Recent' }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-6 space-y-4">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h3 class="text-base font-semibold text-(--ui-text-highlighted) flex items-center gap-2">
            <UIcon name="i-lucide-bell" class="w-4 h-4 text-primary-500" />
            Push Notifications & Terminal Alerts
          </h3>
          <p class="text-xs text-(--ui-text-muted) mt-0.5">
            Receive instant alerts for low inventory thresholds, cashier shift summaries, and platform broadcasts.
          </p>
        </div>
        <USwitch
          v-if="isSupported && permissionState !== 'denied'"
          :model-value="isSubscribed"
          :disabled="isPushLoading"
          @update:model-value="handleTogglePush"
        />
      </div>

      <div v-if="!isSupported" class="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400 flex items-center gap-2">
        <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 shrink-0" />
        <span>Push notifications are not supported on this browser engine.</span>
      </div>

      <div v-else-if="permissionState === 'denied'" class="p-4 rounded-xl bg-red-500/10 border border-red-500/20 space-y-2">
        <div class="flex items-center gap-2 text-xs font-semibold text-red-400">
          <UIcon name="i-lucide-bell-off" class="w-4 h-4" />
          <span>Notifications Blocked by Browser</span>
        </div>
        <p class="text-xs text-red-300/80 leading-relaxed">
          Browser notifications have been denied on this device. To allow alerts, tap the lock or settings icon in your browser address bar and set <strong>Notifications</strong> to <strong>Allow</strong>.
        </p>
      </div>

      <div v-else-if="isSubscribed" class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 flex items-center gap-2">
        <UIcon name="i-lucide-check-circle" class="w-4 h-4 shrink-0" />
        <span>This device is active and receiving background push alerts.</span>
      </div>
    </div>

    <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-6 space-y-4">
      <div>
        <h3 class="text-base font-semibold text-(--ui-text-highlighted)">Change Password</h3>
        <p class="text-xs text-(--ui-text-muted)">Update your password to keep your account secure.</p>
      </div>

      <form class="space-y-4 max-w-md" @submit.prevent="handleChangePassword">
        <UFormField label="Current Password" required>
          <UInput
            v-model="passwordForm.old_password"
            type="password"
            placeholder="••••••••"
            autocomplete="current-password"
          />
        </UFormField>

        <UFormField label="New Password" required>
          <UInput
            v-model="passwordForm.new_password"
            type="password"
            placeholder="••••••••"
            autocomplete="new-password"
          />
        </UFormField>

        <UFormField label="Confirm New Password" required>
          <UInput
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="••••••••"
            autocomplete="new-password"
          />
        </UFormField>

        <div class="pt-2">
          <UButton type="submit" :loading="isChangingPassword" icon="i-lucide-lock">
            Update Password
          </UButton>
        </div>
      </form>
    </div>
  </div>
</template>
