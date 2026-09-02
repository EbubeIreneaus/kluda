<script setup lang="ts">
import { computed } from 'vue'

definePageMeta({ layout: 'marchant' })

const auth = useAuthStore()

const ownedStores = computed(() => auth.stores.filter(s => s.is_owner))
const memberStores = computed(() => auth.stores.filter(s => !s.is_owner))

const kpis = computed(() => [
  {
    title: 'Total Retail Branches',
    value: String(auth.stores.length),
    icon: 'i-lucide-store',
    subtitle: `${ownedStores.value.length} owned, ${memberStores.value.length} managed`,
    color: 'emerald'
  },
  {
    title: 'Account Role',
    value: 'Merchant Owner',
    icon: 'i-lucide-crown',
    subtitle: auth.user?.email || auth.staff?.email || '',
    color: 'amber'
  },
  {
    title: 'Offline Sync Engine',
    value: 'Active',
    icon: 'i-lucide-shield-check',
    subtitle: 'IndexedDB multi-store isolation',
    color: 'teal'
  },
  {
    title: 'Subscription Tier',
    value: 'Growth Plan',
    icon: 'i-lucide-credit-card',
    subtitle: 'Unlimited multi-store access',
    color: 'blue'
  }
])

function handleLaunchTerminal(storeId: string) {
  auth.switchStore(storeId)
  navigateTo('/')
}
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black tracking-tight text-(--ui-text-highlighted)">
          Merchant Portfolio Overview 👋
        </h1>
        <p class="text-sm text-(--ui-text-muted) mt-1">
          Executive summary of all your retail branches, staff teams, account credentials, and subscription.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <NuxtLink to="/marchant/stores">
          <UButton color="primary" size="md" class="font-bold px-4 py-2.5">
            <UIcon name="i-lucide-plus" class="w-4 h-4 mr-1.5" />
            Add Store Branch
          </UButton>
        </NuxtLink>

        <NuxtLink to="/">
          <UButton variant="outline" color="neutral" size="md" class="font-bold px-4 py-2.5">
            <UIcon name="i-lucide-scan-barcode" class="w-4 h-4 mr-1.5 text-emerald-500" />
            Open Register
          </UButton>
        </NuxtLink>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="kpi in kpis"
        :key="kpi.title"
        class="rounded-2xl p-5 border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xs"
      >
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-(--ui-text-muted)">{{ kpi.title }}</span>
          <div class="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center">
            <UIcon :name="kpi.icon" class="w-4 h-4" />
          </div>
        </div>
        <div class="text-2xl font-black text-(--ui-text-highlighted) truncate">{{ kpi.value }}</div>
        <div class="text-xs text-(--ui-text-muted) mt-1 truncate">{{ kpi.subtitle }}</div>
      </div>
    </div>

    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-(--ui-text-highlighted)">Store Branches & Outlets</h2>
          <p class="text-xs text-(--ui-text-muted)">Click on any branch to manage its details, staff members, and settings.</p>
        </div>

        <NuxtLink to="/marchant/stores">
          <UButton variant="ghost" color="neutral" size="sm" class="font-semibold text-xs">
            View All ({{ auth.stores.length }})
            <UIcon name="i-lucide-arrow-right" class="w-3.5 h-3.5 ml-1" />
          </UButton>
        </NuxtLink>
      </div>

      <div v-if="auth.stores.length === 0" class="py-16 text-center rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)">
        <UIcon name="i-lucide-store" class="w-12 h-12 mx-auto mb-3 text-zinc-500" />
        <h3 class="text-base font-bold text-(--ui-text-highlighted)">No Store Branches Yet</h3>
        <p class="text-sm text-(--ui-text-muted) mt-1 mb-4">Create your first retail branch to start managing products and cashiers.</p>
        <NuxtLink to="/marchant/stores">
          <UButton color="primary" size="md" class="font-bold px-5 py-2.5">Create First Store</UButton>
        </NuxtLink>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="store in auth.stores"
          :key="store.store_id"
          class="rounded-3xl p-5 border border-(--ui-border) bg-(--ui-bg-elevated) hover:border-amber-500/50 transition flex flex-col justify-between group shadow-xs"
        >
          <div>
            <div class="flex items-start justify-between gap-2 mb-3">
              <div class="w-10 h-10 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold">
                <UIcon name="i-lucide-store" class="w-5 h-5" />
              </div>
              <span
                v-if="store.is_owner"
                class="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20"
              >
                Owner
              </span>
              <span
                v-else
                class="text-[10px] px-2.5 py-0.5 rounded-full font-medium bg-zinc-500/10 text-zinc-400"
              >
                {{ store.role }}
              </span>
            </div>

            <h3 class="text-base font-bold text-(--ui-text-highlighted) group-hover:text-amber-400 transition">
              {{ store.name }}
            </h3>
            <p class="text-xs text-(--ui-text-muted) mt-0.5">{{ store.category }}</p>
            <p v-if="store.address" class="text-xs text-(--ui-text-dimmed) mt-2 line-clamp-1">
              <UIcon name="i-lucide-map-pin" class="w-3.5 h-3.5 inline mr-1 text-zinc-500" />
              {{ store.address }}
            </p>
          </div>

          <div class="mt-5 pt-3 border-t border-(--ui-border) flex items-center justify-between gap-2">
            <NuxtLink :to="`/marchant/stores/${store.store_id}`">
              <UButton size="xs" variant="soft" color="neutral" icon="i-lucide-settings-2">
                Manage Branch
              </UButton>
            </NuxtLink>

            <UButton
              size="xs"
              variant="subtle"
              color="primary"
              icon="i-lucide-scan-barcode"
              @click="handleLaunchTerminal(store.store_id)"
            >
              Open POS
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
      <div class="p-6 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-3 shadow-xs">
        <div class="flex items-center gap-2 text-(--ui-text-highlighted)">
          <UIcon name="i-lucide-shield-check" class="w-5 h-5 text-amber-400" />
          <h3 class="font-bold text-sm">Owner Account & Security</h3>
        </div>
        <p class="text-xs text-(--ui-text-muted)">
          Logged in as <strong>{{ auth.user?.fullname || auth.fullName }}</strong> ({{ auth.user?.email || auth.staff?.email }}). Manage master security keys and password.
        </p>
        <div class="pt-2">
          <NuxtLink to="/marchant/account">
            <UButton size="sm" variant="outline" color="neutral">
              Security Settings
            </UButton>
          </NuxtLink>
        </div>
      </div>

      <div class="p-6 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-3 shadow-xs">
        <div class="flex items-center gap-2 text-(--ui-text-highlighted)">
          <UIcon name="i-lucide-credit-card" class="w-5 h-5 text-emerald-400" />
          <h3 class="font-bold text-sm">Subscription & Billing</h3>
        </div>
        <p class="text-xs text-(--ui-text-muted)">
          Current Plan: <strong>Merchant Growth Plan (Early Access)</strong>. Unlimited multi-branch support and offline sync.
        </p>
        <div class="pt-2">
          <NuxtLink to="/marchant/billing">
            <UButton size="sm" variant="outline" color="neutral">
              View Billing Details
            </UButton>
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
