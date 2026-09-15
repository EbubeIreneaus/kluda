<script setup lang="ts">
import { ref, computed, nextTick, onUnmounted } from "vue";

const props = defineProps<{
  activeProducts: any[];
  isPrinterConnected: boolean;
  printerName: string;
}>();

const emit = defineEmits<{
  (e: "scan-barcode", code: string): void;
  (e: "add-product", product: any): void;
  (e: "open-printer"): void;
}>();

const { format } = useFormatCurrency();

const searchQuery = ref("");
const barcodeRef = ref<any>();
const showSearchResults = ref(false);
const videoRef = ref<HTMLVideoElement>();

const {
  isCameraActive,
  isCameraLoading,
  hasTorch,
  isTorchActive,
  isNativeEngine,
  startScanner,
  stopScanner,
  toggleTorch,
  triggerAutofocus,
} = useBarcodeScanner({
  cooldownMs: 1500,
  throttleMs: 100,
  playBeep: false,
  vibrate: false,
});

const searchResults = computed(() => {
  if (!searchQuery.value || searchQuery.value.length < 2) return [];
  const q = searchQuery.value.toLowerCase();
  return props.activeProducts
    .filter(
      (p: any) =>
        (p.name && p.name.toLowerCase().includes(q)) ||
        (p.barcode_id && p.barcode_id.includes(q))
    )
    .slice(0, 6);
});

function focusBarcode() {
  nextTick(() => {
    const inputEl =
      barcodeRef.value?.$el?.querySelector("input") || barcodeRef.value?.$el;
    if (inputEl && typeof inputEl.focus === "function") {
      inputEl.focus();
    }
  });
}

function handleBarcodeScan() {
  const query = searchQuery.value.trim();
  if (!query) return;

  let product = props.activeProducts.find((p: any) => p.barcode_id === query);

  if (!product) {
    product = props.activeProducts.find(
      (p: any) => p.name.toLowerCase() === query.toLowerCase()
    );
  }

  if (!product && searchResults.value.length === 1 && searchResults.value[0]) {
    product = searchResults.value[0];
  }

  if (product) {
    emit("scan-barcode", product.barcode_id);
  } else {
    emit("scan-barcode", query);
  }

  searchQuery.value = "";
  showSearchResults.value = false;
  focusBarcode();
}

function onBarcodeKeydown(e: KeyboardEvent) {
  if (e.key === "Enter") {
    handleBarcodeScan();
  }
}

function handleSelectSearchProduct(product: any) {
  emit("add-product", product);
  searchQuery.value = "";
  showSearchResults.value = false;
  focusBarcode();
}

function handleSearchBlur() {
  setTimeout(() => {
    showSearchResults.value = false;
  }, 200);
}

async function startCameraScanner() {
  await nextTick();
  if (videoRef.value) {
    await startScanner(videoRef.value, (code) => {
      emit("scan-barcode", code);
    });
  }
}

function stopCameraScanner() {
  stopScanner();
}

function toggleCameraScanner() {
  if (isCameraActive.value) {
    stopCameraScanner();
  } else {
    startCameraScanner();
  }
}

onUnmounted(() => {
  stopCameraScanner();
});

defineExpose({
  focusBarcode,
});
</script>

<template>
  <div class="space-y-3">
    <div class="relative">
      <!-- Status Top Bar (Scanner Active + Thermal Printer Status) -->
      <div class="flex items-center justify-between gap-2 mb-1.5">
        <div class="flex items-center gap-1.5">
          <span class="relative flex h-2.5 w-2.5">
            <span
              class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"
            />
            <span
              class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"
            />
          </span>
          <span class="text-xs font-medium text-green-600 dark:text-green-400">
            Scanner Active
          </span>
        </div>

        <!-- Thermal Printer Hardware Status Indicator -->
        <button
          type="button"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition cursor-pointer"
          :class="[
            isPrinterConnected
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20'
              : 'bg-neutral-800 text-neutral-400 border-neutral-700 hover:text-neutral-200',
          ]"
          @click="emit('open-printer')"
        >
          <UIcon name="i-lucide-printer" class="w-3.5 h-3.5" />
          <span>{{
            isPrinterConnected ? printerName : "Connect Printer"
          }}</span>
          <span
            v-if="isPrinterConnected"
            class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"
          />
        </button>
      </div>

      <!-- Main Input Bar + Camera Toggle -->
      <div class="flex items-center gap-2">
        <UButton
          :color="isCameraActive ? 'error' : 'primary'"
          variant="solid"
          size="xl"
          :icon="isCameraActive ? 'i-lucide-camera-off' : 'i-lucide-camera'"
          class="shrink-0 cursor-pointer"
          @click="toggleCameraScanner"
        />
        <div class="flex-1 scanner-active rounded-xl">
          <UInput
            ref="barcodeRef"
            v-model="searchQuery"
            placeholder="Enter name or scan barcode..."
            icon="i-lucide-scan-barcode"
            size="xl"
            @focus="showSearchResults = true"
            @blur="handleSearchBlur"
            @keydown="onBarcodeKeydown"
          />
        </div>
      </div>

      <!-- Camera Scanner Stream Overlay -->
      <div
        v-show="isCameraActive"
        class="overflow-hidden bg-black flex items-center justify-center mt-2.5 fixed inset-0 z-[60] p-4 flex flex-col xl:relative xl:inset-auto xl:z-10 xl:aspect-video xl:max-h-64 xl:rounded-xl xl:border xl:border-(--ui-border) xl:p-0 xl:mt-2.5"
      >
        <!-- Camera Controls -->
        <div class="absolute top-3 right-3 flex items-center gap-2 z-[70]">
          <span
            v-if="isNativeEngine"
            class="text-[10px] font-bold px-2.5 py-1 rounded-full bg-emerald-500/80 backdrop-blur-md text-white border border-emerald-400/40 shadow-lg tracking-wider uppercase font-mono"
          >
            Fast ML
          </span>

          <button
            v-if="hasTorch"
            type="button"
            class="size-10 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-lg active:scale-95"
            :class="{ 'bg-amber-500! text-black! border-amber-400! shadow-amber-500/50': isTorchActive }"
            title="Toggle Flashlight"
            @click="toggleTorch"
          >
            <UIcon :name="isTorchActive ? 'i-lucide-zap' : 'i-lucide-zap-off'" class="size-5" />
          </button>

          <button
            type="button"
            class="size-10 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer shadow-lg active:scale-95"
            title="Close Camera"
            @click="stopCameraScanner"
          >
            <UIcon name="i-lucide-x" class="size-5" />
          </button>
        </div>

        <!-- Camera Loading Spinner -->
        <div
          v-if="isCameraLoading"
          class="absolute inset-0 bg-black/85 flex flex-col items-center justify-center gap-2 z-[65] text-zinc-300"
        >
          <UIcon name="i-lucide-loader-2" class="size-7 animate-spin text-primary-400" />
          <span class="text-xs font-medium">Starting camera...</span>
        </div>

        <video
          ref="videoRef"
          class="w-full h-full object-cover rounded-xl cursor-pointer"
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
          <div
            class="w-2/3 h-1/3 border-2 border-dashed border-emerald-500 rounded-lg opacity-65 relative transition hover:opacity-100"
          >
            <div
              class="absolute inset-x-0 h-0.5 bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]"
              style="top: 50%"
            />
            <span class="absolute -bottom-5 inset-x-0 text-center text-[10px] text-emerald-400 font-medium tracking-wide drop-shadow">
              Tap to Focus
            </span>
          </div>
        </div>
      </div>

      <!-- Search Results Dropdown -->
      <Transition name="fade">
        <div
          v-if="showSearchResults && searchResults.length"
          class="relative xl:absolute z-50 xl:top-full xl:mt-1 mt-2 w-full rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xl overflow-hidden"
        >
          <button
            v-for="product in searchResults"
            :key="product.slug"
            type="button"
            class="flex items-center justify-between w-full px-4 py-3 text-left hover:bg-(--ui-bg-accented) transition border-b border-(--ui-border)/50 last:border-0 cursor-pointer"
            @mousedown.prevent="handleSelectSearchProduct(product)"
          >
            <div>
              <p class="text-sm font-medium text-(--ui-text-highlighted)">
                {{ product.name }}
              </p>
              <p class="text-xs text-(--ui-text-dimmed) font-mono mt-0.5">
                {{ product.barcode_id }}
              </p>
            </div>
            <span
              class="text-sm font-semibold text-green-600 dark:text-green-400"
            >
              {{ format(product.unit_price) }}
            </span>
          </button>
        </div>
      </Transition>
    </div>
  </div>
</template>
