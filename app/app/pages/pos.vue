<script setup lang="ts">
definePageMeta({
  ssr: false,
});

import { ref, computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useCartStore } from "~/stores/cart";
import { useSalesStore } from "~/stores/sales";
import { useProductsStore } from "~/stores/product";
import { useCustomerStore } from "~/stores/customer";
import { useAuthStore } from "~/stores/auth";
import PosScannerBar from "~/components/pos/PosScannerBar.vue";

const cart = useCartStore();
const salesStore = useSalesStore();
const productStore = useProductsStore();
const auth = useAuthStore();
const toast = useToast();

const {
  isQuotaBlocked,
  quotaBlockReason,
  isOfflineLeaseExpired,
  offlineDisclaimer,
  fetchCurrentSubscription,
} = useSubscription();

const { vibrate } = useVibrate({ pattern: [200], interval: 100 });
const { playScanSound } = useAudioChime();

const {
  isConnected: isPrinterConnected,
  deviceName: printerName,
  autoPrint,
  isPrinting,
  printReceipt,
} = usePrinter();

const { customers: fetchedCustomers } = storeToRefs(useCustomerStore());

const scannerBarRef = ref<InstanceType<typeof PosScannerBar>>();
const showReceipt = ref(false);
const showCustomerSearch = ref(false);
const showPrinterModal = ref(false);

const currentStore = computed(() => {
  return (
    auth.stores?.find((s: any) => s.store_id === auth.store_id) ||
    auth.stores?.[0] ||
    null
  );
});

const activeProducts = computed(() => {
  return productStore.products.filter((p: any) => !p.deleted);
});

const activeCustomers = computed(() => {
  return fetchedCustomers.value;
});

const selectedCustomerName = computed(() => {
  if (!cart.customerId) return null;
  return (
    activeCustomers.value.find((c) => c.customer_id === cart.customerId)
      ?.fullname || null
  );
});

function focusBarcode() {
  scannerBarRef.value?.focusBarcode();
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

function handleQuickAdd(product: any) {
  const existing = cart.items.find((item) => item.slug === product.slug);
  cart.addItem(product);

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

function handleSelectCustomer(customer: any) {
  cart.customerId = customer.customer_id;
  showCustomerSearch.value = false;
  toast.add({
    title: "Customer linked",
    description: customer.fullname,
    color: "info",
  });
  focusBarcode();
}

function handleCompleteSale() {
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
  if (cart.paymentMethod !== "debt") {
    cart.amountReceived = cart.grandTotal;
  }
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
      amount: item.unit_price,
      quantities: item.quantity,
    })),
    discount: cart.discount,
    customer_id: cart.customerId,
    payment_method: cart.paymentMethod,
    amount_recived: cart.amountReceived,
    staff_note: cart.staffNote || null,
    status: "completed" as const,
  };

  await salesStore.addSale(saleData);

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

onMounted(() => {
  fetchCurrentSubscription();
  focusBarcode();
});
</script>

<template>
  <ClientOnly>
    <div class="flex flex-col xl:flex-row gap-4 h-[calc(100vh-7rem)]">
      <!-- Left Column: Scanner Bar + Quick Add Grid -->
      <div class="flex-1 flex flex-col min-h-0 space-y-4 " >
        <PosScannerBar
          ref="scannerBarRef"
          :active-products="activeProducts"
          :is-printer-connected="isPrinterConnected"
          :printer-name="printerName"
          @scan-barcode="handleScannedBarcode"
          @add-product="handleQuickAdd"
          @open-printer="showPrinterModal = true"
        />

        <PosQuickAddGrid
          :products="activeProducts"
          @add="handleQuickAdd"
        />
      </div>

      <!-- Right Column: Cart Panel -->
      <PosCartPanel
        :selected-customer-name="selectedCustomerName"
        :is-quota-blocked="isQuotaBlocked"
        :quota-block-reason="quotaBlockReason"
        :is-offline-lease-expired="isOfflineLeaseExpired"
        :offline-disclaimer="offlineDisclaimer"
        @link-customer="showCustomerSearch = true"
        @complete-sale="handleCompleteSale"
      />

      <!-- Customer Select Modal -->
      <PosCustomerSelectModal
        v-model:open="showCustomerSearch"
        :customers="activeCustomers"
        @select="handleSelectCustomer"
      />

      <!-- Receipt Preview & Print Modal -->
      <PosReceiptModal
        v-model:open="showReceipt"
        :cart="cart"
        :is-printing="isPrinting"
        :is-printer-connected="isPrinterConnected"
        @print-and-close="handlePrintAndClose"
        @done="finalizeAndReset(false)"
      />

      <!-- Thermal Printer Settings Modal -->
      <PosPrinterSettingsModal v-model:open="showPrinterModal" />

      <!-- Offline Sync Overlay Indicator -->
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
