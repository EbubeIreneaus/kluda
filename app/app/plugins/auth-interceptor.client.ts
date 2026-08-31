export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  const auth = useAuthStore()

  if (import.meta.client) {
    auth.loadFromStorage()
    if (auth.staff) {
      auth.fetchMe()
    }
  }

  let isRefreshing = false
  let refreshPromise: Promise<boolean> | null = null

  async function performRefresh(): Promise<boolean> {
    if (isRefreshing && refreshPromise) {
      return refreshPromise
    }
    isRefreshing = true
    refreshPromise = (async () => {
      try {
        const res = await $fetch<{
          success: boolean
          staff?: any
          access_token?: string
          store_id?: string
        }>(`${config.public.apiBase}/staff/auth/refresh-token`, {
          method: 'POST',
          credentials: 'include'
        })
        if (res && res.success && res.staff) {
          auth.setAuth(
            res.access_token || auth.token || '',
            res.staff,
            (res.store_id || auth.store_id) as string
          )
          return true
        }
        return false
      } catch (err: any) {
        const status = err?.statusCode || err?.status || err?.response?.status
        if (status === 401 || status === 403) {
          await auth.logout(true)
        }
        return false
      } finally {
        isRefreshing = false
        refreshPromise = null
      }
    })()
    return refreshPromise
  }

  nuxtApp.hook('app:error', (err: any) => {
    const url = String(err?.url || '')
    const status = err?.statusCode || err?.status || err?.response?.status
    const isRefreshEndpoint = url.includes('/staff/auth/refresh-token')
    if (status === 401 && isRefreshEndpoint) {
      auth.logout(true)
    }
  })
})
