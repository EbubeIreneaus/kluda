export default defineNuxtPlugin((nuxtApp) => {
  const auth = useAuthStore()

  // Load from local storage and validate with backend
  if (import.meta.client) {
    auth.loadFromStorage()
    if (auth.staff) {
      auth.fetchMe()
    }
  }

  // Provide a global error hook for fetch errors
  nuxtApp.hook('app:error', (err: any) => {
    const status = err?.statusCode || err?.status || err?.response?.status
    const detail = String(err?.data?.detail || '')
    if (status === 401 || (status === 403 && (detail.includes('token') || detail.includes('suspended') || detail.includes('terminated') || detail.includes('Session rejected')))) {
      auth.logout(true)
    }
  })
})
