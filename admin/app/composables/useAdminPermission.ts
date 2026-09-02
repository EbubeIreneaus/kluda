export function useAdminPermission() {
  const { adminUser } = useAdminAuth()

  function hasPermission(perm: string): boolean {
    if (!adminUser.value) return false
    if (adminUser.value.role === 'SUPER_ADMIN') return true
    const permissions: string[] = adminUser.value.permission || []
    if (permissions.includes('manage:all')) return true
    return permissions.includes(perm)
  }

  const canManageAdmins = computed(() => hasPermission('manage:admins'))
  const canManageStores = computed(() => hasPermission('manage:stores'))
  const canManageMerchants = computed(() => hasPermission('manage:users'))
  const canManageBillings = computed(() => hasPermission('manage:billings'))
  const canManageEmails = computed(() => hasPermission('manage:emails'))
  const canManageSupport = computed(() => hasPermission('manage:support'))
  const canManageSettings = computed(() => hasPermission('manage:settings'))
  const canViewAudit = computed(() => hasPermission('view:audit_logs'))
  const canViewAnalytics = computed(() => hasPermission('view:analytics'))
  const isSuperAdmin = computed(() => {
    const role = String(adminUser.value?.role || '').toUpperCase()
    return role === 'SUPER_ADMIN' || role === 'ADMIN' || (adminUser.value?.permission || []).includes('manage:all')
  })

  return {
    hasPermission,
    isSuperAdmin,
    canManageAdmins,
    canManageStores,
    canManageMerchants,
    canManageBillings,
    canManageEmails,
    canManageSupport,
    canManageSettings,
    canViewAudit,
    canViewAnalytics
  }
}
