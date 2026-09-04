<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

const auth = useAuthStore()
const route = useRoute()
const toast = useToast()
const isMobileMenuOpen = ref(false)
const isNotificationsOpen = ref(false)
const notifications = ref<any[]>([])
const isLoadingNotifications = ref(false)
const showStoreModal = ref(false)

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)
const canAccessMerchant = computed(() => auth.isOwner || auth.stores.some(s => s.is_owner || s.role?.toLowerCase() === 'owner'))

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
  if (auth.isOwner || auth.hasPermission('record:sales')) {
    items.push({ label: 'POS Terminal', icon: 'i-lucide-scan-barcode', to: '/pos' })
  }
  if (auth.isOwner || auth.hasPermission('view:product') || auth.hasPermission('manage:product')) {
    items.push({ label: 'Products', icon: 'i-lucide-package', to: '/products' })
  }
  if (auth.isOwner || auth.hasPermission('record:sales')) {
    items.push({ label: 'Sales', icon: 'i-lucide-receipt', to: '/sales' })
  }
  if (auth.isOwner || auth.hasPermission('manage:user')) {
    items.push({ label: 'Customers', icon: 'i-lucide-users', to: '/customers' })
  }
  if (auth.isOwner || auth.hasPermission('view:analytics')) {
    items.push({ label: 'Analytics', icon: 'i-lucide-bar-chart-2', to: '/analytics' })
  }
  if (auth.isOwner || auth.hasPermission('manage:staff')) {
    items.push({ label: 'Staff', icon: 'i-lucide-shield-check', to: '/staff' })
  }
  if (auth.isOwner || auth.hasPermission('view:audit-log') || auth.hasPermission('manage:all')) {
    items.push({ label: 'Audit Logs', icon: 'i-lucide-shield-alert', to: '/audit' })
  }
  items.push({ label: 'Settings', icon: 'i-lucide-settings', to: '/settings' })
  return items
})

onMounted(() => {
  auth.loadFromStorage()
  auth.fetchMe()
  fetchNotifications()
})

async function handleLogout() {
  await auth.logout(true)
}

function handleSelectStore(storeId: string) {
  auth.switchStore(storeId)
  showStoreModal.value = false
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
      <div class="flex items-center h-16 px-4 border-b border-(--ui-border) shrink-0 justify-between">
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

      <div v-if="!isCollapsed" class="px-3 pt-3 pb-1 border-b border-(--ui-border)">
        <button
          type="button"
          class="w-full px-3 py-2 rounded-xl bg-(--ui-bg-accented)/50 hover:bg-(--ui-bg-accented) border border-(--ui-border) flex items-center justify-between text-left transition"
          @click="showStoreModal = true"
        >
          <div class="truncate">
            <p class="text-xs font-bold text-(--ui-text-highlighted) truncate">
              {{ auth.current_store?.name || 'Active Store' }}
            </p>
            <p class="text-[10px] text-(--ui-text-muted) capitalize truncate">
              {{ auth.current_store?.category || 'Retail' }} • {{ auth.isOwner ? 'Owner' : (auth.current_store?.role || 'Staff') }}
            </p>
          </div>
          <UIcon name="i-lucide-chevrons-up-down" class="size-4 text-(--ui-text-dimmed) shrink-0 ml-1" />
        </button>
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

        <div v-if="canAccessMerchant" class="pt-4 mt-4 border-t border-(--ui-border)">
          <NuxtLink
            to="/marchant"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-amber-500 hover:bg-amber-500/10',
            ]"
            :title="isCollapsed ? 'Merchant Hub' : undefined"
          >
            <UIcon name="i-lucide-layout-grid" class="w-5 h-5 shrink-0" />
            <Transition name="fade">
              <span v-if="!isCollapsed" class="whitespace-nowrap font-bold">Merchant Hub</span>
            </Transition>
          </NuxtLink>
        </div>
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
          
          <button
            type="button"
            class="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-accented)/40 hover:bg-(--ui-bg-accented) text-xs font-semibold text-(--ui-text-highlighted) transition"
            @click="showStoreModal = true"
          >
            <UIcon name="i-lucide-store" class="size-4 text-emerald-500" />
            <span>{{ auth.current_store?.name || 'Active Store' }}</span>
            <UIcon name="i-lucide-chevron-down" class="size-3.5 text-(--ui-text-dimmed)" />
          </button>
        </div>

        <div class="flex items-center gap-2">
          <NuxtLink v-if="canAccessMerchant" to="/marchant">
            <UButton
              size="sm"
              color="warning"
              variant="subtle"
              icon="i-lucide-layout-grid"
              class="hidden sm:inline-flex font-bold"
            >
              Merchant Hub
            </UButton>
          </NuxtLink>

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
              [{ label: auth.fullName || auth.user?.fullname || 'User', type: 'label' as const }],
              [
                ...(canAccessMerchant ? [{ label: 'Merchant Hub', icon: 'i-lucide-layout-grid', to: '/marchant', onSelect: () => navigateTo('/marchant') }] : []),
                { label: 'Switch Store', icon: 'i-lucide-store', onSelect: () => { showStoreModal = true } },
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
        <div class="mb-4 pb-4 border-b border-(--ui-border)">
          <button
            type="button"
            class="w-full p-3 rounded-xl bg-(--ui-bg-accented)/50 border border-(--ui-border) flex items-center justify-between text-left"
            @click="showStoreModal = true"
          >
            <div>
              <p class="text-xs font-bold text-(--ui-text-highlighted)">{{ auth.current_store?.name || 'Active Store' }}</p>
              <p class="text-[10px] text-(--ui-text-muted)">{{ auth.current_store?.category || 'Retail' }}</p>
            </div>
            <UIcon name="i-lucide-chevrons-up-down" class="size-4 text-(--ui-text-dimmed)" />
          </button>
        </div>

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

          <NuxtLink
            v-if="canAccessMerchant"
            to="/marchant"
            class="flex items-center gap-3 w-full px-3 py-4 rounded-lg text-base font-bold text-amber-500 hover:bg-amber-500/10 transition mt-4"
          >
            <UIcon name="i-lucide-layout-grid" class="w-6 h-6" />
            Merchant Hub
            <UIcon name="i-lucide-chevron-right" class="w-6 h-6 ml-auto" />
          </NuxtLink>
        </nav>
      </template>
    </USlideover>

    <UModal v-model:open="showStoreModal" title="Select Active Store">
      <template #body>
        <div class="p-5 space-y-4">
          <p class="text-sm text-(--ui-text-muted)">Choose which store terminal you want to operate:</p>
          <div class="space-y-2 max-h-72 overflow-y-auto">
            <button
              v-for="store in auth.stores"
              :key="store.store_id"
              type="button"
              :class="[
                'w-full p-4 rounded-xl border flex items-center justify-between text-left transition',
                store.store_id === auth.store_id
                  ? 'border-emerald-500/50 bg-emerald-500/10 text-(--ui-text-highlighted)'
                  : 'border-(--ui-border) bg-(--ui-bg-accented)/30 hover:bg-(--ui-bg-accented) text-(--ui-text-muted)'
              ]"
              @click="handleSelectStore(store.store_id)"
            >
              <div>
                <div class="flex items-center gap-2">
                  <p class="font-semibold text-sm text-(--ui-text-highlighted)">{{ store.name }}</p>
                  <span v-if="store.is_owner" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                    Owner
                  </span>
                  <span v-else class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-500/20 text-zinc-300">
                    {{ store.role }}
                  </span>
                </div>
                <p class="text-xs text-(--ui-text-muted) mt-0.5">{{ store.category }} • {{ store.address || 'Main Branch' }}</p>
              </div>
              <UIcon
                v-if="store.store_id === auth.store_id"
                name="i-lucide-check-circle"
                class="size-5 text-emerald-400 shrink-0"
              />
              <UIcon
                v-else
                name="i-lucide-chevron-right"
                class="size-5 text-(--ui-text-dimmed) shrink-0"
              />
            </button>
          </div>
        </div>
      </template>
    </UModal>

    <USlideover v-model:open="isNotificationsOpen" side="right" title="Notifications">
      <template #body>
        <div v-if="isLoadingNotifications" class="flex items-center justify-center py-12">
          <UIcon name="i-lucide-loader" class="w-6 h-6 animate-spin text-primary-500" />
        </div>
        <div v-else-if="notifications.length === 0" class="text-center py-12 space-y-2 text-(--ui-text-muted)">
          <UIcon name="i-lucide-bell-off" class="w-8 h-8 mx-auto opacity-50" />
          <p class="text-sm">No notifications yet</p>
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="item in notifications"
            :key="item.notification_id"
            :class="[
              'p-3 rounded-lg border transition cursor-pointer',
              item.is_read
                ? 'border-(--ui-border) bg-(--ui-bg-elevated) opacity-70'
                : 'border-primary-500/30 bg-primary-500/5'
            ]"
            @click="markNotificationAsRead(item)"
          >
            <div class="flex items-start justify-between gap-2 mb-1">
              <span class="font-medium text-sm text-(--ui-text-highlighted)">{{ item.title }}</span>
              <span class="text-[10px] text-(--ui-text-dimmed) shrink-0">{{ formatNotificationDate(item.created_at) }}</span>
            </div>
            <p class="text-xs text-(--ui-text-muted) line-clamp-2">{{ item.message }}</p>
          </div>
        </div>
      </template>
    </USlideover>
  </div>
</template>
