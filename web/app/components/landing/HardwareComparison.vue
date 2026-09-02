<script setup lang="ts">
const comparisonPoints = [
  {
    title: 'Counter Terminal',
    traditional: '₦250,000 - ₦500,000 per counter (Bulky desktop PC & monitor)',
    kluda: '₦0 (Use any Android phone, iPhone, iPad, tablet, or laptop)'
  },
  {
    title: 'Theft & Cash Control',
    traditional: 'High risk: Sales staff pocket cash or under-report daily sales',
    kluda: 'Complete lock: Every sale is tied to cashier shift & receipt'
  },
  {
    title: 'Stock & Inventory Keeping',
    traditional: 'Manual guesswork or evening book counting with missing items',
    kluda: 'Real-time deduction: Know exact units and cartons remaining'
  },
  {
    title: 'Customer Debt Tracking',
    traditional: 'Scribbled in torn paper books (frequently disputed or lost)',
    kluda: 'Digital Debt Ledger: Log credit in 2 taps & track repayments'
  },
  {
    title: 'Barcode Scanner Gun',
    traditional: '₦25,000 - ₦45,000 dedicated handheld USB/Bluetooth laser gun',
    kluda: 'Included: High-speed phone camera scanner with audio chime'
  },
  {
    title: 'Setup & Operation',
    traditional: '3 - 7 days waiting for hardware setup & technician visits',
    kluda: 'Instant in 60 seconds: Open web link and start selling'
  }
]
</script>

<template>
  <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/60 p-6 sm:p-10 shadow-2xl backdrop-blur-xl">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
        <UIcon name="i-lucide-scale" class="w-3.5 h-3.5" />
        <span>Smart Store Economics</span>
      </div>
      <h3 class="text-2xl sm:text-3xl font-black text-(--ui-text-highlighted) tracking-tight">
        Why buy a ₦300,000+ POS machine when your phone is all you need?
      </h3>
      <p class="text-sm text-(--ui-text-muted) mt-2">
        Get full supermarket-grade sales tracking, theft protection, and stock monitoring without the heavy price tag.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <div data-aos="fade-right" data-aos-duration="600" class="p-6 rounded-2xl border border-rose-500/20 bg-rose-500/5 relative">
        <div class="flex items-center justify-between mb-4">
          <span class="text-xs font-bold text-rose-500 uppercase tracking-wider">Paper Books & Bulky POS Towers</span>
          <UIcon name="i-lucide-x-circle" class="w-5 h-5 text-rose-500" />
        </div>
        <div class="space-y-3 text-xs text-(--ui-text-muted)">
          <div class="p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <p class="font-bold text-(--ui-text-highlighted)">💸 Cash Pocketing & Staff Theft</p>
            <p class="text-[11px] text-(--ui-text-dimmed)">Unrecorded sales and missing cash at the end of the day</p>
          </div>
          <div class="p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <p class="font-bold text-(--ui-text-highlighted)">📖 Lost & Disputed Customer Debts</p>
            <p class="text-[11px] text-(--ui-text-dimmed)">Customer credit recorded in paper books that get torn or lost</p>
          </div>
          <div class="p-3 rounded-xl bg-(--ui-bg)/60 border border-(--ui-border)">
            <p class="font-bold text-(--ui-text-highlighted)">🖥️ ₦300,000+ Upfront Machine Setup</p>
            <p class="text-[11px] text-(--ui-text-dimmed)">Expensive desktop towers, external laser guns, and wiring</p>
          </div>
        </div>
        <div class="mt-6 pt-4 border-t border-rose-500/20 text-center">
          <span class="text-xs font-bold text-rose-400">High Risk of Lost Profits & Stolen Cash</span>
        </div>
      </div>

      <div data-aos="fade-left" data-aos-duration="600" class="p-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 relative shadow-lg shadow-emerald-500/5">
        <div class="flex items-center justify-between mb-4">
          <span class="text-xs font-bold text-emerald-500 uppercase tracking-wider">Kluda Modern POS</span>
          <UIcon name="i-lucide-check-circle-2" class="w-5 h-5 text-emerald-500" />
        </div>
        <div class="space-y-3 text-xs text-(--ui-text-muted)">
          <div class="p-3 rounded-xl bg-(--ui-bg)/80 border border-emerald-500/30">
            <p class="font-bold text-(--ui-text-highlighted)">🛡️ 100% Cash & Stock Accountability</p>
            <p class="text-[11px] text-emerald-500">Every single transaction is logged, time-stamped, and tied to cashier</p>
          </div>
          <div class="p-3 rounded-xl bg-(--ui-bg)/80 border border-emerald-500/30">
            <p class="font-bold text-(--ui-text-highlighted)">📒 Integrated Digital Debt Ledger</p>
            <p class="text-[11px] text-emerald-500">Log customer credits in 2 taps and track every partial repayment</p>
          </div>
          <div class="p-3 rounded-xl bg-(--ui-bg)/80 border border-emerald-500/30">
            <p class="font-bold text-(--ui-text-highlighted)">📱 ₦0 Terminal Setup (Your Existing Phone)</p>
            <p class="text-[11px] text-emerald-500">Turn any smartphone or tablet into a high-speed checkout register</p>
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
            <th class="py-3 px-4 font-bold">Store Capability</th>
            <th class="py-3 px-4 font-bold text-rose-400">Paper Books / Old POS Machines</th>
            <th class="py-3 px-4 font-bold text-emerald-400">Kluda Mobile POS</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-(--ui-border)">
          <tr v-for="pt in comparisonPoints" :key="pt.title" class="hover:bg-(--ui-bg)/40 transition">
            <td class="py-3.5 px-4 font-bold text-(--ui-text-highlighted)">{{ pt.title }}</td>
            <td class="py-3.5 px-4 text-rose-300/80">{{ pt.traditional }}</td>
            <td class="py-3.5 px-4 font-bold text-emerald-400">{{ pt.kluda }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
