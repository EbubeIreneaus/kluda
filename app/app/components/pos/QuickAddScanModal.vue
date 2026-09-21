<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useProductsStore } from "~/stores/product";

const props = defineProps<{
  open: boolean;
  barcode: string | null;
  initialName?: string;
}>();

const emit = defineEmits<{
  (e: "update:open", val: boolean): void;
  (e: "product-added", product: any): void;
}>();

const { api } = useApi();
const productStore = useProductsStore();
const toast = useToast();

const name = ref("");
const price = ref<number | null>(null);
const unit = ref("piece");
const isLookingUp = ref(false);
const isSaving = ref(false);
const catalogMatch = ref<{ name: string; category?: string; suggested_price?: number } | null>(null);

const nameInputRef = ref<any>();
const priceInputRef = ref<any>();

const commonUnits = ["piece", "pack", "bottle", "can", "kg", "carton", "bag", "sachet"];

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      name.value = props.initialName || "";
      price.value = null;
      unit.value = "piece";
      catalogMatch.value = null;
      isSaving.value = false;

      if (props.barcode && props.barcode.trim()) {
        await lookupBarcode(props.barcode.trim());
      } else {
        // Opened from manual typing: focus price if name is prefilled, else focus name
        await nextTick();
        if (name.value) {
          focusInput(priceInputRef);
        } else {
          focusInput(nameInputRef);
        }
      }
    }
  }
);

async function lookupBarcode(code: string) {
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    await nextTick();
    focusInput(name.value ? priceInputRef : nameInputRef);
    return;
  }

  isLookingUp.value = true;
  try {
    const res = await api<any>(`/catalog-templates/lookup?barcode=${encodeURIComponent(code)}`);
    if (res?.found) {
      name.value = res.name || name.value;
      if (res.unit_in) unit.value = res.unit_in;
      if (res.suggested_price && !price.value) {
        price.value = Math.round(res.suggested_price / 100);
      }
      catalogMatch.value = {
        name: res.name,
        category: res.category,
        suggested_price: res.suggested_price
      };
      await nextTick();
      focusInput(priceInputRef);
    } else {
      await nextTick();
      focusInput(name.value ? priceInputRef : nameInputRef);
    }
  } catch {
    await nextTick();
    focusInput(name.value ? priceInputRef : nameInputRef);
  } finally {
    isLookingUp.value = false;
  }
}

function focusInput(refElement: any) {
  const el = refElement.value?.$el?.querySelector("input") || refElement.value?.$el;
  if (el && typeof el.focus === "function") {
    el.focus();
    if (typeof el.select === "function") el.select();
  }
}

async function handleSaveAndAdd() {
  const cleanName = name.value.trim();
  if (!cleanName) {
    toast.add({
      title: "Product Name Required",
      description: "Please enter a name for this product.",
      color: "error"
    });
    focusInput(nameInputRef);
    return;
  }

  const numericPrice = Number(price.value);
  if (!numericPrice || numericPrice <= 0) {
    toast.add({
      title: "Selling Price Required",
      description: "Please enter a valid selling price.",
      color: "error"
    });
    focusInput(priceInputRef);
    return;
  }

  isSaving.value = true;
  try {
    const newProduct = await productStore.addQuickProduct({
      name: cleanName,
      barcode_id: props.barcode || null,
      unit_price: Math.round(numericPrice * 100),
      unit_in: unit.value || "piece"
    });

    toast.add({
      title: "Added to Cart & Inventory",
      description: `${cleanName} is ready to sell!`,
      color: "success",
      icon: "i-lucide-check-circle"
    });

    emit("product-added", newProduct);
    emit("update:open", false);
  } catch (err: any) {
    toast.add({
      title: "Error Saving Product",
      description: err?.message || "Could not save product.",
      color: "error"
    });
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <AppBottomSheet
    :model-value="open"
    title="Quick Add Product"
    :description="barcode ? 'New item scanned! Set a selling price to ring it up.' : 'Add a new product to your cart and inventory.'"
    maxWidth="max-w-md"
    @update:model-value="emit('update:open', $event)"
  >
    <form class="space-y-4" @submit.prevent="handleSaveAndAdd">
      <!-- Barcode / Source Pill -->
      <div v-if="barcode" class="flex items-center justify-between p-2.5 rounded-xl bg-(--ui-bg-accented)/50 border border-(--ui-border) text-xs">
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-scan-barcode" class="size-4 text-primary-500 shrink-0" />
          <span class="font-mono font-bold text-(--ui-text-highlighted)">{{ barcode }}</span>
        </div>
        <span
          v-if="isLookingUp"
          class="flex items-center gap-1 text-[11px] text-primary-600 dark:text-primary-400 font-medium"
        >
          <UIcon name="i-lucide-loader-2" class="size-3 animate-spin" />
          Looking up name...
        </span>
        <span
          v-else-if="catalogMatch"
          class="flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20"
        >
          <UIcon name="i-lucide-check" class="size-3" />
          Catalog Matched
        </span>
        <span v-else class="text-[11px] text-(--ui-text-dimmed)">
          New barcode
        </span>
      </div>

      <!-- Product Name Input -->
      <div class="space-y-1">
        <label class="text-xs font-bold text-(--ui-text-highlighted) flex items-center justify-between">
          <span>Product Name <span class="text-rose-500">*</span></span>
          <span v-if="catalogMatch?.category" class="text-[10px] text-(--ui-text-dimmed) font-normal">
            {{ catalogMatch.category }}
          </span>
        </label>
        <UInput
          ref="nameInputRef"
          v-model="name"
          placeholder="e.g. Milo Refill 500g, Cold Malt..."
          size="lg"
          icon="i-lucide-tag"
          :disabled="isSaving"
        />
      </div>

      <!-- Selling Price Input -->
      <div class="space-y-1">
        <label class="text-xs font-bold text-(--ui-text-highlighted) flex items-center justify-between">
          <span>Selling Price (₦) <span class="text-rose-500">*</span></span>
          <span v-if="catalogMatch?.suggested_price" class="text-[10px] text-emerald-600 dark:text-emerald-400">
            Suggested: ₦{{ (catalogMatch.suggested_price / 100).toLocaleString() }}
          </span>
        </label>
        <UInput
          ref="priceInputRef"
          v-model="price"
          type="number"
          step="any"
          min="1"
          placeholder="0.00"
          size="xl"
          icon="i-lucide-banknote"
          class="font-mono text-base font-bold"
          :disabled="isSaving"
          @keydown.enter.prevent="handleSaveAndAdd"
        />
      </div>

      <!-- Unit Selector -->
      <div class="space-y-1.5">
        <label class="text-xs font-bold text-(--ui-text-highlighted)">
          Sold Per (Unit)
        </label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="u in commonUnits"
            :key="u"
            type="button"
            class="px-2.5 py-1 text-xs rounded-lg border transition cursor-pointer font-medium"
            :class="[
              unit === u
                ? 'bg-primary-500 text-white border-primary-600 shadow-xs'
                : 'bg-(--ui-bg) border-(--ui-border) text-(--ui-text-muted) hover:bg-(--ui-bg-accented)'
            ]"
            @click="unit = u"
          >
            {{ u }}
          </button>
        </div>
      </div>

      <!-- Zero-Hassle Info Banner -->
      <div class="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-500/20 text-[11px] text-emerald-800 dark:text-emerald-300 flex items-start gap-2">
        <UIcon name="i-lucide-sparkles" class="size-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
        <p class="leading-relaxed">
          This product is saved to your inventory immediately with stock quantity <strong>0</strong>. You can adjust stock or add cost prices later whenever you have time.
        </p>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2 pt-2">
        <UButton
          type="button"
          color="neutral"
          variant="ghost"
          size="lg"
          class="flex-1"
          :disabled="isSaving"
          @click="emit('update:open', false)"
        >
          Cancel
        </UButton>
        <UButton
          type="submit"
          color="primary"
          size="lg"
          class="flex-2 font-bold cursor-pointer"
          :loading="isSaving"
        >
          <UIcon name="i-lucide-check-circle" class="size-4 mr-1.5" />
          Add & Ring Up
        </UButton>
      </div>
    </form>
  </AppBottomSheet>
</template>
