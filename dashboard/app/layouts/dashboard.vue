<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const isMobileMenuOpen = ref(false)

// Mount POS WebSocket once — shared across all dashboard pages
usePosSocket()
const isCollapsed = ref(false)

const navItems = computed(() => {
  const items = [
    { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/dashboard' },
  ]
  if (auth.hasPermission('record:sales')) {
    items.push({ label: 'POS Terminal', icon: 'i-lucide-scan-barcode', to: '/dashboard/pos' })
  }
  if (auth.hasPermission('view:product') || auth.hasPermission('manage:product')) {
    items.push({ label: 'Products', icon: 'i-lucide-package', to: '/dashboard/products' })
  }
  if (auth.hasPermission('record:sales')) {
    items.push({ label: 'Sales', icon: 'i-lucide-receipt', to: '/dashboard/sales' })
  }
  if (auth.hasPermission('manage:user')) {
    items.push({ label: 'Customers', icon: 'i-lucide-users', to: '/dashboard/customers' })
  }
  if (auth.hasPermission('view:analytics')) {
    items.push({ label: 'Analytics', icon: 'i-lucide-bar-chart-2', to: '/dashboard/analytics' })
  }
  if (auth.hasPermission('manage:staff')) {
    items.push({ label: 'Staff', icon: 'i-lucide-shield-check', to: '/dashboard/staff' })
  }
  return items
})

onMounted(() => {
  auth.fetchMe()
})

async function handleLogout() {
  await auth.logout(true)
}

const isActive = (path: string) => {
  if (path === '/dashboard') return route.path === '/dashboard'
  return route.path.startsWith(path)
}

watch(() => route.path, () => {
  isMobileMenuOpen.value = false
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-(--ui-bg)">
    <!-- Desktop Sidebar -->
    <aside
      :class="[
        'hidden lg:flex flex-col border-r border-(--ui-border) bg-(--ui-bg-elevated) transition-all duration-300 shrink-0',
        isCollapsed ? 'w-[72px]' : 'w-64'
      ]"
    >
      <!-- Logo area -->
      <div class="flex items-center h-16 px-4 border-b border-(--ui-border) shrink-0">
        <div class="flex items-center gap-3 overflow-hidden">
          <div class="flex items-center justify-center w-9 h-9 rounded-lg bg-green-500 text-white font-bold text-sm shrink-0">
            RP
          </div>
          <Transition name="fade">
            <span v-if="!isCollapsed" class="font-semibold text-(--ui-text-highlighted) whitespace-nowrap">
              RetailPOS
            </span>
          </Transition>
        </div>
      </div>

      <!-- Nav links -->
      <nav class="flex-1 p-3 space-y-1 overflow-y-auto">
        <NuxtLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
            isActive(item.to)
              ? 'bg-green-500/10 text-green-600 dark:text-green-400'
              : 'text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented)'
          ]"
        >
          <UIcon :name="item.icon" class="w-5 h-5 shrink-0" />
          <Transition name="fade">
            <span v-if="!isCollapsed" class="whitespace-nowrap">{{ item.label }}</span>
          </Transition>
        </NuxtLink>
      </nav>

      <!-- Collapse toggle -->
      <div class="p-3 border-t border-(--ui-border)">
        <button
          class="flex items-center justify-center w-full py-2 rounded-lg text-(--ui-text-muted) hover:bg-(--ui-bg-accented) transition"
          @click="isCollapsed = !isCollapsed"
        >
          <UIcon :name="isCollapsed ? 'i-lucide-chevrons-right' : 'i-lucide-chevrons-left'" class="w-5 h-5" />
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex flex-col flex-1 overflow-hidden">
      <!-- Top bar -->
      <header class="flex items-center justify-between h-16 px-4 lg:px-6 border-b border-(--ui-border) bg-(--ui-bg-elevated) shrink-0">
        <div class="flex items-center gap-3">
          <!-- Mobile menu button -->
          <button class="lg:hidden" @click="isMobileMenuOpen = true">
            <UIcon name="i-lucide-menu" class="w-6 h-6 text-(--ui-text-muted)" />
          </button>
          <h1 class="text-lg font-semibold text-(--ui-text-highlighted)">
            {{ navItems.find(i => isActive(i.to))?.label || 'Dashboard' }}
          </h1>
        </div>

        <div class="flex items-center gap-2">
          <UColorModeButton />

          <UDropdownMenu
            :items="[
              [{ label: auth.fullName || 'Staff Member', type: 'label' as const }],
              [
                { label: 'Settings', icon: 'i-lucide-settings', to: '/dashboard/settings', onSelect: () => navigateTo('/dashboard/settings') },
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

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto p-4 lg:p-6">
        <slot />
      </main>
    </div>

    <!-- Mobile Sidebar Overlay -->
    <USlideover v-model:open="isMobileMenuOpen" side="left" title="Navigation">
      <template #body>
        <nav class="space-y-2">
          <NuxtLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            :class="[
              'flex items-center gap-4 px-4 py-3.5 rounded-xl text-base font-medium transition-all',
              isActive(item.to)
                ? 'bg-green-500/10 text-green-600 dark:text-green-400'
                : 'text-(--ui-text-muted) hover:text-(--ui-text-highlighted) hover:bg-(--ui-bg-accented)'
            ]"
          >
            <UIcon :name="item.icon" class="w-6 h-6 shrink-0" />
            <span>{{ item.label }}</span>
          </NuxtLink>
        </nav>
      </template>
    </USlideover>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
