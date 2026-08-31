import { defineStore } from 'pinia'

interface Staff {
  staff_id: string
  store_id: string
  first_name: string
  last_name: string
  other_name?: string
  role: string
  email: string
  phone?: string
  permission: string[]
  status: string
  has_pin?: boolean
  pin_hash?: string | null
  pin_salt?: string | null
  last_login?: string
  created_at: string
}

interface AuthState {
  token: string | null
  staff: Staff | null
  store_id: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    staff: null,
    store_id: null
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
    setAuth(token: string, staff: Staff, storeId?: string) {
      this.token = token || 'cookie_session'
      if (this.staff?.has_pin && !staff.has_pin) {
        staff.has_pin = true
        staff.pin_hash = this.staff.pin_hash
        staff.pin_salt = this.staff.pin_salt
      }
      this.staff = staff
      this.store_id = storeId || staff?.store_id || null
      if (import.meta.client) {
        localStorage.setItem('pos_token', token || 'cookie_session')
        localStorage.setItem('pos_staff', JSON.stringify(staff))
        if (this.store_id) {
          localStorage.setItem('pos_store_id', this.store_id)
        }
      }
    },

    loadFromStorage() {
      if (import.meta.client) {
        this.token = localStorage.getItem('pos_token')
        const staffJson = localStorage.getItem('pos_staff')
        this.staff = (staffJson && staffJson != "undefined" && staffJson != "null") ? JSON.parse(staffJson) : null
        this.store_id = localStorage.getItem('pos_store_id') || this.staff?.store_id || null
      }
    },

    async fetchMe() {
      if (import.meta.client && typeof navigator !== 'undefined' && !navigator.onLine) {
        this.loadFromStorage()
        return
      }

      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      try {
        const res = await $fetch<Staff>(`${apiBase}/staff/auth/me`, {
          credentials: 'include',
          headers: this.token ? { Authorization: `Bearer ${this.token}` } : {}
        })
        if (res) {
          if (this.staff?.has_pin && !res.has_pin) {
            res.has_pin = true
            res.pin_hash = this.staff.pin_hash
            res.pin_salt = this.staff.pin_salt
          }
          this.staff = res
          this.store_id = res.store_id || this.store_id
          if (import.meta.client) {
            localStorage.setItem('pos_staff', JSON.stringify(res))
            if (this.store_id) {
              localStorage.setItem('pos_store_id', this.store_id)
            }
          }
        }
      } catch (err: any) {
        const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
        if (!statusCode) {
          this.loadFromStorage()
          return
        }
        if (statusCode === 401) {
          try {
            const refreshRes = await $fetch<{ success: boolean; staff?: Staff; access_token?: string; store_id?: string }>(
              `${apiBase}/staff/auth/refresh-token`,
              { method: 'POST', credentials: 'include' }
            )
            if (refreshRes && refreshRes.success && refreshRes.staff) {
              this.setAuth(refreshRes.access_token || '', refreshRes.staff, refreshRes.store_id)
              return
            }
          } catch (refreshErr: any) {
            const refreshStatus = refreshErr?.response?.status ?? refreshErr?.statusCode ?? refreshErr?.status
            if (refreshStatus === 401 || refreshStatus === 403) {
              await this.logout(true)
              return
            }
          }
        }
        this.loadFromStorage()
      }
    },

    async logout(redirectToLogin = true) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      try {
        await $fetch(`${apiBase}/staff/auth/logout`, {
          method: 'POST',
          credentials: 'include'
        })
      } catch {}

      this.token = null
      this.staff = null
      this.store_id = null
      if (import.meta.client) {
        localStorage.removeItem('pos_token')
        localStorage.removeItem('pos_staff')
        localStorage.removeItem('pos_store_id')
        if (redirectToLogin) {
          try {
            await navigateTo('/login', { replace: true })
          } catch {
            window.location.href = '/login'
          }
        }
      }
    }
  }
})
