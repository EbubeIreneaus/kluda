<script setup lang="ts">
import { ref, computed } from 'vue'

definePageMeta({ layout: 'marchant' })

const auth = useAuthStore()
const toast = useToast()
const { api } = useApi()

const search = ref('')
const showCreateModal = ref(false)
const isSubmitting = ref(false)

const newStore = ref({
  name: '',
  category: 'General Retail',
  address: '',
  phone: '',
  website: ''
})

const categories = [
  'General Retail',
  'Supermarket & Grocery',
  'Pharmacy & Chemist',
  'Fashion Boutique',
  'Electronics & Gadgets',
  'Restaurant & Cafe',
  'Cosmetics & Beauty',
  'Hardware & Building Materials'
]

const filteredStores = computed(() => {
  if (!search.value) return auth.stores
  const q = search.value.toLowerCase()
  return auth.stores.filter(s =>
    s.name.toLowerCase().includes(q) ||
    s.category.toLowerCase().includes(q) ||
    (s.address && s.address.toLowerCase().includes(q))
  )
})

async function handleCreateStore() {
  if (!newStore.value.name) {
    toast.add({ title: 'Store name is required', color: 'warning' })
    return
  }

  isSubmitting.value = true
  try {
    const payload = {
      name: newStore.value.name,
      category: newStore.value.category,
      address: newStore.value.address || undefined,
      phone: newStore.value.phone || undefined,
      website: newStore.value.website || undefined
    }

    const created = await api<any>('/stores', {
      method: 'POST',
      body: payload
    })

    toast.add({
      title: 'Store Branch Created!',
      description: `${created.name || newStore.value.name} is ready for operations.`,
      color: 'success'
    })

    showCreateModal.value = false
    newStore.value = {
      name: '',
      category: 'General Retail',
      address: '',
      phone: '',
      website: ''
    }

    await auth.fetchMe()
  } catch (err: any) {
    toast.add({
      title: 'Failed to create store',
      description: err?.data?.detail || err?.message || 'Server error',
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

function handleLaunchTerminal(storeId: string) {
  auth.switchStore(storeId)
  navigateTo('/')
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
  toast.add({ title: 'Store ID copied', color: 'success' })
}
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black tracking-tight text-(--ui-text-highlighted)">
          Store Branches
        </h1>
        <p class="text-sm text-(--ui-text-muted) mt-1">
          Manage all retail branches, outlets, cashier access, and location settings.
        </p>
      </div>

      <UButton
        color="primary"
        size="md"
        class="font-bold px-4 py-2.5"
        @click="showCreateModal = true"
      >
        <UIcon name="i-lucide-plus" class="w-4 h-4 mr-1.5" />
        Add Store Branch
      </UButton>
    </div>

    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <UInput
        v-model="search"
        placeholder="Search branches by name, category, location..."
        icon="i-lucide-search"
        class="max-w-sm w-full"
      />
    </div>

    <div
      v-if="filteredStores.length === 0"
      class="py-16 text-center rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)"
    >
      <UIcon
        name="i-lucide-store"
        class="w-12 h-12 mx-auto mb-3 text-zinc-500"
      />
      <h3 class="text-base font-bold text-(--ui-text-highlighted)">
        No Store Branches Found
      </h3>
      <p class="text-sm text-(--ui-text-muted) mt-1 mb-4">
        {{ search ? 'No branches matched your search query.' : 'Create your first store branch to start.' }}
      </p>
      <UButton
        color="primary"
        size="md"
        class="font-bold px-5 py-2.5"
        @click="showCreateModal = true"
      >
        Create Store Branch
      </UButton>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="store in filteredStores"
        :key="store.store_id"
        class="rounded-3xl p-6 border border-(--ui-border) bg-(--ui-bg-elevated) transition-all duration-200 flex flex-col justify-between hover:border-amber-500/50 shadow-xs"
      >
        <div>
          <div class="flex items-start justify-between gap-2 mb-3">
            <div
              class="w-10 h-10 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold"
            >
              <UIcon name="i-lucide-store" class="w-5 h-5" />
            </div>
            <span
              v-if="store.is_owner"
              class="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20"
            >
              Owner
            </span>
            <span
              v-else
              class="text-[10px] px-2.5 py-0.5 rounded-full font-medium bg-zinc-500/10 text-zinc-400"
            >
              {{ store.role }}
            </span>
          </div>

          <h3 class="text-lg font-bold text-(--ui-text-highlighted)">
            {{ store.name }}
          </h3>
          <p class="text-xs text-amber-400 font-semibold mt-0.5">
            {{ store.category }}
          </p>

          <div class="mt-4 pt-3 border-t border-(--ui-border) space-y-2.5 text-xs">
            <div>
              <span class="text-(--ui-text-muted)">Store ID:</span>
              <div
                class="flex items-center justify-between mt-1 p-2 rounded-xl bg-(--ui-bg-accented)/40 border border-(--ui-border)"
              >
                <code class="font-mono text-[11px] text-emerald-400 truncate max-w-[200px]">{{ store.store_id }}</code>
                <button
                  type="button"
                  class="text-(--ui-text-muted) hover:text-emerald-400 p-1 transition"
                  title="Copy Store ID"
                  @click="copyToClipboard(store.store_id)"
                >
                  <UIcon name="i-lucide-copy" class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div v-if="store.address" class="text-(--ui-text-muted)">
              <span class="font-semibold text-(--ui-text-highlighted)">Address:</span>
              {{ store.address }}
            </div>
            <div v-if="store.phone" class="text-(--ui-text-muted)">
              <span class="font-semibold text-(--ui-text-highlighted)">Phone:</span>
              {{ store.phone }}
            </div>
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-(--ui-border) flex items-center justify-between gap-2">
          <NuxtLink :to="`/marchant/stores/${store.store_id}`">
            <UButton
              size="sm"
              variant="soft"
              color="neutral"
              icon="i-lucide-settings-2"
              class="font-semibold"
            >
              Manage Branch
            </UButton>
          </NuxtLink>

          <UButton
            size="sm"
            variant="subtle"
            color="primary"
            icon="i-lucide-scan-barcode"
            class="font-semibold"
            @click="handleLaunchTerminal(store.store_id)"
          >
            Open POS
          </UButton>
        </div>
      </div>
    </div>

    <AppBottomSheet
      v-model="showCreateModal"
      title="Create Store Branch"
      description="Add a new store branch to your merchant account."
    >
      <form class="space-y-4" @submit.prevent="handleCreateStore">
        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Store Name *</label>
          <input
            v-model="newStore.name"
            type="text"
            required
            placeholder="e.g. Lekki Phase 1 Branch"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          />
        </div>

        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Business Category</label>
          <select
            v-model="newStore.category"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          >
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Branch Address</label>
          <input
            v-model="newStore.address"
            type="text"
            placeholder="e.g. 15 Admiralty Way, Lekki"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          />
        </div>

        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Branch Phone</label>
          <input
            v-model="newStore.phone"
            type="tel"
            placeholder="e.g. 08012345678"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          />
        </div>

        <div class="space-y-1">
          <label class="text-xs font-bold text-(--ui-text-highlighted)">Website / Social Link</label>
          <input
            v-model="newStore.website"
            type="text"
            placeholder="e.g. https://mystore.ng"
            class="w-full bg-(--ui-bg) border border-(--ui-border) rounded-xl px-3.5 py-2.5 text-sm text-(--ui-text-highlighted) outline-none focus:border-amber-500"
          />
        </div>

        <div class="flex items-center justify-end gap-3 pt-4 border-t border-(--ui-border)">
          <UButton
            type="button"
            variant="ghost"
            color="neutral"
            @click="showCreateModal = false"
          >
            Cancel
          </UButton>
          <UButton
            type="submit"
            color="primary"
            :loading="isSubmitting"
            class="font-bold px-5 py-2"
          >
            Create Branch
          </UButton>
        </div>
      </form>
    </AppBottomSheet>
  </div>
</template>
