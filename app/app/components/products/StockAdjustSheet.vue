<script setup lang="ts">
import { ref, watch } from 'vue'
import { REASON_OPTIONS, getStockBadge, type ProductItem } from './types'

const open = defineModel<boolean>({ default: false })
const props = defineProps<{
  product: ProductItem | null
}>()

const emit = defineEmits<{
  (e: 'stock-adjusted'): void
}>()

const toast = useToast()
const productStore = useProductsStore()
const { withPinAuth } = usePinAuth()

const showConfirmDialog = ref(false)
const isSubmitting = ref(false)

const adjustForm = ref({
  action_type: 'addition' as 'addition' | 'subtract',
  reason: 'restock' as 'restock' | 'damage' | 'adjustment' | 'return',
  quantity: 1,
  note: ''
})

watch(open, (isOpen) => {
  if (isOpen) {
    adjustForm.value = {
      action_type: 'addition',
      reason: 'restock',
      quantity: 1,
      note: ''
    }
    showConfirmDialog.value = false
  }
})

function proceedToConfirm() {
  if (!adjustForm.value.quantity || adjustForm.value.quantity <= 0) {
    toast.add({
      title: 'Invalid quantity',
      description: 'Quantity must be greater than zero',
      color: 'error'
    })
    return
  }
  showConfirmDialog.value = true
}

async function handleApplyAdjustment() {
  if (!props.product) return

  showConfirmDialog.value = false

  await withPinAuth(
    async () => {
      isSubmitting.value = true
      try {
        await productStore.adjustStock({
          stock_slug: props.product!.slug,
          quantity: Number(adjustForm.value.quantity),
          action_type: adjustForm.value.action_type,
          reason: adjustForm.value.reason,
          note: adjustForm.value.note || undefined
        })

        toast.add({
          title: 'Stock Updated',
          description: `${props.product!.name} quantity successfully updated`,
          color: 'success'
        })

        open.value = false
        emit('stock-adjusted')
      } catch (err: any) {
        toast.add({
          title: 'Adjustment Failed',
          description: err?.data?.detail || 'Could not update stock',
          color: 'error'
        })
      } finally {
        isSubmitting.value = false
      }
    },
    {
      title: 'Authorize Stock Adjustment',
      description: `Enter your PIN to confirm adjusting ${props.product.name} by ${adjustForm.value.quantity} ${props.product.unit || 'units'}.`,
      requiredPermission: 'manage:product'
    }
  )
}
</script>

<template>
  <div>
    <!-- Main Adjust Bottom Sheet -->
    <AppBottomSheet
      v-model="open"
      title="Adjust Stock"
      description="Add or deduct inventory quantity for this product."
    >
      <div v-if="product" class="space-y-4">
        <!-- Product Header Card -->
        <div class="p-3.5 rounded-lg bg-(--ui-bg-accented)/50 border border-(--ui-border) flex items-center justify-between">
          <div>
            <p class="font-semibold text-(--ui-text-highlighted)">
              {{ product.name }}
            </p>
            <p class="text-xs text-(--ui-text-muted)">
              Current Stock:
              <span class="font-bold text-(--ui-text-highlighted)">
                {{ product.quantity }} {{ product.unit }}
              </span>
            </p>
          </div>
          <UBadge
            :color="getStockBadge(product.quantity).color"
            variant="subtle"
            size="xs"
          >
            {{ getStockBadge(product.quantity).label }}
          </UBadge>
        </div>

        <!-- Action Type Buttons -->
        <div class="grid grid-cols-2 gap-3">
          <UButton
            type="button"
            :variant="adjustForm.action_type === 'addition' ? 'solid' : 'outline'"
            :color="adjustForm.action_type === 'addition' ? 'primary' : 'neutral'"
            icon="i-lucide-plus"
            class="justify-center"
            @click="adjustForm.action_type = 'addition'; adjustForm.reason = 'restock'"
          >
            Add Stock
          </UButton>
          <UButton
            type="button"
            :variant="adjustForm.action_type === 'subtract' ? 'solid' : 'outline'"
            :color="adjustForm.action_type === 'subtract' ? 'error' : 'neutral'"
            icon="i-lucide-minus"
            class="justify-center"
            @click="adjustForm.action_type = 'subtract'; adjustForm.reason = 'damage'"
          >
            Deduct Stock
          </UButton>
        </div>

        <!-- Quantity and Reason -->
        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Quantity to Adjust" required>
            <UInput
              v-model.number="adjustForm.quantity"
              type="number"
              min="0.01"
              step="any"
              placeholder="0"
            />
          </UFormField>
          <UFormField label="Reason" required>
            <div class="relative w-full">
              <select
                v-model="adjustForm.reason"
                class="w-full h-10 px-3 py-2 text-sm rounded-md bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-highlighted) focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none pr-8 cursor-pointer font-medium"
              >
                <option v-for="r in REASON_OPTIONS" :key="r.value" :value="r.value">
                  {{ r.label }}
                </option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-(--ui-text-dimmed)">
                <UIcon name="i-lucide-chevron-down" class="size-4" />
              </div>
            </div>
          </UFormField>
        </div>

        <!-- Note -->
        <UFormField label="Notes / Reference">
          <UInput
            v-model="adjustForm.note"
            placeholder="e.g. Invoice #4812, Damaged during offloading..."
          />
        </UFormField>

        <!-- Actions -->
        <div class="flex justify-end gap-2 pt-2">
          <UButton
            variant="outline"
            color="neutral"
            type="button"
            @click="open = false"
          >
            Cancel
          </UButton>
          <UButton
            :color="adjustForm.action_type === 'addition' ? 'primary' : 'error'"
            @click="proceedToConfirm"
          >
            Review Adjustment
          </UButton>
        </div>
      </div>
    </AppBottomSheet>

    <!-- Confirmation Modal -->
    <UModal v-model:open="showConfirmDialog" title="Confirm Stock Adjustment" class="z-9999">
      <template #body>
        <div v-if="product" class="p-5 space-y-4 ">
          <div class="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-start gap-3">
            <UIcon
              name="i-lucide-alert-triangle"
              class="text-amber-500 size-6 shrink-0 mt-0.5"
            />
            <div class="space-y-1 text-sm">
              <p class="font-semibold text-(--ui-text-highlighted)">
                {{ product.name }} will be
                <span
                  :class="adjustForm.action_type === 'addition' ? 'text-emerald-500 font-bold' : 'text-red-500 font-bold'"
                >
                  {{ adjustForm.action_type === 'addition' ? 'incremented' : 'decremented' }}
                </span>
                by {{ adjustForm.quantity }} {{ product.unit }}.
              </p>
              <p class="text-xs text-(--ui-text-muted)">
                New expected quantity:
                <span class="font-bold text-(--ui-text-highlighted)">
                  {{
                    adjustForm.action_type === 'addition'
                      ? Number(product.quantity) + Number(adjustForm.quantity)
                      : Math.max(0, Number(product.quantity) - Number(adjustForm.quantity))
                  }}
                  {{ product.unit }}
                </span>
              </p>
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <UButton
              variant="outline"
              color="neutral"
              :disabled="isSubmitting"
              @click="showConfirmDialog = false"
            >
              Back
            </UButton>
            <UButton
              :color="adjustForm.action_type === 'addition' ? 'primary' : 'error'"
              :loading="isSubmitting"
              @click="handleApplyAdjustment"
            >
              Confirm & Apply
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
