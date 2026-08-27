<script setup lang="ts">
const config = useRuntimeConfig()
const posUrl = config.public.posAppUrl || 'http://localhost:3000'
</script>

<template>
  <section class="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
    <div data-aos="zoom-in-up" data-aos-duration="700" class="max-w-6xl mx-auto rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-(--ui-bg-elevated) to-teal-950/30 p-8 sm:p-14 text-center relative shadow-2xl backdrop-blur-xl">
      <div class="absolute -right-20 -top-20 w-80 h-80 rounded-full bg-emerald-500/15 blur-3xl pointer-events-none" />
      <div class="absolute -left-20 -bottom-20 w-80 h-80 rounded-full bg-teal-500/15 blur-3xl pointer-events-none" />

      <div class="relative z-10 max-w-3xl mx-auto space-y-6">
        <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-extrabold tracking-wide uppercase">
          <UIcon name="i-lucide-sparkles" class="w-3.5 h-3.5" />
          <span>Zero Hardware. 100% Offline Resilient.</span>
        </div>

        <h2 class="text-3xl sm:text-5xl font-black text-(--ui-text-highlighted) tracking-tight leading-tight">
          Keep selling. Keep tracking.<br />
          <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            Even when you're offline.
          </span>
        </h2>

        <p class="text-sm sm:text-base text-(--ui-text-muted) max-w-2xl mx-auto leading-relaxed">
          Join early retail merchants transforming their smartphones and tablets into full checkout registers without buying specialized POS hardware.
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <NuxtLink
            to="/register"
            class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-extrabold text-sm shadow-xl shadow-emerald-500/25 transition active:scale-95"
          >
            <span>Start Selling Free</span>
            <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
          </NuxtLink>

          <a
            :href="posUrl"
            target="_blank"
            class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) hover:bg-(--ui-bg-accented) text-(--ui-text-highlighted) font-bold text-sm transition"
          >
            <UIcon name="i-lucide-scan-barcode" class="w-4 h-4 text-emerald-500" />
            <span>Launch POS Terminal</span>
          </a>
        </div>

        <div class="pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-(--ui-text-dimmed)">
          <div class="flex items-center gap-1.5">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500" />
            <span>No POS hardware to buy</span>
          </div>
          <div class="flex items-center gap-1.5">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500" />
            <span>Works offline on battery</span>
          </div>
          <div class="flex items-center gap-1.5">
            <UIcon name="i-lucide-check" class="w-4 h-4 text-emerald-500" />
            <span>Syncs automatically</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
