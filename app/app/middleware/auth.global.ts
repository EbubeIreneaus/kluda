export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  const publicRoutes = ['/auth/login', '/auth/register', '/auth/forgot-password']
  const isPublicRoute = publicRoutes.includes(to.path) || to.path.startsWith('/auth/')

  if (import.meta.client) {
    auth.loadFromStorage()
  }

  const staffAccessToken = useCookie('staff_access_token')
  const userAccessToken = useCookie('user_access_token')
  const staffRefreshToken = useCookie('staff_refresh_token')
  const userRefreshToken = useCookie('user_refresh_token')
  const hasServerSession = !!(staffAccessToken.value || userAccessToken.value || staffRefreshToken.value || userRefreshToken.value)
  const isAuthenticated = auth.isLoggedIn || (import.meta.server && hasServerSession)

  if (!isAuthenticated && !isPublicRoute) {
    return navigateTo(`/auth/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }

  if (isAuthenticated && (to.path.startsWith("/auth"))) {
    return navigateTo('/')
  }

  if (auth.isLoggedIn) {
    if (to.path.startsWith('/marchant')) {
      const isOwnerOfAnyStore = auth.isOwner || auth.stores.some(s => s.is_owner || s.role?.toLowerCase() === 'owner')
      if (!isOwnerOfAnyStore) {
        if (import.meta.client) {
          const toast = useToast()
          toast.add({
            title: 'Merchant Access Required',
            description: 'You need store owner privileges to access the Merchant Hub.',
            color: 'warning'
          })
        }
        return navigateTo('/')
      }
    }

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
