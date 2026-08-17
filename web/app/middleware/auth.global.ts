export default defineNuxtRouteMiddleware((to) => {
  const ownerStore = useOwnerStore()
  ownerStore.loadFromStorage()

  const isPublicRoute = to.path === '/' || to.path === '/login' || to.path === '/register'

  if (to.path.startsWith('/dashboard') && !ownerStore.isLoggedIn) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }

  if (ownerStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    return navigateTo('/dashboard')
  }
})
