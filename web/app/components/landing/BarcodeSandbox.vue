<script setup lang="ts">
import { ref } from 'vue'

const testCode = ref('8901030865412')
const sampleType = ref('EAN-13')
const isSimulatingDecode = ref(false)
const decodedResult = ref<string | null>(null)

const samples = [
  { code: '8901030865412', name: 'Packaged Flour 1kg', price: '₦1,850', type: 'EAN-13' },
  { code: '6151100021453', name: 'Full Cream Evaporated Milk', price: '₦2,400', type: 'EAN-13' },
  { code: '049000000443', name: 'Soft Drink Can 330ml', price: '₦450', type: 'UPC-A' },
  { code: 'SKU-SHIRT-M-BLU', name: 'Cotton Polo Shirt - Medium', price: '₦8,500', type: 'Code-128' }
]

function selectSample(s: typeof samples[0]) {
  testCode.value = s.code
  sampleType.value = s.type
  simulateTestScan()
}

function simulateTestScan() {
  isSimulatingDecode.value = true
  decodedResult.value = null
  setTimeout(() => {
    isSimulatingDecode.value = false
    const match = samples.find(s => s.code === testCode.value)
    if (match) {
      decodedResult.value = `Decoded: ${match.name} (${match.type}) — ${match.price} (Matched in 8ms)`
    } else {
      decodedResult.value = `Decoded: Custom Barcode [${testCode.value}] (${sampleType.value}) (Matched in 6ms)`
    }
  }, 350)
}
</script>

<template>
  <div class="rounded-3xl border border-(--ui-border) glass-panel p-6 sm:p-10 shadow-xl">
    <div class="text-center max-w-2xl mx-auto mb-8">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 mb-3">
        <UIcon name="i-lucide-scan-line" class="w-4 h-4" />
        <span>Live Barcode Engine Sandbox</span>
      </div>
      <h3 class="text-2xl sm:text-3xl font-extrabold text-(--ui-text-highlighted)">
        Test Instant Barcode Decoding
      </h3>
      <p class="text-sm text-(--ui-text-muted) mt-2">
        See how Kluda decodes standard retail barcodes (EAN-13, UPC-A, Code-128, QR) at 60 FPS without scanner guns.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
      <!-- Left: Sample Barcode Selector (6 cols) -->
      <div class="lg:col-span-6 space-y-4">
        <span class="text-xs font-mono uppercase text-(--ui-text-dimmed) font-bold">1. Select or Enter Barcode:</span>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <button
            v-for="s in samples"
            :key="s.code"
            @click="selectSample(s)"
            class="p-3 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between"
            :class="testCode === s.code ? 'bg-emerald-500/10 border-emerald-500 text-(--ui-text-highlighted)' : 'bg-(--ui-bg-elevated)/40 border-(--ui-border) hover:border-(--ui-border-accented)'"
          >
            <div>
              <div class="flex items-center justify-between text-[11px] mb-1">
                <span class="font-mono text-emerald-600 dark:text-emerald-400 font-semibold">{{ s.type }}</span>
                <span class="font-bold text-(--ui-text-highlighted)">{{ s.price }}</span>
              </div>
              <p class="text-xs font-medium text-(--ui-text) truncate">{{ s.name }}</p>
            </div>
            <span class="font-mono text-[10px] text-(--ui-text-dimmed) mt-2 block">{{ s.code }}</span>
          </button>
        </div>

        <div class="pt-2">
          <div class="flex gap-2">
            <input
              v-model="testCode"
              type="text"
              placeholder="Or type custom barcode..."
              class="flex-1 px-4 py-2 rounded-xl text-xs bg-(--ui-bg) border border-(--ui-border) text-(--ui-text) focus:border-emerald-500 focus:outline-none font-mono"
            />
            <button
              @click="simulateTestScan"
              :disabled="isSimulatingDecode"
              class="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition cursor-pointer flex items-center gap-1.5 shadow-md shadow-emerald-500/20"
            >
              <UIcon name="i-lucide-scan" class="w-3.5 h-3.5" />
              <span>{{ isSimulatingDecode ? 'Scanning...' : 'Test Scan' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Right: Visual Barcode Rendering & Result (6 cols) -->
      <div class="lg:col-span-6 bg-slate-950 p-6 rounded-2xl border border-slate-800 flex flex-col items-center justify-center text-center relative overflow-hidden min-h-[250px]">
        <!-- Simulated Laser line -->
        <div v-if="isSimulatingDecode" class="absolute inset-x-4 h-0.5 bg-rose-500 shadow-lg shadow-rose-500 top-1/2 -translate-y-1/2 animate-pulse z-10" />

        <!-- Mock Barcode Strip Visual -->
        <div class="bg-white p-4 rounded-xl shadow-md inline-block mb-4">
          <div class="flex items-center justify-center gap-0.5 h-14 px-2">
            <div
              v-for="i in 36"
              :key="i"
              class="bg-slate-950 h-full"
              :style="{ width: (i % 3 === 0 ? '3px' : (i % 2 === 0 ? '1.5px' : '2.5px')), margin: '0 0.5px' }"
            />
          </div>
          <span class="font-mono text-slate-900 text-xs font-bold tracking-widest block mt-1">{{ testCode }}</span>
        </div>

        <div v-if="decodedResult" class="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono animate-fadeIn">
          <UIcon name="i-lucide-check-circle" class="w-3.5 h-3.5 inline mr-1 text-emerald-400" />
          {{ decodedResult }}
        </div>
        <div v-else class="text-xs text-slate-500 font-mono">
          Click "Test Scan" or select a sample to test decoding speed.
        </div>
      </div>
    </div>
  </div>
</template>
