<script setup lang="ts">
import { BrowserMultiFormatReader, BarcodeFormat, DecodeHintType } from '@zxing/library'

definePageMeta({ layout: 'dashboard' })

const { format } = useFormatCurrency()
const toast = useToast()

const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const auth = useAuthStore()

const productStore = useProductsStore()

const search = ref('')
const showAddModal = ref(false)
const showEditSlideover = ref(false)
const editingProduct = ref<any>(null)

// New product form
const newProduct = ref({
  name: '',
  price: 0,
  barcode_id: '',
  quantity: 0,
  unit: 'piece',
  description: ''
})

const units = ['piece', 'kg', 'g', 'litre', 'ml', 'pack', 'carton', 'dozen', 'bag']

const products = computed(() => {
  return productStore.products.map(p => ({
    slug: p.slug,
    name: p.name,
    barcode_id: p.barcode_id || '',
    price: p.unit_price, // in kobo
    quantity: p.quantities,
    unit: p.unit_in,
    status: p.deleted ? 'inactive' : 'active',
    description: p.description || ''
  }))
})

const filteredProducts = computed(() => {
  if (!search.value) return products.value
  const q = search.value.toLowerCase()
  return products.value.filter(p =>
    p.name.toLowerCase().includes(q) ||
    p.barcode_id.toLowerCase().includes(q)
  )
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

async function saveEdit() {
  try {
    const updateData = {
      name: editingProduct.value.name,
      barcode_id: editingProduct.value.barcode_id || '',
      unit_price: Math.round(editingProduct.value.price * 100), // Naira to Kobo
      quantities: editingProduct.value.quantity,
      unit_in: editingProduct.value.unit,
      description: editingProduct.value.description || ''
    }
    await productStore.updateProduct(editingProduct.value.slug, updateData)
    toast.add({ title: 'Product updated', color: 'success' })
    showEditSlideover.value = false
  } catch (err) {
    console.error('Failed to update product:', err)
    toast.add({ title: 'Error', description: 'Could not update product', color: 'error' })
  }
}

async function handleAddProduct() {
  try {
    const addData = {
      name: newProduct.value.name,
      barcode_id: newProduct.value.barcode_id || '',
      unit_price: Math.round(newProduct.value.price * 100), // Naira to Kobo
      quantities: newProduct.value.quantity,
      unit_in: newProduct.value.unit,
      description: newProduct.value.description || ''
    }
    await productStore.addProduct(addData)
    toast.add({ title: 'Product added', description: newProduct.value.name, color: 'success' })
    showAddModal.value = false
    newProduct.value = { name: '', price: 0, barcode_id: '', quantity: 0, unit: 'piece', description: '' }
  } catch (err) {
    console.error('Failed to add product:', err)
    toast.add({ title: 'Error', description: 'Could not add product', color: 'error' })
  }
}

async function confirmDelete(product: any) {
  try {
    await productStore.deleteProduct(product.slug)
    toast.add({ title: 'Product removed', description: product.name, color: 'warning' })
  } catch (err) {
    console.error('Failed to delete product:', err)
    toast.add({ title: 'Error', description: 'Could not delete product', color: 'error' })
  }
}

// Camera Barcode Scanner for Forms using ZXing
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
    // Graceful wait to let the modal/slideover finish mounting in the DOM
    await new Promise((resolve) => setTimeout(resolve, 200))
    let videoEl = field === 'add' ? addVideoRef.value : editVideoRef.value
    
    // Quick retry loop
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
      codeReader.decodeFromVideoDevice(undefined, videoEl, (result: any, err: any) => {
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
    } else {
      console.warn('Video element ref not found for barcode scanner')
    }
  } catch (err) {
    console.error('Failed to open camera scanner:', err)
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
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-bold text-(--ui-text-highlighted)">Products & Inventory</h2>
        <p class="text-sm text-(--ui-text-muted)">{{ products.length }} products in stock</p>
      </div>
      <UButton v-if="auth.hasPermission('manage:product')" icon="i-lucide-plus" @click="showAddModal = true">
        Add Product
      </UButton>
    </div>

    <!-- Search -->
    <UInput
      v-model="search"
      placeholder="Search by name, barcode, or SKU..."
      icon="i-lucide-search"
      size="lg"
      class="max-w-md"
    />

    <!-- Products Table -->
    <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden">
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
              v-for="product in filteredProducts"
              :key="product.slug"
              class="border-b border-(--ui-border)/50 last:border-0 hover:bg-(--ui-bg-accented)/30 transition"
            >
              <td class="py-3 px-4">
                <div>
                  <p class="font-medium text-(--ui-text-highlighted)">{{ product.name }}</p>
                </div>
              </td>
              <td class="py-3 px-4 font-mono text-xs text-(--ui-text-muted)">{{ product.barcode_id }}</td>
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
                  <UButton variant="ghost" color="neutral" size="xs" icon="i-lucide-pencil" @click="openEdit(product)" />
                  <UButton variant="ghost" color="error" size="xs" icon="i-lucide-trash-2" @click="confirmDelete(product)" />
                </div>
                <span v-else class="text-xs text-(--ui-text-dimmed)">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Product Modal -->
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

          <!-- Camera Viewfinder for Add Form -->
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

    <!-- Edit Product Slideover -->
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

          <!-- Camera Viewfinder for Edit Form -->
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
            <UFormField label="Quantity">
              <UInput v-model.number="editingProduct.quantity" type="number" />
            </UFormField>
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
  </div>
</template>
