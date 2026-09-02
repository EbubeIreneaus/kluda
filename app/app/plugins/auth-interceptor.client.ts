export default defineNuxtPlugin((nuxtApp) => {
  const auth = useAuthStore()

  if (import.meta.client) {
    auth.loadFromStorage()
    if (auth.staff) {
      auth.fetchMe()
    }
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
