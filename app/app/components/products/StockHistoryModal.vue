<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ProductItem } from './types'

const open = defineModel<boolean>({ default: false })
const props = defineProps<{
  product: ProductItem | null
}>()

const productStore = useProductsStore()

const historyList = ref<any[]>([])
const isLoading = ref(false)

async function loadHistory() {
  if (!props.product?.slug) return
  isLoading.value = true
  try {
    historyList.value = await productStore.fetchStockHistory(props.product.slug)
  } catch {
    historyList.value = []
  } finally {
    isLoading.value = false
  }
}

watch([open, () => props.product], ([isOpen, prod]) => {
  if (isOpen && prod) {
    loadHistory()
  } else if (!isOpen) {
    historyList.value = []
  }
})
</script>

<template>
  <AppFullScreenModal
    v-model="open"
    :title="`Stock History - ${product?.name || ''}`"
    description="Audit log of all stock increases and decreases for this product."
  >
    <div class="space-y-4">
      <!-- Loading State -->
      <div
        v-if="isLoading"
        class="py-10 text-center text-sm text-(--ui-text-muted)"
      >
        Loading history...
      </div>

      <!-- Empty State -->
      <div
        v-else-if="historyList.length === 0"
        class="py-10 text-center text-sm text-(--ui-text-muted)"
      >
        No stock adjustments recorded yet for this product.
      </div>

      <!-- History List -->
      <div v-else class="space-y-2">
        <div
          v-for="item in historyList"
          :key="item.sid"
          class="p-3 rounded-lg border border-(--ui-border) bg-(--ui-bg-accented)/30 flex items-center justify-between"
        >
          <div>
            <div class="flex items-center gap-2">
              <UBadge
                :color="item.action_type === 'addition' ? 'success' : 'error'"
                variant="subtle"
                size="xs"
              >
                {{ item.action_type === 'addition' ? '+' : '-' }}{{ item.quantity }}
              </UBadge>
              <span class="text-xs font-semibold uppercase tracking-wider text-(--ui-text-highlighted)">
                {{ item.reason }}
              </span>
            </div>
            <p v-if="item.note" class="text-xs text-(--ui-text-muted) mt-1">
              {{ item.note }}
            </p>
          </div>
          <div class="text-right text-xs text-(--ui-text-dimmed)">
            <p>{{ new Date(item.created_at).toLocaleDateString() }}</p>
            <p>{{ new Date(item.created_at).toLocaleTimeString() }}</p>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <UButton
          variant="outline"
          color="neutral"
          @click="open = false"
        >
          Close
        </UButton>
      </div>
    </template>
  </AppFullScreenModal>
</template>
