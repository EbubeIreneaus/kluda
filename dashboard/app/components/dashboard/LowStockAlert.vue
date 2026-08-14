<script setup lang="ts">
import { computed } from 'vue'

const productStore = useProductsStore()

const alerts = computed(() => {
  return productStore.lowStockProducts.map(p => ({
    name: p.name,
    quantity: p.quantities,
    barcode: p.barcode_id || 'N/A'
  }))
})
</script>

<template>
  <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/15">
          <UIcon name="i-lucide-triangle-alert" class="w-4 h-4 text-amber-500" />
        </div>
        <div>
          <h3 class="text-sm font-medium text-(--ui-text-muted)">Low Stock Alerts</h3>
          <p class="text-xs text-(--ui-text-dimmed)">
            {{ alerts.length === 0 ? 'All products well stocked' : `${alerts.length} products need restocking` }}
          </p>
        </div>
      </div>
    </div>
    
    <div v-if="alerts.length > 0" class="space-y-3">
      <div
        v-for="item in alerts"
        :key="item.barcode"
        class="flex items-center justify-between p-3 rounded-lg bg-(--ui-bg-accented)/50"
      >
        <div>
          <p class="text-sm font-medium text-(--ui-text-highlighted)">{{ item.name }}</p>
          <p class="text-xs text-(--ui-text-dimmed) mt-0.5 font-mono">{{ item.barcode }}</p>
        </div>
        <div class="text-right">
          <UBadge
            :color="item.quantity <= 3 ? 'error' : 'warning'"
            variant="subtle"
            size="xs"
          >
            {{ item.quantity }} left
          </UBadge>
        </div>
      </div>
    </div>

    <div v-else class="py-6 text-center">
      <UIcon name="i-lucide-check-circle-2" class="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
      <p class="text-xs font-medium text-(--ui-text-muted)">No low stock alerts</p>
      <p class="text-[11px] text-(--ui-text-dimmed) mt-0.5">Inventory levels look good!</p>
    </div>
  </div>
</template>
