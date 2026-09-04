<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { adminUser } = useAdminAuth()

const overview = ref<any>({
  total_merchants: 0,
  new_merchants_today: 0,
  total_stores: 0,
  active_stores: 0,
  active_paid_subscriptions: 0,
  trial_subscriptions: 0,
  free_subscriptions: 0,
  monthly_recurring_revenue: 0,
  subscription_distribution: [],
  open_tickets: 0,
  unread_threads: 0
})

const isLoading = ref(true)

async function fetchOverview() {
  isLoading.value = true
  try {
    const data = await apiFetch<any>('/admin/analytics/overview')
    overview.value = data
  } catch {
    // fallback
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchOverview()
})

const kpiCards = computed(() => [
  {
    title: 'Monthly Recurring Revenue (MRR)',
    value: `₦${Number(overview.value.monthly_recurring_revenue || 0).toLocaleString()}`,
    sub: `${overview.value.active_paid_subscriptions || 0} active paying merchants`,
    icon: 'i-lucide-banknote',
    color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
  },
  {
    title: 'Merchants & Store Owners',
    value: `${overview.value.total_merchants || 0}`,
    sub: `+${overview.value.new_merchants_today || 0} registered today`,
    icon: 'i-lucide-users',
    color: 'text-blue-400 bg-blue-500/10 border-blue-500/20'
  },
  {
    title: 'Active Paid & Pro Trials',
    value: `${(overview.value.active_paid_subscriptions || 0) + (overview.value.trial_subscriptions || 0)}`,
    sub: `${overview.value.trial_subscriptions || 0} in active 30-day Pro Trial`,
    icon: 'i-lucide-sparkles',
    color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20'
  },
  {
    title: 'Active Retail Branches',
    value: `${overview.value.active_stores || 0}`,
    sub: `${overview.value.total_stores || 0} total stores on platform`,
    icon: 'i-lucide-store',
    color: 'text-teal-400 bg-teal-500/10 border-teal-500/20'
  }
])
</script>

<template>
  <div class="overflow-y-auto p-6 md:p-8 flex flex-col gap-8 max-w-7xl w-full mx-auto">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800/80 pb-6">
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-2xl font-bold tracking-tight text-white">Kluda Platform Dashboard</h1>
          <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Live SaaS Control
          </span>
        </div>
        <p class="text-xs text-zinc-400 mt-1">Platform management overview for {{ adminUser?.fullname }} ({{ adminUser?.role }})</p>
      </div>

      <div class="flex items-center gap-2.5">
        <UButton
          to="/campaigns"
          icon="i-lucide-megaphone"
          label="New Campaign"
          color="primary"
          size="sm"
        />
        <UButton
          to="/notifications"
          icon="i-lucide-send"
          label="Push Broadcast"
          color="neutral"
          variant="outline"
          size="sm"
        />
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="(kpi, i) in kpiCards"
        :key="i"
        class="bg-zinc-900/60 border border-zinc-800/80 p-5 rounded-2xl flex flex-col justify-between gap-4 backdrop-blur-sm shadow-sm"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-zinc-400">{{ kpi.title }}</span>
          <div :class="['w-8 h-8 rounded-xl flex items-center justify-center border', kpi.color]">
            <UIcon :name="kpi.icon" class="w-4 h-4" />
          </div>
        </div>
        <div>
          <div class="text-2xl font-black tracking-tight text-white font-mono">{{ kpi.value }}</div>
          <div class="text-[11px] text-zinc-400 mt-1">{{ kpi.sub }}</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-bold text-white">Platform Subsystems & Shortcuts</h2>
            <p class="text-xs text-zinc-400 mt-0.5">Direct management of platform resources and operational teams</p>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
          <NuxtLink
            to="/merchants"
            class="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80 hover:border-emerald-500/30 hover:bg-zinc-900 transition-all flex items-start gap-3.5 group"
          >
            <div class="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <UIcon name="i-lucide-users" class="w-5 h-5" />
            </div>
            <div>
              <div class="text-xs font-bold text-zinc-200 group-hover:text-emerald-400 transition-colors">Merchant Accounts</div>
              <div class="text-[11px] text-zinc-400 mt-0.5">Manage store owners, inspect active subscriptions, and trigger password reset codes.</div>
            </div>
          </NuxtLink>

          <NuxtLink
            to="/stores"
            class="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80 hover:border-emerald-500/30 hover:bg-zinc-900 transition-all flex items-start gap-3.5 group"
          >
            <div class="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <UIcon name="i-lucide-store" class="w-5 h-5" />
            </div>
            <div>
              <div class="text-xs font-bold text-zinc-200 group-hover:text-emerald-400 transition-colors">Store Branches & Terminals</div>
              <div class="text-[11px] text-zinc-400 mt-0.5">Moderate retail stores, inspect cashier staff, product counts, and suspend/activate.</div>
            </div>
          </NuxtLink>

          <NuxtLink
            to="/campaigns"
            class="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80 hover:border-emerald-500/30 hover:bg-zinc-900 transition-all flex items-start gap-3.5 group"
          >
            <div class="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <UIcon name="i-lucide-megaphone" class="w-5 h-5" />
            </div>
            <div>
              <div class="text-xs font-bold text-zinc-200 group-hover:text-emerald-400 transition-colors">Email Campaigns</div>
              <div class="text-[11px] text-zinc-400 mt-0.5">Visual WYSIWYG newsletter composer with Cloudinary media and audience targeting.</div>
            </div>
          </NuxtLink>

          <NuxtLink
            to="/inbox"
            class="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80 hover:border-emerald-500/30 hover:bg-zinc-900 transition-all flex items-start gap-3.5 group"
          >
            <div class="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <UIcon name="i-lucide-mail" class="w-5 h-5" />
            </div>
            <div>
              <div class="text-xs font-bold text-zinc-200 group-hover:text-emerald-400 transition-colors">Support Email Desk</div>
              <div class="text-[11px] text-zinc-400 mt-0.5">Company mailboxes, outbound customer composition, and 1-on-1 response chains.</div>
            </div>
          </NuxtLink>
        </div>
      </div>

      <div class="bg-zinc-900/60 border border-zinc-800/80 p-6 rounded-2xl flex flex-col justify-between gap-4">
        <div>
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-sm font-bold text-white">Subscription Health</h2>
              <p class="text-xs text-zinc-400 mt-0.5">Active tier distribution</p>
            </div>
            <NuxtLink to="/plans" class="text-[11px] text-emerald-400 hover:underline">
              Manage Tiers
            </NuxtLink>
          </div>

          <div class="flex flex-col gap-2.5 mt-4">
            <div
              v-for="item in overview.subscription_distribution || []"
              :key="item.slug"
              class="flex items-center justify-between text-xs p-2.5 rounded-lg bg-zinc-950/80 border border-zinc-800"
            >
              <div class="flex items-center gap-2">
                <div
                  :class="[
                    'w-2 h-2 rounded-full',
                    item.slug === 'growth' ? 'bg-emerald-400' :
                    item.slug === 'enterprise' ? 'bg-indigo-400' :
                    item.slug === 'trial' ? 'bg-amber-400' : 'bg-zinc-500'
                  ]"
                />
                <span class="text-zinc-300 font-medium">{{ item.plan }}</span>
              </div>
              <span class="font-mono font-bold text-white">{{ item.count }}</span>
            </div>
          </div>
        </div>

        <div class="flex gap-2">
          <UButton
            to="/plans"
            label="View Plans"
            icon="i-lucide-credit-card"
            color="primary"
            variant="solid"
            block
            size="sm"
          />
          <UButton
            to="/settings"
            label="System Config"
            icon="i-lucide-sliders-horizontal"
            color="neutral"
            variant="outline"
            block
            size="sm"
          />
        </div>
      </div>
    </div>
  </div>
</template>
