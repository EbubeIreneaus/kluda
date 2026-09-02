export default defineNuxtRouteMiddleware((to) => {
  if (to.path === '/login' || to.path === '/forgot-password') {
    return
  }

  const { adminUser } = useAdminAuth()
  if (!adminUser.value) {
    return
  }

  if (adminUser.value.role === 'SUPER_ADMIN') {
    return
  }

  const perms: string[] = adminUser.value.permission || []
  if (perms.includes('manage:all')) {
    return
  }

  const routePermMap: Record<string, string[]> = {
    '/stores': ['manage:stores'],
    '/merchants': ['manage:users'],
    '/plans': ['manage:billings'],
    '/campaigns': ['manage:emails'],
    '/inbox': ['manage:emails', 'manage:support'],
    '/support': ['manage:support'],
    '/notifications': ['manage:admins', 'manage:emails'],
    '/admins': ['manage:admins'],
    '/settings': ['manage:settings', 'view:audit_logs']
  }

  const requiredPerms = routePermMap[to.path]
  if (requiredPerms && !requiredPerms.some((p) => perms.includes(p))) {
    return navigateTo('/')
  }
})
