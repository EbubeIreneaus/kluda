<script setup lang="ts">
import { ref, watch } from 'vue'
import { UNIT_OPTIONS, type ProductItem } from './types'
import CameraScanner from './CameraScanner.vue'

const open = defineModel<boolean>({ default: false })
const props = defineProps<{
  product: ProductItem | null
}>()

const emit = defineEmits<{
  (e: 'product-updated'): void
}>()

const toast = useToast()
const productStore = useProductsStore()
const { withPinAuth } = usePinAuth()

const isScanning = ref(false)
const isSubmitting = ref(false)

const form = ref({
  name: '',
  price: 0,
  cost_price: 0,
  barcode_id: '',
  quantity: 0,
  unit: 'piece',
  description: ''
})

watch(
  () => props.product,
  (p) => {
    if (p) {
      form.value = {
        name: p.name || '',
        price: p.price ? p.price / 100 : 0,
        cost_price: p.cost_price ? p.cost_price / 100 : 0,
        barcode_id: p.barcode_id || '',
        quantity: p.quantity || 0,
        unit: p.unit || 'piece',
        description: p.description || ''
      }
    }
  },
  { immediate: true }
)

watch(open, (isOpen) => {
  if (!isOpen) {
    isScanning.value = false
  }
})

function onBarcodeScanned(code: string) {
  form.value.barcode_id = code
  isScanning.value = false
  toast.add({
    title: 'Barcode Scanned',
    description: `Captured: ${code}`,
    color: 'success',
    icon: 'i-lucide-check-circle'
  })
}

async function handleSave() {
  if (!props.product) return

  await withPinAuth(
    async () => {
      isSubmitting.value = true
      try {
        const updateData = {
          name: form.value.name.trim(),
          barcode_id: form.value.barcode_id?.trim() || '',
          unit_price: Math.round(form.value.price * 100),
          cost_price: Math.round((form.value.cost_price || 0) * 100),
          unit_in: form.value.unit,
          description: form.value.description?.trim() || ''
        }

        await productStore.updateProduct(props.product!.slug, updateData)
        toast.add({ title: 'Product updated', color: 'success' })
        open.value = false
        emit('product-updated')
      } catch (err: any) {
        toast.add({
          title: 'Error',
          description: err?.data?.detail || 'Could not update product',
          color: 'error'
        })
      } finally {
        isSubmitting.value = false
      }
    },
    {
      title: 'Authorize Product Changes',
      description: `Enter PIN to confirm changes to ${props.product.name}`,
      requiredPermission: 'manage:product'
    }
  )
}
</script>

<template>
  <AppBottomSheet
    v-model="open"
    title="Edit Product"
    description="Update pricing, barcode, or details for this item."
  >
    <form v-if="product" class="space-y-4" @submit.prevent="handleSave">
      <!-- Product Name -->
      <UFormField label="Product Name" required>
        <UInput v-model="form.name" />
      </UFormField>

      <!-- Pricing: Selling Price & Cost Price -->
      <div class="grid grid-cols-2 gap-4">
        <UFormField label="Selling Price (₦)" required>
          <UInput
            v-model.number="form.price"
            type="number"
            step="any"
          />
        </UFormField>
        <UFormField label="Cost Price (₦)">
          <UInput
            v-model.number="form.cost_price"
            type="number"
            step="any"
          />
        </UFormField>
      </div>

      <!-- Barcode with Camera Scanner -->
      <UFormField label="Barcode ID">
        <div class="flex gap-1.5 w-full">
          <UInput v-model="form.barcode_id" class="flex-1" />
          <UButton
            type="button"
            :color="isScanning ? 'error' : 'primary'"
            variant="solid"
            :icon="isScanning ? 'i-lucide-camera-off' : 'i-lucide-camera'"
            :title="isScanning ? 'Stop Camera' : 'Scan with Camera'"
            @click="isScanning = !isScanning"
          />
        </div>
      </UFormField>

      <!-- Live Camera Scanner -->
      <CameraScanner
        v-if="isScanning"
        @scanned="onBarcodeScanned"
        @close="isScanning = false"
      />

      <!-- Inventory: Quantity (Locked) & Unit -->
      <div class="grid grid-cols-2 gap-4">
        <div class="space-y-1">
          <UFormField label="Quantity (Locked)">
            <UInput
              :model-value="form.quantity"
              type="number"
              disabled
              class="opacity-60 cursor-not-allowed"
            />
          </UFormField>
          <p class="text-xs text-amber-500 font-medium">
            For quantity update use stock adjustment
          </p>
        </div>
        <UFormField label="Unit">
          <div class="relative w-full">
            <select
              v-model="form.unit"
              class="w-full h-10 px-3 py-2 text-sm rounded-md bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-highlighted) focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none pr-8 cursor-pointer font-medium"
            >
              <option
                v-if="form.unit && !UNIT_OPTIONS.some((u) => u.value === form.unit)"
                :value="form.unit"
              >
                {{ form.unit }}
              </option>
              <option
                v-for="u in UNIT_OPTIONS"
                :key="u.value"
                :value="u.value"
              >
                {{ u.label }}
              </option>
            </select>
            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-(--ui-text-dimmed)">
              <UIcon name="i-lucide-chevron-down" class="size-4" />
            </div>
          </div>
        </UFormField>
      </div>

      <!-- Description -->
      <UFormField label="Description (Optional)">
        <UTextarea v-model="form.description" :rows="3" />
      </UFormField>

      <!-- Action Buttons -->
      <div class="flex justify-end gap-2 pt-4">
        <UButton
          variant="outline"
          color="neutral"
          type="button"
          @click="open = false"
        >
          Cancel
        </UButton>
        <UButton type="submit" :loading="isSubmitting">
          Save Changes
        </UButton>
      </div>
    </form>
  </AppBottomSheet>
</template>
