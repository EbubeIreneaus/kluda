<script setup lang="ts">
const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
}>();

const isOpen = computed({
  get: () => props.open,
  set: (v) => emit("update:open", v),
});

const {
  isBluetoothSupported,
  isUsbSupported,
  isConnected,
  connectionType,
  deviceName,
  paperWidth,
  autoPrint,
  isConnecting,
  isPrinting,
  setPaperWidth,
  setAutoPrint,
  connectBluetooth,
  connectUsb,
  disconnect,
  printTestReceipt,
} = usePrinter();

const connectingTarget = ref<"bluetooth" | "usb" | null>(null);

async function handleConnectBluetooth() {
  connectingTarget.value = "bluetooth";
  try {
    await connectBluetooth();
  } finally {
    connectingTarget.value = null;
  }
}

async function handleConnectUsb() {
  connectingTarget.value = "usb";
  try {
    await connectUsb();
  } finally {
    connectingTarget.value = null;
  }
}
</script>

<template>
  <UModal v-model:open="isOpen" title="Receipt Printer Hardware">
    <template #body>
      <div class="p-6 space-y-6">
        <!-- Header status pill -->
        <div
          class="flex items-center justify-between p-4 rounded-2xl border transition"
          :class="[
            isConnected
              ? 'bg-emerald-500/10 border-emerald-500/30'
              : 'bg-(--ui-bg-accented) border-(--ui-border)',
          ]"
        >
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
              :class="
                isConnected
                  ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30'
                  : 'bg-neutral-800 text-neutral-400'
              "
            >
              <UIcon name="i-lucide-printer" class="w-5 h-5" />
            </div>
            <div>
              <h4 class="text-sm font-bold text-(--ui-text-highlighted)">
                {{ isConnected ? deviceName : "No Printer Connected" }}
              </h4>
              <p class="text-xs text-(--ui-text-dimmed)">
                {{
                  isConnected
                    ? `Connected via ${connectionType.toUpperCase()} (${paperWidth})`
                    : "Pair your 58mm or 80mm thermal receipt printer"
                }}
              </p>
            </div>
          </div>

          <UButton
            v-if="isConnected"
            size="xs"
            variant="ghost"
            color="error"
            icon="i-lucide-power"
            @click="disconnect"
          >
            Disconnect
          </UButton>
        </div>

        <!-- Connection actions if not connected -->
        <div v-if="!isConnected" class="space-y-3">
          <label
            class="text-xs font-bold text-(--ui-text-muted) uppercase tracking-wider"
          >
            Pair Thermal Printer
          </label>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <!-- Bluetooth -->
            <div
              class="p-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) flex flex-col justify-between gap-3"
            >
              <div class="space-y-1">
                <div
                  class="flex items-center gap-2 text-indigo-400 font-bold text-sm"
                >
                  <UIcon name="i-lucide-bluetooth" class="w-4 h-4" />
                  <span>Bluetooth</span>
                </div>
                <p class="text-xs text-(--ui-text-dimmed)">
                  Best for portable handheld 58mm & 80mm belt printers on
                  Android phones.
                </p>
              </div>

              <UButton
                block
                color="primary"
                variant="soft"
                size="sm"
                :loading="isConnecting && connectingTarget === 'bluetooth'"
                :disabled="!isBluetoothSupported"
                @click="handleConnectBluetooth"
              >
                <UIcon name="i-lucide-bluetooth" class="w-4 h-4 mr-1.5" />
                {{
                  isBluetoothSupported ? "Pair Bluetooth" : "Not Supported Here"
                }}
              </UButton>
            </div>

            <!-- USB -->
            <div
              class="p-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) flex flex-col justify-between gap-3"
            >
              <div class="space-y-1">
                <div
                  class="flex items-center gap-2 text-emerald-400 font-bold text-sm"
                >
                  <UIcon name="i-lucide-cable" class="w-4 h-4" />
                  <span>USB Direct</span>
                </div>
                <p class="text-xs text-(--ui-text-dimmed)">
                  For desktop counter POS terminals or Android devices with OTG
                  cable.
                </p>
              </div>

              <UButton
                block
                color="primary"
                variant="outline"
                size="sm"
                :loading="isConnecting && connectingTarget === 'usb'"
                :disabled="!isUsbSupported"
                @click="handleConnectUsb"
              >
                <UIcon name="i-lucide-usb" class="w-4 h-4 mr-1.5" />
                {{ isUsbSupported ? "Connect USB" : "Not Supported" }}
              </UButton>
            </div>
          </div>
        </div>

        <!-- Hardware Configurations -->
        <div class="space-y-4 pt-4 border-t border-(--ui-border)">
          <label
            class="text-xs font-bold text-(--ui-text-muted) uppercase tracking-wider"
          >
            Printer Configuration
          </label>

          <!-- Paper Width Toggle -->
          <div
            class="flex items-center justify-between p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)"
          >
            <div>
              <p class="text-sm font-semibold text-(--ui-text-highlighted)">
                Thermal Paper Width
              </p>
              <p class="text-xs text-(--ui-text-dimmed)">
                Adjust character formatting per line
              </p>
            </div>
            <div
              class="flex items-center gap-1 bg-(--ui-bg-accented) p-1 rounded-xl border border-(--ui-border)"
            >
              <button
                type="button"
                class="px-3 py-1 text-xs font-bold rounded-lg transition cursor-pointer"
                :class="
                  paperWidth === '58mm'
                    ? 'bg-primary-500 text-slate-950 shadow-sm'
                    : 'text-(--ui-text-dimmed) hover:text-(--ui-text-highlighted)'
                "
                @click="setPaperWidth('58mm')"
              >
                58mm (32 Col)
              </button>
              <button
                type="button"
                class="px-3 py-1 text-xs font-bold rounded-lg transition cursor-pointer"
                :class="
                  paperWidth === '80mm'
                    ? 'bg-primary-500 text-slate-950 shadow-sm'
                    : 'text-(--ui-text-dimmed) hover:text-(--ui-text-highlighted)'
                "
                @click="setPaperWidth('80mm')"
              >
                80mm (48 Col)
              </button>
            </div>
          </div>

          <!-- Auto-print Checkout Toggle -->
          <div
            class="flex items-center justify-between p-3 rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated)"
          >
            <div class="pr-4">
              <p class="text-sm font-semibold text-(--ui-text-highlighted)">
                Auto-Print on Checkout
              </p>
              <p class="text-xs text-(--ui-text-dimmed)">
                Automatically dispatch receipt as soon as payment is confirmed
              </p>
            </div>
            <input
              type="checkbox"
              :checked="autoPrint"
              class="w-4 h-4 rounded border-neutral-700 bg-neutral-900 text-emerald-500 focus:ring-0 cursor-pointer"
              @change="setAutoPrint(!autoPrint)"
            />
          </div>
        </div>

        <!-- Diagnostic Actions -->
        <div v-if="isConnected" class="pt-2">
          <UButton
            block
            variant="solid"
            color="neutral"
            size="sm"
            :loading="isPrinting"
            @click="printTestReceipt"
          >
            <UIcon
              name="i-lucide-receipt"
              class="w-4 h-4 mr-1.5 text-emerald-400"
            />
            Print Diagnostic Test Slip
          </UButton>
        </div>

        <!-- Platform Note for Android vs iOS -->
        <div
          class="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/25 border border-amber-200 dark:border-amber-800/40 text-xs flex items-start gap-2.5 shadow-xs"
        >
          <UIcon
            name="i-lucide-info"
            class="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5"
          />
          <div class="space-y-1">
            <p class="font-bold text-amber-950 dark:text-amber-100">Hardware Compatibility Guide</p>
            <p class="text-amber-900 dark:text-amber-200/90 leading-relaxed">
              Bluetooth & USB receipt printing works right out of the box in
              Chrome on Android and PC — no extra setup needed. iPhone note:
              Safari can't access printers directly, so for Bluetooth printers,
              open Kluda in <strong>Bluefy</strong> (a free browser that adds
              Bluetooth support to iOS). USB printers currently require Android
              or PC.
            </p>
          </div>
        </div>
      </div>
    </template>
  </UModal>
</template>
