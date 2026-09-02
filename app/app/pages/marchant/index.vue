<script setup lang="ts">
import { computed, onMounted } from 'vue'

definePageMeta({ layout: 'marchant' })

const auth = useAuthStore()
const {
  rawSub,
  plan,
  status,
  usage,
  priceFormatted,
  nextRenewalFormatted,
  daysRemaining,
  fetchCurrentSubscription
} = useSubscription()

onMounted(() => {
  fetchCurrentSubscription()
})

const ownedStores = computed(() => auth.stores.filter(s => s.is_owner))
const memberStores = computed(() => auth.stores.filter(s => !s.is_owner))

const isStoreLimitReached = computed(() => {
  return usage.value.storesLimit > 0 && usage.value.storesCount >= usage.value.storesLimit
})

function handleLaunchTerminal(storeId: string) {
  auth.switchStore(storeId)
  navigateTo('/')
}
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <!-- Executive Merchant Hero Banner -->
    <div class="p-6 md:p-8 rounded-3xl border border-(--ui-border) bg-gradient-to-br from-(--ui-bg-elevated) via-(--ui-bg-elevated)/90 to-emerald-950/20 shadow-sm relative overflow-hidden">
      <div class="absolute -right-16 -bottom-16 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
        <div class="space-y-2">
          <div class="flex flex-wrap items-center gap-2.5">
            <span class="text-xs font-bold uppercase tracking-wider text-emerald-400">
              Merchant Organization
            </span>
            <span
              class="px-2.5 py-0.5 rounded-full text-xs font-bold border"
              :class="[
                status === 'ACTIVE'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              ]"
            >
              {{ plan.name }} • {{ status }}
            </span>
            <span v-if="plan.slug === 'trial'" class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
              {{ daysRemaining }} days trial left
            </span>
          </div>

          <h1 class="text-2xl sm:text-3xl font-black tracking-tight text-(--ui-text-highlighted)">
            Welcome back, {{ auth.fullName || auth.user?.fullname || 'Merchant' }} 👋
          </h1>
          <p class="text-xs sm:text-sm text-(--ui-text-muted) max-w-2xl">
            Overview of your {{ ownedStores.length }} retail branches, team operations, and subscription quota health.
          </p>

          <!-- Active Offer/Referral Audit Description Banner if exists -->
          <div
            v-if="rawSub?.description"
            class="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium mt-2"
          >
            <UIcon name="i-lucide-gift" class="w-4 h-4 text-amber-400 shrink-0" />
            <span>Offer Active: {{ rawSub.description }}</span>
          </div>
        </div>

        <div class="flex items-center gap-3 shrink-0">
          <NuxtLink to="/marchant/billing">
            <UButton variant="outline" color="neutral" size="md" class="font-bold px-4 py-2.5">
              <UIcon name="i-lucide-credit-card" class="w-4 h-4 mr-1.5 text-emerald-400" />
              Manage Billing
            </UButton>
          </NuxtLink>

          <NuxtLink to="/">
            <UButton color="primary" size="md" class="font-bold px-5 py-2.5">
              <UIcon name="i-lucide-scan-barcode" class="w-4 h-4 mr-1.5" />
              Launch Active Register
            </UButton>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Organization Resource & Quota Health Widget -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Monthly Sales Quota -->
      <div class="p-5 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) flex flex-col justify-between gap-3 shadow-xs">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <UIcon name="i-lucide-shopping-cart" class="w-4 h-4" />
            </div>
            <span class="text-xs font-bold text-(--ui-text-highlighted)">Monthly Sales Quota</span>
          </div>
          <span class="text-xs font-mono font-bold text-(--ui-text-muted)">
            {{ usage.monthlySalesLimit > 0 ? `${usage.salesPercent}%` : 'Unlimited' }}
          </span>
        </div>

        <div>
          <div class="text-2xl font-black text-(--ui-text-highlighted) font-mono">
            {{ usage.monthlySalesCount.toLocaleString() }}
            <span class="text-xs font-normal text-(--ui-text-muted)">
              / {{ usage.monthlySalesLimit > 0 ? usage.monthlySalesLimit.toLocaleString() : '∞' }} sales
            </span>
          </div>
          <div class="w-full bg-zinc-800 rounded-full h-2 mt-2 overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="usage.salesPercent >= 90 ? 'bg-red-500' : usage.salesPercent >= 70 ? 'bg-amber-500' : 'bg-emerald-500'"
              :style="{ width: `${usage.monthlySalesLimit > 0 ? Math.min(usage.salesPercent, 100) : 100}%` }"
            />
          </div>
        </div>

        <div class="text-[11px] text-(--ui-text-muted) flex items-center justify-between">
          <span>Resets every 30 days</span>
          <NuxtLink to="/marchant/billing" class="text-emerald-400 hover:underline font-semibold">
            {{ usage.salesPercent >= 80 ? 'Upgrade Plan' : 'Plan Details' }}
          </NuxtLink>
        </div>
      </div>

      <!-- Product Catalog Capacity -->
      <div class="p-5 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) flex flex-col justify-between gap-3 shadow-xs">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <UIcon name="i-lucide-package" class="w-4 h-4" />
            </div>
            <span class="text-xs font-bold text-(--ui-text-highlighted)">Product Catalog</span>
          </div>
          <span class="text-xs font-mono font-bold text-(--ui-text-muted)">
            {{ usage.productsLimit > 0 ? `${usage.productsPercent}%` : 'Unlimited' }}
          </span>
        </div>

        <div>
          <div class="text-2xl font-black text-(--ui-text-highlighted) font-mono">
            {{ usage.productsCount.toLocaleString() }}
            <span class="text-xs font-normal text-(--ui-text-muted)">
              / {{ usage.productsLimit > 0 ? usage.productsLimit.toLocaleString() : '∞' }} products
            </span>
          </div>
          <div class="w-full bg-zinc-800 rounded-full h-2 mt-2 overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="usage.productsPercent >= 90 ? 'bg-red-500' : 'bg-blue-500'"
              :style="{ width: `${usage.productsLimit > 0 ? Math.min(usage.productsPercent, 100) : 100}%` }"
            />
          </div>
        </div>

        <div class="text-[11px] text-(--ui-text-muted) flex items-center justify-between">
          <span>Across all store branches</span>
          <NuxtLink to="/products" class="text-blue-400 hover:underline font-semibold">
            View Inventory
          </NuxtLink>
        </div>
      </div>

      <!-- Retail Store Branches Capacity -->
      <div class="p-5 rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) flex flex-col justify-between gap-3 shadow-xs">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <UIcon name="i-lucide-store" class="w-4 h-4" />
            </div>
            <span class="text-xs font-bold text-(--ui-text-highlighted)">Store Branches</span>
          </div>
          <span class="text-xs font-mono font-bold text-(--ui-text-muted)">
            {{ usage.storesLimit > 0 ? `${usage.storesPercent}%` : 'Unlimited' }}
          </span>
        </div>

        <div>
          <div class="text-2xl font-black text-(--ui-text-highlighted) font-mono">
            {{ usage.storesCount }}
            <span class="text-xs font-normal text-(--ui-text-muted)">
              / {{ usage.storesLimit > 0 ? usage.storesLimit : '∞' }} branches
            </span>
          </div>
          <div class="w-full bg-zinc-800 rounded-full h-2 mt-2 overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="isStoreLimitReached ? 'bg-red-500' : 'bg-purple-500'"
              :style="{ width: `${usage.storesLimit > 0 ? Math.min(usage.storesPercent, 100) : 100}%` }"
            />
          </div>
        </div>

        <div class="text-[11px] text-(--ui-text-muted) flex items-center justify-between">
          <span>{{ nextRenewalFormatted ? `Renews on ${nextRenewalFormatted}` : 'Active Plan' }}</span>
          <NuxtLink to="/marchant/billing" class="text-purple-400 hover:underline font-semibold">
            {{ isStoreLimitReached ? 'Upgrade Tier' : priceFormatted }}
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Store Branches Section -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-(--ui-text-highlighted)">Store Branches & Cashier Terminals</h2>
          <p class="text-xs text-(--ui-text-muted)">Select any outlet to launch register or manage staff members</p>
        </div>

        <NuxtLink v-if="!isStoreLimitReached" to="/marchant/stores">
          <UButton color="primary" size="xs" icon="i-lucide-plus" class="font-bold">
            Add Branch
          </UButton>
        </NuxtLink>
        <NuxtLink v-else to="/marchant/billing">
          <span class="text-xs text-amber-400 hover:underline font-semibold flex items-center gap-1">
            <UIcon name="i-lucide-alert-circle" class="w-3.5 h-3.5" />
            Branch limit reached (Upgrade)
          </span>
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
          class="rounded-3xl p-5 border border-(--ui-border) bg-(--ui-bg-elevated) hover:border-emerald-500/40 transition flex flex-col justify-between group shadow-xs"
        >
          <div>
            <div class="flex items-start justify-between gap-2 mb-3">
              <div class="w-10 h-10 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">
                <UIcon name="i-lucide-store" class="w-5 h-5" />
              </div>
              <span
                v-if="store.is_owner"
                class="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
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

            <h3 class="text-base font-bold text-(--ui-text-highlighted) group-hover:text-emerald-400 transition">
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
                Manage
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

        <!-- Inline Add Branch Card if under limit -->
        <NuxtLink
          v-if="!isStoreLimitReached"
          to="/marchant/stores"
          class="rounded-3xl p-6 border-2 border-dashed border-(--ui-border) hover:border-emerald-500/40 bg-(--ui-bg-elevated)/30 hover:bg-(--ui-bg-elevated) transition flex flex-col items-center justify-center text-center gap-2 group min-h-[160px]"
        >
          <div class="w-10 h-10 rounded-2xl bg-zinc-800 text-zinc-400 group-hover:text-emerald-400 group-hover:bg-emerald-500/10 flex items-center justify-center transition">
            <UIcon name="i-lucide-plus" class="w-5 h-5" />
          </div>
          <span class="text-sm font-bold text-(--ui-text-highlighted) group-hover:text-emerald-400 transition">
            Add New Branch
          </span>
          <span class="text-[11px] text-(--ui-text-muted)">
            {{ usage.storesCount }} of {{ usage.storesLimit > 0 ? usage.storesLimit : 'Unlimited' }} branches in use
          </span>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
