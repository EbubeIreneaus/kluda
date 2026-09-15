<script setup lang="ts">
defineProps<{
  products: any[]
}>()

const emit = defineEmits<{
  (e: 'add', product: any): void
}>()

const { format } = useFormatCurrency()
</script>

<template>
  <div class="hidden xl:block flex-1 overflow-y-auto min-h-0">
    <p class="text-xs font-medium text-(--ui-text-dimmed) uppercase tracking-wider mb-3">
      Quick Add
    </p>
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
      <button
        v-for="product in products"
        :key="product.slug"
        type="button"
        class="card-hover flex flex-col items-start p-3.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) text-left transition-all hover:border-green-500/30 cursor-pointer"
        @click="emit('add', product)"
      >
        <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-green-500/10 mb-2.5">
          <UIcon
            name="i-lucide-package"
            class="w-5 h-5 text-green-600 dark:text-green-400"
          />
        </div>
        <p class="text-sm font-medium text-(--ui-text-highlighted) leading-tight line-clamp-2">
          {{ product.name }}
        </p>
        <p class="text-xs font-mono text-(--ui-text-dimmed) mt-1">
          {{ product.barcode_id }}
        </p>
        <p class="text-sm font-semibold text-green-600 dark:text-green-400 mt-auto pt-2">
          {{ format(product.unit_price) }}
        </p>
      </button>
    </div>
  </div>
</template>
