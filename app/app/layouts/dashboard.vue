<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const toast = useToast()
const isMobileMenuOpen = ref(false)
const isGeneratingSSO = ref(false)
const isNotificationsOpen = ref(false)

usePosSocket()
const isCollapsed = ref(false)

const navItems = computed(() => {
  const items = [
    { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/' },
  ]
  if (auth.hasPermission('record:sales')) {
    items.push({ label: 'POS Terminal', icon: 'i-lucide-scan-barcode', to: '/pos' })
  }
  if (auth.hasPermission('view:product') || auth.hasPermission('manage:product')) {
    items.push({ label: 'Products', icon: 'i-lucide-package', to: '/products' })
  }
  if (auth.hasPermission('record:sales')) {
    items.push({ label: 'Sales', icon: 'i-lucide-receipt', to: '/sales' })
  }
  if (auth.hasPermission('manage:user')) {
    items.push({ label: 'Customers', icon: 'i-lucide-users', to: '/customers' })
  }
  if (auth.hasPermission('view:analytics')) {
    items.push({ label: 'Analytics', icon: 'i-lucide-bar-chart-2', to: '/analytics' })
  }
  if (auth.hasPermission('manage:staff')) {
    items.push({ label: 'Staff', icon: 'i-lucide-shield-check', to: '/staff' })
  }
  items.push({ label: 'Settings', icon: 'i-lucide-settings', to: '/settings' })
  return items
})

onMounted(() => {
  auth.fetchMe()
})

async function openManagementDashboard() {
  isGeneratingSSO.value = true
  try {
    const { api } = useApi()
    const res = await api<{ ticket: string }>('/auth/sso/ticket', { method: 'POST' })
    if (res?.ticket) {
      const config = useRuntimeConfig()
      let webUrl = (config.public.webDashboardUrl as string) || ''
      if (!webUrl || (webUrl.includes('localhost') && window.location.hostname !== 'localhost')) {
        const origin = window.location.origin
        webUrl = origin.replace('app.', '').replace('pos.', '')
      }
      window.open(`${webUrl}/auth/sso?ticket=${encodeURIComponent(res.ticket)}`, '_blank')
    }
  } catch (err: any) {
    toast.add({
      title: 'Management Access',
      description: err?.data?.detail || 'Could not initiate single sign-on ticket',
      color: 'error'
    })
  } finally {
    isGeneratingSSO.value = false
  }
}

async function handleLogout() {
  await auth.logout(true)
}

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

watch(() => route.path, () => {
  isMobileMenuOpen.value = false
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-(--ui-bg)">
    <aside
      :class="[
        'hidden lg:flex flex-col border-r border-(--ui-border) bg-(--ui-bg-elevated) transition-all duration-300 shrink-0',
        isCollapsed ? 'w-[72px]' : 'w-64'
      ]"
    >
      <div class="flex items-center h-16 px-4 border-b border-(--ui-border) shrink-0">
        <div class="flex items-center gap-3 overflow-hidden">
          <div class="flex items-center justify-center w-9 h-9 rounded-xl bg-[#090d16] border border-emerald-500/30 overflow-hidden shrink-0 shadow-md shadow-emerald-500/20">
            <img src="/kluda_icon.jpg" alt="Kluda" class="w-full h-full object-cover" />
          </div>
          <Transition name="fade">
            <div v-if="!isCollapsed" class="flex flex-col leading-none">
              <span class="font-black text-lg tracking-wider text-(--ui-text-highlighted) whitespace-nowrap">
                KLUDA
              </span>
              <span class="text-[9px] font-medium text-emerald-500 tracking-wider uppercase">POS Terminal</span>
            </div>
          </Transition>
        </div>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <NuxtLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group',
            isActive(item.to)
              ? 'bg-primary-500/10 text-primary-500 font-semibold shadow-xs'
              : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented) hover:text-(--ui-text-highlighted)'
          ]"
          :title="isCollapsed ? item.label : undefined"
        >
          <UIcon :name="item.icon" class="w-5 h-5 shrink-0" />
          <Transition name="fade">
            <span v-if="!isCollapsed" class="whitespace-nowrap">{{ item.label }}</span>
          </Transition>
        </NuxtLink>

        <button
          v-if="auth.hasPermission('manage:all') || auth.hasPermission('manage:store') || auth.staff?.role === 'manager' || auth.staff?.role === 'owner' || auth.staff?.role === 'admin'"
          type="button"
          :class="[
            'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-amber-500 hover:bg-amber-500/10 mt-4',
          ]"
          :title="isCollapsed ? 'Store Management' : undefined"
          @click="openManagementDashboard"
        >
          <UIcon :name="isGeneratingSSO ? 'i-lucide-loader' : 'i-lucide-external-link'" :class="['w-5 h-5 shrink-0', isGeneratingSSO ? 'animate-spin' : '']" />
          <Transition name="fade">
            <span v-if="!isCollapsed" class="whitespace-nowrap">Store Management</span>
          </Transition>
        </button>
      </nav>

      <div class="p-3 border-t border-(--ui-border)">
        <button
          class="flex items-center justify-center w-full py-2 rounded-lg text-(--ui-text-muted) hover:bg-(--ui-bg-accented) transition"
          @click="isCollapsed = !isCollapsed"
        >
          <UIcon :name="isCollapsed ? 'i-lucide-chevrons-right' : 'i-lucide-chevrons-left'" class="w-5 h-5" />
        </button>
      </div>
    </aside>

    <div class="flex flex-col flex-1 overflow-hidden">
      <header class="flex items-center justify-between h-16 px-4 lg:px-6 border-b border-(--ui-border) bg-(--ui-bg-elevated) shrink-0">
        <div class="flex items-center gap-3">
          <button class="lg:hidden" @click="isMobileMenuOpen = true">
            <UIcon name="i-lucide-menu" class="w-6 h-6 text-(--ui-text-muted)" />
          </button>
          <h1 class="text-lg font-semibold text-(--ui-text-highlighted)">
            {{ navItems.find(i => isActive(i.to))?.label || 'Dashboard' }}
          </h1>
        </div>

        <div class="flex items-center gap-2">
          <UButton
            v-if="auth.hasPermission('manage:all') || auth.hasPermission('manage:store') || auth.staff?.role === 'manager' || auth.staff?.role === 'owner' || auth.staff?.role === 'admin'"
            size="sm"
            color="primary"
            variant="subtle"
            icon="i-lucide-external-link"
            :loading="isGeneratingSSO"
            class="hidden sm:inline-flex"
            @click="openManagementDashboard"
          >
            Management
          </UButton>

          <UButton
            icon="i-lucide-bell"
            color="neutral"
            variant="ghost"
            size="sm"
            title="Terminal Notifications"
            @click="isNotificationsOpen = true"
          />

          <UColorModeButton />

          <UDropdownMenu
            :items="[
              [{ label: auth.fullName || 'Staff Member', type: 'label' as const }],
              [
                { label: 'Store Management', icon: 'i-lucide-external-link', onSelect: () => openManagementDashboard() },
                { label: 'Settings', icon: 'i-lucide-settings', to: '/settings', onSelect: () => navigateTo('/settings') },
                { label: 'Logout', icon: 'i-lucide-log-out', onSelect: () => handleLogout(), click: () => handleLogout() }
              ]
            ]"
          >
            <UButton color="neutral" variant="ghost" class="rounded-full">
              <UAvatar :text="auth.initials" size="sm" />
            </UButton>
          </UDropdownMenu>
        </div>
      </header>

      <main class="flex-1 overflow-y-auto p-4 lg:p-6">
        <slot />
      </main>
    </div>

    <USlideover v-model:open="isMobileMenuOpen" side="left" title="Navigation">
      <template #body>
        <nav class="space-y-2">
          <NuxtLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            :class="[
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition',
              isActive(item.to)
                ? 'bg-primary-500/10 text-primary-500 font-semibold'
                : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented)'
            ]"
          >
            <UIcon :name="item.icon" class="w-5 h-5" />
            {{ item.label }}
          </NuxtLink>
        </nav>
      </template>
    </USlideover>

    <USlideover v-model:open="isNotificationsOpen" side="right" title="Terminal Alerts & Notifications">
      <template #body>
        <div class="flex flex-col gap-4">
          <div class="p-4 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-primary-500 uppercase tracking-wider">System Broadcast</span>
              <span class="text-[10px] text-(--ui-text-dimmed)">Live</span>
            </div>
            <h4 class="text-sm font-bold text-(--ui-text-highlighted)">Offline Sync Active</h4>
            <p class="text-xs text-(--ui-text-muted) leading-relaxed">
              Your register terminal is operating with full local SQLite/IndexedDB caching. All sales transactions and inventory updates will synchronize automatically.
            </p>
          </div>

          <div class="p-4 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-emerald-500 uppercase tracking-wider">Hardware Status</span>
              <span class="text-[10px] text-(--ui-text-dimmed)">Connected</span>
            </div>
            <h4 class="text-sm font-bold text-(--ui-text-highlighted)">Printer & Barcode Scanner</h4>
            <p class="text-xs text-(--ui-text-muted) leading-relaxed">
              Thermal receipt printer communication and USB/Bluetooth HID scanner listeners are active.
            </p>
          </div>

          <div class="pt-2 text-center">
            <NuxtLink
              to="/settings"
              class="text-xs text-primary-500 hover:underline font-medium"
              @click="isNotificationsOpen = false"
            >
              Configure Push Alert Preferences &rarr;
            </NuxtLink>
          </div>
        </div>
      </template>
    </USlideover>
  </div>
</template>
