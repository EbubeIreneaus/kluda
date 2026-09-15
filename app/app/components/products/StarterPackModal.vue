<script setup lang="ts">
import { ref, watch } from 'vue'

const open = defineModel<boolean>({ default: false })
const emit = defineEmits<{
  (e: 'catalog-imported'): void
}>()

const toast = useToast()
const { api } = useApi()
const auth = useAuthStore()
const productStore = useProductsStore()

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

async function fetchTemplates() {
  if (catalogTemplates.value.length > 0) return
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

watch(open, (isOpen) => {
  if (isOpen) {
    confirmingTemplate.value = null
    fetchTemplates()
  }
})

async function handleImportCatalog(template: any) {
  const storeId = auth.store_id
  if (!storeId) {
    toast.add({
      title: 'Error',
      description: 'Store ID not found',
      color: 'error'
    })
    return
  }

  importingSlug.value = template.slug
  try {
    const res = await api<any>(
      `/catalog-templates/${template.slug}/import?store_id=${storeId}`,
      { method: 'POST' }
    )

    toast.add({
      title: 'Import Successful',
      description: res?.message || `Imported products from ${template.name}`,
      color: 'success'
    })

    open.value = false
    confirmingTemplate.value = null
    await productStore.fetchProducts()
    emit('catalog-imported')
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
</script>

<template>
  <AppFullScreenModal
    v-model="open"
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
          <div
            class="w-9 h-9 rounded-lg bg-primary-500/20 flex items-center justify-center text-primary-500 shrink-0"
          >
            <UIcon
              :name="getTemplateIcon(confirmingTemplate.icon)"
              class="size-5"
            />
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
        <UIcon
          name="i-lucide-package-x"
          class="size-8 text-(--ui-text-dimmed) mx-auto"
        />
        <p class="text-xs font-semibold text-(--ui-text-highlighted)">
          No starter packs available
        </p>
        <p class="text-[11px] text-(--ui-text-muted)">
          Please check back later or add products manually.
        </p>
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
            <div
              class="w-10 h-10 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-500 shrink-0 mt-0.5"
            >
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
</template>
