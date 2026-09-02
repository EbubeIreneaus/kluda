<script setup lang="ts">
const route = useRoute()
const { adminUser, logout } = useAdminAuth()
const { hasPermission } = useAdminPermission()
const isSidebarOpen = ref(false)

const allNavLinks = [
  { label: 'Overview', to: '/', icon: 'i-lucide-layout-dashboard', permission: 'view:analytics' },
  { label: 'Stores', to: '/stores', icon: 'i-lucide-store', permission: 'manage:stores' },
  { label: 'Merchants', to: '/merchants', icon: 'i-lucide-users', permission: 'manage:users' },
  { label: 'Plans & Billing', to: '/plans', icon: 'i-lucide-credit-card', permission: 'manage:billings' },
  { label: 'Campaigns', to: '/campaigns', icon: 'i-lucide-megaphone', permission: 'manage:emails' },
  { label: 'Support Inbox', to: '/inbox', icon: 'i-lucide-mail', permission: 'manage:emails' },
  { label: 'Support Tickets', to: '/support', icon: 'i-lucide-ticket', permission: 'manage:support' },
  { label: 'Notifications', to: '/notifications', icon: 'i-lucide-bell', permission: 'manage:admins' },
  { label: 'Admin Team', to: '/admins', icon: 'i-lucide-shield-check', permission: 'manage:admins' },
  { label: 'System Settings', to: '/settings', icon: 'i-lucide-sliders-horizontal', permission: 'manage:settings' }
]

const navLinks = computed(() => {
  return allNavLinks.filter(l => !l.permission || hasPermission(l.permission))
})
</script>

<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col md:flex-row antialiased selection:bg-emerald-500 selection:text-white">
    <aside class="hidden md:flex flex-col w-64 border-r border-zinc-800/80 bg-zinc-900/60 backdrop-blur-xl shrink-0 p-4 justify-between sticky top-0 h-screen">
      <div class="flex flex-col gap-6">
        <div class="flex items-center gap-3 px-2">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center font-black text-zinc-950 text-lg shadow-lg shadow-emerald-500/20">
            K
          </div>
          <div>
            <div class="font-bold text-sm tracking-tight text-white flex items-center gap-1.5">
              Kluda Admin
              <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">PROD</span>
            </div>
            <div class="text-[11px] text-zinc-400 font-mono">Control Center</div>
          </div>
        </div>

        <nav class="flex flex-col gap-1">
          <NuxtLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all"
            :class="route.path === link.to ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm' : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'"
          >
            <UIcon :name="link.icon" class="w-4 h-4 shrink-0" />
            <span>{{ link.label }}</span>
          </NuxtLink>
        </nav>
      </div>

      <div class="border-t border-zinc-800/80 pt-4 flex flex-col gap-3">
        <div class="flex items-center justify-between px-2 text-xs text-zinc-400">
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span class="text-[11px]">System Online</span>
          </div>
          <div class="flex items-center gap-1">
            <NuxtLink
              to="/notifications"
              class="p-1.5 rounded-lg text-zinc-400 hover:text-emerald-400 hover:bg-zinc-800 transition-colors"
              title="Notifications"
            >
              <UIcon name="i-lucide-bell" class="w-4 h-4" />
            </NuxtLink>
            <UColorModeButton size="xs" />
          </div>
        </div>

        <div class="flex items-center justify-between bg-zinc-900 border border-zinc-800 p-2.5 rounded-xl">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs shrink-0">
              {{ adminUser?.fullname?.charAt(0) || 'A' }}
            </div>
            <div class="min-w-0">
              <div class="text-xs font-semibold text-zinc-100 truncate">{{ adminUser?.fullname }}</div>
              <div class="text-[10px] text-zinc-400 font-mono truncate">{{ adminUser?.company_email }}</div>
            </div>
          </div>
          <button
            class="text-zinc-400 hover:text-rose-400 transition-colors p-1.5 rounded-lg hover:bg-zinc-800"
            title="Sign Out"
            @click="logout"
          >
            <UIcon name="i-lucide-log-out" class="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>

    <header class="md:hidden flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-900/90 backdrop-blur-lg sticky top-0 z-40">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-emerald-500 flex items-center justify-center font-black text-zinc-950 text-xs">
          K
        </div>
        <span class="font-bold text-sm text-zinc-100">Kluda Admin</span>
      </div>
      <div class="flex items-center gap-2">
        <NuxtLink
          to="/notifications"
          class="p-2 rounded-lg text-zinc-400 hover:text-emerald-400"
        >
          <UIcon name="i-lucide-bell" class="w-5 h-5" />
        </NuxtLink>
        <UButton
          icon="i-lucide-menu"
          color="neutral"
          variant="ghost"
          size="sm"
          @click="isSidebarOpen = !isSidebarOpen"
        />
      </div>
    </header>

    <div
      v-if="isSidebarOpen"
      class="md:hidden fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex"
      @click="isSidebarOpen = false"
    >
      <div
        class="w-80 max-w-[85vw] bg-zinc-900 border-r border-zinc-800 h-full p-5 flex flex-col justify-between shadow-2xl overflow-y-auto"
        @click.stop
      >
        <div class="flex flex-col gap-6">
          <div class="flex items-center justify-between border-b border-zinc-800/80 pb-4">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center font-black text-zinc-950 text-base shadow-lg shadow-emerald-500/20">
                K
              </div>
              <div>
                <div class="font-bold text-sm text-white">Kluda Admin</div>
                <div class="text-xs text-zinc-400 font-mono">Control Center</div>
              </div>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="sm" @click="isSidebarOpen = false" />
          </div>

          <nav class="flex flex-col gap-1.5">
            <NuxtLink
              v-for="link in navLinks"
              :key="link.to"
              :to="link.to"
              class="flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all"
              :class="route.path === link.to ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-xs' : 'text-zinc-300 hover:text-white hover:bg-zinc-800/60 active:bg-zinc-800'"
              @click="isSidebarOpen = false"
            >
              <UIcon :name="link.icon" class="w-5 h-5 shrink-0" />
              <span>{{ link.label }}</span>
            </NuxtLink>
          </nav>
        </div>

        <div class="border-t border-zinc-800/80 pt-4 flex flex-col gap-3">
          <div class="flex items-center justify-between bg-zinc-950 border border-zinc-800 p-3 rounded-xl">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-sm shrink-0">
                {{ adminUser?.fullname?.charAt(0) || 'A' }}
              </div>
              <div class="min-w-0">
                <div class="text-xs font-bold text-zinc-100 truncate">{{ adminUser?.fullname }}</div>
                <div class="text-[11px] text-zinc-400 font-mono truncate">{{ adminUser?.company_email }}</div>
              </div>
            </div>
          </div>

          <UButton
            label="Sign Out"
            icon="i-lucide-log-out"
            color="error"
            variant="soft"
            block
            size="md"
            class="font-semibold py-3"
            @click="logout"
          />
        </div>
      </div>
    </div>

    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">
      <slot />
    </main>
  </div>
</template>
