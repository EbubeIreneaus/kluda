<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { hasPermission } = useAdminPermission()
const toast = useToast()

const canManage = computed(() => hasPermission('manage:settings'))

// =========================================================================
// Interfaces
// =========================================================================
interface CatalogTemplateItem {
  id: number
  name: string
  slug: string
  description?: string | null
  icon?: string | null
  is_active: boolean
  sort_order: number
  total_imports: number
  total_items: number
  created_at: string
  updated_at: string
}

interface CatalogProductItem {
  id: number
  template_id: number
  name: string
  barcode?: string | null
  category: string
  suggested_price: number // in kobo
  cost_price: number // in kobo
  unit_in: string
  description?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

interface PaginatedItemsResponse {
  items: CatalogProductItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// =========================================================================
// State: Templates
// =========================================================================
const templates = ref<CatalogTemplateItem[]>([])
const isLoadingTemplates = ref(true)
const searchTemplate = ref('')
const isSubmitting = ref(false)

// Modals
const isCreateTemplateOpen = ref(false)
const isEditTemplateOpen = ref(false)
const editingTemplate = ref<CatalogTemplateItem | null>(null)

const templateForm = reactive({
  name: '',
  slug: '',
  description: '',
  icon: 'shopping-cart',
  is_active: true,
  sort_order: 0
})

function getTemplateIcon(icon?: string | null): string {
  if (!icon || typeof icon !== 'string') return 'i-lucide-package'
  const clean = icon.trim().toLowerCase()
  if (!clean) return 'i-lucide-package'
  if (clean.startsWith('i-')) return clean
  return `i-lucide-${clean}`
}

// =========================================================================
// State: Items Viewer & Bottom Sheet
// =========================================================================
const selectedTemplate = ref<CatalogTemplateItem | null>(null)
const isViewItemsOpen = ref(false)
const items = ref<CatalogProductItem[]>([])
const isLoadingItems = ref(false)
const itemsPage = ref(1)
const itemsPageSize = ref(15)
const itemsTotal = ref(0)
const itemsTotalPages = ref(1)
const searchItem = ref('')
const filterNoBarcode = ref(false)

// Bottom sheet for single item detail
const selectedItem = ref<CatalogProductItem | null>(null)
const isItemSheetOpen = ref(false)

// Item modals
const isCreateItemOpen = ref(false)
const isEditItemOpen = ref(false)
const editingItem = ref<CatalogProductItem | null>(null)

const itemForm = reactive({
  name: '',
  barcode: '',
  category: 'General',
  suggested_price_naira: 0,
  cost_price_naira: 0,
  unit_in: 'piece',
  description: '',
  is_active: true
})

const supportedUnits = [
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

// =========================================================================
// Methods: Templates
// =========================================================================
async function fetchTemplates() {
  isLoadingTemplates.value = true
  try {
    const data = await apiFetch<CatalogTemplateItem[]>('/catalog-templates?include_inactive=true')
    templates.value = data || []
  } catch (err: any) {
    templates.value = []
    toast.add({
      title: 'Error loading templates',
      description: err?.data?.detail || 'Could not fetch catalog starter packs.',
      color: 'error'
    })
  } finally {
    isLoadingTemplates.value = false
  }
}

const filteredTemplates = computed(() => {
  if (!searchTemplate.value.trim()) return templates.value
  const q = searchTemplate.value.toLowerCase().trim()
  return templates.value.filter(t =>
    t.name.toLowerCase().includes(q) ||
    t.slug.toLowerCase().includes(q) ||
    (t.description && t.description.toLowerCase().includes(q))
  )
})

function openCreateTemplate() {
  templateForm.name = ''
  templateForm.slug = ''
  templateForm.description = ''
  templateForm.icon = 'shopping-cart'
  templateForm.is_active = true
  templateForm.sort_order = templates.value.length
  isCreateTemplateOpen.value = true
}

function onTemplateNameInput() {
  if (!isEditTemplateOpen.value) {
    templateForm.slug = templateForm.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
  }
}

async function handleSaveTemplate() {
  if (!templateForm.name.trim() || !templateForm.slug.trim()) {
    toast.add({ title: 'Validation Error', description: 'Name and slug are required.', color: 'warning' })
    return
  }

  isSubmitting.value = true
  try {
    await apiFetch('/admin/catalog-templates', {
      method: 'POST',
      body: {
        name: templateForm.name.trim(),
        slug: templateForm.slug.trim(),
        description: templateForm.description.trim() || null,
        icon: templateForm.icon || 'shopping-cart',
        is_active: templateForm.is_active,
        sort_order: Number(templateForm.sort_order) || 0
      }
    })

    toast.add({ title: 'Template Created', description: 'Starter pack successfully added.', color: 'success' })
    isCreateTemplateOpen.value = false
    await fetchTemplates()
  } catch (err: any) {
    toast.add({ title: 'Creation Failed', description: err?.data?.detail || 'Could not create template.', color: 'error' })
  } finally {
    isSubmitting.value = false
  }
}

function openEditTemplate(template: CatalogTemplateItem) {
  editingTemplate.value = template
  templateForm.name = template.name
  templateForm.slug = template.slug
  templateForm.description = template.description || ''
  templateForm.icon = template.icon || 'shopping-cart'
  templateForm.is_active = template.is_active
  templateForm.sort_order = template.sort_order
  isEditTemplateOpen.value = true
}

async function handleUpdateTemplate() {
  if (!editingTemplate.value) return
  isSubmitting.value = true
  try {
    await apiFetch(`/admin/catalog-templates/${editingTemplate.value.id}`, {
      method: 'PUT',
      body: {
        name: templateForm.name.trim(),
        slug: templateForm.slug.trim(),
        description: templateForm.description.trim() || null,
        icon: templateForm.icon || 'shopping-cart',
        is_active: templateForm.is_active,
        sort_order: Number(templateForm.sort_order) || 0
      }
    })

    toast.add({ title: 'Template Updated', description: 'Changes saved & cache refreshed.', color: 'success' })
    isEditTemplateOpen.value = false
    await fetchTemplates()
  } catch (err: any) {
    toast.add({ title: 'Update Failed', description: err?.data?.detail || 'Could not update template.', color: 'error' })
  } finally {
    isSubmitting.value = false
  }
}

async function handleDeleteTemplate(template: CatalogTemplateItem) {
  if (!confirm(`Are you sure you want to delete "${template.name}"? This will permanently delete all associated items in this starter pack!`)) return

  try {
    await apiFetch(`/admin/catalog-templates/${template.id}`, {
      method: 'DELETE'
    })
    toast.add({ title: 'Template Deleted', description: 'Starter pack removed.', color: 'success' })
    await fetchTemplates()
  } catch (err: any) {
    toast.add({ title: 'Delete Failed', description: err?.data?.detail || 'Could not delete template.', color: 'error' })
  }
}

// =========================================================================
// Methods: Items Viewer
// =========================================================================
async function openViewItems(template: CatalogTemplateItem) {
  selectedTemplate.value = template
  itemsPage.value = 1
  searchItem.value = ''
  filterNoBarcode.value = false
  isViewItemsOpen.value = true
  await fetchItems()
}

async function fetchItems() {
  if (!selectedTemplate.value) return
  isLoadingItems.value = true
  try {
    const q = searchItem.value.trim() ? `&search=${encodeURIComponent(searchItem.value.trim())}` : ''
    const barcodeQ = filterNoBarcode.value ? '&has_barcode=false' : ''
    const url = `/catalog-templates/${selectedTemplate.value.slug}/items?page=${itemsPage.value}&page_size=${itemsPageSize.value}${q}${barcodeQ}`
    const res = await apiFetch<PaginatedItemsResponse>(url)
    items.value = res.items || []
    itemsTotal.value = res.total || 0
    itemsTotalPages.value = res.total_pages || 1
  } catch (err: any) {
    items.value = []
    itemsTotal.value = 0
    toast.add({ title: 'Error', description: err?.data?.detail || 'Could not fetch template items.', color: 'error' })
  } finally {
    isLoadingItems.value = false
  }
}

function toggleNoBarcodeFilter() {
  filterNoBarcode.value = !filterNoBarcode.value
  itemsPage.value = 1
  fetchItems()
}

function handleItemSearch() {
  itemsPage.value = 1
  fetchItems()
}

function goToPage(p: number) {
  if (p < 1 || p > itemsTotalPages.value) return
  itemsPage.value = p
  fetchItems()
}

// =========================================================================
// Methods: Bottom Sheet Detail
// =========================================================================
function viewItemDetail(item: CatalogProductItem) {
  selectedItem.value = item
  isItemSheetOpen.value = true
}

function copyBarcode(barcode?: string | null) {
  if (!barcode) return
  navigator.clipboard.writeText(barcode)
  toast.add({ title: 'Copied', description: `Barcode ${barcode} copied to clipboard.`, color: 'success' })
}

// =========================================================================
// Methods: Items CRUD
// =========================================================================
function openCreateItem() {
  if (!selectedTemplate.value) return
  itemForm.name = ''
  itemForm.barcode = ''
  itemForm.category = 'General'
  itemForm.suggested_price_naira = 0
  itemForm.cost_price_naira = 0
  itemForm.unit_in = 'piece'
  itemForm.description = ''
  itemForm.is_active = true
  isCreateItemOpen.value = true
}

async function handleSaveItem() {
  if (!selectedTemplate.value || !itemForm.name.trim()) {
    toast.add({ title: 'Validation Error', description: 'Product name is required.', color: 'warning' })
    return
  }

  isSubmitting.value = true
  try {
    await apiFetch(`/admin/catalog-templates/${selectedTemplate.value.id}/items`, {
      method: 'POST',
      body: {
        name: itemForm.name.trim(),
        barcode: itemForm.barcode.trim() || null,
        category: itemForm.category.trim() || 'General',
        suggested_price: Math.round(Number(itemForm.suggested_price_naira || 0) * 100),
        cost_price: Math.round(Number(itemForm.cost_price_naira || 0) * 100),
        unit_in: itemForm.unit_in,
        description: itemForm.description.trim() || null,
        is_active: itemForm.is_active
      }
    })

    toast.add({ title: 'Product Added', description: 'Item added to catalog.', color: 'success' })
    isCreateItemOpen.value = false
    await fetchItems()
    await fetchTemplates() // update counts
  } catch (err: any) {
    toast.add({ title: 'Failed to Add', description: err?.data?.detail || 'Could not add item.', color: 'error' })
  } finally {
    isSubmitting.value = false
  }
}

function openEditItem(item: CatalogProductItem) {
  editingItem.value = item
  itemForm.name = item.name
  itemForm.barcode = item.barcode || ''
  itemForm.category = item.category
  itemForm.suggested_price_naira = item.suggested_price / 100
  itemForm.cost_price_naira = item.cost_price / 100
  itemForm.unit_in = item.unit_in || 'piece'
  itemForm.description = item.description || ''
  itemForm.is_active = item.is_active
  isItemSheetOpen.value = false
  isEditItemOpen.value = true
}

async function handleUpdateItem() {
  if (!editingItem.value) return
  isSubmitting.value = true
  try {
    await apiFetch(`/admin/catalog-templates/items/${editingItem.value.id}`, {
      method: 'PUT',
      body: {
        name: itemForm.name.trim(),
        barcode: itemForm.barcode.trim() || null,
        category: itemForm.category.trim() || 'General',
        suggested_price: Math.round(Number(itemForm.suggested_price_naira || 0) * 100),
        cost_price: Math.round(Number(itemForm.cost_price_naira || 0) * 100),
        unit_in: itemForm.unit_in,
        description: itemForm.description.trim() || null,
        is_active: itemForm.is_active
      }
    })

    toast.add({ title: 'Product Updated', description: 'Item saved & cache refreshed.', color: 'success' })
    isEditItemOpen.value = false
    await fetchItems()
  } catch (err: any) {
    toast.add({ title: 'Update Failed', description: err?.data?.detail || 'Could not update item.', color: 'error' })
  } finally {
    isSubmitting.value = false
  }
}

async function handleDeleteItem(item: CatalogProductItem) {
  if (!confirm(`Delete "${item.name}" from this catalog?`)) return
  try {
    await apiFetch(`/admin/catalog-templates/items/${item.id}`, {
      method: 'DELETE'
    })
    toast.add({ title: 'Product Deleted', description: 'Item removed from catalog.', color: 'success' })
    isItemSheetOpen.value = false
    await fetchItems()
    await fetchTemplates()
  } catch (err: any) {
    toast.add({ title: 'Delete Failed', description: err?.data?.detail || 'Could not delete item.', color: 'error' })
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>

<template>
  <div class="overflow-y-auto p-4 sm:p-6 md:p-8 space-y-6 max-w-7xl w-full min-w-0 mx-auto">
    <!-- Header Section -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5 min-w-0">
      <div class="min-w-0">
        <h1 class="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <UIcon name="i-lucide-boxes" class="size-5" />
          </div>
          <span>Catalog Starter Packs</span>
        </h1>
        <p class="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
          Pre-populated inventory catalogs for 1-click merchant onboarding. Cached in Redis for zero-latency lookups.
        </p>
      </div>

      <div class="flex items-center gap-2 shrink-0">
        <UButton
          v-if="canManage"
          label="Create Template"
          icon="i-lucide-plus"
          size="sm"
          color="primary"
          class="font-semibold shadow-lg shadow-emerald-500/20"
          @click="openCreateTemplate"
        />
      </div>
    </div>

    <!-- Search & Filters -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="relative w-full sm:w-80">
        <UInput
          v-model="searchTemplate"
          icon="i-lucide-search"
          placeholder="Search templates by name, slug..."
          size="sm"
          class="w-full"
        />
      </div>

      <div class="text-xs text-zinc-400 font-mono flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-400" />
        <span>{{ filteredTemplates.length }} Templates Configured</span>
      </div>
    </div>

    <!-- Templates Loading Skeleton -->
    <div v-if="isLoadingTemplates" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="i in 3"
        :key="i"
        class="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-5 space-y-4 animate-pulse"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-zinc-800" />
          <div class="space-y-2 flex-1">
            <div class="h-4 bg-zinc-800 rounded w-3/4" />
            <div class="h-3 bg-zinc-800/60 rounded w-1/2" />
          </div>
        </div>
        <div class="h-12 bg-zinc-800/40 rounded-lg" />
        <div class="h-8 bg-zinc-800/40 rounded-lg" />
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="filteredTemplates.length === 0"
      class="bg-zinc-900/30 border border-zinc-800/60 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-3"
    >
      <div class="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-400">
        <UIcon name="i-lucide-package-search" class="size-6" />
      </div>
      <h3 class="text-sm font-semibold text-white">No Starter Packs Found</h3>
      <p class="text-xs text-zinc-400 max-w-sm">
        {{ searchTemplate ? 'No templates match your search filter.' : 'Get started by creating your first industry catalog starter pack.' }}
      </p>
      <UButton
        v-if="canManage && !searchTemplate"
        label="Create First Template"
        icon="i-lucide-plus"
        size="xs"
        color="primary"
        @click="openCreateTemplate"
      />
    </div>

    <!-- Templates Grid (Cards on mobile & desktop, no table!) -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="template in filteredTemplates"
        :key="template.id"
        class="bg-zinc-900/60 border border-zinc-800/90 rounded-2xl p-5 flex flex-col justify-between backdrop-blur-sm transition-all hover:border-zinc-700/80 shadow-lg shadow-black/20 group"
      >
        <div>
          <!-- Top Tag & Status -->
          <div class="flex items-center justify-between gap-2 mb-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-zinc-800 text-zinc-300 border border-zinc-700">
              {{ template.slug }}
            </span>
            <span
              class="px-2 py-0.5 rounded text-[10px] font-semibold border"
              :class="template.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'"
            >
              {{ template.is_active ? 'ACTIVE' : 'INACTIVE' }}
            </span>
          </div>

          <!-- Title & Icon -->
          <div class="flex items-start gap-3 mb-2.5">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500/20 to-emerald-400/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0 group-hover:scale-105 transition-transform">
              <UIcon :name="getTemplateIcon(template.icon)" class="size-5" />
            </div>
            <div>
              <h3 class="text-base font-bold text-white tracking-tight leading-snug">
                {{ template.name }}
              </h3>
              <p class="text-xs text-zinc-400 line-clamp-2 mt-0.5">
                {{ template.description || 'No description provided.' }}
              </p>
            </div>
          </div>

          <!-- Metrics Row -->
          <div class="grid grid-cols-2 gap-2 my-4 bg-zinc-950/60 border border-zinc-800/80 rounded-xl p-3 text-center">
            <div class="flex flex-col items-center">
              <span class="text-[10px] uppercase font-semibold tracking-wider text-zinc-400">Total Items</span>
              <span class="text-base font-extrabold text-white font-mono mt-0.5">{{ template.total_items }}</span>
            </div>
            <div class="flex flex-col items-center border-l border-zinc-800">
              <span class="text-[10px] uppercase font-semibold tracking-wider text-zinc-400">Merchant Imports</span>
              <span class="text-base font-extrabold text-emerald-400 font-mono mt-0.5">{{ template.total_imports }}</span>
            </div>
          </div>
        </div>

        <!-- Card Actions -->
        <div class="pt-3 border-t border-zinc-800/80 flex items-center gap-2">
          <UButton
            label="View Items"
            icon="i-lucide-layers"
            size="xs"
            color="primary"
            class="flex-1 font-semibold"
            @click="openViewItems(template)"
          />
          <UButton
            v-if="canManage"
            icon="i-lucide-edit-3"
            size="xs"
            color="neutral"
            variant="outline"
            title="Edit Template"
            @click="openEditTemplate(template)"
          />
          <UButton
            v-if="canManage"
            icon="i-lucide-trash-2"
            size="xs"
            color="error"
            variant="ghost"
            title="Delete Template"
            @click="handleDeleteTemplate(template)"
          />
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- View Items: Full Screen Modal Dialog with Lazy Loading               -->
    <!-- ===================================================================== -->
    <AdminFullScreenModal
      v-model="isViewItemsOpen"
      :title="selectedTemplate ? `${selectedTemplate.name} Products` : 'Catalog Products'"
      :description="`${itemsTotal} products configured in this starter pack. Click on any item to view full details.`"
      max-width="max-w-4xl"
    >
      <div class="flex flex-col gap-4">
        <!-- Controls Bar -->
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-zinc-900/80 p-3 rounded-xl border border-zinc-800">
          <div class="flex-1 relative">
            <UInput
              v-model="searchItem"
              icon="i-lucide-search"
              placeholder="Search by name, barcode, or category..."
              size="sm"
              class="w-full"
              @keyup.enter="handleItemSearch"
            />
          </div>

          <div class="flex items-center gap-2 justify-between sm:justify-end flex-wrap">
            <UButton
              :label="filterNoBarcode ? 'No Barcode (Active)' : 'No Barcode Only'"
              :icon="filterNoBarcode ? 'i-lucide-alert-triangle' : 'i-lucide-scan-line'"
              size="xs"
              :color="filterNoBarcode ? 'warning' : 'neutral'"
              :variant="filterNoBarcode ? 'solid' : 'outline'"
              title="Filter items without a barcode"
              @click="toggleNoBarcodeFilter"
            />
            <UButton
              label="Search"
              size="xs"
              color="neutral"
              variant="outline"
              @click="handleItemSearch"
            />
            <UButton
              v-if="canManage"
              label="Add Product"
              icon="i-lucide-plus"
              size="xs"
              color="primary"
              @click="openCreateItem"
            />
          </div>
        </div>

        <!-- Items Loading State -->
        <div v-if="isLoadingItems" class="space-y-2 py-4">
          <div
            v-for="i in 5"
            :key="i"
            class="h-16 bg-zinc-900/60 border border-zinc-800/60 rounded-xl animate-pulse"
          />
        </div>

        <!-- Items Empty State -->
        <div
          v-else-if="items.length === 0"
          class="p-8 text-center bg-zinc-900/30 rounded-xl border border-zinc-800/60 space-y-2"
        >
          <UIcon name="i-lucide-inbox" class="size-8 text-zinc-500 mx-auto" />
          <p class="text-xs font-semibold text-white">No products found</p>
          <p class="text-[11px] text-zinc-400">
            {{ filterNoBarcode ? 'All products in this category currently have barcodes.' : 'Try adjusting your search query or add new items.' }}
          </p>
        </div>

        <!-- Items List: Compact, Mobile-Friendly Cards/Rows -->
        <div v-else class="space-y-2 max-h-[55vh] overflow-y-auto pr-1">
          <div
            v-for="item in items"
            :key="item.id"
            class="flex items-center justify-between p-3 rounded-xl bg-zinc-900/60 hover:bg-zinc-800/70 border border-zinc-800/80 transition-all cursor-pointer group"
            @click="viewItemDetail(item)"
          >
            <!-- Left: Name & Barcode -->
            <div class="min-w-0 flex-1 pr-3">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs sm:text-sm font-semibold text-white group-hover:text-emerald-300 transition-colors">
                  {{ item.name }}
                </span>
                <span class="px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-400 border border-zinc-700/60">
                  {{ item.category }}
                </span>
              </div>

              <div class="flex items-center gap-3 mt-1 text-[11px] text-zinc-400">
                <span v-if="item.barcode" class="font-mono flex items-center gap-1 text-zinc-300">
                  <UIcon name="i-lucide-barcode" class="size-3.5 text-zinc-400" />
                  {{ item.barcode }}
                </span>
                <span v-else class="inline-flex items-center gap-1 font-medium text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 text-[10px]">
                  <UIcon name="i-lucide-alert-circle" class="size-3 text-amber-400" />
                  No Barcode
                </span>
                <span class="text-zinc-600">·</span>
                <span class="capitalize">{{ item.unit_in }}</span>
              </div>
            </div>

            <!-- Right: Pricing & Arrow -->
            <div class="flex items-center gap-3 shrink-0 text-right">
              <div>
                <div class="text-xs sm:text-sm font-bold text-white font-mono">
                  ₦{{ (item.suggested_price / 100).toLocaleString() }}
                </div>
                <div class="text-[10px] text-zinc-400 font-mono">
                  Cost: ₦{{ (item.cost_price / 100).toLocaleString() }}
                </div>
              </div>
              <UIcon name="i-lucide-chevron-right" class="size-4 text-zinc-500 group-hover:text-white transition-colors" />
            </div>
          </div>
        </div>

        <!-- Pagination Controls -->
        <div v-if="itemsTotalPages > 1" class="flex items-center justify-between pt-3 border-t border-zinc-800 text-xs text-zinc-400">
          <span>Page {{ itemsPage }} of {{ itemsTotalPages }} ({{ itemsTotal }} total)</span>
          <div class="flex items-center gap-2">
            <UButton
              label="Previous"
              icon="i-lucide-arrow-left"
              size="xs"
              color="neutral"
              variant="outline"
              :disabled="itemsPage <= 1"
              @click="goToPage(itemsPage - 1)"
            />
            <UButton
              label="Next"
              trailing-icon="i-lucide-arrow-right"
              size="xs"
              color="neutral"
              variant="outline"
              :disabled="itemsPage >= itemsTotalPages"
              @click="goToPage(itemsPage + 1)"
            />
          </div>
        </div>
      </div>
    </AdminFullScreenModal>

    <!-- ===================================================================== -->
    <!-- Item Detail: Bottom Sheet Dialog                                      -->
    <!-- ===================================================================== -->
    <AdminBottomSheet
      v-model="isItemSheetOpen"
      :title="selectedItem ? selectedItem.name : 'Product Details'"
      description="Full catalog item configuration & pricing overview."
      max-width="max-w-lg"
    >
      <div v-if="selectedItem" class="space-y-4">
        <!-- Badge & Category -->
        <div class="flex items-center justify-between pb-2 border-b border-zinc-800">
          <span class="px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {{ selectedItem.category }}
          </span>
          <span class="text-xs text-zinc-400 uppercase font-mono">Unit: {{ selectedItem.unit_in }}</span>
        </div>

        <!-- Barcode Banner -->
        <div class="bg-zinc-900/80 p-3 rounded-xl border border-zinc-800 flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <UIcon
              :name="selectedItem.barcode ? 'i-lucide-barcode' : 'i-lucide-alert-triangle'"
              :class="selectedItem.barcode ? 'text-emerald-400' : 'text-amber-400'"
              class="size-5"
            />
            <div>
              <div class="text-[10px] uppercase font-semibold text-zinc-400">Barcode / SKU</div>
              <div v-if="selectedItem.barcode" class="font-mono text-sm font-bold text-white">
                {{ selectedItem.barcode }}
              </div>
              <div v-else class="text-xs font-medium text-amber-400">
                Unassigned (Click Edit to Add)
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <UButton
              v-if="selectedItem.barcode"
              icon="i-lucide-copy"
              size="xs"
              color="neutral"
              variant="ghost"
              title="Copy Barcode"
              @click="copyBarcode(selectedItem.barcode)"
            />
            <UButton
              v-else-if="canManage"
              label="Add Barcode"
              icon="i-lucide-plus"
              size="xs"
              color="warning"
              variant="subtle"
              @click="openEditItem(selectedItem)"
            />
          </div>
        </div>

        <!-- Pricing Grid -->
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-zinc-900/80 p-3 rounded-xl border border-zinc-800">
            <span class="text-[10px] uppercase font-semibold text-zinc-400">Suggested Retail Price</span>
            <div class="text-lg font-bold text-white font-mono mt-0.5">
              ₦{{ (selectedItem.suggested_price / 100).toLocaleString() }}
            </div>
          </div>

          <div class="bg-zinc-900/80 p-3 rounded-xl border border-zinc-800">
            <span class="text-[10px] uppercase font-semibold text-zinc-400">Estimated Wholesale Cost</span>
            <div class="text-lg font-bold text-zinc-300 font-mono mt-0.5">
              ₦{{ (selectedItem.cost_price / 100).toLocaleString() }}
            </div>
          </div>
        </div>

        <!-- Profit Margin -->
        <div class="bg-emerald-950/20 border border-emerald-500/30 p-3 rounded-xl flex items-center justify-between">
          <div>
            <span class="text-[10px] uppercase font-semibold text-emerald-400">Estimated Gross Margin</span>
            <div class="text-sm font-bold text-emerald-300 font-mono">
              +₦{{ ((selectedItem.suggested_price - selectedItem.cost_price) / 100).toLocaleString() }}
            </div>
          </div>
          <span class="text-xs font-bold text-emerald-400 font-mono bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
            {{ selectedItem.suggested_price > 0 ? Math.round(((selectedItem.suggested_price - selectedItem.cost_price) / selectedItem.suggested_price) * 100) : 0 }}% Margin
          </span>
        </div>

        <!-- Description -->
        <div v-if="selectedItem.description" class="text-xs text-zinc-400 bg-zinc-900/40 p-3 rounded-xl border border-zinc-800/60">
          {{ selectedItem.description }}
        </div>

        <!-- Bottom Sheet Actions -->
        <div v-if="canManage" class="pt-4 border-t border-zinc-800 flex items-center gap-2">
          <UButton
            label="Edit Product"
            icon="i-lucide-edit"
            size="sm"
            color="neutral"
            variant="outline"
            class="flex-1 font-semibold"
            @click="openEditItem(selectedItem)"
          />
          <UButton
            label="Delete"
            icon="i-lucide-trash-2"
            size="sm"
            color="error"
            variant="ghost"
            @click="handleDeleteItem(selectedItem)"
          />
        </div>
      </div>
    </AdminBottomSheet>

    <!-- ===================================================================== -->
    <!-- Template Create / Edit Modals                                         -->
    <!-- ===================================================================== -->
    <AdminFullScreenModal
      v-model="isCreateTemplateOpen"
      title="Create Starter Pack Template"
      description="Define a new industry starter pack with custom product blueprints."
      max-width="max-w-xl"
    >
      <div class="space-y-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Template Name <span class="text-rose-400">*</span></label>
          <UInput
            v-model="templateForm.name"
            placeholder="e.g. Supermarket & Provisions, Pharmacy OTC"
            size="sm"
            @input="onTemplateNameInput"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Unique Slug <span class="text-rose-400">*</span></label>
            <UInput v-model="templateForm.slug" placeholder="e.g. supermarket-provisions" size="sm" />
            <span class="text-[10px] text-zinc-500 font-mono">Used for Redis keys and API URLs</span>
          </div>

          <div class="flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-zinc-300">Icon Name</label>
              <div class="flex items-center gap-1.5 text-[11px] text-zinc-400">
                <span>Preview:</span>
                <UIcon :name="getTemplateIcon(templateForm.icon)" class="size-4 text-emerald-400" />
              </div>
            </div>
            <UInput v-model="templateForm.icon" placeholder="shopping-cart, pill, sparkles" size="sm" />
            <div class="flex items-center gap-1 flex-wrap mt-0.5">
              <span class="text-[10px] text-zinc-500">Suggestions:</span>
              <button
                v-for="suggested in ['shopping-cart', 'pill', 'sparkles', 'package', 'store', 'shirt']"
                :key="suggested"
                type="button"
                class="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition"
                @click="templateForm.icon = suggested"
              >
                {{ suggested }}
              </button>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Description</label>
          <UTextarea
            v-model="templateForm.description"
            placeholder="Brief overview of goods included in this starter pack..."
            :rows="3"
            size="sm"
          />
        </div>

        <div class="pt-4 border-t border-zinc-800 flex items-center justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isCreateTemplateOpen = false" />
          <UButton label="Create Template" color="primary" size="sm" :loading="isSubmitting" @click="handleSaveTemplate" />
        </div>
      </div>
    </AdminFullScreenModal>

    <AdminFullScreenModal
      v-model="isEditTemplateOpen"
      title="Edit Starter Pack Template"
      description="Update template metadata and display options."
      max-width="max-w-xl"
    >
      <div class="space-y-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Template Name <span class="text-rose-400">*</span></label>
          <UInput v-model="templateForm.name" size="sm" />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Unique Slug <span class="text-rose-400">*</span></label>
            <UInput v-model="templateForm.slug" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-zinc-300">Icon Name</label>
              <div class="flex items-center gap-1.5 text-[11px] text-zinc-400">
                <span>Preview:</span>
                <UIcon :name="getTemplateIcon(templateForm.icon)" class="size-4 text-emerald-400" />
              </div>
            </div>
            <UInput v-model="templateForm.icon" placeholder="shopping-cart, pill, sparkles" size="sm" />
            <div class="flex items-center gap-1 flex-wrap mt-0.5">
              <span class="text-[10px] text-zinc-500">Suggestions:</span>
              <button
                v-for="suggested in ['shopping-cart', 'pill', 'sparkles', 'package', 'store', 'shirt']"
                :key="suggested"
                type="button"
                class="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition"
                @click="templateForm.icon = suggested"
              >
                {{ suggested }}
              </button>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Description</label>
          <UTextarea v-model="templateForm.description" :rows="3" size="sm" />
        </div>

        <div class="pt-4 border-t border-zinc-800 flex items-center justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isEditTemplateOpen = false" />
          <UButton label="Save Changes" color="primary" size="sm" :loading="isSubmitting" @click="handleUpdateTemplate" />
        </div>
      </div>
    </AdminFullScreenModal>

    <!-- ===================================================================== -->
    <!-- Item Create / Edit Modals                                             -->
    <!-- ===================================================================== -->
    <AdminFullScreenModal
      v-model="isCreateItemOpen"
      :title="`Add Product to ${selectedTemplate?.name}`"
      description="Add a new catalog product with suggested market price and barcode."
      max-width="max-w-xl"
    >
      <div class="space-y-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Product Name <span class="text-rose-400">*</span></label>
          <UInput v-model="itemForm.name" placeholder="e.g. Indomie Super Pack 120g" size="sm" />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Barcode / EAN-13</label>
            <UInput v-model="itemForm.barcode" placeholder="e.g. 089686120110" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Category</label>
            <UInput v-model="itemForm.category" placeholder="e.g. Noodles & Pasta" size="sm" />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Suggested Price (₦)</label>
            <UInput v-model="itemForm.suggested_price_naira" type="number" step="any" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Cost Price (₦)</label>
            <UInput v-model="itemForm.cost_price_naira" type="number" step="any" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Default Unit</label>
            <select
              v-model="itemForm.unit_in"
              class="w-full h-8 px-2.5 rounded-md bg-zinc-900 border border-zinc-800 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option v-for="u in supportedUnits" :key="u.value" :value="u.value">
                {{ u.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Description</label>
          <UTextarea v-model="itemForm.description" placeholder="Product size, flavor, packaging details..." :rows="2" size="sm" />
        </div>

        <div class="pt-4 border-t border-zinc-800 flex items-center justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isCreateItemOpen = false" />
          <UButton label="Add Product" color="primary" size="sm" :loading="isSubmitting" @click="handleSaveItem" />
        </div>
      </div>
    </AdminFullScreenModal>

    <AdminFullScreenModal
      v-model="isEditItemOpen"
      title="Edit Catalog Product"
      description="Update product name, barcode, prices, or unit."
      max-width="max-w-xl"
    >
      <div class="space-y-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Product Name <span class="text-rose-400">*</span></label>
          <UInput v-model="itemForm.name" size="sm" />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Barcode / EAN-13</label>
            <UInput v-model="itemForm.barcode" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Category</label>
            <UInput v-model="itemForm.category" size="sm" />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Suggested Price (₦)</label>
            <UInput v-model="itemForm.suggested_price_naira" type="number" step="any" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Cost Price (₦)</label>
            <UInput v-model="itemForm.cost_price_naira" type="number" step="any" size="sm" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Default Unit</label>
            <select
              v-model="itemForm.unit_in"
              class="w-full h-8 px-2.5 rounded-md bg-zinc-900 border border-zinc-800 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option v-for="u in supportedUnits" :key="u.value" :value="u.value">
                {{ u.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Description</label>
          <UTextarea v-model="itemForm.description" :rows="2" size="sm" />
        </div>

        <div class="pt-4 border-t border-zinc-800 flex items-center justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isEditItemOpen = false" />
          <UButton label="Save Changes" color="primary" size="sm" :loading="isSubmitting" @click="handleUpdateItem" />
        </div>
      </div>
    </AdminFullScreenModal>
  </div>
</template>
