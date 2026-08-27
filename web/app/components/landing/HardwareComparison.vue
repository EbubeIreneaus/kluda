<script setup lang="ts">
const comparisonPoints = [
  {
    title: 'Hardware Terminal',
    traditional: '₦250,000 - ₦500,000 per counter (Desktop PC or proprietary terminal)',
    kluda: '₦0 (Use any Android phone, iPhone, iPad, tablet, or existing laptop)'
  },
  {
    title: 'Barcode Scanner Gun',
    traditional: '₦25,000 - ₦45,000 dedicated handheld USB/Bluetooth laser gun',
    kluda: 'Included (Instant continuous camera barcode scanner built-in)'
  },
  {
    title: 'Setup & Technician',
    traditional: '3 - 7 business days waiting for technician installation',
    kluda: 'Instant in 60 seconds. Open web browser and start selling.'
  },
  {
    title: 'Power Outage Survival',
    traditional: 'Crashes immediately unless connected to expensive commercial inverter',
    kluda: 'Operates continuously on device battery'
  },
  {
    title: 'Software License',
    traditional: '₦15,000 - ₦30,000/month recurring maintenance per machine',
    kluda: 'Free during Public Beta. No hardware lock-in ever.'
  }
]
</script>

<template>
  <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/60 p-6 sm:p-10 shadow-2xl backdrop-blur-xl">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
        <UIcon name="i-lucide-coins" class="w-3.5 h-3.5" />
        <span>Hardware Economics</span>
      </div>
      <h3 class="text-2xl sm:text-3xl font-black text-(--ui-text-highlighted) tracking-tight">
        Why buy a ₦250,000+ POS machine when you already have a phone?
      </h3>
      <p class="text-sm text-(--ui-text-muted) mt-2">
        Eliminate bulky checkout towers, laser guns, and specialized hardware.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <div data-aos="fade-right" data-aos-duration="600" class="p-6 rounded-2xl border border-rose-500/20 bg-rose-500/5 relative">
        <div class="flex items-center justify-between mb-4">
          <span class="text-xs font-bold text-rose-500 uppercase tracking-wider">Traditional Retail POS</span>
          <UIcon name="i-lucide-x-circle" class="w-5 h-5 text-rose-500" />
        </div>
        <div class="space-y-3 text-xs text-(--ui-text-muted)">
          <div class="p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <p class="font-bold text-(--ui-text-highlighted)">🖥️ ₦250k - ₦500k Terminal Machine</p>
            <p class="text-[11px] text-(--ui-text-dimmed)">Expensive hardware investment before opening doors</p>
          </div>
          <div class="p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <p class="font-bold text-(--ui-text-highlighted)">🔫 ₦35k Laser Barcode Scanner</p>
            <p class="text-[11px] text-(--ui-text-dimmed)">Extra cables, USB adapters, and breakable hardware</p>
          </div>
          <div class="p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <p class="font-bold text-(--ui-text-highlighted)">⚡ High Power Consumption</p>
            <p class="text-[11px] text-(--ui-text-dimmed)">Shuts down instantly during power cuts</p>
          </div>
        </div>
        <div class="mt-6 pt-4 border-t border-rose-500/20 text-center">
          <span class="text-xs font-bold text-rose-400">Total Upfront Cost: ₦300,000+ per counter</span>
        </div>
      </div>

      <div data-aos="fade-left" data-aos-duration="600" class="p-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 relative shadow-lg shadow-emerald-500/5">
        <div class="flex items-center justify-between mb-4">
          <span class="text-xs font-bold text-emerald-500 uppercase tracking-wider">Kluda Modern POS</span>
          <UIcon name="i-lucide-check-circle-2" class="w-5 h-5 text-emerald-500" />
        </div>
        <div class="space-y-3 text-xs text-(--ui-text-muted)">
          <div class="p-3 rounded-xl bg-(--ui-bg)/80 border border-emerald-500/30">
            <p class="font-bold text-(--ui-text-highlighted)">📱 ₦0 Terminal (Your Existing Phone)</p>
            <p class="text-[11px] text-emerald-500">Android, iPhone, tablet, or laptop you already carry</p>
          </div>
          <div class="p-3 rounded-xl bg-(--ui-bg)/80 border border-emerald-500/30">
            <p class="font-bold text-(--ui-text-highlighted)">📸 ₦0 Built-in Camera Scanner</p>
            <p class="text-[11px] text-emerald-500">Instant scan beep with zero external accessories</p>
          </div>
          <div class="p-3 rounded-xl bg-(--ui-bg)/80 border border-emerald-500/30">
            <p class="font-bold text-(--ui-text-highlighted)">🔋 Battery Operated Continuity</p>
            <p class="text-[11px] text-emerald-500">Runs for hours on device battery during power cuts</p>
          </div>
        </div>
        <div class="mt-6 pt-4 border-t border-emerald-500/20 text-center">
          <span class="text-xs font-extrabold text-emerald-400">Total Upfront Hardware Cost: ₦0</span>
        </div>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs border-collapse">
        <thead>
          <tr class="border-b border-(--ui-border) text-(--ui-text-muted)">
            <th class="py-3 px-4 font-bold">Category</th>
            <th class="py-3 px-4 font-bold">Traditional POS Machine</th>
            <th class="py-3 px-4 font-bold text-emerald-500">Kluda Retail Platform</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-(--ui-border)">
          <tr v-for="item in comparisonPoints" :key="item.title" class="hover:bg-(--ui-bg-accented)/50 transition">
            <td class="py-3 px-4 font-bold text-(--ui-text-highlighted)">{{ item.title }}</td>
            <td class="py-3 px-4 text-(--ui-text-muted)">{{ item.traditional }}</td>
            <td class="py-3 px-4 font-semibold text-emerald-500">{{ item.kluda }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
