<script setup lang="ts">
definePageMeta({ layout: 'dashboard' })

const auth = useAuthStore()
const toast = useToast()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

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

    // Since token is revoked on backend upon password change, log out cleanly
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
</script>

<template>
  <div class="max-w-4xl space-y-6">
    <div>
      <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Account Settings</h2>
      <p class="text-sm text-(--ui-text-muted)">View your staff profile and update your security credentials.</p>
    </div>

    <!-- Staff Profile Card (Read Only) -->
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
                :key="typeof perm === 'string' ? perm : perm.value"
                :color="(typeof perm === 'string' ? perm : perm.value) === 'manage:all' ? 'error' : 'info'"
                variant="subtle"
                size="xs"
              >
                {{ typeof perm === 'string' ? perm : perm.value }}
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

    <!-- Change Password Form -->
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
