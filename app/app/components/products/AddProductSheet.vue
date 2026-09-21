<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { UNIT_OPTIONS } from './types'
import CameraScanner from './CameraScanner.vue'

const open = defineModel<boolean>({ default: false })
const emit = defineEmits<{
  (e: 'product-added'): void
}>()

const toast = useToast()
const { api } = useApi()
const productStore = useProductsStore()

const isScanning = ref(false)
const isLookingUpBarcode = ref(false)
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

const catalogMatchInfo = ref<{
  name: string
  source: 'catalog' | 'community'
  category?: string
  suggested_price?: number
} | null>(null)

let lookupDebounceTimer: ReturnType<typeof setTimeout> | null = null

function resetForm() {
  form.value = {
    name: '',
    price: 0,
    cost_price: 0,
    barcode_id: '',
    quantity: 0,
    unit: 'piece',
    description: ''
  }
  catalogMatchInfo.value = null
  isScanning.value = false
  isLookingUpBarcode.value = false
}

watch(open, (isOpen) => {
  if (isOpen) {
    resetForm()
  } else {
    isScanning.value = false
  }
})

onUnmounted(() => {
  if (lookupDebounceTimer) clearTimeout(lookupDebounceTimer)
})

async function lookupBarcode(barcode: string) {
  const clean = barcode.trim()
  if (!clean || clean.length < 3) {
    catalogMatchInfo.value = null
    return
  }

  isLookingUpBarcode.value = true
  try {
    const res = await api<any>(`/catalog-templates/lookup?barcode=${encodeURIComponent(clean)}`)
    if (res?.found) {
      form.value.name = res.name
      if (res.unit_in) form.value.unit = res.unit_in
      if (res.suggested_price && (!form.value.price || form.value.price === 0)) {
        form.value.price = res.suggested_price / 100
      }
      if (res.cost_price && (!form.value.cost_price || form.value.cost_price === 0)) {
        form.value.cost_price = res.cost_price / 100
      }
      if (res.description && !form.value.description) {
        form.value.description = res.description
      }
      catalogMatchInfo.value = {
        name: res.name,
        source: res.source,
        category: res.category,
        suggested_price: res.suggested_price
      }
    } else {
      catalogMatchInfo.value = null
    }
  } catch {
    catalogMatchInfo.value = null
  } finally {
    isLookingUpBarcode.value = false
  }
}

function handleBarcodeManualInput() {
  if (lookupDebounceTimer) clearTimeout(lookupDebounceTimer)
  lookupDebounceTimer = setTimeout(() => {
    const code = form.value.barcode_id?.trim()
    if (code && code.length >= 6) {
      lookupBarcode(code)
    } else {
      catalogMatchInfo.value = null
    }
  }, 450)
}

function onBarcodeScanned(code: string) {
  form.value.barcode_id = code
  isScanning.value = false
  toast.add({
    title: 'Barcode Scanned',
    description: `Captured: ${code}`,
    color: 'success',
    icon: 'i-lucide-check-circle'
  })
  lookupBarcode(code)
}

function clearAutoFill() {
  catalogMatchInfo.value = null
  form.value.name = ''
  form.value.price = 0
  form.value.cost_price = 0
  form.value.description = ''
  form.value.unit = 'piece'
}

async function handleSubmit() {
  if (!form.value.name.trim()) {
    toast.add({ title: 'Validation Error', description: 'Product name is required', color: 'error' })
    return
  }

  isSubmitting.value = true
  try {
    const payload = {
      name: form.value.name.trim(),
      barcode_id: form.value.barcode_id?.trim() || '',
      unit_price: Math.round(form.value.price * 100),
      cost_price: Math.round((form.value.cost_price || 0) * 100),
      quantities: Number(form.value.quantity) || 0,
      unit_in: form.value.unit,
      description: form.value.description?.trim() || ''
    }

    await productStore.addProduct(payload)
    toast.add({
      title: 'Product Added',
      description: form.value.name,
      color: 'success'
    })

    open.value = false
    emit('product-added')
  } catch (err: any) {
    toast.add({
      title: 'Failed to add product',
      description: err?.data?.detail || err?.message || 'Could not save product',
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AppBottomSheet
    v-model="open"
    title="Add New Product"
    description="Scan a barcode to auto-fill product details or enter them manually."
  >
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <!-- Barcode / SKU with Camera Button -->
      <UFormField label="Barcode / SKU">
        <div class="flex gap-1.5 w-full">
          <UInput
            v-model="form.barcode_id"
            placeholder="Scan or enter barcode (e.g. 6291109120360)..."
            class="flex-1"
            :loading="isLookingUpBarcode"
            @input="handleBarcodeManualInput"
          />
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

      <!-- Catalog Recognition Banner -->
      <div
        v-if="catalogMatchInfo"
        class="p-3 rounded-xl bg-primary-500/10 border border-primary-500/30 flex flex-col gap-2.5 text-xs animate-in fade-in slide-in-from-top-1"
      >
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2.5 min-w-0 flex-1">
            <div class="size-7 rounded-lg bg-primary-500/20 text-primary-500 flex items-center justify-center shrink-0">
              <UIcon name="i-lucide-sparkles" class="size-4" />
            </div>
            <div class="min-w-0 flex-1">
              <span class="font-bold text-(--ui-text-highlighted) truncate block">
                {{ catalogMatchInfo.name }}
              </span>
              <p class="text-[11px] text-(--ui-text-muted) truncate">
                Recognized from {{ catalogMatchInfo.source === 'catalog' ? 'Global Catalog' : 'Community' }}
                <span v-if="catalogMatchInfo.suggested_price" class="font-mono text-emerald-500 font-semibold ml-1">
                  · Suggested: ₦{{ (catalogMatchInfo.suggested_price / 100).toLocaleString() }}
                </span>
              </p>
            </div>
          </div>
          <UBadge color="primary" variant="subtle" size="xs" class="shrink-0">
            Auto-Filled
          </UBadge>
        </div>

        <div class="pt-2 border-t border-primary-500/20 flex items-center justify-between gap-2 text-[11px]">
          <span class="flex items-center gap-1 text-amber-500 dark:text-amber-400 font-medium">
            <UIcon name="i-lucide-info" class="size-3.5 shrink-0" />
            Please verify name, unit, and price match your physical item.
          </span>
          <button
            type="button"
            class="text-xs text-primary-500 hover:text-primary-600 dark:hover:text-primary-400 font-semibold underline shrink-0 cursor-pointer"
            @click="clearAutoFill"
          >
            Reset / Edit
          </button>
        </div>
      </div>

      <!-- Product Name -->
      <UFormField label="Product Name" required>
        <UInput
          v-model="form.name"
          placeholder="e.g. Golden Penny Spaghetti 500g"
        />
      </UFormField>

      <!-- Pricing: Selling Price & Cost Price -->
      <div class="grid grid-cols-2 gap-4">
        <UFormField label="Selling Price (₦)" required>
          <UInput
            v-model.number="form.price"
            type="number"
            step="any"
            placeholder="0.00"
          />
        </UFormField>
        <UFormField label="Cost Price (₦)">
          <UInput
            v-model.number="form.cost_price"
            type="number"
            step="any"
            placeholder="0.00"
          />
        </UFormField>
      </div>

      <!-- Inventory: Quantity & Unit -->
      <div class="grid grid-cols-2 gap-4">
        <UFormField label="Quantity on Hand">
          <UInput
            v-model.number="form.quantity"
            type="number"
            step="any"
            placeholder="0"
          />
        </UFormField>
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
        <UTextarea
          v-model="form.description"
          placeholder="Product size, flavor, packaging details..."
          :rows="3"
        />
      </UFormField>

      <!-- Action Buttons -->
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
          type="submit"
          :loading="isSubmitting"
        >
          Add Product
        </UButton>
      </div>
    </form>
  </AppBottomSheet>
</template>
