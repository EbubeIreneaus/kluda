<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const ownerStore = useOwnerStore()
const route = useRoute()
const config = useRuntimeConfig()
const isMobileMenuOpen = ref(false)

const posUrl = config.public.posAppUrl || 'http://localhost:3000'

const navItems = [
  { label: 'Overview', icon: 'i-lucide-layout-dashboard', to: '/dashboard' },
  { label: 'My Stores', icon: 'i-lucide-store', to: '/dashboard/stores' },
  { label: 'Staff & Cashiers', icon: 'i-lucide-users', to: '/dashboard/staff' },
  { label: 'Account Settings', icon: 'i-lucide-settings', to: '/dashboard/settings' }
]

const storeOptions = computed(() => {
  return ownerStore.activeStores.map(s => ({
    label: s.name,
    value: s.store_id
  }))
})

onMounted(async () => {
  ownerStore.loadFromStorage()
  await ownerStore.fetchMe()
  await ownerStore.fetchStores()
})

const isActive = (path: string) => {
  if (path === '/dashboard') return route.path === '/dashboard'
  return route.path.startsWith(path)
}

function handleStoreChange(storeId: any) {
  if (storeId) {
    ownerStore.selectStore(String(storeId))
  }
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-(--ui-bg)">
    <!-- Sidebar for Desktop -->
    <aside class="hidden lg:flex flex-col w-64 border-r border-(--ui-border) bg-(--ui-bg-elevated)/50 shrink-0">
      <!-- Logo header -->
      <div class="h-16 flex items-center px-6 border-b border-(--ui-border)">
        <NuxtLink to="/dashboard">
          <BrandLogo />
        </NuxtLink>
      </div>

      <!-- Store Switcher in sidebar -->
      <div class="p-4 border-b border-(--ui-border)">
        <div class="text-[11px] font-semibold uppercase tracking-wider text-(--ui-text-muted) mb-1.5">Active Store</div>
        <div v-if="ownerStore.stores.length > 0">
          <select
            :value="ownerStore.selectedStoreId"
            @change="handleStoreChange(($event.target as HTMLSelectElement).value)"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3 py-2 text-xs font-semibold text-(--ui-text-highlighted) outline-none focus:border-emerald-500 transition"
          >
            <option v-for="s in ownerStore.activeStores" :key="s.store_id" :value="s.store_id">
              {{ s.name }} ({{ s.category }})
            </option>
          </select>
        </div>
        <div v-else class="text-xs text-(--ui-text-muted)">
          No stores found.
        </div>
      </div>

      <!-- Navigation links -->
      <nav class="flex-1 overflow-y-auto p-4 space-y-1">
        <NuxtLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition cursor-pointer"
          :class="isActive(item.to) ? 'bg-emerald-500/10 text-emerald-500 font-semibold' : 'text-(--ui-text-muted) hover:bg-(--ui-bg-muted) hover:text-(--ui-text)'"
        >
          <UIcon :name="item.icon" class="w-5 h-5 shrink-0" />
          <span>{{ item.label }}</span>
        </NuxtLink>
      </nav>

      <!-- Launch POS app CTA in bottom sidebar -->
      <div class="p-4 border-t border-(--ui-border)">
        <a :href="posUrl" target="_blank" class="block">
          <div class="p-3 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 hover:border-emerald-500/40 transition group">
            <div class="flex items-center gap-2 mb-1">
              <UIcon name="i-lucide-scan-barcode" class="w-4 h-4 text-emerald-500" />
              <span class="text-xs font-bold text-(--ui-text-highlighted)">POS Cashier App</span>
            </div>
            <p class="text-[11px] text-(--ui-text-muted) leading-tight">
              Open the offline cashier register terminal
            </p>
          </div>
        </a>
      </div>

      <!-- User footer in sidebar -->
      <div class="p-4 border-t border-(--ui-border) flex items-center justify-between">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center font-bold text-xs shrink-0">
            {{ ownerStore.initials }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-xs font-semibold text-(--ui-text-highlighted) truncate">{{ ownerStore.user?.fullname || 'Store Owner' }}</div>
            <div class="text-[10px] text-(--ui-text-muted) truncate">{{ ownerStore.user?.email }}</div>
          </div>
        </div>

        <button
          @click="ownerStore.logout(true)"
          class="text-(--ui-text-muted) hover:text-rose-500 p-1.5 rounded-lg transition"
          title="Sign Out"
        >
          <UIcon name="i-lucide-log-out" class="w-4 h-4" />
        </button>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Top header bar -->
      <header class="h-16 border-b border-(--ui-border) bg-(--ui-bg)/80 backdrop-blur-xl px-4 lg:px-8 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-3">
          <!-- Mobile menu trigger -->
          <button
            @click="isMobileMenuOpen = !isMobileMenuOpen"
            class="lg:hidden p-2 rounded-xl border border-(--ui-border) text-(--ui-text-muted)"
          >
            <UIcon name="i-lucide-menu" class="w-5 h-5" />
          </button>

          <div class="hidden sm:block">
            <span class="text-xs text-(--ui-text-muted)">Current Branch:</span>
            <span class="text-sm font-bold text-(--ui-text-highlighted) ml-1.5">
              {{ ownerStore.selectedStore?.name || 'All Stores' }}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <a :href="posUrl" target="_blank">
            <UButton size="xs" color="primary" variant="soft" class="font-semibold">
              <UIcon name="i-lucide-external-link" class="w-3.5 h-3.5 mr-1" />
              Launch POS App
            </UButton>
          </a>

          <UColorModeButton />
        </div>
      </header>

      <!-- Main scrollable view -->
      <main class="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
        <slot />
      </main>
    </div>
  </div>
</template>
