<script setup lang="ts">
import { useCartStore } from "~/stores/cart";

defineProps<{
  selectedCustomerName: string | null;
  isQuotaBlocked: boolean;
  quotaBlockReason: string;
  isOfflineLeaseExpired: boolean;
  offlineDisclaimer: string;
}>();

const emit = defineEmits<{
  (e: "link-customer"): void;
  (e: "complete-sale"): void;
}>();

const cart = useCartStore();
const { format } = useFormatCurrency();

const paymentMethods = [
  { label: "Cash", value: "cash", icon: "i-lucide-banknote" },
  { label: "POS", value: "pos", icon: "i-lucide-credit-card" },
  { label: "Transfer", value: "transfer", icon: "i-lucide-send" },
  { label: "Online", value: "online", icon: "i-lucide-globe" },
  { label: "Debt", value: "debt", icon: "i-lucide-clock" },
];
</script>

<template>
  <div
    class="xl:w-[420px] h-full flex flex-col min-h-0 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden"
  >
    <!-- Cart Header -->
    <div
      class="flex items-center justify-between px-4 py-3 border-b border-(--ui-border) shrink-0"
    >
      <div class="flex items-center gap-2">
        <UIcon
          name="i-lucide-shopping-cart"
          class="w-4 h-4 text-(--ui-text-muted)"
        />
        <h3 class="font-semibold text-sm text-(--ui-text-highlighted)">Cart</h3>
        <UBadge
          v-if="cart?.itemCount && cart.itemCount > 0"
          color="primary"
          variant="subtle"
          size="xs"
        >
          {{ cart?.itemCount }}
        </UBadge>
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

    <!-- Items List -->
    <div
      class="flex-1 overflow-y-auto min-h-[120px] p-3 space-y-2"
    >
      <template v-if="cart.isEmpty">
        <div
          class="flex flex-col items-center justify-center h-full text-center py-8"
        >
          <div
            class="w-12 h-12 rounded-full bg-(--ui-bg-accented) flex items-center justify-center mb-3"
          >
            <UIcon
              name="i-lucide-scan-barcode"
              class="w-6 h-6 text-(--ui-text-dimmed)"
            />
          </div>
          <p class="text-xs font-medium text-(--ui-text-muted)">No items yet</p>
          <p class="text-[11px] text-(--ui-text-dimmed) mt-0.5">
            Scan a barcode or search to add products
          </p>
        </div>
      </template>

      <div
        v-for="item in cart.items"
        :key="item.slug"
        class="p-2.5 rounded-lg bg-(--ui-bg-accented)/50 border border-(--ui-border)/60 flex flex-col gap-2 transition-all"
      >
        <!-- Top Row: Product Name & Delete Button -->
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <p
              class="text-xs font-semibold text-(--ui-text-highlighted) leading-snug line-clamp-2"
            >
              {{ item.name }}
            </p>
            <p class="text-[10px] text-(--ui-text-dimmed) mt-0.5 font-mono">
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
          class="flex items-center justify-between gap-2 pt-1 border-t border-(--ui-border)/40"
        >
          <div
            class="flex items-center gap-1 bg-(--ui-bg) border border-(--ui-border) rounded-md p-0.5"
          >
            <UButton
              variant="ghost"
              color="neutral"
              size="xs"
              icon="i-lucide-minus"
              class="size-6 p-0 flex items-center justify-center rounded-sm"
              :disabled="item.quantity <= 1"
              @click="cart.updateQuantity(item.slug, item.quantity - 1)"
            />
            <span
              class="w-7 text-center text-xs font-bold text-(--ui-text-highlighted) font-mono"
            >
              {{ item.quantity }}
            </span>
            <UButton
              variant="ghost"
              color="neutral"
              size="xs"
              icon="i-lucide-plus"
              class="size-6 p-0 flex items-center justify-center rounded-sm"
              @click="cart.updateQuantity(item.slug, item.quantity + 1)"
            />
          </div>

          <div class="text-right">
            <p class="text-xs font-bold text-(--ui-text-highlighted) font-mono">
              {{ format(item.unit_price * item.quantity) }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Controls & Checkout Section -->
    <div class="shrink-0 border-t border-(--ui-border) p-3 space-y-2 overflow-y-auto max-h-[46vh]">
      <!-- Linked Customer Row -->
      <div class="flex items-center justify-between">
        <span class="text-xs text-(--ui-text-dimmed)">Customer</span>
        <UButton
          variant="ghost"
          :color="cart.customerId ? 'primary' : 'neutral'"
          size="xs"
          :icon="cart.customerId ? 'i-lucide-user-check' : 'i-lucide-user-plus'"
          class="font-medium"
          @click="emit('link-customer')"
        >
          {{ selectedCustomerName || "Link customer" }}
        </UButton>
      </div>

      <!-- Discount Input -->
      <div class="flex items-center gap-2.5">
        <span class="text-xs text-(--ui-text-dimmed) whitespace-nowrap">
          Discount (₦)
        </span>
        <UInput
          :model-value="cart.discount / 100"
          type="number"
          size="xs"
          placeholder="0.00"
          class="flex-1"
          @update:model-value="cart.discount = Number($event) * 100"
        />
      </div>

      <!-- Payment Method -->
      <div>
        <p class="text-[11px] text-(--ui-text-dimmed) mb-1.5 font-medium uppercase tracking-wider">Payment Method</p>
        <div class="grid grid-cols-5 gap-1">
          <button
            v-for="method in paymentMethods"
            :key="method.value"
            type="button"
            :class="[
              'flex flex-col items-center justify-center gap-1 py-1.5 px-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer',
              cart.paymentMethod === method.value
                ? 'bg-green-500/15 text-green-600 dark:text-green-400 ring-1 ring-green-500/30 font-semibold'
                : 'bg-(--ui-bg-accented) text-(--ui-text-muted) hover:bg-(--ui-bg-accented)/80',
            ]"
            @click="
              cart.paymentMethod = method.value as any;
              if (method.value === 'debt') {
                cart.amountReceived = 0;
              } else {
                cart.amountReceived = cart.grandTotal;
              }
            "
          >
            <UIcon :name="method.icon" class="w-3.5 h-3.5" />
            <span class="truncate leading-none">{{ method.label }}</span>
          </button>
        </div>
      </div>

      <!-- Deposit Input for Debt Payments -->
      <div
        v-if="cart.paymentMethod === 'debt'"
        class="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 space-y-1.5"
      >
        <div class="flex items-center justify-between">
          <span
            class="text-xs font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-1.5"
          >
            <UIcon name="i-lucide-wallet" class="size-3.5" />
            Deposit / Amount Paid (₦)
          </span>
          <span class="text-[10px] text-(--ui-text-dimmed)">Optional</span>
        </div>
        <UInput
          :model-value="cart.amountReceived / 100"
          type="number"
          min="0"
          :max="cart.grandTotal / 100"
          step="0.01"
          placeholder="0.00"
          size="xs"
          class="w-full"
          @update:model-value="
            cart.amountReceived = Math.min(
              cart.grandTotal,
              Math.max(0, Math.round(Number($event) * 100)),
            )
          "
        />
      </div>

      <!-- Totals Summary -->
      <div class="space-y-1 pt-1.5 border-t border-(--ui-border)">
        <div class="flex justify-between text-xs">
          <span class="text-(--ui-text-muted)">Subtotal</span>
          <span class="font-medium text-(--ui-text-highlighted)">
            {{ format(cart.subtotal) }}
          </span>
        </div>
        <div v-if="cart.discount > 0" class="flex justify-between text-xs">
          <span class="text-(--ui-text-muted)">Discount</span>
          <span class="font-medium text-rose-500">
            -{{ format(cart.discount) }}
          </span>
        </div>
        <div class="flex justify-between text-base font-bold pt-0.5">
          <span class="text-(--ui-text-highlighted)">Total</span>
          <span class="text-green-600 dark:text-green-400">
            {{ format(cart.grandTotal) }}
          </span>
        </div>
        <div
          v-if="cart.paymentMethod === 'debt' && cart.amountReceived > 0"
          class="flex justify-between text-xs"
        >
          <span class="text-(--ui-text-muted)">Deposit Paid</span>
          <span class="font-medium text-emerald-600 dark:text-emerald-400">
            {{ format(cart.amountReceived) }}
          </span>
        </div>
        <div
          v-if="cart.paymentMethod === 'debt'"
          class="flex justify-between text-xs pt-0.5"
        >
          <span class="font-bold text-rose-500">Debt Balance Owed</span>
          <span class="font-bold text-rose-500 font-mono">
            {{ format(Math.max(0, cart.grandTotal - cart.amountReceived)) }}
          </span>
        </div>
        <div
          v-if="cart.paymentMethod !== 'debt' && cart.change > 0"
          class="flex justify-between text-xs"
        >
          <span class="text-(--ui-text-muted)">Change</span>
          <span class="font-medium text-blue-500">
            {{ format(cart.change) }}
          </span>
        </div>
      </div>

      <!-- Quota Warning -->
      <div
        v-if="isQuotaBlocked"
        class="p-2.5 bg-rose-50 dark:bg-rose-950/25 border border-rose-300 dark:border-rose-800/40 rounded-lg text-xs text-rose-900 dark:text-rose-200 flex items-start gap-2 mb-2 shadow-xs"
      >
        <UIcon
          name="i-lucide-alert-triangle"
          class="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5"
        />
        <div class="space-y-0.5 text-xs">
          <p class="font-bold text-rose-950 dark:text-rose-100">
            {{
              isOfflineLeaseExpired
                ? "Offline Lease Expired"
                : "Sales Limit Reached"
            }}
          </p>
          <p
            class="leading-relaxed opacity-95 text-rose-900 dark:text-rose-200"
          >
            {{ quotaBlockReason }}
          </p>
          <p
            class="text-[10px] text-rose-700 dark:text-rose-300 italic pt-0.5 border-t border-rose-200 dark:border-rose-800/30"
          >
            Notice: {{ offlineDisclaimer }}
          </p>
        </div>
      </div>
    </div>

    <!-- Complete Sale Action Pinned at Bottom -->
    <div class="shrink-0 p-3 pt-2 border-t border-(--ui-border) bg-(--ui-bg-elevated)">
      <UButton
        block
        size="md"
        :disabled="cart.isEmpty || isQuotaBlocked"
        class="font-bold cursor-pointer"
        @click="emit('complete-sale')"
      >
        <UIcon name="i-lucide-check-circle" class="w-4 h-4 mr-2" />
        Complete Sale
      </UButton>
    </div>
  </div>
</template>
