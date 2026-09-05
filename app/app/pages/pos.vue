<script setup lang="ts">
definePageMeta({
  ssr: false,
});

import { ref, computed, nextTick, onMounted, onUnmounted, watch } from "vue";
import {
  BrowserMultiFormatReader,
  BarcodeFormat,
  DecodeHintType,
} from "@zxing/library";
import { useCartStore } from "~/stores/cart";
import { useSalesStore } from "~/stores/sales";
import { useProductsStore } from "~/stores/product";
import { useCustomerStore } from "~/stores/customer";
import { useAuthStore } from "~/stores/auth";

const cart = useCartStore();
const salesStore = useSalesStore();
const { format } = useFormatCurrency();
const toast = useToast();

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;
const auth = useAuthStore();

const {
  isQuotaBlocked,
  quotaBlockReason,
  isOfflineLeaseExpired,
  offlineDisclaimer,
  fetchCurrentSubscription,
} = useSubscription();

const searchQuery = ref("");
const barcodeRef = ref<any>();
const isScanning = ref(true);

const isCameraActive = ref(false);
const videoRef = ref<HTMLVideoElement>();
let lastScannedCode = "";
let lastScanTime = 0;

const { vibrate } = useVibrate({ pattern: [200], interval: 100 });
const showSearchResults = ref(false);

const showReceipt = ref(false);
const showCustomerSearch = ref(false);
const customerSearch = ref("");

const {
  isConnected: isPrinterConnected,
  deviceName: printerName,
  autoPrint,
  isPrinting,
  printReceipt,
} = usePrinter();

const showPrinterModal = ref(false);

const currentStore = computed(() => {
  return (
    auth.stores?.find((s: any) => s.store_id === auth.store_id) ||
    auth.stores?.[0] ||
    null
  );
});

const productStore = useProductsStore();
const { playScanSound } = useAudioChime();

const { customers: fetchedCustomers } = storeToRefs(useCustomerStore());

const activeProducts = computed(() => {
  return productStore.products.filter((p: any) => !p.deleted);
});

const searchResults = computed(() => {
  if (!searchQuery.value || searchQuery.value.length < 2) return [];
  const q = searchQuery.value.toLowerCase();
  return activeProducts.value
    .filter(
      (p: any) => p.name.toLowerCase().includes(q) || p.barcode_id.includes(q),
    )
    .slice(0, 6);
});

const activeCustomers = computed(() => {
  return fetchedCustomers.value;
});

const customerResults = computed(() => {
  if (!customerSearch.value) return activeCustomers.value;
  const q = customerSearch.value.toLowerCase();
  return activeCustomers.value.filter(
    (c) =>
      c.fullname.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q) ||
      c.phone.includes(q),
  );
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

function handleScannedBarcode(code: string) {
  const product = activeProducts.value.find((p: any) => p.barcode_id === code);
  if (product) {
    const existing = cart.items.find((item) => item.slug === product.slug);
    cart.addItem(product);

    playScanSound(true);

    try {
      vibrate();
    } catch (e) {
      if (typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate(200);
      }
    }

    if (existing) {
      toast.add({
        title: "Quantity Incremented",
        description: `${product.name} quantity increased to ${existing.quantity + 1}`,
        color: "success",
        icon: "i-lucide-plus-circle",
      });
    } else {
      toast.add({
        title: "Product Added Successfully",
        description: `${product.name} has been added to cart`,
        color: "success",
        icon: "i-lucide-check-circle",
      });
    }
  } else {
    playScanSound(false);

    try {
      if (typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
      }
    } catch (e) {}

    toast.add({
      title: "Barcode Not Found",
      description: `No product matches barcode: ${code}`,
      color: "error",
      icon: "i-lucide-alert-circle",
    });
  }
}

function handleBarcodeScan() {
  const query = searchQuery.value.trim();
  if (!query) return;

  let product = activeProducts.value.find((p: any) => p.barcode_id === query);

  if (!product) {
    product = activeProducts.value.find(
      (p: any) => p.name.toLowerCase() === query.toLowerCase(),
    );
  }

  if (!product && searchResults.value.length === 1 && searchResults.value[0]) {
    product = searchResults.value[0];
  }

  if (product) {
    handleScannedBarcode(product.barcode_id);
  } else {
    // If not found, show toast
    toast.add({
      title: "Not Found",
      description: `No product matches "${query}"`,
      color: "error",
      icon: "i-lucide-alert-circle",
    });
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

function addFromSearch(product: any) {
  const existing = cart.items.find((item) => item.slug === product.slug);
  cart.addItem(product);
  searchQuery.value = "";
  showSearchResults.value = false;

  if (existing) {
    toast.add({
      title: "Quantity Incremented",
      description: `${product.name} quantity increased to ${existing.quantity + 1}`,
      color: "success",
      icon: "i-lucide-plus-circle",
    });
  } else {
    toast.add({
      title: "Added to cart",
      description: product.name,
      color: "success",
      icon: "i-lucide-check-circle",
    });
  }
  focusBarcode();
}

function selectCustomer(customer: any) {
  cart.customerId = customer.customer_id;
  showCustomerSearch.value = false;
  toast.add({
    title: "Customer linked",
    description: customer.fullname,
    color: "info",
  });
  focusBarcode();
}

function completeSale() {
  if (isQuotaBlocked.value) {
    toast.add({
      title: isOfflineLeaseExpired.value
        ? "Offline Sync Required"
        : "Quota Limit Reached",
      description:
        quotaBlockReason.value || "Checkout is locked for this terminal.",
      color: "error",
    });
    return;
  }
  if (cart.isEmpty) {
    toast.add({
      title: "Cart is empty",
      description: "Add products before completing sale",
      color: "warning",
    });
    return;
  }
  if (cart.paymentMethod === "debt" && !cart.customerId) {
    toast.add({
      title: "Customer Required",
      description: "Debt payment requires a linked customer",
      color: "error",
    });
    return;
  }
  cart.amountReceived = cart.grandTotal;
  showReceipt.value = true;
}

async function finalizeAndReset(shouldPrint = false) {
  const key =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
          const r = (Math.random() * 16) | 0;
          return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
        });

  const receiptNumber = "REC-" + key.slice(0, 8).toUpperCase();
  const receiptPayload = {
    storeName: currentStore.value?.name || "KLUDA RETAIL",
    storeAddress: currentStore.value?.address || undefined,
    storePhone: currentStore.value?.phone || undefined,
    receiptNumber,
    date: new Date().toLocaleString(),
    cashierName: auth.fullName || auth.user?.fullname || "Cashier",
    customerName: selectedCustomerName.value || undefined,
    paymentMethod: cart.paymentMethod,
    items: cart.items.map((item) => ({
      name: item.name,
      quantity: item.quantity,
      unit_price: item.unit_price / 100,
      total: (item.unit_price * item.quantity) / 100,
    })),
    subtotal: cart.subtotal / 100,
    discount: cart.discount > 0 ? cart.discount / 100 : undefined,
    total: cart.grandTotal / 100,
  };

  const saleData = {
    idempotency_key: key,
    items: cart.items.map((item) => ({
      stock_slug: item.slug,
      amount: item.unit_price, // already in kobo
      quantities: item.quantity,
    })),
    discount: cart.discount, // already in kobo
    customer_id: cart.customerId,
    payment_method: cart.paymentMethod,
    amount_recived: cart.amountReceived, // already in kobo
    staff_note: cart.staffNote || null,
    status: "completed" as const,
  };

  await salesStore.addSale(saleData);

  // Dispatch to thermal printer if requested or auto-print is enabled
  if ((shouldPrint || autoPrint.value) && isPrinterConnected.value) {
    printReceipt(receiptPayload);
  }

  showReceipt.value = false;
  toast.add({
    title: "Sale completed!",
    description: "Transaction recorded successfully",
    color: "success",
    icon: "i-lucide-check-circle",
  });
  cart.clearCart();
  focusBarcode();
}

async function handlePrintAndClose() {
  if (!isPrinterConnected.value) {
    showPrinterModal.value = true;
    return;
  }
  await finalizeAndReset(true);
}

const selectedCustomerName = computed(() => {
  if (!cart.customerId) return null;
  return (
    activeCustomers.value.find((c) => c.customer_id === cart.customerId)
      ?.fullname || null
  );
});

let codeReader: any = null;

async function startCameraScanner() {
  isCameraActive.value = true;
  try {
    await nextTick();
    if (!codeReader) {
      const hints = new Map();
      const formats = [
        BarcodeFormat.EAN_13,
        BarcodeFormat.EAN_8,
        BarcodeFormat.CODE_128,
        BarcodeFormat.CODE_39,
        BarcodeFormat.UPC_A,
        BarcodeFormat.UPC_E,
      ];
      hints.set(DecodeHintType.POSSIBLE_FORMATS, formats);
      codeReader = new BrowserMultiFormatReader(hints);
    }
    const videoEl = videoRef.value;
    if (videoEl) {
      codeReader.decodeFromVideoDevice(
        undefined,
        videoEl,
        (result: any, err: any) => {
          if (result) {
            const code = result.getText();
            const now = Date.now();
            // 1.5 second cooldown for same barcode scanning
            if (code !== lastScannedCode || now - lastScanTime > 1500) {
              lastScannedCode = code;
              lastScanTime = now;
              handleScannedBarcode(code);
            }
          }
        },
      );
    }
  } catch (err) {
    console.error("Camera access failed:", err);
    toast.add({
      title: "Camera access failed",
      description: "Please check camera permissions",
      color: "error",
    });
    isCameraActive.value = false;
  }
}

function stopCameraScanner() {
  isCameraActive.value = false;
  if (codeReader) {
    codeReader.reset();
  }
}

function toggleCameraScanner() {
  if (isCameraActive.value) {
    stopCameraScanner();
  } else {
    startCameraScanner();
  }
}

onMounted(() => {
  fetchCurrentSubscription();
  focusBarcode();
});

onUnmounted(() => {
  stopCameraScanner();
});

const paymentMethods = [
  { label: "Cash", value: "cash", icon: "i-lucide-banknote" },
  { label: "POS", value: "pos", icon: "i-lucide-credit-card" },
  { label: "Transfer", value: "transfer", icon: "i-lucide-send" },
  { label: "Online", value: "online", icon: "i-lucide-globe" },
  { label: "Debt", value: "debt", icon: "i-lucide-clock" },
];

function handleSearchBlur() {
  setTimeout(() => {
    showSearchResults.value = false;
  }, 200);
}
</script>

<template>
  <ClientOnly>
    <div class="flex flex-col xl:flex-row gap-4 h-[calc(100vh-7rem)]">
    <div class="flex-1 flex flex-col min-h-0 space-y-4">
      <div class="space-y-3">
        <div class="relative">
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
              <span
                class="text-xs font-medium text-green-600 dark:text-green-400"
                >Scanner Active</span
              >
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
              @click="showPrinterModal = true"
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
          <div class="flex items-center gap-2">
            <UButton
              :color="isCameraActive ? 'error' : 'primary'"
              variant="solid"
              size="xl"
              :icon="isCameraActive ? 'i-lucide-camera-off' : 'i-lucide-camera'"
              class="shrink-0"
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

          <div
            v-show="isCameraActive"
            class="overflow-hidden bg-black flex items-center justify-center mt-2.5 fixed inset-0 z-[60] p-4 flex flex-col xl:relative xl:inset-auto xl:z-10 xl:aspect-video xl:max-h-64 xl:rounded-xl xl:border xl:border-(--ui-border) xl:p-0 xl:mt-2.5"
          >
            <div class="absolute top-4 right-4 z-[70] xl:hidden">
              <UButton
                color="neutral"
                variant="solid"
                icon="i-lucide-x"
                size="lg"
                class="rounded-full bg-black/40 text-white hover:bg-black/60"
                @click="stopCameraScanner"
              />
            </div>

            <video
              ref="videoRef"
              class="w-full h-full object-cover rounded-xl"
              autoplay
              playsinline
              muted
            />
            <div
              class="absolute inset-0 flex items-center justify-center pointer-events-none"
            >
              <div
                class="w-2/3 h-1/3 border-2 border-dashed border-green-500 rounded-lg opacity-60 relative"
              >
                <div
                  class="absolute inset-x-0 h-0.5 bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]"
                  style="top: 50%"
                />
              </div>
            </div>
          </div>

          <Transition name="fade">
            <div
              v-if="showSearchResults && searchResults.length"
              class="relative xl:absolute z-50 xl:top-full xl:mt-1 mt-2 w-full rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xl overflow-hidden"
            >
              <button
                v-for="product in searchResults"
                :key="product.slug"
                class="flex items-center justify-between w-full px-4 py-3 text-left hover:bg-(--ui-bg-accented) transition border-b border-(--ui-border)/50 last:border-0"
                @mousedown.prevent="addFromSearch(product)"
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
                  >{{ format(product.unit_price) }}</span
                >
              </button>
            </div>
          </Transition>
        </div>
      </div>

      <div class="hidden xl:block flex-1 overflow-y-auto min-h-0">
        <p
          class="text-xs font-medium text-(--ui-text-dimmed) uppercase tracking-wider mb-3"
        >
          Quick Add
        </p>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <button
            v-for="product in activeProducts"
            :key="product.slug"
            class="card-hover flex flex-col items-start p-3.5 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) text-left transition-all hover:border-green-500/30"
            @click="cart.addItem(product)"
          >
            <div
              class="flex items-center justify-center w-10 h-10 rounded-lg bg-green-500/10 mb-2.5"
            >
              <UIcon
                name="i-lucide-package"
                class="w-5 h-5 text-green-600 dark:text-green-400"
              />
            </div>
            <p
              class="text-sm font-medium text-(--ui-text-highlighted) leading-tight line-clamp-2"
            >
              {{ product.name }}
            </p>
            <p class="text-xs font-mono text-(--ui-text-dimmed) mt-1">
              {{ product.barcode_id }}
            </p>
            <p
              class="text-sm font-semibold text-green-600 dark:text-green-400 mt-auto pt-2"
            >
              {{ format(product.unit_price) }}
            </p>
          </button>
        </div>
      </div>
    </div>

    <div
      class="xl:w-[420px] flex flex-col min-h-0 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)"
    >
      <div
        class="flex items-center justify-between px-5 py-4 border-b border-(--ui-border)"
      >
        <div class="flex items-center gap-2">
          <UIcon
            name="i-lucide-shopping-cart"
            class="w-5 h-5 text-(--ui-text-muted)"
          />
          <h3 class="font-semibold text-(--ui-text-highlighted)">Cart</h3>
          <UBadge
            v-if="cart?.itemCount && cart.itemCount > 0"
            color="primary"
            variant="subtle"
            size="xs"
            >{{ cart?.itemCount }}</UBadge
          >
        </div>
        <UButton
          v-if="cart && !cart.isEmpty"
          variant="ghost"
          color="error"
          size="xs"
          icon="i-lucide-trash-2"
          @click="cart.clearCart()"
        >
          Clear
        </UButton>
      </div>

      <div
        class="flex-1 overflow-y-auto xl:max-h-none max-h-[300px] min-h-0 p-4 space-y-2"
      >
        <template v-if="cart.isEmpty">
          <div
            class="flex flex-col items-center justify-center h-full text-center py-8"
          >
            <div
              class="w-16 h-16 rounded-full bg-(--ui-bg-accented) flex items-center justify-center mb-4"
            >
              <UIcon
                name="i-lucide-scan-barcode"
                class="w-8 h-8 text-(--ui-text-dimmed)"
              />
            </div>
            <p class="text-sm font-medium text-(--ui-text-muted)">
              No items yet
            </p>
            <p class="text-xs text-(--ui-text-dimmed) mt-1">
              Scan a barcode or search to add products
            </p>
          </div>
        </template>

        <div
          v-for="item in cart.items"
          :key="item.slug"
          class="p-3 rounded-xl bg-(--ui-bg-accented)/50 border border-(--ui-border)/60 flex flex-col gap-2.5 transition-all"
        >
          <!-- Top Row: Product Name (Full Width, line-clamp-2) & Delete Button -->
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <p
                class="text-sm font-semibold text-(--ui-text-highlighted) leading-snug line-clamp-2"
              >
                {{ item.name }}
              </p>
              <p class="text-[11px] text-(--ui-text-dimmed) mt-0.5 font-mono">
                {{ format(item.unit_price) }} each
              </p>
            </div>
            <UButton
              variant="ghost"
              color="error"
              size="xs"
              icon="i-lucide-x"
              class="shrink-0 -mr-1 -mt-1 text-(--ui-text-dimmed) hover:text-rose-500 hover:bg-rose-500/10 transition rounded-lg"
              title="Remove item"
              @click="cart.removeItem(item.slug)"
            />
          </div>

          <!-- Bottom Row: Quantity Stepper & Subtotal -->
          <div
            class="flex items-center justify-between gap-3 pt-1 border-t border-(--ui-border)/40"
          >
            <!-- Stepper with touch-friendly tap targets -->
            <div
              class="flex items-center gap-1.5 bg-(--ui-bg) border border-(--ui-border) rounded-lg p-0.5"
            >
              <UButton
                variant="ghost"
                color="neutral"
                size="xs"
                icon="i-lucide-minus"
                class="size-7 p-0 flex items-center justify-center rounded-md"
                :disabled="item.quantity <= 1"
                @click="cart.updateQuantity(item.slug, item.quantity - 1)"
              />
              <span
                class="w-8 text-center text-xs font-bold text-(--ui-text-highlighted) font-mono"
                >{{ item.quantity }}</span
              >
              <UButton
                variant="ghost"
                color="neutral"
                size="xs"
                icon="i-lucide-plus"
                class="size-7 p-0 flex items-center justify-center rounded-md"
                @click="cart.updateQuantity(item.slug, item.quantity + 1)"
              />
            </div>

            <!-- Item Total -->
            <div class="text-right">
              <p
                class="text-sm font-bold text-(--ui-text-highlighted) font-mono"
              >
                {{ format(item.unit_price * item.quantity) }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="border-t border-(--ui-border) p-4 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs text-(--ui-text-dimmed)">Customer</span>
          <UButton
            variant="ghost"
            :color="cart.customerId ? 'primary' : 'neutral'"
            size="xs"
            :icon="
              cart.customerId ? 'i-lucide-user-check' : 'i-lucide-user-plus'
            "
            @click="showCustomerSearch = true"
          >
            {{ selectedCustomerName || "Link customer" }}
          </UButton>
        </div>

        <div class="flex items-center gap-3">
          <span class="text-xs text-(--ui-text-dimmed) whitespace-nowrap"
            >Discount (₦)</span
          >
          <UInput
            :model-value="cart.discount / 100"
            type="number"
            size="sm"
            placeholder="0.00"
            class="flex-1"
            @update:model-value="cart.discount = Number($event) * 100"
          />
        </div>

        <div>
          <p class="text-xs text-(--ui-text-dimmed) mb-2">Payment Method</p>
          <div class="grid grid-cols-5 gap-1.5">
            <button
              v-for="method in paymentMethods"
              :key="method.value"
              :class="[
                'flex flex-col items-center gap-1 py-2 px-1 rounded-lg text-xs font-medium transition-all',
                cart.paymentMethod === method.value
                  ? 'bg-green-500/15 text-green-600 dark:text-green-400 ring-1 ring-green-500/30'
                  : 'bg-(--ui-bg-accented) text-(--ui-text-muted) hover:bg-(--ui-bg-accented)/80',
              ]"
              @click="cart.paymentMethod = method.value as any"
            >
              <UIcon :name="method.icon" class="w-4 h-4" />
              <span>{{ method.label }}</span>
            </button>
          </div>
        </div>

        <div class="space-y-1.5 pt-2 border-t border-(--ui-border)">
          <div class="flex justify-between text-sm">
            <span class="text-(--ui-text-muted)">Subtotal</span>
            <span class="font-medium text-(--ui-text-highlighted)">{{
              format(cart.subtotal)
            }}</span>
          </div>
          <div v-if="cart.discount > 0" class="flex justify-between text-sm">
            <span class="text-(--ui-text-muted)">Discount</span>
            <span class="font-medium text-rose-500"
              >-{{ format(cart.discount) }}</span
            >
          </div>
          <div class="flex justify-between text-lg font-bold pt-1">
            <span class="text-(--ui-text-highlighted)">Total</span>
            <span class="text-green-600 dark:text-green-400">{{
              format(cart.grandTotal)
            }}</span>
          </div>
          <div
            v-if="cart.paymentMethod !== 'debt' && cart.change > 0"
            class="flex justify-between text-sm"
          >
            <span class="text-(--ui-text-muted)">Change</span>
            <span class="font-medium text-blue-500">{{
              format(cart.change)
            }}</span>
          </div>
        </div>

        <div
          v-if="isQuotaBlocked"
          class="p-3 bg-rose-50 dark:bg-rose-950/25 border border-rose-300 dark:border-rose-800/40 rounded-xl text-xs text-rose-900 dark:text-rose-200 flex items-start gap-2.5 mb-3 shadow-xs"
        >
          <UIcon
            name="i-lucide-alert-triangle"
            class="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5"
          />
          <div class="space-y-1">
            <p class="font-bold text-rose-950 dark:text-rose-100">
              {{
                isOfflineLeaseExpired
                  ? "Offline Lease Expired"
                  : "Sales Limit Reached"
              }}
            </p>
            <p class="leading-relaxed opacity-95 text-rose-900 dark:text-rose-200">{{ quotaBlockReason }}</p>
            <p
              class="text-[11px] text-rose-700 dark:text-rose-300 italic pt-1 border-t border-rose-200 dark:border-rose-800/30"
            >
              Notice: {{ offlineDisclaimer }}
            </p>
          </div>
        </div>

        <UButton
          block
          size="lg"
          :disabled="cart.isEmpty || isQuotaBlocked"
          @click="completeSale"
        >
          <UIcon name="i-lucide-check-circle" class="w-5 h-5 mr-2" />
          Complete Sale
        </UButton>
      </div>
    </div>

    <AppBottomSheet
      v-model="showCustomerSearch"
      title="Link Customer"
      description="Search and assign a registered customer to this order."
    >
      <div class="space-y-4">
        <UInput
          v-model="customerSearch"
          placeholder="Search customers..."
          icon="i-lucide-search"
        />
        <div class="space-y-2 max-h-64 overflow-y-auto">
          <button
            v-for="customer in customerResults"
            :key="customer.customer_id"
            class="flex items-center gap-3 w-full p-3 rounded-lg text-left hover:bg-(--ui-bg-accented) transition"
            @click="selectCustomer(customer)"
          >
            <UAvatar
              :text="
                customer.fullname
                  .split(' ')
                  .map((n: string) => n[0])
                  .join('')
              "
              size="sm"
            />
            <div>
              <p class="text-sm font-medium text-(--ui-text-highlighted)">
                {{ customer.fullname }}
              </p>
              <p class="text-xs text-(--ui-text-dimmed)">
                {{ customer.phone }} • {{ customer.email }}
              </p>
            </div>
          </button>
        </div>
      </div>
    </AppBottomSheet>

    <AppBottomSheet
      v-model="showReceipt"
      title="Receipt"
      description="Order completed successfully."
    >
      <div class="space-y-4">
        <div
          class="text-center border-b border-dashed border-(--ui-border) pb-4"
        >
          <div
            class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#090d16] border border-emerald-500/40 overflow-hidden mb-2"
          >
            <img
              src="/kluda_icon.jpg"
              alt="Kluda"
              class="w-full h-full object-cover"
            />
          </div>
          <h3
            class="font-black text-lg tracking-wider text-(--ui-text-highlighted)"
          >
            KLUDA
          </h3>
          <p class="text-xs text-(--ui-text-dimmed)">
            {{ new Date().toLocaleString() }}
          </p>
        </div>

        <div class="space-y-2">
          <div
            v-for="item in cart.items"
            :key="item.slug"
            class="flex justify-between text-sm"
          >
            <span class="text-(--ui-text-muted)"
              >{{ item.name }} × {{ item.quantity }}</span
            >
            <span class="font-medium text-(--ui-text-highlighted)">{{
              format(item.unit_price * item.quantity)
            }}</span>
          </div>
        </div>

        <div
          class="border-t border-dashed border-(--ui-border) pt-3 space-y-1"
        >
          <div class="flex justify-between font-bold text-lg">
            <span>Total</span>
            <span class="text-green-600 dark:text-green-400">{{
              format(cart.grandTotal)
            }}</span>
          </div>
          <div class="flex justify-between text-sm text-(--ui-text-muted)">
            <span>Payment</span>
            <span class="capitalize">{{ cart.paymentMethod }}</span>
          </div>
        </div>

        <div class="flex justify-center pt-2">
          <div class="p-3 bg-white rounded-lg">
            <div
              class="w-24 h-24 bg-gray-200 rounded flex items-center justify-center"
            >
              <UIcon
                name="i-lucide-qr-code"
                class="w-16 h-16 text-gray-600"
              />
            </div>
          </div>
        </div>

        <p class="text-center text-xs text-(--ui-text-dimmed)">
          Thank you for your purchase!
        </p>

        <div class="flex gap-2">
          <UButton
            block
            variant="outline"
            color="neutral"
            :loading="isPrinting"
            @click="handlePrintAndClose"
          >
            <UIcon
              name="i-lucide-printer"
              class="w-4 h-4 mr-1 text-emerald-400"
            />
            {{ isPrinterConnected ? "Print & Close" : "Pair & Print" }}
          </UButton>
          <UButton block color="primary" @click="finalizeAndReset(false)">
            Done
          </UButton>
        </div>
      </div>
    </AppBottomSheet>

    <PosPrinterSettingsModal v-model:open="showPrinterModal" />

    <div
      v-if="salesStore.isSyncing"
      class="fixed inset-0 z-[100] bg-black/55 backdrop-blur-sm flex flex-col items-center justify-center text-white"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-10 h-10 animate-spin text-green-500 mb-3"
      />
      <p class="font-semibold text-lg">Syncing local sales...</p>
      <p class="text-xs text-gray-400 mt-1">
        Please wait while we sync offline data to the server
      </p>
    </div>
  </div>
    <template #fallback>
      <div class="flex items-center justify-center min-h-[400px]">
        <UIcon name="i-lucide-loader" class="w-8 h-8 animate-spin text-primary-500" />
      </div>
    </template>
  </ClientOnly>
</template>
