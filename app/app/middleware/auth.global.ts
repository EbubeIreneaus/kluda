export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()

  // Load persisted session on every navigation (safe — reads localStorage)
  auth.loadFromStorage()

  const isPublicRoute = to.path === '/login'

  if (!auth.isLoggedIn && !isPublicRoute) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }

  // Redirect already-logged-in users away from login page
  if (auth.isLoggedIn && to.path === '/login') {
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
