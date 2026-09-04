<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { canManageBillings, isSuperAdmin } = useAdminPermission()
const toast = useToast()

interface PlanItem {
  id: number
  slug: string
  name: string
  description: string
  price: number // in kobo
  interval?: string
  has_trial?: boolean
  trial_duration_days?: number
  store_limit: number
  product_limit: number
  sales_limit_per_month: number
  analytics_read_per_month: number
  status: string
  paystack_planid: string | null
  created_at: string
  updated_at: string
}

function isPlanActive(plan: PlanItem | null | undefined): boolean {
  if (!plan || !plan.status) return false
  return String(plan.status).toLowerCase() === 'available'
}

const plans = ref<PlanItem[]>([])
const isLoading = ref(true)
const isCreateOpen = ref(false)
const isEditOpen = ref(false)
const isGrantOpen = ref(false)
const isSubmitting = ref(false)
const selectedPlan = ref<PlanItem | null>(null)

interface MerchantOption {
  user_id: string
  fullname: string
  email: string
  status: string
}
const merchantsList = ref<MerchantOption[]>([])
const merchantSearch = ref('')
const isSearchingMerchants = ref(false)

const grantForm = reactive({
  user_id: '',
  plan_slug: 'growth',
  duration_days: 14,
  description: 'Referral reward: 2 weeks complimentary Growth access',
  amountNaira: 0
})

const createForm = reactive({
  slug: '',
  name: '',
  description: '',
  priceNaira: 0,
  interval: 'monthly',
  has_trial: false,
  trial_duration_days: 14,
  store_limit: 1,
  product_limit: 100,
  sales_limit_per_month: 500,
  analytics_read_per_month: 100,
  status: 'available',
  paystack_planid: ''
})

// Form for editing an existing plan
const editForm = reactive({
  name: '',
  description: '',
  priceNaira: 0,
  interval: 'monthly',
  has_trial: false,
  trial_duration_days: 14,
  store_limit: 0,
  product_limit: 0,
  sales_limit_per_month: 0,
  analytics_read_per_month: 0,
  status: 'available',
  paystack_planid: ''
})

async function fetchPlans() {
  isLoading.value = true
  try {
    const data = await apiFetch<PlanItem[]>('/admin/plans')
    plans.value = data || []
  } catch {
    plans.value = []
  } finally {
    isLoading.value = false
  }
}

function openCreateModal() {
  createForm.slug = ''
  createForm.name = ''
  createForm.description = ''
  createForm.priceNaira = 5000
  createForm.interval = 'monthly'
  createForm.has_trial = false
  createForm.trial_duration_days = 14
  createForm.store_limit = 1
  createForm.product_limit = 100
  createForm.sales_limit_per_month = 500
  createForm.analytics_read_per_month = 100
  createForm.status = 'available'
  createForm.paystack_planid = ''
  isCreateOpen.value = true
}

function openEditModal(plan: PlanItem) {
  selectedPlan.value = plan
  editForm.name = plan.name
  editForm.description = plan.description
  // Convert kobo to Naira for editing
  editForm.priceNaira = Math.round(plan.price / 100)
  editForm.interval = plan.interval || 'monthly'
  editForm.has_trial = Boolean(plan.has_trial)
  editForm.trial_duration_days = plan.trial_duration_days || 14
  editForm.store_limit = plan.store_limit
  editForm.product_limit = plan.product_limit
  editForm.sales_limit_per_month = plan.sales_limit_per_month
  editForm.analytics_read_per_month = plan.analytics_read_per_month
  editForm.status = isPlanActive(plan) ? 'available' : 'unavailable'
  editForm.paystack_planid = plan.paystack_planid || ''
  isEditOpen.value = true
}

async function handleCreatePlan() {
  if (!createForm.slug.trim() || !createForm.name.trim()) {
    toast.add({ title: 'Missing Information', description: 'Slug and Plan Name are required.', color: 'warning' })
    return
  }

  isSubmitting.value = true
  try {
    await apiFetch('/admin/plans', {
      method: 'POST',
      body: {
        slug: createForm.slug.trim().toLowerCase(),
        name: createForm.name.trim(),
        description: createForm.description.trim(),
        // Convert Naira to kobo for backend storage
        price: Math.round(Number(createForm.priceNaira) * 100),
        interval: createForm.interval,
        has_trial: createForm.has_trial,
        trial_duration_days: createForm.has_trial ? Number(createForm.trial_duration_days || 0) : 0,
        store_limit: Number(createForm.store_limit),
        product_limit: Number(createForm.product_limit),
        sales_limit_per_month: Number(createForm.sales_limit_per_month),
        analytics_read_per_month: Number(createForm.analytics_read_per_month),
        status: createForm.status.toLowerCase(),
        paystack_planid: createForm.paystack_planid.trim() || null
      }
    })
    toast.add({ title: 'Plan Created', description: `Plan "${createForm.name}" created successfully.`, color: 'success' })
    isCreateOpen.value = false
    await fetchPlans()
  } catch (err: any) {
    const msg = getErrorMessage(err, 'Failed to create plan')
    toast.add({ title: 'Failed to Create Plan', description: msg, color: 'error' })
  } finally {
    isSubmitting.value = false
  }
}

async function handleUpdatePlan() {
  if (!selectedPlan.value) return

  isSubmitting.value = true
  try {
    await apiFetch(`/admin/plans/${selectedPlan.value.slug}`, {
      method: 'PUT',
      body: {
        name: editForm.name.trim(),
        description: editForm.description.trim(),
        // Convert Naira to kobo for backend storage
        price: Math.round(Number(editForm.priceNaira) * 100),
        interval: editForm.interval,
        has_trial: editForm.has_trial,
        trial_duration_days: editForm.has_trial ? Number(editForm.trial_duration_days || 0) : 0,
        store_limit: Number(editForm.store_limit),
        product_limit: Number(editForm.product_limit),
        sales_limit_per_month: Number(editForm.sales_limit_per_month),
        analytics_read_per_month: Number(editForm.analytics_read_per_month),
        status: editForm.status.toLowerCase(),
        paystack_planid: editForm.paystack_planid.trim() || null
      }
    })
    toast.add({ title: 'Plan Updated', description: `Plan "${editForm.name}" updated successfully.`, color: 'success' })
    isEditOpen.value = false
    await fetchPlans()
  } catch (err: any) {
    const msg = getErrorMessage(err, 'Failed to update plan')
    toast.add({ title: 'Failed to Update Plan', description: msg, color: 'error' })
  } finally {
    isSubmitting.value = false
  }
}

async function togglePlanStatus(plan: PlanItem) {
  const isAvailable = isPlanActive(plan)
  const newStatus = isAvailable ? 'unavailable' : 'available'
  const actionText = isAvailable ? 'deactivate' : 'activate'
  if (!confirm(`Are you sure you want to ${actionText} the "${plan.name}" plan?`)) return

  try {
    await apiFetch(`/admin/plans/${plan.slug}`, {
      method: 'PUT',
      body: { status: newStatus }
    })
    toast.add({ title: 'Status Updated', description: `Plan "${plan.name}" has been ${actionText}d.`, color: 'success' })
    await fetchPlans()
  } catch (err: any) {
    const msg = getErrorMessage(err, `Failed to ${actionText} plan`)
    toast.add({ title: 'Failed to Update Status', description: msg, color: 'error' })
  }
}

async function handleDeletePlan(plan: PlanItem) {
  if (plan.slug === 'free') {
    toast.add({ title: 'Action Not Allowed', description: 'The core Free plan cannot be deleted.', color: 'warning' })
    return
  }

  if (!confirm(`Are you sure you want to permanently delete "${plan.name}" (${plan.slug})?\n\nNote: Deletion will be rejected if merchants are currently assigned to this plan.`)) return

  try {
    await apiFetch(`/admin/plans/${plan.slug}`, {
      method: 'DELETE'
    })
    toast.add({ title: 'Plan Deleted', description: `Plan "${plan.name}" was permanently deleted.`, color: 'success' })
    await fetchPlans()
  } catch (err: any) {
    const msg = getErrorMessage(err, 'Failed to delete plan')
    toast.add({ title: 'Cannot Delete Plan', description: msg, color: 'error' })
  }
}

const activePlansCount = computed(() => plans.value.filter(p => isPlanActive(p)).length)
const highestPrice = computed(() => {
  if (!plans.value.length) return 0
  return Math.max(...plans.value.map(p => p.price)) / 100
})
const lowestPrice = computed(() => {
  if (!plans.value.length) return 0
  return Math.min(...plans.value.map(p => p.price)) / 100
})

async function searchMerchants() {
  isSearchingMerchants.value = true
  try {
    const data = await apiFetch<MerchantOption[]>(
      `/admin/merchants?limit=25${merchantSearch.value ? '&search=' + encodeURIComponent(merchantSearch.value) : ''}`
    )
    merchantsList.value = data || []
  } catch {
    // fallback
  } finally {
    isSearchingMerchants.value = false
  }
}

function openGrantModal() {
  grantForm.user_id = ''
  grantForm.plan_slug = plans.value.find(p => p.slug !== 'free')?.slug || 'growth'
  grantForm.duration_days = 14
  grantForm.description = 'Referral reward: 2 weeks complimentary access'
  grantForm.amountNaira = 0
  merchantSearch.value = ''
  isGrantOpen.value = true
  searchMerchants()
}

async function handleGrantOffer() {
  if (!grantForm.user_id) {
    toast.add({ title: 'Merchant Required', description: 'Please select a recipient merchant.', color: 'warning' })
    return
  }
  if (!grantForm.description || grantForm.description.trim().length < 3) {
    toast.add({ title: 'Reason Required', description: 'Please provide an audit description (e.g. Referral reward, Early VIP).', color: 'warning' })
    return
  }

  isSubmitting.value = true
  try {
    const res = await apiFetch<any>('/admin/subscriptions/grant', {
      method: 'POST',
      body: {
        user_id: grantForm.user_id,
        plan_slug: grantForm.plan_slug,
        duration_days: Number(grantForm.duration_days),
        description: grantForm.description.trim(),
        amount: Math.round((grantForm.amountNaira || 0) * 100) // to kobo
      }
    })
    toast.add({
      title: 'Offer Granted Successfully!',
      description: res.message || 'Subscription offer activated for merchant.',
      color: 'success',
      icon: 'i-lucide-check-circle'
    })
    isGrantOpen.value = false
  } catch (err: any) {
    toast.add({
      title: 'Grant Failed',
      description: getErrorMessage(err, 'Could not grant subscription offer'),
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  fetchPlans()
})
</script>

<template>
  <div class="p-6 md:p-8 flex flex-col gap-6 max-w-7xl w-full mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <UIcon name="i-lucide-credit-card" class="size-6 text-emerald-400" />
          Subscription Plans & Billing
        </h1>
        <p class="text-xs text-zinc-400 mt-0.5">
          Configure merchant billing tiers, feature quotas, pricing, and Paystack recurring subscriptions
        </p>
      </div>
      <div class="flex items-center gap-2.5">
        <UButton
          v-if="isSuperAdmin"
          label="Grant Custom Offer"
          icon="i-lucide-gift"
          color="neutral"
          variant="outline"
          size="sm"
          @click="openGrantModal"
        />
        <UButton
          v-if="canManageBillings"
          label="Create New Plan"
          icon="i-lucide-plus"
          color="primary"
          size="sm"
          @click="openCreateModal"
        />
      </div>
    </div>

    <!-- Quick Stats Bar -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-4 flex flex-col gap-1 backdrop-blur-sm">
        <span class="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">Total Plans</span>
        <div class="text-2xl font-black text-white font-mono">{{ plans.length }}</div>
        <span class="text-[10px] text-zinc-500">Configured in system</span>
      </div>

      <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-4 flex flex-col gap-1 backdrop-blur-sm">
        <span class="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">Active Tiers</span>
        <div class="text-2xl font-black text-emerald-400 font-mono">{{ activePlansCount }}</div>
        <span class="text-[10px] text-emerald-500/80">Available for checkout</span>
      </div>

      <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-4 flex flex-col gap-1 backdrop-blur-sm">
        <span class="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">Lowest Tier</span>
        <div class="text-2xl font-black text-zinc-200 font-mono">₦{{ lowestPrice.toLocaleString() }}</div>
        <span class="text-[10px] text-zinc-500">Starting price</span>
      </div>

      <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-4 flex flex-col gap-1 backdrop-blur-sm">
        <span class="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">Top Tier</span>
        <div class="text-2xl font-black text-indigo-400 font-mono">₦{{ highestPrice.toLocaleString() }}</div>
        <span class="text-[10px] text-indigo-400/70">Highest tier pricing</span>
      </div>
    </div>

    <!-- Plans Grid -->
    <div v-if="isLoading" class="p-12 text-center text-zinc-500 text-xs flex flex-col items-center gap-2">
      <UIcon name="i-lucide-loader-2" class="size-6 animate-spin text-emerald-500" />
      <span>Loading subscription plans...</span>
    </div>

    <div v-else-if="plans.length === 0" class="p-12 text-center text-zinc-500 text-xs bg-zinc-900/40 border border-zinc-800 rounded-2xl flex flex-col items-center gap-3">
      <UIcon name="i-lucide-package-open" class="size-10 text-zinc-600" />
      <div>
        <p class="text-sm font-semibold text-zinc-300">No subscription plans found</p>
        <p class="text-zinc-500 mt-1">Get started by creating your first merchant subscription tier.</p>
      </div>
      <UButton
        v-if="canManageBillings"
        label="Create Starter Plan"
        icon="i-lucide-plus"
        color="primary"
        size="xs"
        @click="openCreateModal"
      />
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="plan in plans"
        :key="plan.id"
        class="bg-zinc-900/60 border rounded-2xl p-5 flex flex-col justify-between backdrop-blur-sm transition-all relative overflow-hidden"
        :class="[
          isPlanActive(plan)
            ? 'border-zinc-800/90 hover:border-zinc-700/80 shadow-lg shadow-black/20'
            : 'border-zinc-800/40 opacity-75'
        ]"
      >
        <!-- Top Status & Slug -->
        <div>
          <div class="flex items-center justify-between gap-2 mb-3">
            <div class="flex items-center gap-1.5">
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-zinc-800 text-zinc-300 border border-zinc-700">
                {{ plan.slug }}
              </span>
              <span
                class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border"
                :class="[
                  plan.interval === 'yearly' || plan.interval === 'annually'
                    ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                    : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                ]"
              >
                {{ plan.interval || 'monthly' }}
              </span>
              <span
                v-if="plan.has_trial"
                class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-amber-500/15 text-amber-300 border border-amber-500/30 flex items-center gap-1"
              >
                <UIcon name="i-lucide-sparkles" class="size-3" />
                {{ plan.trial_duration_days || 0 }}-Day Trial
              </span>
            </div>

            <span
              :class="[
                'px-2 py-0.5 rounded text-[10px] font-semibold border',
                isPlanActive(plan)
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              ]"
            >
              {{ isPlanActive(plan) ? 'AVAILABLE' : 'UNAVAILABLE' }}
            </span>
          </div>

          <h3 class="text-lg font-bold text-white tracking-tight">{{ plan.name }}</h3>
          <p class="text-xs text-zinc-400 mt-1 min-h-[32px] line-clamp-2">{{ plan.description || 'No description provided.' }}</p>

          <!-- Price Display (converted to Naira) -->
          <div class="mt-4 pb-4 border-b border-zinc-800 flex items-baseline gap-1.5">
            <span class="text-2xl font-black text-white font-mono">₦{{ (plan.price / 100).toLocaleString() }}</span>
            <span class="text-xs text-zinc-400 font-medium">/ {{ plan.interval || 'month' }}</span>
            <span class="text-[10px] text-zinc-500 font-mono ml-auto">({{ plan.price.toLocaleString() }} kobo)</span>
          </div>

          <!-- Quotas / Limits -->
          <div class="mt-4 flex flex-col gap-2 text-xs">
            <div class="flex items-center justify-between text-zinc-300">
              <span class="flex items-center gap-1.5 text-zinc-400">
                <UIcon name="i-lucide-store" class="size-3.5 text-emerald-400" />
                Stores Allowed:
              </span>
              <span class="font-semibold font-mono text-white">
                {{ plan.store_limit && plan.store_limit > 0 ? plan.store_limit : 'Unlimited' }}
              </span>
            </div>

            <div class="flex items-center justify-between text-zinc-300">
              <span class="flex items-center gap-1.5 text-zinc-400">
                <UIcon name="i-lucide-package" class="size-3.5 text-emerald-400" />
                Products Limit:
              </span>
              <span class="font-semibold font-mono text-white">
                {{ plan.product_limit && plan.product_limit > 0 ? plan.product_limit.toLocaleString() : 'Unlimited' }}
              </span>
            </div>

            <div class="flex items-center justify-between text-zinc-300">
              <span class="flex items-center gap-1.5 text-zinc-400">
                <UIcon name="i-lucide-receipt" class="size-3.5 text-emerald-400" />
                Sales / Month:
              </span>
              <span class="font-semibold font-mono text-white">
                {{ plan.sales_limit_per_month && plan.sales_limit_per_month > 0 ? plan.sales_limit_per_month.toLocaleString() : 'Unlimited' }}
              </span>
            </div>

            <div class="flex items-center justify-between text-zinc-300">
              <span class="flex items-center gap-1.5 text-zinc-400">
                <UIcon name="i-lucide-bar-chart-3" class="size-3.5 text-emerald-400" />
                Analytics Queries:
              </span>
              <span class="font-semibold font-mono text-white">
                {{ plan.analytics_read_per_month && plan.analytics_read_per_month > 0 ? plan.analytics_read_per_month.toLocaleString() : 'Unlimited' }}
              </span>
            </div>
          </div>

          <!-- Paystack Plan Code Badge -->
          <div class="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-[11px]">
            <span class="text-zinc-500 flex items-center gap-1">
              <UIcon name="i-lucide-link-2" class="size-3" />
              Paystack Code:
            </span>
            <span v-if="plan.paystack_planid" class="font-mono text-emerald-400 font-semibold bg-emerald-950/40 border border-emerald-800/50 px-2 py-0.5 rounded text-[10px]">
              {{ plan.paystack_planid }}
            </span>
            <span v-else class="text-zinc-500 italic text-[10px]">
              Not linked
            </span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div v-if="canManageBillings" class="mt-5 pt-3 border-t border-zinc-800 flex items-center gap-2">
          <UButton
            label="Edit Plan"
            icon="i-lucide-edit-3"
            size="xs"
            color="neutral"
            variant="outline"
            class="flex-1"
            @click="openEditModal(plan)"
          />
          <UButton
            :label="isPlanActive(plan) ? 'Deactivate' : 'Activate'"
            :icon="isPlanActive(plan) ? 'i-lucide-eye-off' : 'i-lucide-eye'"
            size="xs"
            :color="isPlanActive(plan) ? 'warning' : 'primary'"
            variant="ghost"
            @click="togglePlanStatus(plan)"
          />
          <UButton
            v-if="plan.slug !== 'free'"
            label="Delete"
            icon="i-lucide-trash-2"
            size="xs"
            color="error"
            variant="ghost"
            @click="handleDeletePlan(plan)"
          />
        </div>
      </div>
    </div>

    <!-- Create Plan Modal -->
    <AdminFullScreenModal
      v-model="isCreateOpen"
      title="Create Subscription Plan"
      description="Define pricing tier limits and sync directly with Paystack"
      max-width="max-w-xl"
    >
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Plan Slug <span class="text-rose-400">*</span></label>
            <UInput v-model="createForm.slug" placeholder="e.g. starter, pro, enterprise" size="sm" />
            <span class="text-[10px] text-zinc-500 font-mono">Unique machine identifier</span>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Display Name <span class="text-rose-400">*</span></label>
            <UInput v-model="createForm.name" placeholder="e.g. Starter Plan" size="sm" />
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Description</label>
          <textarea
            v-model="createForm.description"
            rows="2"
            placeholder="Features, target merchant profile, and highlights..."
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Price (₦ Naira) <span class="text-rose-400">*</span></label>
            <UInput v-model.number="createForm.priceNaira" type="number" min="0" placeholder="5000" size="sm" />
            <span class="text-[10px] text-zinc-500 font-mono">
              = {{ ((createForm.priceNaira || 0) * 100).toLocaleString() }} kobo stored
            </span>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Billing Interval</label>
            <select
              v-model="createForm.interval"
              class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="daily">Daily Pass (24 Hours)</option>
              <option value="weekly">Weekly (7 Days)</option>
              <option value="monthly">Monthly (30 Days)</option>
              <option value="quarterly">Quarterly (90 Days)</option>
              <option value="yearly">Yearly (365 Days)</option>
            </select>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Initial Status</label>
            <select
              v-model="createForm.status"
              class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="available">AVAILABLE (Active for purchase)</option>
              <option value="unavailable">UNAVAILABLE (Hidden / Inactive)</option>
            </select>
          </div>
        </div>

        <!-- Free Trial Configuration -->
        <div class="p-3.5 bg-zinc-950/60 border border-zinc-800/80 rounded-xl flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <label class="text-xs font-bold text-zinc-200 flex items-center gap-2 cursor-pointer">
              <input
                v-model="createForm.has_trial"
                type="checkbox"
                class="rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-0 size-4"
              />
              Offer Free Trial for this Plan
            </label>
            <span v-if="createForm.has_trial" class="text-[10px] text-amber-400 font-mono">
              No Paystack charge during trial
            </span>
          </div>

          <div v-if="createForm.has_trial" class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-zinc-800/60">
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Trial Duration (in Days)</label>
              <UInput v-model.number="createForm.trial_duration_days" type="number" min="1" max="365" placeholder="14" size="xs" />
              <span class="text-[10px] text-zinc-500">e.g. 1, 3, 7, 14, 30 days</span>
            </div>
          </div>
        </div>

        <!-- Resource Quotas -->
        <div class="p-3.5 bg-zinc-950/60 border border-zinc-800/80 rounded-xl flex flex-col gap-3">
          <span class="text-xs font-bold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5">
            <UIcon name="i-lucide-sliders" class="size-3.5 text-emerald-400" />
            Resource Limits (0 = Unlimited)
          </span>

          <div class="grid grid-cols-2 gap-3">
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Stores Limit</label>
              <UInput v-model.number="createForm.store_limit" type="number" min="0" size="xs" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Products Limit</label>
              <UInput v-model.number="createForm.product_limit" type="number" min="0" size="xs" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Monthly Sales Limit</label>
              <UInput v-model.number="createForm.sales_limit_per_month" type="number" min="0" size="xs" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Analytics Reads / Mo</label>
              <UInput v-model.number="createForm.analytics_read_per_month" type="number" min="0" size="xs" />
            </div>
          </div>
        </div>

        <!-- Paystack Plan Code Override -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300 flex items-center justify-between">
            <span>Paystack Plan ID (Optional)</span>
            <span class="text-[10px] text-zinc-500 font-mono">e.g. PLN_gx2edhub320ndfa</span>
          </label>
          <UInput v-model="createForm.paystack_planid" placeholder="Leave blank to auto-create plan on Paystack" size="sm" />
          <span class="text-[10px] text-zinc-500">
            If left blank, Kluda will automatically provision this plan in your Paystack dashboard.
          </span>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isCreateOpen = false" />
          <UButton
            label="Create Plan"
            icon="i-lucide-check"
            color="primary"
            size="sm"
            :loading="isSubmitting"
            @click="handleCreatePlan"
          />
        </div>
      </template>
    </AdminFullScreenModal>

    <!-- Edit Plan Modal -->
    <AdminFullScreenModal
      v-if="selectedPlan"
      v-model="isEditOpen"
      :title="'Edit Plan: ' + selectedPlan.name"
      :description="'slug: ' + selectedPlan.slug"
      max-width="max-w-xl"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Display Name</label>
          <UInput v-model="editForm.name" size="sm" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Description</label>
          <textarea
            v-model="editForm.description"
            rows="2"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Price (₦ Naira)</label>
            <UInput v-model.number="editForm.priceNaira" type="number" min="0" size="sm" />
            <span class="text-[10px] text-zinc-500 font-mono">
              = {{ ((editForm.priceNaira || 0) * 100).toLocaleString() }} kobo stored
            </span>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Billing Interval</label>
            <select
              v-model="editForm.interval"
              class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="daily">Daily Pass (24 Hours)</option>
              <option value="weekly">Weekly (7 Days)</option>
              <option value="monthly">Monthly (30 Days)</option>
              <option value="quarterly">Quarterly (90 Days)</option>
              <option value="yearly">Yearly (365 Days)</option>
            </select>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-zinc-300">Status</label>
            <select
              v-model="editForm.status"
              class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="available">AVAILABLE (Active)</option>
              <option value="unavailable">UNAVAILABLE (Inactive / Hidden)</option>
            </select>
          </div>
        </div>

        <!-- Free Trial Configuration -->
        <div class="p-3.5 bg-zinc-950/60 border border-zinc-800/80 rounded-xl flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <label class="text-xs font-bold text-zinc-200 flex items-center gap-2 cursor-pointer">
              <input
                v-model="editForm.has_trial"
                type="checkbox"
                class="rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-0 size-4"
              />
              Offer Free Trial for this Plan
            </label>
            <span v-if="editForm.has_trial" class="text-[10px] text-amber-400 font-mono">
              No Paystack charge during trial
            </span>
          </div>

          <div v-if="editForm.has_trial" class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-zinc-800/60">
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Trial Duration (in Days)</label>
              <UInput v-model.number="editForm.trial_duration_days" type="number" min="1" max="365" placeholder="14" size="xs" />
              <span class="text-[10px] text-zinc-500">e.g. 1, 3, 7, 14, 30 days</span>
            </div>
          </div>
        </div>

        <!-- Resource Quotas -->
        <div class="p-3.5 bg-zinc-950/60 border border-zinc-800/80 rounded-xl flex flex-col gap-3">
          <span class="text-xs font-bold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5">
            <UIcon name="i-lucide-sliders" class="size-3.5 text-emerald-400" />
            Resource Limits (0 = Unlimited)
          </span>

          <div class="grid grid-cols-2 gap-3">
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Stores Limit</label>
              <UInput v-model.number="editForm.store_limit" type="number" min="0" size="xs" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Products Limit</label>
              <UInput v-model.number="editForm.product_limit" type="number" min="0" size="xs" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Monthly Sales Limit</label>
              <UInput v-model.number="editForm.sales_limit_per_month" type="number" min="0" size="xs" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[11px] text-zinc-400">Analytics Reads / Mo</label>
              <UInput v-model.number="editForm.analytics_read_per_month" type="number" min="0" size="xs" />
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-zinc-300">Paystack Plan Code</label>
          <UInput v-model="editForm.paystack_planid" placeholder="PLN_..." size="sm" />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isEditOpen = false" />
          <UButton
            label="Save Changes"
            icon="i-lucide-save"
            color="primary"
            size="sm"
            :loading="isSubmitting"
            @click="handleUpdatePlan"
          />
        </div>
      </template>
    </AdminFullScreenModal>

    <!-- Grant Custom Offer Modal (Super Admin Only) -->
    <AdminBottomSheet
      v-model="isGrantOpen"
      title="Grant Custom Subscription Offer"
      description="Super Admin Privilege: Assign complimentary access or custom promos"
      max-width="max-w-lg"
    >
      <div class="flex flex-col gap-4 text-xs">
        <!-- Merchant Selection -->
        <div class="flex flex-col gap-1.5">
          <label class="font-medium text-zinc-300 flex items-center justify-between">
            <span>Select Recipient Merchant</span>
            <span v-if="isSearchingMerchants" class="text-[10px] text-emerald-400 flex items-center gap-1">
              <UIcon name="i-lucide-loader-2" class="size-3 animate-spin" /> Searching...
            </span>
          </label>
          <div class="flex gap-2">
            <UInput
              v-model="merchantSearch"
              placeholder="Search by name or email..."
              size="sm"
              class="flex-1"
              @keyup.enter="searchMerchants"
            />
            <UButton label="Search" icon="i-lucide-search" color="neutral" variant="soft" size="sm" @click="searchMerchants" />
          </div>

          <!-- Merchant dropdown list -->
          <select
            v-model="grantForm.user_id"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500 mt-1"
          >
            <option value="" disabled>-- Select a merchant --</option>
            <option
              v-for="m in merchantsList"
              :key="m.user_id"
              :value="m.user_id"
            >
              {{ m.fullname }} ({{ m.email }})
            </option>
          </select>
        </div>

        <!-- Plan Tier -->
        <div class="flex flex-col gap-1.5">
          <label class="font-medium text-zinc-300">Target Plan Tier</label>
          <select
            v-model="grantForm.plan_slug"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
          >
            <option
              v-for="p in plans"
              :key="p.slug"
              :value="p.slug"
            >
              {{ p.name }} ({{ p.slug }}) - ₦{{ (p.price / 100).toLocaleString() }}/mo
            </option>
          </select>
        </div>

        <!-- Duration in Days & Presets -->
        <div class="flex flex-col gap-1.5">
          <label class="font-medium text-zinc-300 flex items-center justify-between">
            <span>Duration (Days)</span>
            <span class="text-[10px] text-zinc-500">Free access period length</span>
          </label>
          <div class="flex gap-1.5 mb-1.5 flex-wrap">
            <button
              type="button"
              class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition"
              :class="grantForm.duration_days === 14 ? 'bg-amber-500/20 border-amber-500/50 text-amber-300' : 'bg-zinc-800/60 border-zinc-700/60 text-zinc-400 hover:text-zinc-200'"
              @click="grantForm.duration_days = 14; grantForm.description = 'Referral reward: 2 weeks complimentary access'"
            >
              14 Days (Referral)
            </button>
            <button
              type="button"
              class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition"
              :class="grantForm.duration_days === 30 ? 'bg-amber-500/20 border-amber-500/50 text-amber-300' : 'bg-zinc-800/60 border-zinc-700/60 text-zinc-400 hover:text-zinc-200'"
              @click="grantForm.duration_days = 30; grantForm.description = 'VIP Promo: 1 month complimentary access'"
            >
              30 Days
            </button>
            <button
              type="button"
              class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition"
              :class="grantForm.duration_days === 90 ? 'bg-amber-500/20 border-amber-500/50 text-amber-300' : 'bg-zinc-800/60 border-zinc-700/60 text-zinc-400 hover:text-zinc-200'"
              @click="grantForm.duration_days = 90; grantForm.description = 'Quarterly Early Adopter Offer (90 Days)'"
            >
              90 Days
            </button>
            <button
              type="button"
              class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition"
              :class="grantForm.duration_days === 365 ? 'bg-amber-500/20 border-amber-500/50 text-amber-300' : 'bg-zinc-800/60 border-zinc-700/60 text-zinc-400 hover:text-zinc-200'"
              @click="grantForm.duration_days = 365; grantForm.description = 'Annual Founder VIP Grant (1 Year)'"
            >
              1 Year
            </button>
          </div>
          <UInput v-model.number="grantForm.duration_days" type="number" min="1" max="3650" size="sm" />
        </div>

        <!-- Audit Reason / Description -->
        <div class="flex flex-col gap-1.5">
          <label class="font-medium text-zinc-300 flex items-center justify-between">
            <span>Audit Reason / Description (Required)</span>
            <span class="text-[10px] text-zinc-500">Visible to merchant & logged in audit</span>
          </label>
          <textarea
            v-model="grantForm.description"
            rows="2"
            placeholder="e.g. Referral reward: 2 weeks Premium for referring Store ABC"
            class="bg-zinc-950 border border-zinc-800 text-xs rounded-lg p-2.5 text-zinc-200 focus:outline-none focus:border-emerald-500 resize-none"
          />
        </div>

        <!-- Custom Billed Amount (Naira, default 0) -->
        <div class="flex flex-col gap-1.5">
          <label class="font-medium text-zinc-300 flex items-center justify-between">
            <span>Billed Amount (₦ NGN)</span>
            <span class="text-[10px] text-zinc-500">0 for free/complimentary grants</span>
          </label>
          <UInput v-model.number="grantForm.amountNaira" type="number" min="0" size="sm" placeholder="0" />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isGrantOpen = false" />
          <UButton
            label="Activate Offer"
            icon="i-lucide-gift"
            color="warning"
            size="sm"
            :loading="isSubmitting"
            @click="handleGrantOffer"
          />
        </div>
      </template>
    </AdminBottomSheet>
  </div>
</template>
