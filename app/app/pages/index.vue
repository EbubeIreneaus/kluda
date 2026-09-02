<script setup lang="ts">
import { ref, computed } from "vue";

definePageMeta({ layout: "dashboard" });

const auth = useAuthStore();
const productStore = useProductsStore();
const salesStore = useSalesStore();
const { format } = useFormatCurrency();

const isAmountVisible = ref(true);

const todayStr = computed(() => {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
});

const todaySales = computed(() => {
  return salesStore.sales.filter(
    (s) =>
      s.date && s.date.startsWith(todayStr.value) && s.status !== "cancelled",
  );
});

const todayRevenueKobo = computed(() => {
  return todaySales.value.reduce((sum, s) => sum + (s.total || 0), 0);
});

const totalProducts = computed(() => {
  return productStore.productCount;
});

const staffName = computed(() => {
  if (auth.staff) {
    const name =
      `${auth.staff.first_name || ""} ${auth.staff.last_name || ""}`.trim();
    if (name) return name;
    if (auth.staff.role === "owner") return "Store Owner";
  }
  return "Store Cashier";
});
</script>

<template>
  <div class="space-y-6">
    <div class="w-full max-w-lg">
      <div
        class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-zinc-900 via-emerald-950/80 to-zinc-950 p-6 text-white border border-emerald-500/30 shadow-2xl shadow-emerald-950/40 select-none"
      >
        <div
          class="absolute -right-16 -top-16 w-56 h-56 rounded-full bg-emerald-500/15 blur-3xl pointer-events-none"
        />
        <div
          class="absolute -left-16 -bottom-16 w-56 h-56 rounded-full bg-blue-500/10 blur-3xl pointer-events-none"
        />
        <div
          class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-white/5 via-transparent to-transparent pointer-events-none"
        />

        <div
          class="relative z-10 flex flex-col justify-between min-h-[190px] gap-6"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="w-9 h-7 rounded-md bg-gradient-to-tr from-green-400 via-green-300 to-green-500 p-1 flex items-center justify-center shadow-md shadow-green-950/30 border border-green-300/40"
              >
                <div
                  class="w-full h-full border border-green-600/40 rounded-sm grid grid-cols-2 gap-0.5 opacity-80"
                />
              </div>
              <div class="flex flex-col">
                <span
                  class="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest leading-none"
                  >Cashier</span
                >
                <span
                  class="text-sm font-bold text-zinc-100 tracking-wide mt-0.5"
                  >{{ staffName }}</span
                >
              </div>
            </div>

            <div class="flex items-center gap-2">
              <button
                type="button"
                class="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/10 transition-colors"
                @click="isAmountVisible = !isAmountVisible"
              >
                <UIcon
                  :name="isAmountVisible ? 'i-lucide-eye' : 'i-lucide-eye-off'"
                  class="size-4"
                />
              </button>
              <div
                class="px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-[10px] font-bold text-emerald-300 uppercase tracking-wider"
              >
                Kluda POS
              </div>
            </div>
          </div>

          <div class="flex flex-col">
            <span class="text-xs font-medium text-emerald-300/90 tracking-wide"
              >Money Sold Today</span
            >
            <div
              class="text-3xl sm:text-4xl font-black text-white tracking-tight mt-1 flex items-center gap-2"
            >
              <span v-if="isAmountVisible">{{ format(todayRevenueKobo) }}</span>
              <span v-else class="tracking-widest">••••••••</span>
            </div>
            <span class="text-[11px] text-zinc-400 mt-1">
              {{
                todaySales.length === 1
                  ? "1 sale completed today"
                  : `${todaySales.length} sales completed today`
              }}
            </span>
          </div>

          <div class="pt-4 border-t border-white/10 grid grid-cols-2 gap-4">
            <div class="flex flex-col">
              <span
                class="text-[10px] uppercase tracking-wider font-semibold text-zinc-400"
                >Total Products</span
              >
              <span class="text-sm font-bold text-zinc-100 mt-0.5"
                >{{ totalProducts }} items</span
              >
            </div>
            <div class="flex flex-col items-end text-right">
              <span
                class="text-[10px] uppercase tracking-wider font-semibold text-zinc-400"
                >Credit Balance</span
              >
              <span class="text-sm font-bold text-emerald-400 mt-0.5"
                >Free</span
              >
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-3 w-full max-w-lg">
      <NuxtLink
        to="/pos"
        class="flex flex-col items-center justify-center gap-2 p-3.5 rounded-2xl bg-(--ui-bg-elevated) border border-(--ui-border) hover:border-primary-500/40 hover:bg-(--ui-bg-accented) active:scale-95 transition-all text-center group shadow-xs"
      >
        <div
          class="w-11 h-11 rounded-xl bg-primary-500/10 text-primary-500 border border-primary-500/20 flex items-center justify-center group-hover:scale-105 group-hover:bg-primary-500 group-hover:text-white transition-all shadow-xs"
        >
          <UIcon name="i-lucide-scan-barcode" class="size-6" />
        </div>
        <div class="flex flex-col">
          <span
            class="text-xs font-bold text-(--ui-text-highlighted) group-hover:text-primary-500 transition-colors"
            >Scan to Sell</span
          >
          <span class="text-[10px] text-(--ui-text-muted)">Terminal</span>
        </div>
      </NuxtLink>

      <NuxtLink
        to="/products"
        class="flex flex-col items-center justify-center gap-2 p-3.5 rounded-2xl bg-(--ui-bg-elevated) border border-(--ui-border) hover:border-primary-500/40 hover:bg-(--ui-bg-accented) active:scale-95 transition-all text-center group shadow-xs"
      >
        <div
          class="w-11 h-11 rounded-xl bg-blue-500/10 text-blue-500 dark:text-blue-400 border border-blue-500/20 flex items-center justify-center group-hover:scale-105 group-hover:bg-blue-500 group-hover:text-white transition-all shadow-xs"
        >
          <UIcon name="i-lucide-package" class="size-6" />
        </div>
        <div class="flex flex-col">
          <span
            class="text-xs font-bold text-(--ui-text-highlighted) group-hover:text-blue-500 transition-colors"
            >Products</span
          >
          <span class="text-[10px] text-(--ui-text-muted)">Inventory</span>
        </div>
      </NuxtLink>

      <NuxtLink
        to="/sales"
        class="flex flex-col items-center justify-center gap-2 p-3.5 rounded-2xl bg-(--ui-bg-elevated) border border-(--ui-border) hover:border-primary-500/40 hover:bg-(--ui-bg-accented) active:scale-95 transition-all text-center group shadow-xs"
      >
        <div
          class="w-11 h-11 rounded-xl bg-purple-500/10 text-purple-500 dark:text-purple-400 border border-purple-500/20 flex items-center justify-center group-hover:scale-105 group-hover:bg-purple-500 group-hover:text-white transition-all shadow-xs"
        >
          <UIcon name="i-lucide-receipt" class="size-6" />
        </div>
        <div class="flex flex-col">
          <span
            class="text-xs font-bold text-(--ui-text-highlighted) group-hover:text-purple-500 transition-colors"
            >Sales</span
          >
          <span class="text-[10px] text-(--ui-text-muted)">History</span>
        </div>
      </NuxtLink>
    </div>

    <div class="">
      <DashboardPaymentMethodChart />
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="xl:col-span-2">
        <DashboardRecentSalesTable />
      </div>
      <div class="space-y-4">
        <DashboardTopProductsChart />
        <DashboardLowStockAlert />
      </div>
      <div class="">
        <DashboardRevenueChart />
      </div>
    </div>
  </div>
</template>
