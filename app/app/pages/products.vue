<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { getStockBadge, type ProductItem } from '~/components/products/types'
import AddProductSheet from '~/components/products/AddProductSheet.vue'
import EditProductSheet from '~/components/products/EditProductSheet.vue'
import StockAdjustSheet from '~/components/products/StockAdjustSheet.vue'
import StockHistoryModal from '~/components/products/StockHistoryModal.vue'
import StarterPackModal from '~/components/products/StarterPackModal.vue'

const { format } = useFormatCurrency()
const toast = useToast()
const auth = useAuthStore()
const productStore = useProductsStore()
const { withPinAuth } = usePinAuth()

// Modals and Active Product
const showAddModal = ref(false)
const showEditModal = ref(false)
const showAdjustModal = ref(false)
const showHistoryModal = ref(false)
const showImportModal = ref(false)
const selectedProduct = ref<ProductItem | null>(null)

// Search and Pagination
const search = ref('')
const currentPage = ref(1)
const pageSize = ref(15)

const products = computed<ProductItem[]>(() => {
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

// Store Inventory Valuation (Store Worth)
const canViewStoreWorth = computed(() => {
  return auth.isOwner || auth.hasPermission('view:profit') || auth.hasPermission('view:analytics') || auth.hasPermission('manage:all')
})
const isWorthVisible = ref(true)

const activeProducts = computed(() => products.value.filter(p => p.status === 'active'))

const totalRetailWorth = computed(() => {
  return activeProducts.value.reduce((sum, p) => {
    const qty = Math.max(0, Number(p.quantity) || 0)
    return sum + (qty * (p.price || 0))
  }, 0)
})

const totalStockUnits = computed(() => {
  return activeProducts.value.reduce((sum, p) => {
    return sum + Math.max(0, Number(p.quantity) || 0)
  }, 0)
})

const activeTooltip = ref<'worth' | 'stock' | null>(null)

const metricExplanations: Record<string, { title: string; desc: string }> = {
  worth: {
    title: 'Store Worth (Selling Value)',
    desc: 'The total money you will make if you sell every single item currently in your shop at your set selling prices.'
  },
  stock: {
    title: 'Total Stock',
    desc: 'The total number of physical pieces/units currently on your shelves across all products.'
  }
}

function toggleMetricTooltip(metric: 'worth' | 'stock') {
  activeTooltip.value = activeTooltip.value === metric ? null : metric
}

onMounted(() => {
  if (!productStore.products.length) {
    productStore.fetchProducts()
  }
})

const filteredProducts = computed(() => {
  if (!search.value) return products.value
  const q = search.value.toLowerCase()
  return products.value.filter(
    (p) =>
      p.name.toLowerCase().includes(q) ||
      p.barcode_id.toLowerCase().includes(q)
  )
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredProducts.value.length / pageSize.value))
)

const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredProducts.value.slice(start, start + pageSize.value)
})

watch(search, () => {
  currentPage.value = 1
})

function openEdit(product: ProductItem) {
  selectedProduct.value = product
  showEditModal.value = true
}

function openAdjust(product: ProductItem) {
  selectedProduct.value = product
  showAdjustModal.value = true
}

function openHistory(product: ProductItem) {
  selectedProduct.value = product
  showHistoryModal.value = true
}

async function confirmDelete(product: ProductItem) {
  await withPinAuth(
    async () => {
      try {
        await productStore.deleteProduct(product.slug)
        toast.add({
          title: 'Product removed',
          description: product.name,
          color: 'warning'
        })
      } catch (err: any) {
        toast.add({
          title: 'Error',
          description: err?.data?.detail || 'Could not delete product',
          color: 'error'
        })
      }
    },
    {
      title: 'Authorize Product Deletion',
      description: `Enter PIN to permanently delete ${product.name}`,
      requiredPermission: 'manage:product'
    }
  )
}
</script>

<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-bold text-(--ui-text-highlighted)">
          Products & Inventory
        </h2>
        <p class="text-sm text-(--ui-text-muted)">
          {{ products.length }} products in stock
        </p>
      </div>

      <div class="flex items-center gap-2">
        <UButton
          v-if="auth.hasPermission('create:product') || auth.hasPermission('manage:product')"
          class="p-2.5 font-medium"
          icon="i-lucide-plus"
          @click="showAddModal = true"
        >
          Add Product
        </UButton>
      </div>
    </div>

    <!-- High-Contrast Store Valuation Banner with Layman Tooltips -->
    <div
      v-if="canViewStoreWorth && products.length > 0"
      class="rounded-2xl border border-emerald-300/80 dark:border-emerald-500/30 bg-linear-to-r from-emerald-50/90 via-white to-emerald-50/60 dark:from-emerald-950/60 dark:via-zinc-900 dark:to-zinc-900 px-4 py-3 text-xs shadow-xs dark:shadow-md transition-colors"
    >
      <div class="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <!-- Store Worth (Primary) -->
        <div class="flex items-center gap-3">
          <div class="size-8 rounded-xl bg-emerald-100 text-emerald-700 border border-emerald-300/80 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30 flex items-center justify-center shrink-0 shadow-xs">
            <UIcon name="i-lucide-vault" class="size-4.5" />
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">
              Store Worth:
            </span>
            <span class="text-base sm:text-lg font-black text-emerald-600 dark:text-emerald-400 font-mono tracking-tight">
              <template v-if="isWorthVisible">{{ format(totalRetailWorth) }}</template>
              <template v-else>••••••••</template>
            </span>
            <button
              type="button"
              class="text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white transition-colors p-1 rounded-md hover:bg-zinc-200/60 dark:hover:bg-zinc-800/60"
              :title="isWorthVisible ? 'Hide Worth' : 'Show Worth'"
              @click="isWorthVisible = !isWorthVisible"
            >
              <UIcon :name="isWorthVisible ? 'i-lucide-eye' : 'i-lucide-eye-off'" class="size-3.5" />
            </button>
            <button
              type="button"
              class="text-zinc-500 hover:text-emerald-600 dark:text-zinc-400 dark:hover:text-emerald-400 transition-colors p-1 rounded-md hover:bg-emerald-100/60 dark:hover:bg-zinc-800/60"
              :class="{ 'text-emerald-600 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-500/10': activeTooltip === 'worth' }"
              title="Click to explain Store Worth"
              @click="toggleMetricTooltip('worth')"
            >
              <UIcon name="i-lucide-info" class="size-3.5" />
            </button>
          </div>
        </div>

        <!-- Total Stock Units -->
        <div class="flex items-center gap-1.5 text-xs text-zinc-700 dark:text-zinc-300">
          <span class="text-zinc-600 dark:text-zinc-400 font-semibold">Total Stock:</span>
          <span class="font-mono font-bold text-zinc-900 dark:text-zinc-100 text-sm">
            {{ totalStockUnits.toLocaleString() }}
          </span>
          <span class="text-zinc-500 dark:text-zinc-400 text-[11px] font-medium">units</span>
          <button
            type="button"
            class="text-zinc-400 hover:text-emerald-600 dark:text-zinc-400 dark:hover:text-emerald-400 transition-colors p-0.5 rounded hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50"
            :class="{ 'text-emerald-600 dark:text-emerald-400': activeTooltip === 'stock' }"
            title="Click to explain Total Stock"
            @click="toggleMetricTooltip('stock')"
          >
            <UIcon name="i-lucide-info" class="size-3.5" />
          </button>
        </div>
      </div>

      <!-- Expandable Layman Tooltip Ribbon on Click -->
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 -translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition-all duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-1"
      >
        <div
          v-if="activeTooltip && metricExplanations[activeTooltip]"
          class="mt-3 pt-2.5 flex items-start justify-between gap-3 text-xs bg-emerald-50/90 dark:bg-zinc-950/80 p-2.5 rounded-xl border border-emerald-200/80 dark:border-zinc-800 shadow-xs"
        >
          <div class="flex items-start gap-2.5">
            <UIcon name="i-lucide-info" class="size-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
            <div class="space-y-0.5">
              <span class="font-bold text-zinc-900 dark:text-white tracking-wide">
                {{ metricExplanations[activeTooltip]?.title }}:
              </span>
              <p class="text-zinc-700 dark:text-zinc-300 leading-relaxed">
                {{ metricExplanations[activeTooltip]?.desc }}
              </p>
            </div>
          </div>
          <button
            type="button"
            class="text-zinc-400 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-white p-1 rounded-md hover:bg-zinc-200/60 dark:hover:bg-zinc-800/50 transition-colors shrink-0"
            title="Dismiss explanation"
            @click="activeTooltip = null"
          >
            <UIcon name="i-lucide-x" class="size-3.5" />
          </button>
        </div>
      </Transition>
    </div>

    <!-- Search bar -->
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
              <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                Product
              </th>
              <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                Barcode
              </th>
              <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                Price
              </th>
              <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                Quantity
              </th>
              <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                Status
              </th>
              <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- Empty State -->
            <tr v-if="filteredProducts.length === 0">
              <td colspan="6" class="text-center py-12 px-4">
                <UIcon
                  name="i-lucide-package-search"
                  class="size-10 text-(--ui-text-dimmed) mx-auto mb-2"
                />
                <p class="text-sm font-semibold text-(--ui-text-highlighted)">
                  No products in inventory
                </p>
                <p class="text-xs text-(--ui-text-dimmed) max-w-sm mx-auto mt-1">
                  Add products with barcode scanning, starter packs, or manual entry.
                </p>
                <div class="flex items-center justify-center gap-2 pt-3">
                  <UButton
                    v-if="auth.hasPermission('create:product') || auth.hasPermission('manage:product')"
                    icon="i-lucide-package-plus"
                    size="xs"
                    variant="outline"
                    color="neutral"
                    label="Starter Packs"
                    @click="showImportModal = true"
                  />
                  <UButton
                    v-if="auth.hasPermission('create:product') || auth.hasPermission('manage:product')"
                    icon="i-lucide-plus"
                    size="xs"
                    color="primary"
                    label="Add Product"
                    @click="showAddModal = true"
                  />
                </div>
              </td>
            </tr>

            <!-- Product Rows -->
            <tr
              v-for="product in paginatedProducts"
              :key="product.slug"
              class="border-b border-(--ui-border)/50 last:border-0 hover:bg-(--ui-bg-accented)/30 transition"
            >
              <td class="py-3 px-4">
                <p class="font-medium text-(--ui-text-highlighted)">
                  {{ product.name }}
                </p>
              </td>
              <td class="py-3 px-4 font-mono text-xs text-(--ui-text-muted)">
                {{ product.barcode_id || '—' }}
              </td>
              <td class="py-3 px-4 text-right font-semibold text-(--ui-text-highlighted)">
                {{ format(product.price) }}
              </td>
              <td class="py-3 px-4 text-center">
                <span class="font-medium text-(--ui-text-highlighted)">
                  {{ product.quantity }}
                </span>
                <span class="text-(--ui-text-dimmed) text-xs ml-1">
                  {{ product.unit }}
                </span>
              </td>
              <td class="py-3 px-4 text-center">
                <UBadge
                  :color="getStockBadge(product.quantity).color"
                  variant="subtle"
                  size="xs"
                >
                  {{ getStockBadge(product.quantity).label }}
                </UBadge>
              </td>
              <td class="py-3 px-4 text-right">
                <div
                  v-if="
                    auth.hasPermission('manage:product') ||
                    auth.hasPermission('edit:product') ||
                    auth.hasPermission('delete:product') ||
                    auth.hasPermission('adjust:stock')
                  "
                  class="flex items-center justify-end gap-1"
                >
                  <UButton
                    v-if="auth.hasPermission('adjust:stock') || auth.hasPermission('manage:product')"
                    variant="ghost"
                    color="primary"
                    size="xs"
                    icon="i-lucide-boxes"
                    title="Adjust Stock"
                    @click="openAdjust(product)"
                  />
                  <UButton
                    v-if="auth.hasPermission('view:product') || auth.hasPermission('manage:product')"
                    variant="ghost"
                    color="neutral"
                    size="xs"
                    icon="i-lucide-history"
                    title="Stock History"
                    @click="openHistory(product)"
                  />
                  <UButton
                    v-if="auth.hasPermission('edit:product') || auth.hasPermission('manage:product')"
                    variant="ghost"
                    color="neutral"
                    size="xs"
                    icon="i-lucide-pencil"
                    title="Edit"
                    @click="openEdit(product)"
                  />
                  <UButton
                    v-if="auth.hasPermission('delete:product') || auth.hasPermission('manage:product')"
                    variant="ghost"
                    color="error"
                    size="xs"
                    icon="i-lucide-trash-2"
                    title="Delete"
                    @click="confirmDelete(product)"
                  />
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
        <UIcon
          name="i-lucide-package-search"
          class="size-10 text-(--ui-text-dimmed) mx-auto"
        />
        <p class="text-sm font-semibold text-(--ui-text-highlighted)">
          No products in inventory
        </p>
        <p class="text-xs text-(--ui-text-dimmed) max-w-sm mx-auto">
          Add products with barcode scanning, starter packs, or manual entry.
        </p>
        <div class="flex items-center justify-center gap-2 pt-1">
          <UButton
            v-if="auth.hasPermission('create:product') || auth.hasPermission('manage:product')"
            icon="i-lucide-plus"
            size="xs"
            color="primary"
            label="Add Product"
            @click="showAddModal = true"
          />
        </div>
      </div>

      <div
        v-for="product in paginatedProducts"
        :key="product.slug"
        class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4 shadow-xs space-y-3"
      >
        <!-- Top: Name & Stock Badge -->
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <h3 class="font-bold text-sm text-(--ui-text-highlighted) leading-snug">
              {{ product.name }}
            </h3>
            <p
              v-if="product.barcode_id"
              class="text-xs font-mono text-(--ui-text-dimmed) mt-0.5 flex items-center gap-1"
            >
              <UIcon name="i-lucide-scan-barcode" class="size-3.5" />
              {{ product.barcode_id }}
            </p>
          </div>
          <UBadge
            :color="getStockBadge(product.quantity).color"
            variant="subtle"
            size="sm"
            class="shrink-0 font-medium"
          >
            {{ getStockBadge(product.quantity).label }}
          </UBadge>
        </div>

        <!-- Middle: Price & Available Quantity -->
        <div class="grid grid-cols-2 gap-2 py-2 px-3 rounded-xl bg-(--ui-bg-accented)/40 border border-(--ui-border)/50">
          <div>
            <span class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider block">
              Unit Price
            </span>
            <span class="text-base font-black text-(--ui-text-highlighted) font-mono">
              {{ format(product.price) }}
            </span>
          </div>
          <div class="text-right">
            <span class="text-[10px] uppercase font-bold text-(--ui-text-dimmed) tracking-wider block">
              In Stock
            </span>
            <span class="text-sm font-bold text-(--ui-text-highlighted)">
              {{ product.quantity }}
              <span class="text-xs font-normal text-(--ui-text-dimmed)">
                {{ product.unit }}
              </span>
            </span>
          </div>
        </div>

        <!-- Bottom: Action Buttons for Mobile -->
        <div
          v-if="
            auth.hasPermission('manage:product') ||
            auth.hasPermission('edit:product') ||
            auth.hasPermission('delete:product') ||
            auth.hasPermission('adjust:stock')
          "
          class="grid grid-cols-4 gap-1.5 pt-1"
        >
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
        <span class="font-bold text-(--ui-text-highlighted)">
          {{ (currentPage - 1) * pageSize + 1 }}
        </span>
        to
        <span class="font-bold text-(--ui-text-highlighted)">
          {{ Math.min(currentPage * pageSize, filteredProducts.length) }}
        </span>
        of
        <span class="font-bold text-(--ui-text-highlighted)">
          {{ filteredProducts.length }}
        </span>
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

    <!-- Sub-component Modals & Bottom Sheets -->
    <AddProductSheet
      v-model="showAddModal"
      @product-added="productStore.fetchProducts()"
    />

    <EditProductSheet
      v-model="showEditModal"
      :product="selectedProduct"
      @product-updated="productStore.fetchProducts()"
    />

    <StockAdjustSheet
      v-model="showAdjustModal"
      :product="selectedProduct"
      @stock-adjusted="productStore.fetchProducts()"
    />

    <StockHistoryModal
      v-model="showHistoryModal"
      :product="selectedProduct"
    />

    <StarterPackModal
      v-model="showImportModal"
      @catalog-imported="productStore.fetchProducts()"
    />
  </div>
</template>
