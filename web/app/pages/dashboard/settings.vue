<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({ layout: 'dashboard' })

const ownerStore = useOwnerStore()
const toast = useToast()

const currentPassword = ref('')
const newPassword = ref('')
const isUpdatingPassword = ref(false)

async function handleUpdatePassword() {
  if (!currentPassword.value || !newPassword.value) {
    toast.add({ title: 'Please fill both password fields', color: 'warning' })
    return
  }

  isUpdatingPassword.value = true
  try {
    const config = useRuntimeConfig()
    await $fetch(`${config.public.apiBase}/auth/change-password`, {
      method: 'POST',
      credentials: 'include',
      headers: ownerStore.token && ownerStore.token !== 'cookie_session' ? { Authorization: `Bearer ${ownerStore.token}` } : {},
      body: {
        old_password: currentPassword.value,
        new_password: newPassword.value
      }
    })

    toast.add({ title: 'Password changed successfully', color: 'success' })
    currentPassword.value = ''
    newPassword.value = ''
  } catch (err: any) {
    toast.add({
      title: 'Failed to update password',
      description: err?.data?.detail || 'Incorrect current password',
      color: 'error'
    })
  } finally {
    isUpdatingPassword.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-(--ui-text-highlighted)">Account Settings</h1>
      <p class="text-sm text-(--ui-text-muted) mt-1">
        Manage your merchant account profile and security.
      </p>
    </div>

    <!-- Profile Details Card -->
    <div class="rounded-3xl p-6 border border-(--ui-border) glass-panel space-y-4">
      <h3 class="text-base font-bold text-(--ui-text-highlighted)">Merchant Profile</h3>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
        <div class="p-3 rounded-2xl bg-(--ui-bg) border border-(--ui-border)">
          <div class="text-xs text-(--ui-text-muted)">Full Name</div>
          <div class="font-semibold text-(--ui-text-highlighted) mt-0.5">{{ ownerStore.user?.fullname || '—' }}</div>
        </div>

        <div class="p-3 rounded-2xl bg-(--ui-bg) border border-(--ui-border)">
          <div class="text-xs text-(--ui-text-muted)">Email Address</div>
          <div class="font-semibold text-(--ui-text-highlighted) mt-0.5">{{ ownerStore.user?.email || '—' }}</div>
        </div>

        <div class="p-3 rounded-2xl bg-(--ui-bg) border border-(--ui-border)">
          <div class="text-xs text-(--ui-text-muted)">Phone Number</div>
          <div class="font-semibold text-(--ui-text-highlighted) mt-0.5">{{ ownerStore.user?.phone || 'Not configured' }}</div>
        </div>

        <div class="p-3 rounded-2xl bg-(--ui-bg) border border-(--ui-border)">
          <div class="text-xs text-(--ui-text-muted)">Merchant ID</div>
          <div class="font-mono text-xs font-semibold text-emerald-500 mt-0.5">{{ ownerStore.user?.user_id || '—' }}</div>
        </div>
      </div>
    </div>

    <!-- Change Password Card -->
    <div class="rounded-3xl p-6 border border-(--ui-border) glass-panel space-y-4">
      <h3 class="text-base font-bold text-(--ui-text-highlighted)">Change Password</h3>

      <form class="space-y-4 max-w-md" @submit.prevent="handleUpdatePassword">
        <UFormField label="Current Password" required>
          <UInput v-model="currentPassword" type="password" placeholder="••••••••" required />
        </UFormField>

        <UFormField label="New Password" required>
          <UInput v-model="newPassword" type="password" placeholder="At least 6 characters" required />
        </UFormField>

        <UButton type="submit" color="primary" size="sm" :loading="isUpdatingPassword">
          Update Password
        </UButton>
      </form>
    </div>
  </div>
</template>
