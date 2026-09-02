<script setup lang="ts">
import { ref } from "vue";

definePageMeta({ layout: "dashboard" });

const ownerStore = useOwnerStore();
const toast = useToast();

const showCreateModal = ref(false);
const isSubmitting = ref(false);

const {form:newStore, reset: resetNewStore} = useForm({
  name: "",
  category: "General Retail",
  address: "",
  phone: "",
  website: undefined,
});

const categories = [
  "General Retail",
  "Supermarket & Grocery",
  "Pharmacy & Chemist",
  "Fashion Boutique",
  "Electronics & Gadgets",
  "Restaurant & Cafe",
  "Cosmetics & Beauty",
  "Hardware & Building Materials",
];

async function handleCreateStore() {
  if (!newStore.value.name) {
    toast.add({ title: "Store name is required", color: "warning" });
    return;
  }

  isSubmitting.value = true;
  try {
    const created = await ownerStore.createStore(newStore.value);
    toast.add({
      title: "Store Created!",
      description: `${created.name} is ready for cashier assignment.`,
      color: "success",
    });

    showCreateModal.value = false;
    resetNewStore()
  } catch (err: any) {
    toast.add({
      title: "Failed to create store",
      description: err?.data?.detail || "Server error",
      color: "error",
    });
  } finally {
    isSubmitting.value = false;
  }
}

function copyToClipboard(text: string, label: string) {
  navigator.clipboard.writeText(text);
  toast.add({ title: `${label} copied to clipboard`, color: "success" });
}
</script>

<template>
  <div class="space-y-6">
    <div
      class="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
    >
      <div>
        <h1 class="text-2xl font-bold text-(--ui-text-highlighted)">
          Store Branches
        </h1>
        <p class="text-sm text-(--ui-text-muted) mt-1">
          Manage all your retail outlets, branches, and register locations.
        </p>
      </div>

      <UButton
        color="primary"
        size="md"
        class="font-semibold px-4 py-2.5"
        @click="showCreateModal = true"
      >
        <UIcon name="i-lucide-plus" class="w-4 h-4 mr-1.5" />
        Create Store Branch
      </UButton>
    </div>

    <div
      v-if="ownerStore.activeStores.length === 0"
      class="py-16 text-center rounded-3xl border border-(--ui-border) glass-panel"
    >
      <UIcon
        name="i-lucide-store"
        class="w-12 h-12 mx-auto mb-3 text-slate-500"
      />
      <h3 class="text-base font-bold text-(--ui-text-highlighted)">
        No Stores Found
      </h3>
      <p class="text-sm text-(--ui-text-muted) mt-1 mb-4">
        You haven't created any stores yet.
      </p>
      <UButton
        color="primary"
        size="md"
        class="font-semibold px-5 py-2.5"
        @click="showCreateModal = true"
      >
        Create First Store
      </UButton>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="store in ownerStore.activeStores"
        :key="store.store_id"
        class="rounded-3xl p-6 border glass-panel transition-all duration-200 flex flex-col justify-between"
        :class="
          store.store_id === ownerStore.selectedStoreId
            ? 'border-emerald-500 shadow-lg shadow-emerald-500/10'
            : 'border-(--ui-border)'
        "
      >
        <div>
          <div class="flex items-start justify-between gap-2 mb-3">
            <div
              class="w-10 h-10 rounded-2xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold"
            >
              <UIcon name="i-lucide-store" class="w-5 h-5" />
            </div>
            <span
              class="text-xs px-2.5 py-0.5 rounded-full font-semibold"
              :class="
                store.status === 'active'
                  ? 'bg-emerald-500/10 text-emerald-500'
                  : 'bg-amber-500/10 text-amber-500'
              "
            >
              {{ store.status }}
            </span>
          </div>

          <h3 class="text-lg font-bold text-(--ui-text-highlighted)">
            {{ store.name }}
          </h3>
          <p class="text-xs text-emerald-500 font-semibold mt-0.5">
            {{ store.category }}
          </p>

          <div
            class="mt-4 pt-3 border-t border-(--ui-border) space-y-2 text-xs"
          >
            <div>
              <span class="text-(--ui-text-muted)">Store ID:</span>
              <div
                class="flex items-center justify-between mt-1 p-2 rounded-xl bg-(--ui-bg) border border-(--ui-border)"
              >
                <code
                  class="font-mono text-[11px] text-emerald-500 truncate max-w-[200px]"
                  >{{ store.store_id }}</code
                >
                <button
                  @click="copyToClipboard(store.store_id, 'Store ID')"
                  class="text-(--ui-text-muted) hover:text-emerald-500 p-1"
                  title="Copy Store ID"
                >
                  <UIcon name="i-lucide-copy" class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div v-if="store.address" class="text-(--ui-text-muted)">
              <span class="font-semibold text-(--ui-text)">Address:</span>
              {{ store.address }}
            </div>
            <div v-if="store.phone" class="text-(--ui-text-muted)">
              <span class="font-semibold text-(--ui-text)">Phone:</span>
              {{ store.phone }}
            </div>
          </div>
        </div>

        <div
          class="mt-6 pt-3 border-t border-(--ui-border) flex items-center justify-between"
        >
          <button
            @click="ownerStore.selectStore(store.store_id)"
            class="text-xs font-semibold px-3.5 py-2 rounded-xl transition cursor-pointer"
            :class="
              store.store_id === ownerStore.selectedStoreId
                ? 'bg-emerald-500 text-slate-950 shadow-sm'
                : 'bg-(--ui-bg-muted) text-(--ui-text-muted) hover:text-(--ui-text)'
            "
          >
            {{
              store.store_id === ownerStore.selectedStoreId
                ? "Active Branch"
                : "Select Branch"
            }}
          </button>

          <NuxtLink :to="`/dashboard/staff?store_id=${store.store_id}`">
            <UButton
              size="sm"
              variant="ghost"
              color="neutral"
              class="font-semibold px-3 py-1.5"
              trailing-icon="i-lucide-arrow-right"
            >
              View Staff
            </UButton>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Create Store Modal -->
    <UModal v-model:open="showCreateModal" title="Create New Store Branch">
      <template #body>
        <form class="space-y-4" @submit.prevent="handleCreateStore">
          <UFormField label="Store Name" required>
            <UInput
              v-model="newStore.name"
              placeholder="e.g. Ikeja Branch"
              required
            />
          </UFormField>

          <UFormField required label="Category">
            <USelect required v-model="newStore.category" :items="categories" />
          </UFormField>

          <UFormField label="Website (Optional)">
            <UInput
              v-model="newStore.website"
              placeholder="https://mystore.ng"
            />
          </UFormField>

          <UFormField required label="Physical Address">
            <UInput
              v-model="newStore.address"
              placeholder="e.g. 14 Allen Avenue, Ikeja"
              required
            />
          </UFormField>

          <UFormField label="Store Contact Phone (Optional)">
            <UInput v-model="newStore.phone" placeholder="08012345678" />
          </UFormField>

          <div class="flex justify-end gap-2 pt-4">
            <UButton
              variant="ghost"
              color="neutral"
              size="md"
              class="font-semibold px-4 py-2.5"
              @click="showCreateModal = false"
            >
              Cancel
            </UButton>
            <UButton
              type="submit"
              color="primary"
              size="md"
              class="font-semibold px-5 py-2.5"
              :loading="isSubmitting"
            >
              Create Store
            </UButton>
          </div>
        </form>
      </template>
    </UModal>
  </div>
</template>
