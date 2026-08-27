<script setup lang="ts">
import { ref, computed } from 'vue'

const isSimulatedOffline = ref(false)
const isScanning = ref(false)
const syncSuccess = ref(false)
const pendingSalesCount = ref(0)

interface DemoItem {
  id: string
  name: string
  price: number
  qty: number
}

const cart = ref<DemoItem[]>([
  { id: '1', name: 'Golden Penny Flour 1kg', price: 1850, qty: 1 },
  { id: '2', name: 'Peak Milk Full Cream 400g', price: 2400, qty: 2 },
  { id: '3', name: 'Colgate Total 140g', price: 850, qty: 1 }
])

const subtotal = computed(() => cart.value.reduce((s, i) => s + (i.price * i.qty), 0))

function addDemoProduct() {
  isScanning.value = true
  setTimeout(() => {
    isScanning.value = false
    const demoItems = [
      { id: String(Date.now()), name: 'Milo Refill Pack 500g', price: 3200, qty: 1 },
      { id: String(Date.now()), name: 'Dano Slim Milk 800g', price: 4100, qty: 1 },
      { id: String(Date.now()), name: 'Indomie Super Pack x5', price: 1750, qty: 1 }
    ]
    const chosen = demoItems[Math.floor(Math.random() * demoItems.length)]
    if (chosen) {
      cart.value.unshift(chosen)
    }
  }, 400)
}

function removeDemoItem(id: string) {
  cart.value = cart.value.filter(i => i.id !== id)
}

function completeCheckout() {
  if (isSimulatedOffline.value) {
    pendingSalesCount.value++
    cart.value = []
  } else {
    syncSuccess.value = true
    cart.value = []
    setTimeout(() => {
      syncSuccess.value = false
    }, 2500)
  }
}

function toggleOffline() {
  isSimulatedOffline.value = !isSimulatedOffline.value
  if (!isSimulatedOffline.value && pendingSalesCount.value > 0) {
    syncSuccess.value = true
    pendingSalesCount.value = 0
    setTimeout(() => {
      syncSuccess.value = false
    }, 2500)
  }
}

function formatNgn(amount: number) {
  return '₦' + amount.toLocaleString('en-NG')
}
</script>

<template>
  <div class="relative rounded-2xl overflow-hidden glass-panel shadow-2xl border border-emerald-500/20 max-w-2xl mx-auto">
    <!-- Terminal Header / Mock OS bar -->
    <div class="bg-slate-900/90 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-rose-500/80" />
        <div class="w-3 h-3 rounded-full bg-amber-500/80" />
        <div class="w-3 h-3 rounded-full bg-emerald-500/80" />
        <span class="text-xs font-mono text-slate-400 ml-2">Terminal #01 • Cashier: Joy (STF102)</span>
      </div>

      <!-- Offline toggle pill -->
      <button
        @click="toggleOffline"
        class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-300 cursor-pointer"
        :class="isSimulatedOffline ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'"
      >
        <span class="w-2 h-2 rounded-full" :class="isSimulatedOffline ? 'bg-amber-400' : 'bg-emerald-400 animate-ping'" />
        <span>{{ isSimulatedOffline ? 'Simulating Offline' : 'Online Sync Active' }}</span>
      </button>
    </div>

    <!-- Terminal Workspace -->
    <div class="p-4 sm:p-5 grid grid-cols-1 sm:grid-cols-5 gap-4">
      <!-- Left: Interactive Scanner & Actions (2 cols) -->
      <div class="sm:col-span-2 flex flex-col gap-3">
        <!-- Live Scanner Viewfinder Simulation -->
        <div class="relative h-36 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col items-center justify-center overflow-hidden p-3 text-center">
          <div class="absolute inset-2 border-2 border-dashed border-emerald-500/40 rounded-lg pointer-events-none" />
          <div v-if="isScanning" class="absolute inset-x-0 h-0.5 bg-emerald-400 shadow-lg shadow-emerald-500/80 top-1/2 -translate-y-1/2 animate-bounce" />

          <UIcon name="i-lucide-camera" class="w-8 h-8 text-emerald-400 mb-1" />
          <span class="text-xs font-medium text-slate-300">Camera Scanner</span>
          <span class="text-[10px] text-slate-500">60 FPS Hardware Decoding</span>

          <button
            @click="addDemoProduct"
            :disabled="isScanning"
            class="mt-2 w-full py-1.5 px-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition flex items-center justify-center gap-1.5 shadow-md shadow-emerald-500/20 cursor-pointer"
          >
            <UIcon name="i-lucide-scan" class="w-3.5 h-3.5" />
            <span>{{ isScanning ? 'Decoding...' : 'Simulate Scan' }}</span>
          </button>
        </div>

        <!-- Offline Sync Status Card -->
        <div class="rounded-xl p-3 bg-slate-900/60 border border-slate-800/80 text-xs">
          <div class="flex items-center justify-between mb-1">
            <span class="text-slate-400">Offline Sales Vault</span>
            <span class="font-mono font-bold text-emerald-400">{{ pendingSalesCount }} saved offline</span>
          </div>
          <p class="text-[11px] text-slate-400 leading-tight">
            {{ isSimulatedOffline ? 'Sale safely locked on this device. Will automatically sync to cloud once connected.' : 'Instant checkout ready. Changes sync across counters in real-time.' }}
          </p>
        </div>
      </div>

      <!-- Right: Active Cart & Charge (3 cols) -->
      <div class="sm:col-span-3 flex flex-col justify-between bg-slate-900/40 rounded-xl p-3 border border-slate-800/60 min-h-[220px]">
        <div>
          <div class="flex items-center justify-between pb-2 border-b border-slate-800 text-xs font-semibold text-slate-300">
            <span>Item</span>
            <span>Total</span>
          </div>

          <div v-if="cart.length === 0" class="py-8 text-center text-xs text-slate-500">
            <template v-if="syncSuccess">
              <div class="inline-flex items-center justify-center w-10 h-10 rounded-full bg-emerald-500/20 text-emerald-400 mb-2">
                <UIcon name="i-lucide-check-check" class="w-6 h-6" />
              </div>
              <p class="text-emerald-400 font-semibold text-sm">Sale Synced Successfully!</p>
              <p class="text-[11px] text-slate-400 mt-0.5">Receipt printed & stock updated</p>
            </template>
            <template v-else>
              <UIcon name="i-lucide-shopping-cart" class="w-6 h-6 mx-auto mb-1 text-slate-600" />
              <span>Cart is empty. Click "Simulate Scan" above!</span>
            </template>
          </div>

          <div v-else class="space-y-1.5 max-h-36 overflow-y-auto py-1.5 pr-1">
            <div
              v-for="item in cart"
              :key="item.id"
              class="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-slate-800/40 hover:bg-slate-800/80 transition"
            >
              <div class="truncate max-w-[130px]">
                <div class="font-medium text-slate-200 truncate">{{ item.name }}</div>
                <div class="text-[10px] text-slate-500">{{ item.qty }} × {{ formatNgn(item.price) }}</div>
              </div>
              <div class="flex items-center gap-2">
                <span class="font-mono font-semibold text-emerald-400">{{ formatNgn(item.price * item.qty) }}</span>
                <button
                  @click="removeDemoItem(item.id)"
                  class="text-slate-500 hover:text-rose-400 transition"
                >
                  <UIcon name="i-lucide-x" class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Total & Checkout -->
        <div class="pt-3 border-t border-slate-800 mt-2">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-slate-400">Subtotal</span>
            <span class="font-mono text-base font-bold text-white">{{ formatNgn(subtotal) }}</span>
          </div>

          <button
            @click="completeCheckout"
            :disabled="cart.length === 0"
            class="w-full py-2 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 disabled:opacity-40 disabled:cursor-not-allowed text-slate-950 font-bold text-xs tracking-wide uppercase transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 cursor-pointer"
          >
            <UIcon name="i-lucide-zap" class="w-4 h-4" />
            <span>{{ isSimulatedOffline ? 'Charge Offline' : 'Instant Checkout' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
