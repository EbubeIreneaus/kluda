<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { BrowserMultiFormatReader, BarcodeFormat, DecodeHintType } from '@zxing/library'

const { format } = useFormatCurrency()
const toast = useToast()

const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const auth = useAuthStore()
const { withPinAuth } = usePinAuth()

const productStore = useProductsStore()

const search = ref('')
const showAddModal = ref(false)
const showEditSlideover = ref(false)
const editingProduct = ref<any>(null)

const showAdjustModal = ref(false)
const showConfirmDialog = ref(false)
const isSubmittingAdjustment = ref(false)
const adjustingProduct = ref<any>(null)
const adjustForm = ref({
  action_type: 'addition' as 'addition' | 'subtract',
  reason: 'restock' as 'restock' | 'damage' | 'adjustment' | 'return',
  quantity: 1,
  note: ''
})

const showHistoryModal = ref(false)
const historyProduct = ref<any>(null)
const historyList = ref<any[]>([])
const isLoadingHistory = ref(false)

const newProduct = ref({
  name: '',
  price: 0,
  barcode_id: "",
  quantity: 0,
  unit: 'piece',
  description: ''
})

const units = ['piece', 'kg', 'g', 'litre', 'ml', 'pack', 'carton', 'dozen', 'bag']
const reasons = [
  { value: 'restock', label: 'Restock / New Shipment' },
  { value: 'return', label: 'Customer Return' },
  { value: 'damage', label: 'Damaged / Expired' },
  { value: 'adjustment', label: 'Stock Audit / Adjustment' }
]

const products = computed(() => {
  return productStore.products.map((p: any) => ({
    slug: p.slug,
    name: p.name,
    barcode_id: p.barcode_id || '',
    price: p.unit_price,
    quantity: p.quantities,
    unit: p.unit_in,
    status: p.deleted ? 'inactive' : 'active',
    description: p.description || ''
  }))
})

const filteredProducts = computed(() => {
  if (!search.value) return products.value
  const q = search.value.toLowerCase()
  return products.value.filter((p: any) =>
    p.name.toLowerCase().includes(q) ||
    p.barcode_id.toLowerCase().includes(q)
  )
})

const currentPage = ref(1)
const pageSize = ref(15)

const totalPages = computed(() => Math.max(1, Math.ceil(filteredProducts.value.length / pageSize.value)))

const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredProducts.value.slice(start, start + pageSize.value)
})

watch(search, () => {
  currentPage.value = 1
})

function getStockBadge(qty: number) {
  if (qty === 0) return { label: 'Out of stock', color: 'error' as const }
  if (qty <= 10) return { label: 'Low stock', color: 'warning' as const }
  return { label: 'In stock', color: 'success' as const }
}

function openEdit(product: any) {
  editingProduct.value = { ...product, price: product.price / 100 }
  showEditSlideover.value = true
}

function openAdjust(product: any) {
  adjustingProduct.value = product
  adjustForm.value = {
    action_type: 'addition',
    reason: 'restock',
    quantity: 1,
    note: ''
  }
  showConfirmDialog.value = false
  showAdjustModal.value = true
}

async function openHistory(product: any) {
  historyProduct.value = product
  showHistoryModal.value = true
  isLoadingHistory.value = true
  try {
    historyList.value = await productStore.fetchStockHistory(product.slug)
  } catch {
    historyList.value = []
  } finally {
    isLoadingHistory.value = false
  }
}

function proceedToConfirm() {
  if (adjustForm.value.quantity <= 0) {
    toast.add({ title: 'Invalid quantity', description: 'Quantity must be greater than zero', color: 'error' })
    return
  }
  showConfirmDialog.value = true
}

async function handleApplyAdjustment() {
  if (!adjustingProduct.value) return

  showConfirmDialog.value = false

  await withPinAuth(async () => {
    isSubmittingAdjustment.value = true
    try {
      await productStore.adjustStock({
        stock_slug: adjustingProduct.value.slug,
        quantity: Number(adjustForm.value.quantity),
        action_type: adjustForm.value.action_type,
        reason: adjustForm.value.reason,
        note: adjustForm.value.note || undefined
      })
      toast.add({
        title: 'Stock Updated',
        description: `${adjustingProduct.value.name} quantity successfully updated`,
        color: 'success'
      })
      showConfirmDialog.value = false
      showAdjustModal.value = false
    } catch (err: any) {
      toast.add({
        title: 'Adjustment Failed',
        description: err?.data?.detail || 'Could not update stock',
        color: 'error'
      })
    } finally {
      isSubmittingAdjustment.value = false
    }
  }, {
    title: 'Authorize Stock Adjustment',
    description: `Enter your PIN to confirm adjusting ${adjustingProduct.value.name} by ${adjustForm.value.quantity} ${adjustingProduct.value.unit || 'units'}.`,
    requiredPermission: 'manage:product'
  })
}

async function saveEdit() {
  if (!editingProduct.value) return

  await withPinAuth(async () => {
    try {
      const updateData = {
        name: editingProduct.value.name,
        barcode_id: editingProduct.value.barcode_id || '',
        unit_price: Math.round(editingProduct.value.price * 100),
        unit_in: editingProduct.value.unit,
        description: editingProduct.value.description || ''
      }
      await productStore.updateProduct(editingProduct.value.slug, updateData)
      toast.add({ title: 'Product updated', color: 'success' })
      showEditSlideover.value = false
    } catch (err) {
      toast.add({ title: 'Error', description: 'Could not update product', color: 'error' })
    }
  }, {
    title: 'Authorize Product Changes',
    description: `Enter PIN to confirm changes to ${editingProduct.value.name}`,
    requiredPermission: 'manage:product'
  })
}

async function handleAddProduct() {
  try {
    const addData = {
      name: newProduct.value.name,
      barcode_id: newProduct.value.barcode_id || '',
      unit_price: Math.round(newProduct.value.price * 100),
      quantities: newProduct.value.quantity,
      unit_in: newProduct.value.unit,
      description: newProduct.value.description || ''
    }
    await productStore.addProduct(addData)
    toast.add({ title: 'Product added', description: newProduct.value.name, color: 'success' })
    showAddModal.value = false
    newProduct.value = { name: '', price: 0, barcode_id: '', quantity: 0, unit: 'piece', description: '' }
  } catch (err) {
    toast.add({ title: 'Error', description: 'Could not add product', color: 'error' })
  }
}

async function confirmDelete(product: any) {
  await withPinAuth(async () => {
    try {
      await productStore.deleteProduct(product.slug)
      toast.add({ title: 'Product removed', description: product.name, color: 'warning' })
    } catch (err) {
      toast.add({ title: 'Error', description: 'Could not delete product', color: 'error' })
    }
  }, {
    title: 'Authorize Product Deletion',
    description: `Enter PIN to permanently delete ${product.name}`,
    requiredPermission: 'manage:product'
  })
}

const isCameraActive = ref(false)
const addVideoRef = ref<HTMLVideoElement | null>(null)
const editVideoRef = ref<HTMLVideoElement | null>(null)
const activeScanningField = ref<'add' | 'edit' | null>(null)
let codeReader: any = null

async function startCameraScanner(field: 'add' | 'edit') {
  if (isCameraActive.value) {
    stopCameraScanner()
  }
  activeScanningField.value = field
  isCameraActive.value = true
  
  try {
    await nextTick()
    await new Promise((resolve) => setTimeout(resolve, 200))
    let videoEl = field === 'add' ? addVideoRef.value : editVideoRef.value
    
    if (!videoEl) {
      await new Promise((resolve) => setTimeout(resolve, 300))
      videoEl = field === 'add' ? addVideoRef.value : editVideoRef.value
    }
    
    if (videoEl) {
      if (!codeReader) {
        const hints = new Map()
        const formats = [
          BarcodeFormat.EAN_13,
          BarcodeFormat.EAN_8,
          BarcodeFormat.CODE_128,
          BarcodeFormat.CODE_39,
          BarcodeFormat.UPC_A,
          BarcodeFormat.UPC_E
        ]
        hints.set(DecodeHintType.POSSIBLE_FORMATS, formats)
        codeReader = new BrowserMultiFormatReader(hints)
      }
      codeReader.decodeFromVideoDevice(undefined, videoEl, (result: any) => {
        if (result) {
          const code = result.getText()
          if (activeScanningField.value === 'add') {
            newProduct.value.barcode_id = code
          } else if (activeScanningField.value === 'edit' && editingProduct.value) {
            editingProduct.value.barcode_id = code
          }
          
          if (typeof navigator !== 'undefined' && navigator.vibrate) {
            navigator.vibrate(200)
          }
          
          toast.add({
            title: 'Barcode Scanned',
            description: `Captured: ${code}`,
            color: 'success',
            icon: 'i-lucide-check-circle'
          })
          stopCameraScanner()
        }
      })
    }
  } catch {
    toast.add({ title: 'Camera Error', description: 'Could not access camera', color: 'error' })
    isCameraActive.value = false
    activeScanningField.value = null
  }
}

function stopCameraScanner() {
  isCameraActive.value = false
  activeScanningField.value = null
  if (codeReader) {
    codeReader.reset()
  }
}

watch([showAddModal, showEditSlideover], () => {
  stopCameraScanner()
})
</script>

<template>
  <div class="space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Products & Inventory</h2>
        <p class="text-sm text-(--ui-text-muted)">{{ products.length }} products in stock</p>
      </div>
      <UButton v-if="auth.hasPermission('manage:product')" icon="i-lucide-plus" @click="showAddModal = true">
        Add Product
      </UButton>
    </div>

    <UInput
      v-model="search"
      placeholder="Search by name, barcode, or SKU..."
      icon="i-lucide-search"
      size="lg"
      class="max-w-md"
    />

    <!-- Desktop Table View (>= md) -->
    <div class="hidden md:block rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-(--ui-border) bg-(--ui-bg-accented)/30">
              <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Product</th>
              <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Barcode</th>
              <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Price</th>
              <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Quantity</th>
              <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Status</th>
              <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="product in paginatedProducts"
              :key="product.slug"
              class="border-b border-(--ui-border)/50 last:border-0 hover:bg-(--ui-bg-accented)/30 transition"
            >
              <td class="py-3 px-4">
                <div>
                  <p class="font-medium text-(--ui-text-highlighted)">{{ product.name }}</p>
                </div>
              </td>
              <td class="py-3 px-4 font-mono text-xs text-(--ui-text-muted)">{{ product.barcode_id || '—' }}</td>
              <td class="py-3 px-4 text-right font-semibold text-(--ui-text-highlighted)">{{ format(product.price) }}</td>
              <td class="py-3 px-4 text-center">
                <span class="font-medium text-(--ui-text-highlighted)">{{ product.quantity }}</span>
                <span class="text-(--ui-text-dimmed) text-xs ml-1">{{ product.unit }}</span>
              </td>
              <td class="py-3 px-4 text-center">
                <UBadge :color="getStockBadge(product.quantity).color" variant="subtle" size="xs">
                  {{ getStockBadge(product.quantity).label }}
                </UBadge>
              </td>
              <td class="py-3 px-4 text-right">
                <div v-if="auth.hasPermission('manage:product')" class="flex items-center justify-end gap-1">
                  <UButton variant="ghost" color="primary" size="xs" icon="i-lucide-boxes" title="Adjust Stock" @click="openAdjust(product)" />
                  <UButton variant="ghost" color="neutral" size="xs" icon="i-lucide-history" title="Stock History" @click="openHistory(product)" />
                  <UButton variant="ghost" color="neutral" size="xs" icon="i-lucide-pencil" title="Edit" @click="openEdit(product)" />
                  <UButton variant="ghost" color="error" size="xs" icon="i-lucide-trash-2" title="Delete" @click="confirmDelete(product)" />
                </div>
                <span v-else class="text-xs text-(--ui-text-dimmed)">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Mobile Card List View (< md) -->
    <div class="block md:hidden space-y-3">
      <div
        v-if="filteredProducts.length === 0"
        class="text-center py-12 px-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)"
      >
        <UIcon name="i-lucide-package-search" class="size-10 text-(--ui-text-dimmed) mx-auto mb-2" />
        <p class="text-sm font-semibold text-(--ui-text-highlighted)">No products found</p>
        <p class="text-xs text-(--ui-text-dimmed) mt-1">Try adjusting your search query or add a new product</p>
      </div>

      <div
        v-for="product in paginatedProducts"
        :key="product.slug"
        class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4 shadow-sm space-y-3"
      >
        <!-- Top: Name & Stock Badge -->
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <h3 class="font-bold text-sm text-(--ui-text-highlighted) leading-snug">
              {{ product.name }}
            </h3>
            <p v-if="product.barcode_id" class="text-xs font-mono text-(--ui-text-dimmed) mt-0.5 flex items-center gap-1">
              <UIcon name="i-lucide-scan-barcode" class="size-3.5" />
              {{ product.barcode_id }}
            </p>
          </div>
          <UBadge :color="getStockBadge(product.quantity).color" variant="subtle" size="sm" class="shrink-0 font-medium">
            {{ getStockBadge(product.quantity).label }}
          </UBadge>
        </div>

        <!-- Middle: Price & Available Quantity -->
        <div class="grid grid-cols-2 gap-2 py-2 px-3 rounded-xl bg-(--ui-bg-accented)/40 border border-(--ui-border)/50">
          <div>
            <span class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider block">Unit Price</span>
            <span class="text-base font-black text-(--ui-text-highlighted) font-mono">
              {{ format(product.price) }}
            </span>
          </div>
          <div class="text-right">
            <span class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider block">In Stock</span>
            <span class="text-sm font-bold text-(--ui-text-highlighted)">
              {{ product.quantity }} <span class="text-xs font-normal text-(--ui-text-dimmed)">{{ product.unit }}</span>
            </span>
          </div>
        </div>

        <!-- Bottom: Action Buttons for Mobile -->
        <div v-if="auth.hasPermission('manage:product')" class="grid grid-cols-4 gap-1.5 pt-1">
          <UButton
            variant="outline"
            color="primary"
            size="xs"
            icon="i-lucide-boxes"
            class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
            @click="openAdjust(product)"
          >
            Adjust
          </UButton>
          <UButton
            variant="outline"
            color="neutral"
            size="xs"
            icon="i-lucide-history"
            class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
            @click="openHistory(product)"
          >
            History
          </UButton>
          <UButton
            variant="outline"
            color="neutral"
            size="xs"
            icon="i-lucide-pencil"
            class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
            @click="openEdit(product)"
          >
            Edit
          </UButton>
          <UButton
            variant="outline"
            color="error"
            size="xs"
            icon="i-lucide-trash-2"
            class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
            @click="confirmDelete(product)"
          >
            Delete
          </UButton>
        </div>
      </div>
    </div>

    <!-- Pagination Controls -->
    <div
      v-if="filteredProducts.length > pageSize"
      class="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 text-xs text-(--ui-text-muted)"
    >
      <p>
        Showing
        <span class="font-bold text-(--ui-text-highlighted)">{{ (currentPage - 1) * pageSize + 1 }}</span>
        to
        <span class="font-bold text-(--ui-text-highlighted)">{{ Math.min(currentPage * pageSize, filteredProducts.length) }}</span>
        of
        <span class="font-bold text-(--ui-text-highlighted)">{{ filteredProducts.length }}</span>
        products
      </p>

      <div class="flex items-center gap-1.5">
        <UButton
          size="xs"
          variant="outline"
          color="neutral"
          icon="i-lucide-chevron-left"
          :disabled="currentPage <= 1"
          @click="currentPage--"
        >
          Previous
        </UButton>

        <span class="px-3 py-1 rounded-lg bg-(--ui-bg-elevated) border border-(--ui-border) font-bold text-(--ui-text-highlighted) font-mono">
          {{ currentPage }} / {{ totalPages }}
        </span>

        <UButton
          size="xs"
          variant="outline"
          color="neutral"
          trailing-icon="i-lucide-chevron-right"
          :disabled="currentPage >= totalPages"
          @click="currentPage++"
        >
          Next
        </UButton>
      </div>
    </div>

    <UModal v-model:open="showAddModal" title="Add New Product">
      <template #body>
        <form class="p-5 space-y-4" @submit.prevent="handleAddProduct">
          <UFormField label="Product Name" required>
            <UInput v-model="newProduct.name" placeholder="e.g. Golden Penny Spaghetti 500g" />
          </UFormField>
          <UFormField label="Price (₦)" required>
            <UInput v-model.number="newProduct.price" type="number" placeholder="0.00" />
          </UFormField>
          <div class="grid grid-cols-2 gap-4">
            <UFormField label="Unit">
              <USelect v-model="newProduct.unit" :items="units" />
            </UFormField>
            <UFormField label="Quantity">
              <UInput v-model.number="newProduct.quantity" type="number" placeholder="0" />
            </UFormField>
          </div>

          <div
            v-if="isCameraActive && activeScanningField === 'add'"
            class="relative overflow-hidden rounded-xl border border-(--ui-border) bg-black aspect-video max-h-48 flex items-center justify-center"
          >
            <video
              ref="addVideoRef"
              class="w-full h-full object-cover"
              autoplay
              playsinline
              muted
            />
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div class="w-3/4 h-1/2 border-2 border-dashed border-green-500 rounded-lg opacity-60 relative">
                <div class="absolute inset-x-0 h-0.5 bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]" style="top: 50%" />
              </div>
            </div>
          </div>
          <UFormField label="Barcode ID">
            <div class="flex gap-1.5 w-full">
              <UInput v-model="newProduct.barcode_id" placeholder="5901234123457" class="flex-1" />
              <UButton
                type="button"
                :color="isCameraActive && activeScanningField === 'add' ? 'error' : 'primary'"
                variant="solid"
                :icon="isCameraActive && activeScanningField === 'add' ? 'i-lucide-camera-off' : 'i-lucide-camera'"
                @click="isCameraActive && activeScanningField === 'add' ? stopCameraScanner() : startCameraScanner('add')"
              />
            </div>
          </UFormField>
          <UFormField label="Description">
            <UTextarea v-model="newProduct.description" placeholder="Product description..." :rows="2" />
          </UFormField>
          <div class="flex justify-end gap-2 pt-2">
            <UButton variant="outline" color="neutral" @click="showAddModal = false">Cancel</UButton>
            <UButton type="submit">Add Product</UButton>
          </div>
        </form>
      </template>
    </UModal>

    <USlideover v-model:open="showEditSlideover" title="Edit Product" side="right">
      <template #body>
        <form v-if="editingProduct" class="p-5 space-y-4" @submit.prevent="saveEdit">
          <UFormField label="Product Name">
            <UInput v-model="editingProduct.name" />
          </UFormField>
          <UFormField label="Price (₦)">
            <UInput v-model.number="editingProduct.price" type="number" />
          </UFormField>
          <UFormField label="Barcode ID">
            <div class="flex gap-1.5 w-full">
              <UInput v-model="editingProduct.barcode_id" class="flex-1" />
              <UButton
                type="button"
                :color="isCameraActive && activeScanningField === 'edit' ? 'error' : 'primary'"
                variant="solid"
                :icon="isCameraActive && activeScanningField === 'edit' ? 'i-lucide-camera-off' : 'i-lucide-camera'"
                @click="isCameraActive && activeScanningField === 'edit' ? stopCameraScanner() : startCameraScanner('edit')"
              />
            </div>
          </UFormField>

          <div
            v-if="isCameraActive && activeScanningField === 'edit'"
            class="relative overflow-hidden rounded-xl border border-(--ui-border) bg-black aspect-video max-h-48 flex items-center justify-center"
          >
            <video
              ref="editVideoRef"
              class="w-full h-full object-cover"
              autoplay
              playsinline
              muted
            />
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div class="w-3/4 h-1/2 border-2 border-dashed border-green-500 rounded-lg opacity-60 relative">
                <div class="absolute inset-x-0 h-0.5 bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]" style="top: 50%" />
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <UFormField label="Quantity (Locked)">
                <UInput :model-value="editingProduct.quantity" type="number" disabled class="opacity-60 cursor-not-allowed" />
              </UFormField>
              <p class="text-xs text-amber-500 font-medium">For quantity update use stock history</p>
            </div>
            <UFormField label="Unit">
              <USelect v-model="editingProduct.unit" :items="units" />
            </UFormField>
          </div>
          <UFormField label="Description">
            <UTextarea v-model="editingProduct.description" :rows="3" />
          </UFormField>
          <div class="flex justify-end gap-2 pt-4">
            <UButton variant="outline" color="neutral" @click="showEditSlideover = false">Cancel</UButton>
            <UButton type="submit">Save Changes</UButton>
          </div>
        </form>
      </template>
    </USlideover>

    <UModal v-model:open="showAdjustModal" title="Adjust Stock">
      <template #body>
        <div v-if="adjustingProduct" class="p-5 space-y-4">
          <div class="p-3.5 rounded-lg bg-(--ui-bg-accented)/50 border border-(--ui-border) flex items-center justify-between">
            <div>
              <p class="font-semibold text-(--ui-text-highlighted)">{{ adjustingProduct.name }}</p>
              <p class="text-xs text-(--ui-text-muted)">Current Stock: <span class="font-bold text-(--ui-text-highlighted)">{{ adjustingProduct.quantity }} {{ adjustingProduct.unit }}</span></p>
            </div>
            <UBadge :color="getStockBadge(adjustingProduct.quantity).color" variant="subtle" size="xs">
              {{ getStockBadge(adjustingProduct.quantity).label }}
            </UBadge>
          </div>

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

          <div class="grid grid-cols-2 gap-4">
            <UFormField label="Quantity to Adjust" required>
              <UInput v-model.number="adjustForm.quantity" type="number" min="0.01" step="any" placeholder="0" />
            </UFormField>
            <UFormField label="Reason" required>
              <USelect
                v-model="adjustForm.reason"
                :items="reasons"
                value-key="value"
                label-key="label"
              />
            </UFormField>
          </div>

          <UFormField label="Notes / Reference">
            <UInput v-model="adjustForm.note" placeholder="e.g. Invoice #4812, Damaged during offloading..." />
          </UFormField>

          <div class="flex justify-end gap-2 pt-2">
            <UButton variant="outline" color="neutral" @click="showAdjustModal = false">Cancel</UButton>
            <UButton :color="adjustForm.action_type === 'addition' ? 'primary' : 'error'" @click="proceedToConfirm">
              Review Adjustment
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <UModal v-model:open="showConfirmDialog" title="Confirm Stock Adjustment">
      <template #body>
        <div v-if="adjustingProduct" class="p-5 space-y-4">
          <div class="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-start gap-3">
            <UIcon name="i-lucide-alert-triangle" class="text-amber-500 size-6 shrink-0 mt-0.5" />
            <div class="space-y-1 text-sm">
              <p class="font-semibold text-(--ui-text-highlighted)">
                {{ adjustingProduct.name }} will be
                <span :class="adjustForm.action_type === 'addition' ? 'text-emerald-500 font-bold' : 'text-red-500 font-bold'">
                  {{ adjustForm.action_type === 'addition' ? 'incremented' : 'decremented' }}
                </span>
                by {{ adjustForm.quantity }} {{ adjustingProduct.unit }}.
              </p>
              <p class="text-xs text-(--ui-text-muted)">
                New expected quantity:
                <span class="font-bold text-(--ui-text-highlighted)">
                  {{ adjustForm.action_type === 'addition' ? Number(adjustingProduct.quantity) + Number(adjustForm.quantity) : Math.max(0, Number(adjustingProduct.quantity) - Number(adjustForm.quantity)) }} {{ adjustingProduct.unit }}
                </span>
              </p>
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <UButton variant="outline" color="neutral" :disabled="isSubmittingAdjustment" @click="showConfirmDialog = false">Back</UButton>
            <UButton
              :color="adjustForm.action_type === 'addition' ? 'primary' : 'error'"
              :loading="isSubmittingAdjustment"
              @click="handleApplyAdjustment"
            >
              Confirm & Apply
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <UModal v-model:open="showHistoryModal" :title="`Stock History - ${historyProduct?.name || ''}`">
      <template #body>
        <div class="p-5 space-y-4 max-h-[65vh] overflow-y-auto">
          <div v-if="isLoadingHistory" class="py-10 text-center text-sm text-(--ui-text-muted)">
            Loading history...
          </div>
          <div v-else-if="historyList.length === 0" class="py-10 text-center text-sm text-(--ui-text-muted)">
            No stock adjustments recorded yet for this product.
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="item in historyList"
              :key="item.sid"
              class="p-3 rounded-lg border border-(--ui-border) bg-(--ui-bg-accented)/30 flex items-center justify-between"
            >
              <div>
                <div class="flex items-center gap-2">
                  <UBadge :color="item.action_type === 'addition' ? 'success' : 'error'" variant="subtle" size="xs">
                    {{ item.action_type === 'addition' ? '+' : '-' }}{{ item.quantity }}
                  </UBadge>
                  <span class="text-xs font-semibold uppercase tracking-wider text-(--ui-text-highlighted)">{{ item.reason }}</span>
                </div>
                <p v-if="item.note" class="text-xs text-(--ui-text-muted) mt-1">{{ item.note }}</p>
              </div>
              <div class="text-right text-xs text-(--ui-text-dimmed)">
                <p>{{ new Date(item.created_at).toLocaleDateString() }}</p>
                <p>{{ new Date(item.created_at).toLocaleTimeString() }}</p>
              </div>
            </div>
          </div>
          <div class="flex justify-end pt-2">
            <UButton variant="outline" color="neutral" @click="showHistoryModal = false">Close</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
