<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

const auth = useAuthStore()
const route = useRoute()
const isMobileMenuOpen = ref(false)
const isCollapsed = ref(false)
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

const merchantNavItems = [
  { label: 'Overview', icon: 'i-lucide-layout-dashboard', to: '/marchant' },
  { label: 'Store Branches', icon: 'i-lucide-store', to: '/marchant/stores' },
  { label: 'Account & Security', icon: 'i-lucide-shield-check', to: '/marchant/account' },
  { label: 'Billing & Plans', icon: 'i-lucide-credit-card', to: '/marchant/billing' },
]

onMounted(() => {
  auth.loadFromStorage()
  auth.fetchMe()
  fetchNotifications()
})

async function handleLogout() {
  await auth.logout(true)
}

const isActive = (path: string) => {
  if (path === '/marchant') return route.path === '/marchant'
  return route.path.startsWith(path)
}

watch(() => route.path, () => {
  isMobileMenuOpen.value = false
})


useHead({
  script: [
    {
      innerHTML: `
        var Tawk_API=Tawk_API||{}, Tawk_LoadStart=new Date();
        (function(){
        var s1=document.createElement("script"),s0=document.getElementsByTagName("script")[0];
        s1.async=true;
        s1.src='https://embed.tawk.to/6a998c98d862ed3449e54d36/1k1jsqdgb';
        s1.charset='UTF-8';
        s1.setAttribute('crossorigin','*');
        s0.parentNode.insertBefore(s1,s0);
        })();
      `,
      type: 'text/javascript',
    },
  ],
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
          <div class="flex items-center justify-center w-9 h-9 rounded-xl bg-[#090d16] border border-amber-500/30 overflow-hidden shrink-0 shadow-md shadow-amber-500/20">
            <img src="/kluda_icon.jpg" alt="Kluda" class="w-full h-full object-cover" />
          </div>
          <Transition name="fade">
            <div v-if="!isCollapsed" class="flex flex-col leading-none">
              <span class="font-black text-lg tracking-wider text-(--ui-text-highlighted) whitespace-nowrap">
                KLUDA
              </span>
              <span class="text-[9px] font-bold text-amber-500 tracking-wider uppercase">Merchant Portfolio</span>
            </div>
          </Transition>
        </div>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <NuxtLink
          v-for="item in merchantNavItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group',
            isActive(item.to)
              ? 'bg-amber-500/10 text-amber-500 font-semibold shadow-xs'
              : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented) hover:text-(--ui-text-highlighted)'
          ]"
          :title="isCollapsed ? item.label : undefined"
        >
          <UIcon :name="item.icon" class="w-5 h-5 shrink-0" />
          <Transition name="fade">
            <span v-if="!isCollapsed" class="whitespace-nowrap">{{ item.label }}</span>
          </Transition>
        </NuxtLink>

        <div class="pt-4 mt-4 border-t border-(--ui-border)">
          <NuxtLink
            to="/"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-emerald-500 hover:bg-emerald-500/10',
            ]"
            :title="isCollapsed ? 'Open POS Terminal' : undefined"
          >
            <UIcon name="i-lucide-scan-barcode" class="w-5 h-5 shrink-0" />
            <Transition name="fade">
              <span v-if="!isCollapsed" class="whitespace-nowrap font-bold">Open POS Terminal</span>
            </Transition>
          </NuxtLink>
        </div>
      </nav>

      <div class="p-3 border-t border-(--ui-border)">
        <button
          class="flex items-center justify-center w-full py-2 rounded-lg text-(--ui-text-muted) hover:bg-(--ui-bg-accented) transition cursor-pointer"
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
          
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Merchant Center
            </span>
            <span class="text-xs text-(--ui-text-dimmed) hidden sm:inline">/</span>
            <span class="text-xs font-medium text-(--ui-text-muted) hidden sm:inline">
              {{ auth.fullName || auth.user?.fullname || 'Owner' }}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-2.5">
          <NuxtLink to="/">
            <UButton
              size="sm"
              color="primary"
              variant="subtle"
              icon="i-lucide-scan-barcode"
              class="font-semibold hidden sm:inline-flex"
            >
              POS Terminal
            </UButton>
          </NuxtLink>

          <div class="relative inline-flex">
            <UButton
              icon="i-lucide-bell"
              color="neutral"
              variant="ghost"
              size="sm"
              title="Notifications"
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
              [{ label: auth.fullName || auth.user?.fullname || 'Owner', type: 'label' as const }],
              [
                { label: 'POS Terminal', icon: 'i-lucide-scan-barcode', to: '/', onSelect: () => navigateTo('/') },
                { label: 'Account & Security', icon: 'i-lucide-shield-check', to: '/marchant/account', onSelect: () => navigateTo('/marchant/account') },
                { label: 'Billing & Plans', icon: 'i-lucide-credit-card', to: '/marchant/billing', onSelect: () => navigateTo('/marchant/billing') },
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

    <USlideover v-model:open="isMobileMenuOpen" side="left" title="Merchant Portfolio">
      <template #body>
        <div class="mb-4 pb-4 border-b border-(--ui-border)">
          <p class="text-xs font-bold text-(--ui-text-highlighted)">{{ auth.fullName || auth.user?.fullname || 'Store Owner' }}</p>
          <p class="text-[10px] text-amber-400 font-semibold">{{ auth.stores.length }} Owned Branches</p>
        </div>

        <nav class="space-y-2">
          <NuxtLink
            v-for="item in merchantNavItems"
            :key="item.to"
            :to="item.to"
            :class="[
              'flex items-center gap-3 px-3 py-4 rounded-lg text-base font-medium transition',
              isActive(item.to)
                ? 'bg-amber-500/10 text-amber-500 font-semibold'
                : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented)'
            ]"
          >
            <UIcon :name="item.icon" class="w-6 h-6" />
            {{ item.label }}
            <UIcon name="i-lucide-chevron-right" class="w-6 h-6 ml-auto" />
          </NuxtLink>

          <div class="pt-4 border-t border-(--ui-border)">
            <NuxtLink
              to="/"
              class="flex items-center gap-3 px-3 py-4 rounded-lg text-base font-bold text-emerald-500 hover:bg-emerald-500/10 transition"
            >
              <UIcon name="i-lucide-scan-barcode" class="w-6 h-6" />
              Open POS Terminal
              <UIcon name="i-lucide-chevron-right" class="w-6 h-6 ml-auto" />
            </NuxtLink>
          </div>
        </nav>
      </template>
    </USlideover>

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
