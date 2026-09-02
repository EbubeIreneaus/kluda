import { ref, computed } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useSalesStore } from '~/stores/sales'
import { useProductsStore } from '~/stores/product'
import { useApi } from '~/composables/useApi'

// Shared reactive state across all components
const currentSubscriptionData = ref<any | null>(null)
const availablePlans = ref<any[]>([])
const isLoading = ref(false)

export function useSubscription() {
  const auth = useAuthStore()
  const salesStore = useSalesStore()
  const productStore = useProductsStore()
  const { api } = useApi()

  async function fetchCurrentSubscription() {
    isLoading.value = true
    try {
      const storeId = auth.current_store?.store_id
      const url = storeId ? `/subscriptions/current?store_id=${storeId}` : '/subscriptions/current'
      const data = await api<any>(url)
      currentSubscriptionData.value = data

      if (typeof window !== 'undefined' && data) {
        if (data.quota_token) {
          localStorage.setItem('kluda_quota_token', data.quota_token)
        }
        localStorage.setItem('kluda_last_sync_ts', String(Date.now()))
        if (data.max_offline_days) {
          localStorage.setItem('kluda_max_offline_days', String(data.max_offline_days))
        }
        if (data.offline_disclaimer) {
          localStorage.setItem('kluda_offline_disclaimer', data.offline_disclaimer)
        }
      }

      if (auth.current_store) {
        auth.current_store.owner_subscription = data
        if (data.owner_name) {
          auth.current_store.owner_name = data.owner_name
        }
      }
      if (auth.user) {
        auth.user.current_subscription = data
      }
      return data
    } catch {
      // Keep existing or fallback state if offline / error
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchAvailablePlans() {
    try {
      const data = await api<any[]>('/subscriptions/plans')
      availablePlans.value = data || []
      return availablePlans.value
    } catch {
      return []
    }
  }

  async function subscribePlan(planSlug: string) {
    isLoading.value = true
    try {
      const res = await api<{
        status: string
        redirect_url?: string | null
        reference?: string | null
        message: string
      }>('/subscriptions/subscribe', {
        method: 'POST',
        body: { plan_slug: planSlug }
      })

      if (res.status === 'active') {
        await fetchCurrentSubscription()
      }
      return res
    } finally {
      isLoading.value = false
    }
  }

  async function cancelPlan() {
    isLoading.value = true
    try {
      const res = await api<{ status: string; message: string }>('/subscriptions/cancel', {
        method: 'POST'
      })
      await fetchCurrentSubscription()
      return res
    } finally {
      isLoading.value = false
    }
  }

  const rawSub = computed(() => {
    return currentSubscriptionData.value || auth.current_store?.owner_subscription || auth.user?.current_subscription || null
  })

  const plan = computed(() => {
    if (rawSub.value?.plan) {
      return rawSub.value.plan
    }
    // Default tier fallback
    return {
      slug: 'free',
      name: 'Free Tier',
      description: 'Essential single-store retail operations with offline checkout.',
      // subunit in kobo
      price: 0,
      store_limit: 1,
      product_limit: 100,
      sales_limit_per_month: 200,
      analytics_read_per_month: 50,
      status: 'AVAILABLE'
    }
  })

  const hasUsedTrial = computed(() => {
    return !!rawSub.value?.has_used_trial
  })

  const status = computed<'ACTIVE' | 'DUE' | 'EXPIRED'>(() => {
    const s = (rawSub.value?.status || 'ACTIVE').toUpperCase()
    if (s === 'DUE') return 'DUE'
    if (s === 'EXPIRED') return 'EXPIRED'
    return 'ACTIVE'
  })

  const isActive = computed(() => status.value === 'ACTIVE')
  const isDue = computed(() => status.value === 'DUE')
  const isExpired = computed(() => status.value === 'EXPIRED')

  const ownerName = computed(() => {
    return rawSub.value?.owner_name || auth.current_store?.owner_name || auth.user?.fullname || 'Store Owner'
  })

  const isOwner = computed(() => {
    if (rawSub.value?.is_owner !== undefined) {
      return !!rawSub.value.is_owner
    }
    return auth.isOwner
  })

  // Combined organization quotas across all stores
  const usage = computed(() => {
    const u = rawSub.value?.usage
    const monthlySalesLimit = plan.value.sales_limit_per_month || 500
    const productsLimit = plan.value.product_limit || 100
    const storesLimit = plan.value.store_limit || 1

    const monthlySalesCount = u?.monthly_sales_count !== undefined 
      ? u.monthly_sales_count 
      : salesStore.sales.length

    const productsCount = u?.products_count !== undefined 
      ? u.products_count 
      : productStore.productCount

    const storesCount = u?.stores_count !== undefined 
      ? u.stores_count 
      : (auth.stores.filter(s => s.is_owner).length || 1)

    const salesPercent = monthlySalesLimit > 0 
      ? Math.min(Math.round((monthlySalesCount / monthlySalesLimit) * 100), 100) 
      : 0

    const productsPercent = productsLimit > 0 
      ? Math.min(Math.round((productsCount / productsLimit) * 100), 100) 
      : 0

    const storesPercent = storesLimit > 0 
      ? Math.min(Math.round((storesCount / storesLimit) * 100), 100) 
      : 0

    return {
      monthlySalesCount,
      monthlySalesLimit,
      salesPercent,
      isNearSalesLimit: salesPercent >= 80,
      isAtSalesLimit: salesPercent >= 100,

      productsCount,
      productsLimit,
      productsPercent,
      isNearProductsLimit: productsPercent >= 85,

      storesCount,
      storesLimit,
      storesPercent,

      monthlyAnalyticsCount: u?.monthly_analytics_count || 14,
      monthlyAnalyticsLimit: plan.value.analytics_read_per_month || 100
    }
  })

  const priceFormatted = computed(() => {
    const kobo = plan.value.price || 0
    if (kobo === 0) return 'Free'
    return `₦${(kobo / 100).toLocaleString()}`
  })

  const nextRenewalFormatted = computed(() => {
    if (rawSub.value?.next_renewal) {
      const d = new Date(rawSub.value.next_renewal)
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    }
    const d = new Date()
    d.setDate(d.getDate() + 30)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  })

  const daysRemaining = computed(() => {
    if (rawSub.value?.next_renewal) {
      const d = new Date(rawSub.value.next_renewal)
      const diff = Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
      return Math.max(diff, 0)
    }
    return 30
  })

  function parseSignedToken(token: string) {
    try {
      const parts = token.split('.')
      if (parts.length !== 2 || !parts[0]) return null
      const b64 = parts[0]
      const jsonStr = atob(b64.replace(/-/g, '+').replace(/_/g, '/'))
      return JSON.parse(jsonStr)
    } catch {
      return null
    }
  }

  const isOnline = useOnline()

  const offlineQuotaState = computed(() => {
    if (typeof window === 'undefined') {
      return { isBlocked: false, reason: '', isOfflineExpired: false, isSalesExceeded: false }
    }

    const tokenStr = localStorage.getItem('kluda_quota_token') || currentSubscriptionData.value?.quota_token
    const lastSyncStr = localStorage.getItem('kluda_last_sync_ts')
    const lastSyncTs = lastSyncStr ? parseInt(lastSyncStr, 10) : Date.now()
    const maxDays = parseInt(localStorage.getItem('kluda_max_offline_days') || '3', 10) || 3

    if (!tokenStr) {
      return { isBlocked: false, reason: '', isOfflineExpired: false, isSalesExceeded: false }
    }

    const parsed = parseSignedToken(tokenStr)
    if (!parsed) {
      return {
        isBlocked: true,
        reason: 'Security Alert: Quota signature validation failed or local data was modified. Please connect to internet to verify your account.',
        isOfflineExpired: false,
        isSalesExceeded: false
      }
    }

    // 1. Offline lease check
    const now = Date.now()
    const offlineMs = now - lastSyncTs
    const maxOfflineMs = maxDays * 24 * 60 * 60 * 1000
    const isExpired = (!isOnline.value) && (offlineMs > maxOfflineMs)

    if (isExpired) {
      return {
        isBlocked: true,
        isOfflineExpired: true,
        isSalesExceeded: false,
        reason: `Terminal Sync Required: Offline mode has expired (maximum ${maxDays} days allowed from last sync). Offline means service disruption won't affect sales, not working offline without turning on data. Please connect to the internet to sync pending transactions.`
      }
    }

    // 2. Sales limit check
    const limit = parsed.monthly_sales_limit || 0
    if (limit > 0) {
      const pendingSalesCount = salesStore.sales.filter(s => s.status === 'pending' || s.sale_id === 'SYNCING').length
      const currentSales = (parsed.monthly_sales_count || 0) + pendingSalesCount
      if (currentSales >= limit) {
        return {
          isBlocked: true,
          isOfflineExpired: false,
          isSalesExceeded: true,
          reason: `Monthly sales limit reached (${currentSales} / ${limit}). Upgrade your subscription plan to record more sales.`
        }
      }
    }

    return { isBlocked: false, reason: '', isOfflineExpired: false, isSalesExceeded: false }
  })

  const isQuotaBlocked = computed(() => offlineQuotaState.value.isBlocked)
  const quotaBlockReason = computed(() => offlineQuotaState.value.reason)
  const isOfflineLeaseExpired = computed(() => offlineQuotaState.value.isOfflineExpired)
  const offlineDisclaimer = computed(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('kluda_offline_disclaimer') || "Offline means service disruption won't affect sales. Not working offline without turning on data."
    }
    return "Offline means service disruption won't affect sales. Not working offline without turning on data."
  })

  return {
    rawSub,
    plan,
    status,
    isActive,
    isDue,
    isExpired,
    ownerName,
    isOwner,
    usage,
    priceFormatted,
    nextRenewalFormatted,
    daysRemaining,
    availablePlans,
    hasUsedTrial,
    isQuotaBlocked,
    quotaBlockReason,
    isOfflineLeaseExpired,
    offlineDisclaimer,
    isLoading,
    fetchCurrentSubscription,
    fetchAvailablePlans,
    subscribePlan,
    cancelPlan
  }
}
