<script setup lang="ts">
const steps = [
  {
    num: '01',
    title: 'Internet Drops',
    desc: 'Fiber, SIM data, or store WiFi disconnects without warning.',
    icon: 'i-lucide-wifi-off',
    badgeColor: 'text-amber-500 bg-amber-500/10 border-amber-500/20'
  },
  {
    num: '02',
    title: 'Keep Selling',
    desc: 'Cashiers scan barcodes with phone cameras and ring up customer carts.',
    icon: 'i-lucide-shopping-cart',
    badgeColor: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20'
  },
  {
    num: '03',
    title: 'Saved Locally',
    desc: 'Every item, quantity, discount, and credit record is stored securely in the browser database.',
    icon: 'i-lucide-database',
    badgeColor: 'text-cyan-500 bg-cyan-500/10 border-cyan-500/20'
  },
  {
    num: '04',
    title: 'Instant Cloud Sync',
    desc: 'When internet connectivity returns, Kluda auto-reconciles all registers and updates stock.',
    icon: 'i-lucide-refresh-cw',
    badgeColor: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20'
  }
]
</script>

<template>
  <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated)/70 p-6 sm:p-10 shadow-2xl relative overflow-hidden backdrop-blur-xl">
    <div class="absolute -right-20 -top-20 w-72 h-72 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
    <div class="absolute -left-20 -bottom-20 w-72 h-72 rounded-full bg-teal-500/10 blur-3xl pointer-events-none" />

    <div class="text-center max-w-2xl mx-auto mb-10">
      <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
        <UIcon name="i-lucide-zap" class="w-3.5 h-3.5" />
        <span>Automated Offline Continuity</span>
      </div>
      <h3 class="text-2xl sm:text-3xl font-black text-(--ui-text-highlighted) tracking-tight">
        How Offline Mode Works
      </h3>
      <p class="text-sm text-(--ui-text-muted) mt-2">
        Zero manual export files. Zero lost sales records. Complete cashier continuity.
      </p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
      <div
        v-for="(step, idx) in steps"
        :key="step.num"
        data-aos="fade-up"
        :data-aos-delay="idx * 100"
        data-aos-duration="600"
        class="relative p-6 rounded-2xl border border-(--ui-border) bg-(--ui-bg)/60 hover:border-emerald-500/30 transition group flex flex-col justify-between"
      >
        <div>
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs font-black px-2.5 py-1 rounded-lg border" :class="step.badgeColor">
              STEP {{ step.num }}
            </span>
            <div class="w-10 h-10 rounded-xl bg-(--ui-bg-elevated) border border-(--ui-border) flex items-center justify-center text-emerald-500 group-hover:scale-110 transition">
              <UIcon :name="step.icon" class="w-5 h-5" />
            </div>
          </div>
          <h4 class="text-base font-bold text-(--ui-text-highlighted) mb-2">
            {{ step.title }}
          </h4>
          <p class="text-xs text-(--ui-text-muted) leading-relaxed">
            {{ step.desc }}
          </p>
        </div>

        <div v-if="idx < steps.length - 1" class="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-10">
          <div class="w-6 h-6 rounded-full bg-(--ui-bg-elevated) border border-(--ui-border) flex items-center justify-center text-(--ui-text-muted) shadow-sm">
            <UIcon name="i-lucide-chevron-right" class="w-3.5 h-3.5" />
          </div>
        </div>
      </div>
    </div>

    <div class="mt-8 pt-6 border-t border-(--ui-border) text-center">
      <p class="text-sm font-extrabold text-emerald-500 tracking-wide">
        "Your cashier doesn't have to do anything. Kluda handles the reconciliation automatically."
      </p>
    </div>
  </div>
</template>
