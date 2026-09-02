<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useSubscription } from '~/composables/useSubscription'

const {
  plan,
  status,
  isDue,
  isExpired,
  ownerName,
  usage,
  priceFormatted,
  nextRenewalFormatted,
  daysRemaining,
  isOwner,
  fetchCurrentSubscription
} = useSubscription()

onMounted(() => {
  fetchCurrentSubscription()
})

const statusColor = computed(() => {
  if (status.value === 'ACTIVE') return 'success'
  if (status.value === 'DUE') return 'warning'
  return 'error'
})

const salesProgressColor = computed(() => {
  if (usage.value.salesPercent >= 90) return 'bg-rose-500'
  if (usage.value.salesPercent >= 75) return 'bg-amber-500'
  return 'bg-emerald-500'
})

const productsProgressColor = computed(() => {
  if (usage.value.productsPercent >= 90) return 'bg-rose-500'
  if (usage.value.productsPercent >= 75) return 'bg-amber-500'
  return 'bg-blue-500'
})
</script>

<template>
  <div class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5 shadow-xs transition-all space-y-4">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 border border-amber-500/20 shrink-0">
          <UIcon name="i-lucide-crown" class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-bold text-(--ui-text-highlighted)">Store Plan & Quotas</h3>
            <UBadge
              :color="statusColor"
              variant="subtle"
              size="xs"
              class="font-bold tracking-wide uppercase"
            >
              {{ status === 'ACTIVE' ? 'Active Plan' : (status === 'DUE' ? 'Payment Due' : 'Expired') }}
            </UBadge>
          </div>
          <p class="text-xs text-(--ui-text-muted) mt-0.5">
            Tied to store owner <span class="font-medium text-(--ui-text-highlighted)">{{ ownerName }}</span>. Quotas are combined across all branches.
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2 self-start sm:self-auto">
        <NuxtLink v-if="isOwner" to="/marchant/billing">
          <UButton
            size="xs"
            color="primary"
            variant="soft"
            trailing-icon="i-lucide-arrow-up-right"
            class="font-semibold"
          >
            Manage Billing
          </UButton>
        </NuxtLink>
        <span v-else class="text-[11px] font-mono text-(--ui-text-dimmed)">
          Staff View
        </span>
      </div>
    </div>

    <!-- Plan Summary Row -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-xl bg-(--ui-bg-accented)/40 border border-(--ui-border)">
      <div>
        <span class="text-[11px] text-(--ui-text-dimmed) uppercase tracking-wider font-semibold">Active Tier</span>
        <div class="text-base font-extrabold text-(--ui-text-highlighted) mt-0.5 flex items-center gap-1.5">
          <span>{{ plan.name }}</span>
          <span class="text-xs font-semibold text-emerald-500 font-mono">({{ priceFormatted }})</span>
        </div>
      </div>

      <div>
        <span class="text-[11px] text-(--ui-text-dimmed) uppercase tracking-wider font-semibold">Renewal Schedule</span>
        <div class="text-xs font-bold text-(--ui-text-highlighted) mt-1">
          {{ nextRenewalFormatted }}
          <span class="text-[11px] text-(--ui-text-muted) font-normal">({{ daysRemaining }}d left)</span>
        </div>
      </div>

      <div>
        <span class="text-[11px] text-(--ui-text-dimmed) uppercase tracking-wider font-semibold">Multi-Store Scope</span>
        <div class="text-xs font-bold text-(--ui-text-highlighted) mt-1 flex items-center gap-1">
          <UIcon name="i-lucide-git-branch" class="w-3.5 h-3.5 text-emerald-400" />
          <span>{{ usage.storesCount }} of {{ usage.storesLimit || 'Unlimited' }} Branches</span>
        </div>
      </div>
    </div>

    <!-- Quotas Progress Bars -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
      <!-- Combined Monthly Sales -->
      <div class="space-y-1.5 p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg)/50">
        <div class="flex items-center justify-between text-xs">
          <span class="font-medium text-(--ui-text-highlighted) flex items-center gap-1.5">
            <UIcon name="i-lucide-receipt" class="w-3.5 h-3.5 text-emerald-500" />
            Monthly Sales (Combined All Outlets)
          </span>
          <span class="font-bold font-mono text-(--ui-text-highlighted)">
            {{ usage.monthlySalesCount }} / {{ usage.monthlySalesLimit > 0 ? usage.monthlySalesLimit : '∞' }}
            <span class="text-(--ui-text-dimmed) text-[11px] font-normal">({{ usage.salesPercent }}%)</span>
          </span>
        </div>

        <div class="h-2 w-full bg-zinc-800/80 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :style="{ width: `${usage.salesPercent}%` }"
            :class="salesProgressColor"
          />
        </div>
        <p class="text-[10px] text-(--ui-text-dimmed)">
          Combined sales volume across all stores owned by {{ ownerName }}.
        </p>
      </div>

      <!-- Product Catalog Limit -->
      <div class="space-y-1.5 p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg)/50">
        <div class="flex items-center justify-between text-xs">
          <span class="font-medium text-(--ui-text-highlighted) flex items-center gap-1.5">
            <UIcon name="i-lucide-package" class="w-3.5 h-3.5 text-blue-500" />
            Product Catalog Capacity
          </span>
          <span class="font-bold font-mono text-(--ui-text-highlighted)">
            {{ usage.productsCount }} / {{ usage.productsLimit > 0 ? usage.productsLimit : '∞' }}
            <span class="text-(--ui-text-dimmed) text-[11px] font-normal">({{ usage.productsPercent }}%)</span>
          </span>
        </div>

        <div class="h-2 w-full bg-zinc-800/80 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :style="{ width: `${usage.productsPercent}%` }"
            :class="productsProgressColor"
          />
        </div>
        <p class="text-[10px] text-(--ui-text-dimmed)">
          Global inventory items managed across your organization.
        </p>
      </div>
    </div>

    <!-- Warning alert if near limit or overdue -->
    <div
      v-if="isDue || isExpired || usage.isNearSalesLimit"
      class="p-3 rounded-xl flex items-center justify-between gap-3 text-xs"
      :class="[
        isExpired || isDue
          ? 'bg-rose-500/10 border border-rose-500/20 text-rose-300'
          : 'bg-amber-500/10 border border-amber-500/20 text-amber-300'
      ]"
    >
      <div class="flex items-center gap-2">
        <UIcon
          :name="isExpired || isDue ? 'i-lucide-alert-octagon' : 'i-lucide-alert-triangle'"
          class="w-4 h-4 shrink-0"
        />
        <span v-if="isDue">
          Subscription payment failed. Update card to maintain uninterrupted POS operations.
        </span>
        <span v-else-if="isExpired">
          Your organization subscription has expired. Renew now to unlock full limits.
        </span>
        <span v-else>
          You have reached {{ usage.salesPercent }}% of your monthly sales quota. Consider upgrading your plan.
        </span>
      </div>

      <NuxtLink v-if="isOwner" to="/marchant/billing" class="shrink-0">
        <UButton
          size="xs"
          :color="isExpired || isDue ? 'error' : 'warning'"
          class="font-bold"
        >
          Upgrade Now
        </UButton>
      </NuxtLink>
    </div>
  </div>
</template>
