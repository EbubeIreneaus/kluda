<script setup lang="ts">
defineProps<{
  open: boolean;
  cart: {
    items: Array<{
      slug: string;
      name: string;
      quantity: number;
      unit_price: number;
    }>;
    grandTotal: number;
    amountReceived?: number;
    paymentMethod: string;
  };
  isPrinting: boolean;
  isPrinterConnected: boolean;
}>();

const emit = defineEmits<{
  (e: "update:open", val: boolean): void;
  (e: "print-and-close"): void;
  (e: "done"): void;
}>();

const { format } = useFormatCurrency();
</script>

<template>
  <AppBottomSheet
    :model-value="open"
    title="Receipt"
    description="Order completed successfully."
    @update:model-value="emit('update:open', $event)"
  >
    <div class="space-y-4">
      <div class="text-center border-b border-dashed border-(--ui-border) pb-4">
        <div
          class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#090d16] border border-emerald-500/40 overflow-hidden mb-2"
        >
          <img
            src="/kluda_icon.jpg"
            alt="Kluda"
            class="w-full h-full object-cover"
          />
        </div>
        <h3 class="font-black text-lg tracking-wider text-(--ui-text-highlighted)">
          KLUDA
        </h3>
        <p class="text-xs text-(--ui-text-dimmed)">
          {{ new Date().toLocaleString() }}
        </p>
      </div>

      <div class="space-y-2 max-h-48 overflow-y-auto">
        <div
          v-for="item in cart.items"
          :key="item.slug"
          class="flex justify-between text-sm"
        >
          <span class="text-(--ui-text-muted)">
            {{ item.name }} × {{ item.quantity }}
          </span>
          <span class="font-medium text-(--ui-text-highlighted)">
            {{ format(item.unit_price * item.quantity) }}
          </span>
        </div>
      </div>

      <div class="border-t border-dashed border-(--ui-border) pt-3 space-y-1">
        <div class="flex justify-between font-bold text-lg">
          <span>Total</span>
          <span class="text-green-600 dark:text-green-400">
            {{ format(cart.grandTotal) }}
          </span>
        </div>
        <div class="flex justify-between text-sm text-(--ui-text-muted)">
          <span>Payment</span>
          <span class="capitalize">{{ cart.paymentMethod }}</span>
        </div>
        <div
          v-if="cart.paymentMethod === 'debt' && (cart.amountReceived || 0) > 0"
          class="flex justify-between text-sm text-(--ui-text-muted)"
        >
          <span>Deposit Paid</span>
          <span class="font-medium text-(--ui-text-highlighted)">
            {{ format(cart.amountReceived || 0) }}
          </span>
        </div>
        <div
          v-if="cart.paymentMethod === 'debt'"
          class="flex justify-between text-sm font-bold text-rose-500 pt-0.5"
        >
          <span>Debt Owed</span>
          <span>
            {{ format(Math.max(0, cart.grandTotal - (cart.amountReceived || 0))) }}
          </span>
        </div>
      </div>

      <div class="flex justify-center pt-2">
        <div class="p-3 bg-white rounded-lg">
          <div class="w-24 h-24 bg-gray-200 rounded flex items-center justify-center">
            <UIcon name="i-lucide-qr-code" class="w-16 h-16 text-gray-600" />
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
          @click="emit('print-and-close')"
        >
          <UIcon
            name="i-lucide-printer"
            class="w-4 h-4 mr-1 text-emerald-400"
          />
          {{ isPrinterConnected ? "Print & Close" : "Pair & Print" }}
        </UButton>
        <UButton block color="primary" @click="emit('done')">
          Done
        </UButton>
      </div>
    </div>
  </AppBottomSheet>
</template>
