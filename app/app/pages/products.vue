<script setup lang="ts">
import { ref, computed, nextTick, watch, onUnmounted } from 'vue'

const { format } = useFormatCurrency()
const toast = useToast()

const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const auth = useAuthStore()
const { withPinAuth } = usePinAuth()
const { api } = useApi()

const productStore = useProductsStore()

// Starter Pack Catalog State
const showImportSheet = ref(false)
const catalogTemplates = ref<any[]>([])
const isLoadingTemplates = ref(false)
const importingSlug = ref<string | null>(null)
const confirmingTemplate = ref<any | null>(null)

function getTemplateIcon(icon?: string | null): string {
  if (!icon || typeof icon !== 'string') return 'i-lucide-package'
  const clean = icon.trim().toLowerCase()
  if (!clean) return 'i-lucide-package'
  if (clean.startsWith('i-')) return clean
  return `i-lucide-${clean}`
}

async function openImportModal() {
  showImportSheet.value = true
  if (catalogTemplates.value.length === 0) {
    isLoadingTemplates.value = true
    try {
      const res = await api<any[]>('/catalog-templates')
      catalogTemplates.value = Array.isArray(res) ? res : []
    } catch (err: any) {
      toast.add({
        title: 'Error loading catalogs',
        description: err?.data?.detail || 'Could not fetch starter packs',
        color: 'error'
      })
    } finally {
      isLoadingTemplates.value = false
    }
  }
}

async function handleImportCatalog(template: any) {
  const storeId = auth.store_id || auth.staff?.store_id
  if (!storeId) {
    toast.add({ title: 'Error', description: 'Store ID not found', color: 'error' })
    return
  }

  importingSlug.value = template.slug
  try {
    const res = await api<any>(`/catalog-templates/${template.slug}/import?store_id=${storeId}`, {
      method: 'POST'
    })

    toast.add({
      title: 'Import Successful',
      description: res?.message || `Imported products from ${template.name}`,
      color: 'success'
    })

    showImportSheet.value = false
    confirmingTemplate.value = null

    // Refresh products in local store
    await productStore.fetchProducts()
  } catch (err: any) {
    toast.add({
      title: 'Import Failed',
      description: err?.data?.detail || err?.message || 'Failed to import catalog',
      color: 'error'
    })
  } finally {
    importingSlug.value = null
  }
}

const addingProductLoader = ref(false)

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
  cost_price: 0,
  barcode_id: "",
  quantity: 0,
  unit: 'piece',
  description: ''
})

const unitOptions = [
  { label: 'Piece (pcs)', value: 'piece' },
  { label: 'Sachet', value: 'sachet' },
  { label: 'Pack', value: 'pack' },
  { label: 'Carton', value: 'carton' },
  { label: 'Kilogram (kg)', value: 'kg' },
  { label: 'Gram (g)', value: 'g' },
  { label: 'Litre (L)', value: 'litre' },
  { label: 'Millilitre (ml)', value: 'ml' },
  { label: 'Dozen', value: 'dozen' },
  { label: 'Bag', value: 'bag' }
]
const units = unitOptions.map(u => u.value)
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
    cost_price: p.cost_price || 0,
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
  editingProduct.value = {
    ...product,
    price: product.price / 100,
    cost_price: product.cost_price ? product.cost_price / 100 : 0
  }
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
        cost_price: Math.round((editingProduct.value.cost_price || 0) * 100),
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
  addingProductLoader.value = true
  try {
    const addData = {
      name: newProduct.value.name,
      barcode_id: newProduct.value.barcode_id || '',
      unit_price: Math.round(newProduct.value.price * 100),
      cost_price: Math.round((newProduct.value.cost_price || 0) * 100),
      quantities: newProduct.value.quantity,
      unit_in: newProduct.value.unit,
      description: newProduct.value.description || ''
    }
    await productStore.addProduct(addData)
    toast.add({ title: 'Product added', description: newProduct.value.name, color: 'success' })
    showAddModal.value = false
    newProduct.value = { name: '', price: 0, cost_price: 0, barcode_id: '', quantity: 0, unit: 'piece', description: '' }
    catalogMatchInfo.value = null
  } catch (err) {
    toast.add({ title: 'Error', description: 'Could not add product', color: 'error' })
  } finally {
    addingProductLoader.value = false
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

const addVideoRef = ref<HTMLVideoElement | null>(null)
const editVideoRef = ref<HTMLVideoElement | null>(null)
const activeScanningField = ref<'add' | 'edit' | null>(null)

const {
  isCameraActive,
  isCameraLoading,
  hasTorch,
  isTorchActive,
  isNativeEngine,
  hasMultipleCameras,
  startScanner,
  stopScanner,
  toggleTorch,
  switchCamera,
  triggerAutofocus
} = useBarcodeScanner({
  cooldownMs: 1200,
  throttleMs: 100,
  playBeep: true,
  vibrate: true
})

// Scan-to-Add State & Logic
const isLookingUpBarcode = ref(false)
const catalogMatchInfo = ref<{
  name: string
  source: 'catalog' | 'community'
  category?: string
  suggested_price?: number
} | null>(null)
let lookupDebounceTimer: any = null

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
      newProduct.value.name = res.name
      if (res.unit_in) newProduct.value.unit = res.unit_in
      if (res.suggested_price && (!newProduct.value.price || newProduct.value.price === 0)) {
        newProduct.value.price = res.suggested_price / 100
      }
      if (res.cost_price && (!newProduct.value.cost_price || newProduct.value.cost_price === 0)) {
        newProduct.value.cost_price = res.cost_price / 100
      }
      if (res.description && !newProduct.value.description) {
        newProduct.value.description = res.description
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

function clearAutoFill() {
  catalogMatchInfo.value = null
  newProduct.value.name = ''
  newProduct.value.price = 0
  newProduct.value.cost_price = 0
  newProduct.value.description = ''
  newProduct.value.unit = 'piece'
}

function handleBarcodeManualInput() {
  clearTimeout(lookupDebounceTimer)
  lookupDebounceTimer = setTimeout(() => {
    const code = newProduct.value.barcode_id?.trim()
    if (code && code.length >= 6) {
      lookupBarcode(code)
    } else {
      catalogMatchInfo.value = null
    }
  }, 450)
}

function openAddProductModal() {
  newProduct.value = { name: '', price: 0, cost_price: 0, barcode_id: '', quantity: 0, unit: 'piece', description: '' }
  catalogMatchInfo.value = null
  isLookingUpBarcode.value = false
  showAddModal.value = true
}

async function startCameraScanner(field: 'add' | 'edit') {
  if (activeScanningField.value) {
    stopCameraScanner()
  }
  activeScanningField.value = field
  
  try {
    await nextTick()
    const videoEl = field === 'add' ? addVideoRef.value : editVideoRef.value
    
    if (videoEl) {
      const success = await startScanner(videoEl, (code: string) => {
        if (activeScanningField.value === 'add') {
          newProduct.value.barcode_id = code
          lookupBarcode(code)
        } else if (activeScanningField.value === 'edit' && editingProduct.value) {
          editingProduct.value.barcode_id = code
        }
        
        toast.add({
          title: 'Barcode Scanned',
          description: `Captured: ${code}`,
          color: 'success',
          icon: 'i-lucide-check-circle'
        })
        stopCameraScanner()
      })

      if (!success) {
        toast.add({ title: 'Camera Error', description: 'Could not access camera', color: 'error' })
        stopCameraScanner()
      }
    }
  } catch (err) {
    console.error('startCameraScanner error:', err)
    toast.add({ title: 'Camera Error', description: 'Could not access camera', color: 'error' })
    stopCameraScanner()
  }
}

function stopCameraScanner() {
  activeScanningField.value = null
  stopScanner()
  if (addVideoRef.value) {
    addVideoRef.value.srcObject = null
  }
  if (editVideoRef.value) {
    editVideoRef.value.srcObject = null
  }
}

watch([showAddModal, showEditSlideover], () => {
  stopCameraScanner()
})

onUnmounted(() => {
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
      <div class="flex items-center gap-2">
        <UButton
          v-if="auth.hasPermission('create:product') || auth.hasPermission('manage:product')"
          class="p-2.5 font-medium"
          icon="i-lucide-plus"
          @click="openAddProductModal"
        >
          Add Product
        </UButton>
      </div>
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
            <tr v-if="filteredProducts.length === 0">
              <td colspan="6" class="text-center py-12 px-4">
                <UIcon name="i-lucide-package-search" class="size-10 text-(--ui-text-dimmed) mx-auto mb-2" />
                <p class="text-sm font-semibold text-(--ui-text-highlighted)">No products in inventory</p>
                <p class="text-xs text-(--ui-text-dimmed) max-w-sm mx-auto mt-1">
                  Add products with barcode scanning or manual entry to start selling.
                </p>
                <div class="flex items-center justify-center gap-2 pt-3">
                  <UButton
                    v-if="auth.hasPermission('create:product') || auth.hasPermission('manage:product')"
                    icon="i-lucide-plus"
                    size="xs"
                    color="primary"
                    label="Add Product"
                    @click="openAddProductModal"
                  />
                </div>
              </td>
            </tr>
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
                <div v-if="auth.hasPermission('manage:product') || auth.hasPermission('edit:product') || auth.hasPermission('delete:product') || auth.hasPermission('adjust:stock')" class="flex items-center justify-end gap-1">
                  <UButton v-if="auth.hasPermission('adjust:stock') || auth.hasPermission('manage:product')" variant="ghost" color="primary" size="xs" icon="i-lucide-boxes" title="Adjust Stock" @click="openAdjust(product)" />
                  <UButton v-if="auth.hasPermission('view:product') || auth.hasPermission('manage:product')" variant="ghost" color="neutral" size="xs" icon="i-lucide-history" title="Stock History" @click="openHistory(product)" />
                  <UButton v-if="auth.hasPermission('edit:product') || auth.hasPermission('manage:product')" variant="ghost" color="neutral" size="xs" icon="i-lucide-pencil" title="Edit" @click="openEdit(product)" />
                  <UButton v-if="auth.hasPermission('delete:product') || auth.hasPermission('manage:product')" variant="ghost" color="error" size="xs" icon="i-lucide-trash-2" title="Delete" @click="confirmDelete(product)" />
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
        class="text-center py-12 px-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) space-y-3"
      >
        <UIcon name="i-lucide-package-search" class="size-10 text-(--ui-text-dimmed) mx-auto" />
        <p class="text-sm font-semibold text-(--ui-text-highlighted)">No products in inventory</p>
        <p class="text-xs text-(--ui-text-dimmed) max-w-sm mx-auto">
          Add products with barcode scanning or manual entry to start selling.
        </p>
        <div class="flex items-center justify-center gap-2 pt-1">
          <UButton
            v-if="auth.hasPermission('create:product') || auth.hasPermission('manage:product')"
            icon="i-lucide-plus"
            size="xs"
            color="primary"
            label="Add Product"
            @click="openAddProductModal"
          />
        </div>
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
        <div v-if="auth.hasPermission('manage:product') || auth.hasPermission('edit:product') || auth.hasPermission('delete:product') || auth.hasPermission('adjust:stock')" class="grid grid-cols-4 gap-1.5 pt-1">
          <UButton
            v-if="auth.hasPermission('adjust:stock') || auth.hasPermission('manage:product')"
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
            v-if="auth.hasPermission('view:product') || auth.hasPermission('manage:product')"
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
            v-if="auth.hasPermission('edit:product') || auth.hasPermission('manage:product')"
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
            v-if="auth.hasPermission('delete:product') || auth.hasPermission('manage:product')"
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

    <AppBottomSheet
      v-model="showAddModal"
      title="Add New Product"
      description="Scan a barcode to auto-fill product details or enter them manually."
    >
      <form class="space-y-4" @submit.prevent="handleAddProduct">
        <!-- 1. Barcode Field & Camera Scanner (At Top for Fast Scan-to-Add) -->
        <UFormField label="Barcode / SKU">
          <div class="flex gap-1.5 w-full">
            <UInput
              v-model="newProduct.barcode_id"
              placeholder="Scan or enter barcode (e.g. 6291109120360)..."
              class="flex-1"
              :loading="isLookingUpBarcode"
              @input="handleBarcodeManualInput"
            />
            <UButton
              type="button"
              :color="activeScanningField === 'add' ? 'error' : 'primary'"
              variant="solid"
              :icon="activeScanningField === 'add' ? 'i-lucide-camera-off' : 'i-lucide-camera'"
              :title="activeScanningField === 'add' ? 'Stop Camera' : 'Scan with Camera'"
              @click="activeScanningField === 'add' ? stopCameraScanner() : startCameraScanner('add')"
            />
          </div>
        </UFormField>

        <!-- Camera Scanner Live Stream Box -->
        <div
          v-if="activeScanningField === 'add'"
          class="relative overflow-hidden rounded-xl border border-(--ui-border) bg-black aspect-video max-h-56 flex items-center justify-center"
        >
          <!-- Loading indicator -->
          <div
            v-if="isCameraLoading"
            class="absolute inset-0 bg-black/85 flex flex-col items-center justify-center gap-2 z-10 text-zinc-300"
          >
            <UIcon name="i-lucide-loader-2" class="size-6 animate-spin text-primary-400" />
            <span class="text-xs font-medium">Opening camera...</span>
          </div>

          <!-- Camera Controls Overlay (Torch, Fast ML, Switch Camera & Close) -->
          <div class="absolute top-2.5 right-2.5 flex items-center gap-1.5 z-20">
            <span
              v-if="isNativeEngine"
              class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/80 backdrop-blur-md text-white border border-emerald-400/40 shadow-sm tracking-wider uppercase font-mono"
            >
              Fast ML
            </span>
            <button
              v-if="hasMultipleCameras"
              type="button"
              class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
              title="Switch Camera"
              @click="switchCamera"
            >
              <UIcon name="i-lucide-refresh-cw" class="size-4" />
            </button>
            <button
              v-if="hasTorch"
              type="button"
              class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
              :class="{ 'bg-amber-500! text-black! border-amber-400! shadow-amber-500/50': isTorchActive }"
              title="Toggle Flashlight / Night Mode"
              @click="toggleTorch"
            >
              <UIcon :name="isTorchActive ? 'i-lucide-zap' : 'i-lucide-zap-off'" class="size-4" />
            </button>
            <button
              type="button"
              class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
              title="Close Camera"
              @click="stopCameraScanner"
            >
              <UIcon name="i-lucide-x" class="size-4" />
            </button>
          </div>

          <video
            ref="addVideoRef"
            class="w-full h-full object-cover cursor-pointer"
            autoplay
            playsinline
            muted
            title="Tap to focus"
            @click="triggerAutofocus"
          />
          <div
            class="absolute inset-0 flex items-center justify-center pointer-events-auto cursor-pointer"
            title="Tap to focus"
            @click="triggerAutofocus"
          >
            <div class="w-3/4 h-1/2 border-2 border-dashed border-emerald-500 rounded-lg opacity-65 relative transition hover:opacity-100">
              <div class="absolute inset-x-0 h-0.5 bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]" style="top: 50%" />
              <span class="absolute -bottom-5 inset-x-0 text-center text-[10px] text-emerald-400 font-medium tracking-wide drop-shadow">
                Tap to Focus
              </span>
            </div>
          </div>
        </div>

        <!-- Catalog Recognition Badge / Banner -->
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
                <div class="flex items-center gap-1.5">
                  <span class="font-bold text-(--ui-text-highlighted) truncate">
                    {{ catalogMatchInfo.name }}
                  </span>
                </div>
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

          <!-- Product Confirmation Disclaimer & Reset Action -->
          <div class="pt-2 border-t border-primary-500/20 flex items-center justify-between gap-2 text-[11px]">
            <span class="flex items-center gap-1 text-amber-500 dark:text-amber-400 font-medium">
              <UIcon name="i-lucide-info" class="size-3.5 shrink-0" />
              Please verify product name, unit size, and price match your physical item.
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
          <UInput v-model="newProduct.name" placeholder="e.g. Golden Penny Spaghetti 500g" />
        </UFormField>

        <!-- Pricing: Selling Price & Cost Price -->
        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Selling Price (₦)" required>
            <UInput v-model.number="newProduct.price" type="number" step="any" placeholder="0.00" />
          </UFormField>
          <UFormField label="Cost Price (₦)">
            <UInput v-model.number="newProduct.cost_price" type="number" step="any" placeholder="0.00" />
          </UFormField>
        </div>

        <!-- Inventory: Quantity on Hand & Unit -->
        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Quantity on Hand">
            <UInput v-model.number="newProduct.quantity" type="number" step="any" placeholder="0" />
          </UFormField>
          <UFormField label="Unit">
            <div class="relative w-full">
              <select
                v-model="newProduct.unit"
                class="w-full h-10 px-3 py-2 text-sm rounded-md bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-highlighted) focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none pr-8 cursor-pointer font-medium"
              >
                <option v-if="newProduct.unit && !unitOptions.some(u => u.value === newProduct.unit)" :value="newProduct.unit">
                  {{ newProduct.unit }}
                </option>
                <option v-for="u in unitOptions" :key="u.value" :value="u.value">
                  {{ u.label }}
                </option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-(--ui-text-dimmed)">
                <UIcon name="i-lucide-chevron-down" class="size-4" />
              </div>
            </div>
          </UFormField>
        </div>

        <!-- Description (Textarea) -->
        <UFormField label="Description">
          <UTextarea v-model="newProduct.description" placeholder="Product size, flavor, packaging details..." :rows="3" />
        </UFormField>

        <div class="flex justify-end gap-2 pt-2">
          <UButton variant="outline" color="neutral" @click="showAddModal = false">Cancel</UButton>
          <UButton type="submit" :loading="addingProductLoader">Add Product</UButton>
        </div>
      </form>
    </AppBottomSheet>

    <AppBottomSheet
      v-model="showEditSlideover"
      title="Edit Product"
      description="Update pricing, barcode, or details for this item."
    >
      <form v-if="editingProduct" class="space-y-4" @submit.prevent="saveEdit">
        <UFormField label="Product Name">
          <UInput v-model="editingProduct.name" />
        </UFormField>
        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Selling Price (₦)">
            <UInput v-model.number="editingProduct.price" type="number" step="any" />
          </UFormField>
          <UFormField label="Cost Price (₦)">
            <UInput v-model.number="editingProduct.cost_price" type="number" step="any" />
          </UFormField>
        </div>
        <UFormField label="Barcode ID">
          <div class="flex gap-1.5 w-full">
            <UInput v-model="editingProduct.barcode_id" class="flex-1" />
            <UButton
              type="button"
              :color="activeScanningField === 'edit' ? 'error' : 'primary'"
              variant="solid"
              :icon="activeScanningField === 'edit' ? 'i-lucide-camera-off' : 'i-lucide-camera'"
              @click="activeScanningField === 'edit' ? stopCameraScanner() : startCameraScanner('edit')"
            />
          </div>
        </UFormField>

        <div
          v-if="activeScanningField === 'edit'"
          class="relative overflow-hidden rounded-xl border border-(--ui-border) bg-black aspect-video max-h-56 flex items-center justify-center"
        >
          <!-- Loading indicator -->
          <div
            v-if="isCameraLoading"
            class="absolute inset-0 bg-black/85 flex flex-col items-center justify-center gap-2 z-10 text-zinc-300"
          >
            <UIcon name="i-lucide-loader-2" class="size-6 animate-spin text-primary-400" />
            <span class="text-xs font-medium">Opening camera...</span>
          </div>

          <!-- Camera Controls Overlay (Torch, Fast ML, Switch Camera & Close) -->
          <div class="absolute top-2.5 right-2.5 flex items-center gap-1.5 z-20">
            <span
              v-if="isNativeEngine"
              class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/80 backdrop-blur-md text-white border border-emerald-400/40 shadow-sm tracking-wider uppercase font-mono"
            >
              Fast ML
            </span>
            <button
              v-if="hasMultipleCameras"
              type="button"
              class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
              title="Switch Camera"
              @click="switchCamera"
            >
              <UIcon name="i-lucide-refresh-cw" class="size-4" />
            </button>
            <button
              v-if="hasTorch"
              type="button"
              class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
              :class="{ 'bg-amber-500! text-black! border-amber-400! shadow-amber-500/50': isTorchActive }"
              title="Toggle Flashlight / Night Mode"
              @click="toggleTorch"
            >
              <UIcon :name="isTorchActive ? 'i-lucide-zap' : 'i-lucide-zap-off'" class="size-4" />
            </button>
            <button
              type="button"
              class="size-8 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-md active:scale-95"
              title="Close Camera"
              @click="stopCameraScanner"
            >
              <UIcon name="i-lucide-x" class="size-4" />
            </button>
          </div>

          <video
            ref="editVideoRef"
            class="w-full h-full object-cover cursor-pointer"
            autoplay
            playsinline
            muted
            title="Tap to focus"
            @click="triggerAutofocus"
          />
          <div
            class="absolute inset-0 flex items-center justify-center pointer-events-auto cursor-pointer"
            title="Tap to focus"
            @click="triggerAutofocus"
          >
            <div class="w-3/4 h-1/2 border-2 border-dashed border-emerald-500 rounded-lg opacity-65 relative transition hover:opacity-100">
              <div class="absolute inset-x-0 h-0.5 bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]" style="top: 50%" />
              <span class="absolute -bottom-5 inset-x-0 text-center text-[10px] text-emerald-400 font-medium tracking-wide drop-shadow">
                Tap to Focus
              </span>
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
            <div class="relative w-full">
              <select
                v-model="editingProduct.unit"
                class="w-full h-10 px-3 py-2 text-sm rounded-md bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-highlighted) focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none pr-8 cursor-pointer font-medium"
              >
                <option v-if="editingProduct.unit && !unitOptions.some(u => u.value === editingProduct.unit)" :value="editingProduct.unit">
                  {{ editingProduct.unit }}
                </option>
                <option v-for="u in unitOptions" :key="u.value" :value="u.value">
                  {{ u.label }}
                </option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-(--ui-text-dimmed)">
                <UIcon name="i-lucide-chevron-down" class="size-4" />
              </div>
            </div>
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
    </AppBottomSheet>

    <AppBottomSheet
      v-model="showAdjustModal"
      title="Adjust Stock"
      description="Add or deduct inventory quantity for this product."
    >
      <div v-if="adjustingProduct" class="space-y-4">
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
            <div class="relative w-full">
              <select
                v-model="adjustForm.reason"
                class="w-full h-10 px-3 py-2 text-sm rounded-md bg-(--ui-bg) border border-(--ui-border) text-(--ui-text-highlighted) focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none pr-8 cursor-pointer font-medium"
              >
                <option v-for="r in reasons" :key="r.value" :value="r.value">
                  {{ r.label }}
                </option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-(--ui-text-dimmed)">
                <UIcon name="i-lucide-chevron-down" class="size-4" />
              </div>
            </div>
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
    </AppBottomSheet>

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

    <AppFullScreenModal
      v-model="showHistoryModal"
      :title="`Stock History - ${historyProduct?.name || ''}`"
      description="Audit log of all stock increases and decreases for this product."
    >
      <div class="space-y-4">
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
      </div>
      <template #footer>
        <div class="flex justify-end">
          <UButton variant="outline" color="neutral" @click="showHistoryModal = false">Close</UButton>
        </div>
      </template>
    </AppFullScreenModal>

    <!-- Import Starter Pack Bottom Sheet -->
    <AppFullScreenModal
      v-model="showImportSheet"
      title="Import Starter Pack"
      description="Choose a pre-configured industry catalog to jumpstart your inventory with barcodes and standard retail prices."
      max-width="max-w-lg"
    >
      <div class="space-y-4">
        <!-- Confirmation Banner -->
        <div
          v-if="confirmingTemplate"
          class="p-4 rounded-xl bg-primary-500/10 border border-primary-500/20 space-y-3"
        >
          <div class="flex items-start gap-3">
            <div class="w-9 h-9 rounded-lg bg-primary-500/20 flex items-center justify-center text-primary-500 shrink-0">
              <UIcon :name="getTemplateIcon(confirmingTemplate.icon)" class="size-5" />
            </div>
            <div class="min-w-0 flex-1">
              <h4 class="font-bold text-sm text-(--ui-text-highlighted)">
                Import {{ confirmingTemplate.name }}?
              </h4>
              <p class="text-xs text-(--ui-text-muted) mt-0.5">
                This will add {{ confirmingTemplate.total_items }} products to your store. Any items with existing barcodes or names will be safely skipped.
              </p>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-1 border-t border-primary-500/20">
            <UButton
              label="Cancel"
              size="xs"
              variant="ghost"
              color="neutral"
              :disabled="!!importingSlug"
              @click="confirmingTemplate = null"
            />
            <UButton
              label="Yes, Import Products"
              icon="i-lucide-download"
              size="xs"
              color="primary"
              :loading="importingSlug === confirmingTemplate.slug"
              @click="handleImportCatalog(confirmingTemplate)"
            />
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoadingTemplates" class="space-y-3 py-2">
          <div
            v-for="i in 3"
            :key="i"
            class="h-20 bg-(--ui-bg-accented)/30 border border-(--ui-border) rounded-xl animate-pulse"
          />
        </div>

        <!-- Empty State -->
        <div
          v-else-if="catalogTemplates.length === 0"
          class="p-8 text-center bg-(--ui-bg-accented)/20 rounded-xl border border-(--ui-border) space-y-2"
        >
          <UIcon name="i-lucide-package-x" class="size-8 text-(--ui-text-dimmed) mx-auto" />
          <p class="text-xs font-semibold text-(--ui-text-highlighted)">No starter packs available</p>
          <p class="text-[11px] text-(--ui-text-muted)">Please check back later or add products manually.</p>
        </div>

        <!-- Catalog List -->
        <div v-else class="space-y-2.5 overflow-y-auto pr-1">
          <div
            v-for="template in catalogTemplates"
            :key="template.id"
            class="p-3.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) hover:border-primary-500/40 transition flex items-center justify-between gap-3 shadow-xs"
          >
            <!-- Left Info -->
            <div class="flex items-start gap-3 min-w-0 flex-1">
              <div class="w-10 h-10 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-500 shrink-0 mt-0.5">
                <UIcon :name="getTemplateIcon(template.icon)" class="size-5" />
              </div>
              <div class="min-w-0 flex-1">
                <h4 class="font-bold text-sm text-(--ui-text-highlighted) truncate">
                  {{ template.name }}
                </h4>
                <p class="text-xs text-(--ui-text-muted) line-clamp-1 mt-0.5">
                  {{ template.description || 'Pre-configured retail products' }}
                </p>
                <div class="flex items-center gap-2 mt-1.5">
                  <span class="inline-flex items-center gap-1 text-[11px] font-semibold text-primary-500 bg-primary-500/10 px-2 py-0.5 rounded-md border border-primary-500/20">
                    <UIcon name="i-lucide-box" class="size-3" />
                    {{ template.total_items }} products
                  </span>
                </div>
              </div>
            </div>

            <!-- Right Action Button -->
            <div class="shrink-0">
              <UButton
                label="Import"
                icon="i-lucide-download"
                size="xs"
                color="primary"
                :loading="importingSlug === template.slug"
                :disabled="!!importingSlug || template.total_items === 0"
                @click="confirmingTemplate = template"
              />
            </div>
          </div>
        </div>
      </div>
    </AppFullScreenModal>
  </div>
</template>
