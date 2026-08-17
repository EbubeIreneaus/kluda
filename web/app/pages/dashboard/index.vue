<script setup lang="ts">
import { computed } from 'vue'

definePageMeta({ layout: 'dashboard' })

const ownerStore = useOwnerStore()
const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'

const totalStores = computed(() => ownerStore.activeStores.length)
const currentStore = computed(() => ownerStore.selectedStore)

const kpis = computed(() => [
  {
    title: 'Total Stores / Branches',
    value: String(totalStores.value),
    icon: 'i-lucide-store',
    subtitle: `${ownerStore.activeStores.filter(s => s.status === 'active').length} active branches`,
    color: 'emerald'
  },
  {
    title: 'Active Store Name',
    value: currentStore.value?.name || 'No Store Selected',
    icon: 'i-lucide-tag',
    subtitle: currentStore.value?.category || 'Create a store to begin',
    color: 'teal'
  },
  {
    title: 'Cashier Terminals',
    value: 'Ready',
    icon: 'i-lucide-scan-barcode',
    subtitle: 'Camera barcode scanning',
    color: 'blue'
  },
  {
    title: 'Offline Sync Engine',
    value: 'Active',
    icon: 'i-lucide-shield-check',
    subtitle: 'Automatic offline sales protection',
    color: 'violet'
  }
])

function copy_txt(txt: string){
  navigator.clipboard.writeText(txt as string)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-(--ui-text-highlighted)">
          Welcome, {{ ownerStore.user?.fullname || 'Merchant' }} 👋
        </h1>
        <p class="text-sm text-(--ui-text-muted) mt-1">
          Here is an overview of your multi-store retail operations.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <NuxtLink to="/dashboard/stores">
          <UButton color="primary" size="sm" class="font-semibold">
            <UIcon name="i-lucide-plus" class="w-4 h-4 mr-1.5" />
            Add New Store
          </UButton>
        </NuxtLink>

        <a :href="posUrl" target="_blank">
          <UButton variant="outline" color="neutral" size="sm">
            <UIcon name="i-lucide-scan-barcode" class="w-4 h-4 mr-1.5 text-emerald-500" />
            Open Register
          </UButton>
        </a>
      </div>
    </div>

    <!-- KPI Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="kpi in kpis"
        :key="kpi.title"
        class="rounded-2xl p-5 border border-(--ui-border) bg-(--ui-bg-elevated)/40 glass-panel"
      >
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-(--ui-text-muted)">{{ kpi.title }}</span>
          <div class="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
            <UIcon :name="kpi.icon" class="w-4 h-4" />
          </div>
        </div>
        <div class="text-2xl font-extrabold text-(--ui-text-highlighted) truncate">{{ kpi.value }}</div>
        <div class="text-xs text-(--ui-text-muted) mt-1">{{ kpi.subtitle }}</div>
      </div>
    </div>

    <!-- Quick Action / Store Info Card -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Active Store Credentials -->
      <div class="lg:col-span-2 rounded-3xl p-6 border border-(--ui-border) glass-panel bg-(--ui-bg-elevated)/40 space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-(--ui-text-highlighted)">Active Store Details</h3>
          <span class="text-xs px-2.5 py-1 rounded-full font-semibold bg-emerald-500/10 text-emerald-500">
            {{ currentStore?.status || 'Active' }}
          </span>
        </div>

        <div v-if="currentStore" class="space-y-3 text-sm">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl bg-(--ui-bg) border border-(--ui-border) gap-2">
            <div>
              <div class="text-xs text-(--ui-text-muted)">Store ID (Needed for Staff Cashiers)</div>
              <div class="font-mono text-sm font-bold text-emerald-500 select-all">{{ currentStore.store_id }}</div>
            </div>
            <UButton
              size="xs"
              variant="soft"
              color="neutral"
              @click="copy_txt(currentStore.store_id)"
            >
              <UIcon name="i-lucide-copy" class="w-3.5 h-3.5 mr-1" />
              Copy ID
            </UButton>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="p-3 rounded-xl bg-(--ui-bg) border border-(--ui-border)">
              <div class="text-xs text-(--ui-text-muted)">Category</div>
              <div class="font-semibold text-(--ui-text-highlighted)">{{ currentStore.category }}</div>
            </div>
            <div class="p-3 rounded-xl bg-(--ui-bg) border border-(--ui-border)">
              <div class="text-xs text-(--ui-text-muted)">Phone</div>
              <div class="font-semibold text-(--ui-text-highlighted)">{{ currentStore.phone || 'Not configured' }}</div>
            </div>
          </div>
        </div>

        <div v-else class="py-8 text-center text-sm text-(--ui-text-muted)">
          <UIcon name="i-lucide-store" class="w-8 h-8 mx-auto mb-2 text-slate-500" />
          <p>No store created yet.</p>
          <NuxtLink to="/dashboard/stores" class="mt-2 inline-block">
            <UButton size="sm" color="primary">Create Your First Store</UButton>
          </NuxtLink>
        </div>
      </div>

      <!-- Quick Steps for Cashier Setup -->
      <div class="rounded-3xl p-6 border border-(--ui-border) glass-panel bg-(--ui-bg-elevated)/40 space-y-4">
        <h3 class="text-base font-bold text-(--ui-text-highlighted)">How to Setup Cashiers</h3>
        <ol class="space-y-3 text-xs text-(--ui-text-muted)">
          <li class="flex items-start gap-2.5">
            <span class="w-5 h-5 rounded-full bg-emerald-500 text-slate-950 font-bold flex items-center justify-center shrink-0 text-[10px]">1</span>
            <span>Go to <NuxtLink to="/dashboard/staff" class="text-emerald-500 font-semibold underline">Staff & Cashiers</NuxtLink> and create an account.</span>
          </li>
          <li class="flex items-start gap-2.5">
            <span class="w-5 h-5 rounded-full bg-emerald-500 text-slate-950 font-bold flex items-center justify-center shrink-0 text-[10px]">2</span>
            <span>Note the auto-generated <strong>Staff ID</strong> (e.g. <code>STF1001</code>) and password.</span>
          </li>
          <li class="flex items-start gap-2.5">
            <span class="w-5 h-5 rounded-full bg-emerald-500 text-slate-950 font-bold flex items-center justify-center shrink-0 text-[10px]">3</span>
            <span>Open the <a :href="posUrl" target="_blank" class="text-emerald-500 font-semibold underline">POS Register App</a> on any phone/tablet and log in.</span>
          </li>
        </ol>
      </div>
    </div>
  </div>
</template>
