<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const toast = useToast()
const isMobileMenuOpen = ref(false)
const isGeneratingSSO = ref(false)
const isNotificationsOpen = ref(false)
const notifications = ref<any[]>([])
const isLoadingNotifications = ref(false)

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

async function fetchNotifications() {
  if (!auth.store_id) return
  isLoadingNotifications.value = true
  try {
    const { api } = useApi()
    const res = await api<any[]>(`/${auth.store_id}/notifications`)
    notifications.value = res || []
  } catch {
    notifications.value = []
  } finally {
    isLoadingNotifications.value = false
  }
}

async function markNotificationAsRead(item: any) {
  if (!auth.store_id || item.is_read) return
  item.is_read = true
  try {
    const { api } = useApi()
    await api(`/${auth.store_id}/notifications/${item.notification_id}/read`, {
      method: 'POST'
    })
  } catch {}
}

function formatNotificationDate(isoString: string) {
  if (!isoString) return ''
  try {
    const d = new Date(isoString)
    return d.toLocaleDateString('en-NG', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoString
  }
}

watch(isNotificationsOpen, (isOpen) => {
  if (isOpen) {
    fetchNotifications()
  }
})

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
  fetchNotifications()
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

          <div class="relative inline-flex">
            <UButton
              icon="i-lucide-bell"
              color="neutral"
              variant="ghost"
              size="sm"
              title="Terminal Notifications"
              @click="isNotificationsOpen = true"
            />
            <span
              v-if="unreadCount > 0"
              class="absolute -top-0.5 -right-0.5 flex h-2 w-2"
            >
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75" />
              <span class="relative inline-flex rounded-full h-2 w-2 bg-primary-500" />
            </span>
          </div>

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
              'flex items-center gap-3 px-3 py-4 rounded-lg text-base font-medium transition',
              isActive(item.to)
                ? 'bg-primary-500/10 text-primary-500 font-semibold'
                : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented)'
            ]"
          >
            <UIcon :name="item.icon" class="w-6 h-6" />
            {{ item.label }}

            <UIcon name="i-lucide-chevron-right" class="w-6 h-6 ml-auto" />
          </NuxtLink>
        </nav>
      </template>
    </USlideover>

    <USlideover v-model:open="isNotificationsOpen" side="right" title="Notifications & Alerts">
      <template #body>
        <div class="flex flex-col gap-4">
          <div v-if="isLoadingNotifications" class="space-y-3">
            <div v-for="i in 3" :key="i" class="p-4 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) animate-pulse space-y-2">
              <div class="h-3 bg-(--ui-bg-accented) rounded w-1/3" />
              <div class="h-4 bg-(--ui-bg-accented) rounded w-3/4" />
              <div class="h-3 bg-(--ui-bg-accented) rounded w-full" />
            </div>
          </div>

          <div v-else-if="notifications.length === 0" class="p-8 text-center flex flex-col items-center justify-center gap-3">
            <div class="w-12 h-12 rounded-full bg-primary-500/10 text-primary-500 flex items-center justify-center">
              <UIcon name="i-lucide-bell-off" class="size-6" />
            </div>
            <div class="space-y-1">
              <h4 class="text-sm font-semibold text-(--ui-text-highlighted)">All caught up!</h4>
              <p class="text-xs text-(--ui-text-muted)">No notifications for your store at the moment.</p>
            </div>
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="item in notifications"
              :key="item.notification_id"
              class="p-4 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) hover:bg-(--ui-bg-accented) transition-all space-y-2 cursor-pointer relative"
              :class="{ 'border-primary-500/30': !item.is_read }"
              @click="markNotificationAsRead(item)"
            >
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-semibold text-primary-500 uppercase tracking-wider">
                  {{ item.scope || 'Alert' }}
                </span>
                <span class="text-[10px] text-(--ui-text-dimmed)">
                  {{ formatNotificationDate(item.created_at) }}
                </span>
              </div>
              <div class="flex items-start justify-between gap-2">
                <h4 class="text-xs font-bold text-(--ui-text-highlighted)" :class="{ 'font-black': !item.is_read }">
                  {{ item.title }}
                </h4>
                <span v-if="!item.is_read" class="size-2 rounded-full bg-primary-500 shrink-0 mt-1" />
              </div>
              <p class="text-xs text-(--ui-text-muted) leading-relaxed">
                {{ item.message }}
              </p>
            </div>
          </div>

          <div class="pt-2 text-center border-t border-(--ui-border)">
            <NuxtLink
              to="/settings"
              class="text-xs text-primary-500 hover:underline font-medium"
              @click="isNotificationsOpen = false"
            >
              Notification Settings &rarr;
            </NuxtLink>
          </div>
        </div>
      </template>
    </USlideover>
  </div>
</template>
