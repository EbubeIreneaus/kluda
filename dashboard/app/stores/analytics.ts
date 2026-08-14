import { defineStore } from 'pinia'
import { ref } from 'vue'

export type AnalyticsPeriod = 'today' | 'week' | 'month' | '3month' | '6month' | '12month' | 'custom'

export interface TopProduct {
  name: string
  qty: number
  revenue: number
}

export interface DailyPoint {
  date: string
  count: number
}

export interface RevenuePoint {
  date: string
  revenue: number
}

export interface AnalyticsData {
  period: string
  date_from: string
  date_to: string
  total_revenue: number
  total_transactions: number
  payment_breakdown: Record<string, number>
  top_products: TopProduct[]
  daily_series: DailyPoint[]
  revenue_series: RevenuePoint[]
}

export const useAnalyticsStore = defineStore('analytics', () => {
  const data = ref<AnalyticsData | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase
  const auth = useAuthStore()

  async function fetchAnalytics(
    period: AnalyticsPeriod = 'today',
    dateFrom?: string,
    dateTo?: string
  ) {
    isLoading.value = true
    error.value = null

    try {
      const params: Record<string, string> = { period }
      if (period === 'custom' && dateFrom && dateTo) {
        params.date_from = dateFrom
        params.date_to = dateTo
      }

      const query = new URLSearchParams(params).toString()
      const result = await $fetch<AnalyticsData>(`${apiBase}/sales/analytics?${query}`, {
        headers: { Authorization: `Bearer ${auth.token ?? ''}` }
      })
      data.value = result
    } catch (err: any) {
      error.value = err?.data?.detail ?? 'Failed to load analytics'
      console.error('[Analytics] fetch error:', err)
    } finally {
      isLoading.value = false
    }
  }

  return {
    data,
    isLoading,
    error,
    fetchAnalytics
  }
})
