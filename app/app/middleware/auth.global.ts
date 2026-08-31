export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  const isPublicRoute = to.path === '/login'

  if (import.meta.client) {
    auth.loadFromStorage()
  }

  const staffAccessToken = useCookie('staff_access_token')
  const staffRefreshToken = useCookie('staff_refresh_token')
  const hasServerSession = !!(staffAccessToken.value || staffRefreshToken.value)
  const isAuthenticated = auth.isLoggedIn || (import.meta.server && hasServerSession)

  if (!isAuthenticated && !isPublicRoute) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }

  if (isAuthenticated && to.path === '/login') {
    return navigateTo('/')
  }

  if (auth.isLoggedIn) {
    const routePermissions: Record<string, string> = {
      '/staff': 'manage:staff',
      '/analytics': 'view:analytics',
      '/customers': 'manage:user',
      '/pos': 'record:sales',
    }

    for (const [routePath, requiredPerm] of Object.entries(routePermissions)) {
      if (to.path.startsWith(routePath)) {
        if (!auth.hasPermission(requiredPerm)) {
          if (import.meta.client) {
            const toast = useToast()
            toast.add({
              title: 'Access Denied',
              description: "You don't have permission to access this page.",
              color: 'error',
            })
          }
          return navigateTo('/')
        }
      }
    }
  }
})
