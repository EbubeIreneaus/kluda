import { defineStore } from 'pinia'

interface Staff {
  staff_id: string
  first_name: string
  last_name: string
  other_name?: string
  role: string
  email: string
  phone?: string
  permission: string[]
  status: string
  last_login?: string
  created_at: string
}

interface AuthState {
  token: string | null
  staff: Staff | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    staff: null
  }),

  getters: {
    isLoggedIn: (state) => !!state.staff,
    fullName: (state) => state.staff ? `${state.staff.first_name} ${state.staff.last_name}` : '',
    initials: (state) => {
      if (!state.staff) return '?'
      return `${state.staff.first_name?.[0] || ''}${state.staff.last_name?.[0] || ''}`.toUpperCase() || '?'
    },
    hasPermission: (state) => (perm: string) => {
      if (!state.staff) return false
      if (state.staff.role?.toLowerCase() === 'admin') return true
      if (!state.staff.permission) return false

      let perms: any[] = []
      if (Array.isArray(state.staff.permission)) {
        perms = state.staff.permission
      } else if (typeof state.staff.permission === 'string') {
        try {
          const parsed = JSON.parse(state.staff.permission)
          perms = Array.isArray(parsed) ? parsed : [parsed]
        } catch {
          perms = [state.staff.permission]
        }
      } else {
        perms = [state.staff.permission]
      }

      return perms.some((p: any) => {
        const val = (typeof p === 'string' ? p : p?.value || String(p)).trim()
        return val === 'manage:all' || val === '*' || val === 'all' || val === perm
      })
    }
  },

  actions: {
    setAuth(token: string, staff: Staff) {
      this.token = token || 'cookie_session'
      this.staff = staff
      if (import.meta.client) {
        localStorage.setItem('pos_token', token || 'cookie_session')
        localStorage.setItem('pos_staff', JSON.stringify(staff))
      }
    },

    loadFromStorage() {
      if (import.meta.client) {
        this.token = localStorage.getItem('pos_token')
        const staffJson = localStorage.getItem('pos_staff')
        this.staff = staffJson ? JSON.parse(staffJson) : null
      }
    },

    async fetchMe() {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      try {
        const res = await $fetch<Staff>(`${apiBase}/auth/me`, {
          credentials: 'include',
          headers: this.token ? { Authorization: `Bearer ${this.token}` } : {}
        })
        if (res) {
          this.staff = res
          if (import.meta.client) {
            localStorage.setItem('pos_staff', JSON.stringify(res))
          }
        }
      } catch (err: any) {
        const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
        if (statusCode === 401) {
          // Attempt silent refresh
          try {
            const refreshRes = await $fetch<{ success: boolean; staff?: Staff; access_token?: string }>(
              `${apiBase}/auth/refresh-token`,
              { method: 'POST', credentials: 'include' }
            )
            if (refreshRes && refreshRes.success && refreshRes.staff) {
              this.setAuth(refreshRes.access_token || '', refreshRes.staff)
              return
            }
          } catch {
            await this.logout(true)
            return
          }
        }
        const detail = String(err?.data?.detail || '')
        if (statusCode === 401 || (statusCode === 403 && (detail.includes('suspended') || detail.includes('terminated')))) {
          await this.logout(true)
        }
      }
    },

    async logout(redirectToLogin = true) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      try {
        await $fetch(`${apiBase}/auth/logout`, {
          method: 'POST',
          credentials: 'include'
        })
      } catch {
        // Continue with local wipe even if server fails
      }

      this.token = null
      this.staff = null
      if (import.meta.client) {
        localStorage.removeItem('pos_token')
        localStorage.removeItem('pos_staff')
        if (redirectToLogin) {
          try {
            await navigateTo('/login', { replace: true })
          } catch (e) {
            window.location.href = '/login'
          }
        }
      }
    }
  }
})

