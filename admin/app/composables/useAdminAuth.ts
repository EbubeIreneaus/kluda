export interface AdminUser {
  id: number
  admin_id: string
  fullname: string
  company_email: string
  personal_email: string
  phone?: string
  role: 'SUPER_ADMIN' | 'ADMIN' | 'MODERATOR'
  permission: string[]
  status: string
  last_login?: string
  created_at: string
}

export function useAdminAuth() {
  const adminUser = useState<AdminUser | null>('admin_user', () => null)
  const isLoaded = useState<boolean>('admin_auth_loaded', () => false)
  const { apiFetch } = useAdminApi()

  const isAuthenticated = computed(() => !!adminUser.value)

  function hasPermission(perm: string): boolean {
    if (!adminUser.value) return false
    if (adminUser.value.role === 'SUPER_ADMIN') return true
    if (adminUser.value.permission.includes('manage:all')) return true
    return adminUser.value.permission.includes(perm)
  }

  async function fetchMe(): Promise<AdminUser | null> {
    try {
      const res = await apiFetch<AdminUser>('/admin/auth/me')
      adminUser.value = res
      isLoaded.value = true
      return res
    } catch {
      adminUser.value = null
      isLoaded.value = true
      return null
    }
  }

  async function login(identifier: string, password: string): Promise<boolean> {
    const res = await apiFetch<{ access_token: string }>('/admin/auth/login', {
      method: 'POST',
      body: { identifier, password }
    })
    if (res?.access_token) {
      await fetchMe()
      return true
    }
    return false
  }

  async function logout(): Promise<void> {
    try {
      await apiFetch('/admin/auth/logout', { method: 'POST' })
    } catch {
      // ignore
    } finally {
      adminUser.value = null
      navigateTo('/login')
    }
  }

  return {
    adminUser,
    isLoaded,
    isAuthenticated,
    hasPermission,
    fetchMe,
    login,
    logout
  }
}
