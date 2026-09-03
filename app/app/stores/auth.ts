import { defineStore } from 'pinia'
import { getTerminalUnlockProof } from '~/composables/usePinAuth'

export interface PlanDetails {
  slug: string
  name: string
  description?: string
  // Price in subunit (kobo for NGN)
  price: number
  store_limit?: number
  product_limit?: number
  sales_limit_per_month?: number
  analytics_read_per_month?: number
  status?: string
}

export interface SubscriptionUsage {
  stores_count: number
  stores_limit: number
  products_count: number
  products_limit: number
  monthly_sales_count: number
  monthly_sales_limit: number
  monthly_analytics_count: number
  monthly_analytics_limit: number
}

export interface StoreOwnerSubscription {
  subscription_id?: string
  plan_id?: string
  status?: 'ACTIVE' | 'DUE' | 'EXPIRED' | string
  amount?: number
  next_renewal?: string
  plan?: PlanDetails
  usage?: SubscriptionUsage
}

export interface StoreItem {
  store_id: string
  name: string
  category: string
  address?: string
  phone?: string
  website?: string
  role: string
  is_owner: boolean
  display_name?: string | null
  permission: string[]
  owner_name?: string | null
  owner_subscription?: StoreOwnerSubscription | null
}

export interface Staff {
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

export interface UserProfile {
  user_id: string
  fullname: string
  email: string
  phone?: string
  status: string
  has_pin?: boolean
  pin_hash?: string | null
  pin_salt?: string | null
  role?: string
  permission?: string[]
  current_subscription?: StoreOwnerSubscription | null
}

interface AuthState {
  token: string | null
  user: UserProfile | null
  staff: Staff | null
  stores: StoreItem[]
  store_id: string | null
  current_store: StoreItem | null
}

let refreshPromise: Promise<boolean> | null = null

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    user: null,
    staff: null,
    stores: [],
    store_id: null,
    current_store: null
  }),

  getters: {
    isLoggedIn: (state) => !!(state.staff || state.user),
    isOwner: (state) => {
      if (state.current_store?.is_owner) return true
      const role = (state.current_store?.role || state.staff?.role || state.user?.role || '').toLowerCase()
      return role === 'owner' || role === 'admin'
    },
    fullName: (state) => {
      if (state.staff) return `${state.staff.first_name} ${state.staff.last_name}`.trim()
      if (state.user) return state.user.fullname || state.user.email
      return ''
    },
    initials: (state) => {
      if (state.staff) {
        return `${state.staff.first_name?.[0] || ''}${state.staff.last_name?.[0] || ''}`.toUpperCase() || '?'
      }
      if (state.user && state.user.fullname) {
        const parts = state.user.fullname.split(' ')
        return `${parts[0]?.[0] || ''}${parts[1]?.[0] || ''}`.toUpperCase() || '?'
      }
      return '?'
    },
    hasPermission: (state) => (perm: string) => {
      if (!state.staff && !state.user) return false
      const role = (state.current_store?.role || state.staff?.role || state.user?.role || '').toLowerCase()
      if (role === 'owner' || role === 'admin' || state.current_store?.is_owner) return true

      const rawPerms = state.current_store?.permission || state.staff?.permission || state.user?.permission || []
      let perms: any[] = []
      if (Array.isArray(rawPerms)) {
        perms = rawPerms
      } else if (typeof rawPerms === 'string') {
        try {
          const parsed = JSON.parse(rawPerms)
          perms = Array.isArray(parsed) ? parsed : [parsed]
        } catch {
          perms = [rawPerms]
        }
      } else {
        perms = [rawPerms]
      }

      return perms.some((p: any) => {
        const val = (typeof p === 'string' ? p : p?.value || String(p)).trim()
        return val === 'manage:all' || val === '*' || val === 'all' || val === perm
      })
    }
  },

  actions: {
    setAuth(token: string, staffData: any, storeId?: string, refreshToken?: string, storesList?: StoreItem[]) {
      this.token = token || 'cookie_session'
      
      const stores = storesList || staffData?.stores || this.stores || []
      this.stores = stores
      
      const firstStore = stores.length > 0 && stores[0] ? stores[0] : null
      const chosenStoreId = storeId || staffData?.store_id || firstStore?.store_id || null
      this.store_id = chosenStoreId
      const matchedStore = chosenStoreId ? stores.find((s: StoreItem) => s.store_id === chosenStoreId) : undefined
      this.current_store = matchedStore || firstStore

      const rawRole = this.current_store?.role || staffData?.role || (this.current_store?.is_owner ? 'owner' : 'staff')
      const rawPerms = this.current_store?.permission || staffData?.permission || (rawRole === 'owner' ? ['manage:all'] : [])

      const normalizedStaff: Staff = {
        staff_id: staffData?.staff_id || staffData?.user_id || 'USR',
        store_id: chosenStoreId || '',
        first_name: staffData?.first_name || (staffData?.fullname ? staffData.fullname.split(' ')[0] : 'User'),
        last_name: staffData?.last_name || (staffData?.fullname ? staffData.fullname.split(' ').slice(1).join(' ') : ''),
        other_name: staffData?.other_name || undefined,
        role: rawRole,
        email: staffData?.email || '',
        phone: staffData?.phone || undefined,
        permission: Array.isArray(rawPerms) ? rawPerms : [rawPerms],
        status: staffData?.status || 'active',
        has_pin: staffData?.has_pin ?? false,
        pin_hash: staffData?.pin_hash || null,
        pin_salt: staffData?.pin_salt || null,
        last_login: staffData?.last_login || new Date().toISOString(),
        created_at: staffData?.created_at || new Date().toISOString()
      }

      this.staff = normalizedStaff
      this.user = {
        user_id: staffData?.user_id || normalizedStaff.staff_id,
        fullname: staffData?.fullname || `${normalizedStaff.first_name} ${normalizedStaff.last_name}`.trim(),
        email: normalizedStaff.email,
        phone: normalizedStaff.phone,
        status: normalizedStaff.status,
        has_pin: normalizedStaff.has_pin,
        pin_hash: normalizedStaff.pin_hash,
        pin_salt: normalizedStaff.pin_salt,
        role: rawRole,
        permission: normalizedStaff.permission
      }

      if (import.meta.client) {
        localStorage.setItem('pos_token', token || 'cookie_session')
        localStorage.setItem('pos_staff', JSON.stringify(this.staff))
        localStorage.setItem('pos_user', JSON.stringify(this.user))
        localStorage.setItem('pos_stores', JSON.stringify(this.stores))
        if (this.store_id) {
          localStorage.setItem('pos_store_id', this.store_id)
        }
        if (refreshToken) {
          localStorage.setItem('pos_refresh_token', refreshToken)
        }
      }
    },

    switchStore(targetStoreId: string) {
      if (!targetStoreId || targetStoreId === this.store_id) return
      this.store_id = targetStoreId
      const matched = this.stores.find((s: StoreItem) => s.store_id === targetStoreId)
      if (matched) {
        this.current_store = matched
        if (this.staff) {
          this.staff.store_id = targetStoreId
          this.staff.role = matched.role
          this.staff.permission = matched.permission
        }
      }
      if (import.meta.client) {
        localStorage.setItem('pos_store_id', targetStoreId)
        if (this.staff) {
          localStorage.setItem('pos_staff', JSON.stringify(this.staff))
        }
        window.location.reload()
      }
    },

    loadFromStorage() {
      if (import.meta.client) {
        this.token = localStorage.getItem('pos_token')
        const staffJson = localStorage.getItem('pos_staff')
        const userJson = localStorage.getItem('pos_user')
        const storesJson = localStorage.getItem('pos_stores')
        
        this.staff = (staffJson && staffJson !== 'undefined' && staffJson !== 'null') ? JSON.parse(staffJson) : null
        this.user = (userJson && userJson !== 'undefined' && userJson !== 'null') ? JSON.parse(userJson) : null
        this.stores = (storesJson && storesJson !== 'undefined' && storesJson !== 'null') ? JSON.parse(storesJson) : []
        
        const firstStore = this.stores.length > 0 && this.stores[0] ? this.stores[0] : null
        const storedStoreId = localStorage.getItem('pos_store_id') || this.staff?.store_id || firstStore?.store_id || null
        this.store_id = storedStoreId
        const matchedStore = storedStoreId ? this.stores.find((s: StoreItem) => s.store_id === storedStoreId) : undefined
        this.current_store = matchedStore || firstStore
      }
    },

    async refreshToken(): Promise<boolean> {
      if (refreshPromise) {
        return refreshPromise
      }

      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase

      refreshPromise = (async () => {
        try {
          const storedRefresh = import.meta.client ? localStorage.getItem('pos_refresh_token') : null
          const pinProof = getTerminalUnlockProof()
          const refreshRes = await $fetch<{
            success: boolean
            staff?: any
            user?: any
            stores?: StoreItem[]
            access_token?: string
            refresh_token?: string
            store_id?: string
          }>(`${apiBase}/auth/refresh-token`, {
            method: 'POST',
            credentials: 'include',
            headers: {
              'X-Client-App': 'pos',
              ...(pinProof ? { 'X-Pin-Proof': pinProof } : {})
            },
            body: {
              ...(storedRefresh ? { refresh_token: storedRefresh } : {}),
              ...(pinProof ? { pin_proof: pinProof } : {})
            }
          })

          if (refreshRes && refreshRes.success) {
            this.setAuth(
              refreshRes.access_token || this.token || '',
              refreshRes.staff || refreshRes.user,
              refreshRes.store_id || this.store_id || undefined,
              refreshRes.refresh_token,
              refreshRes.stores
            )
            return true
          }
          return false
        } catch (refreshErr: any) {
          const refreshStatus = refreshErr?.response?.status ?? refreshErr?.statusCode ?? refreshErr?.status
          if (refreshStatus === 401 || refreshStatus === 403) {
            await this.logout(true)
          }
          return false
        } finally {
          refreshPromise = null
        }
      })()

      return refreshPromise
    },

    async fetchMe() {
      if (import.meta.client && typeof navigator !== 'undefined' && !navigator.onLine) {
        this.loadFromStorage()
        return
      }

      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      try {
        const res = await $fetch<any>(`${apiBase}/auth/me`, {
          credentials: 'include',
          headers: this.token ? { Authorization: `Bearer ${this.token}` } : {}
        })
        if (res) {
          const stores = res.stores || this.stores
          const firstStore = stores.length > 0 && stores[0] ? stores[0] : null
          const activeStoreId = this.store_id || res.store_id || firstStore?.store_id || null
          this.setAuth(
            this.token || '',
            res.staff || res,
            activeStoreId,
            undefined,
            stores
          )
        }
      } catch (err: any) {
        const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
        if (!statusCode) {
          this.loadFromStorage()
          return
        }
        if (statusCode === 401) {
          const ok = await this.refreshToken()
          if (ok) {
            try {
              const meRes = await $fetch<any>(`${apiBase}/auth/me`, {
                credentials: 'include',
                headers: this.token ? { Authorization: `Bearer ${this.token}` } : {}
              })
              if (meRes) {
                const stores = meRes.stores || this.stores
                const activeStoreId = this.store_id || meRes.store_id || (stores.length > 0 ? stores[0].store_id : null)
                this.setAuth(
                  this.token || '',
                  meRes.staff || meRes,
                  activeStoreId,
                  undefined,
                  stores
                )
                return
              }
            } catch {}
          }
        }
        this.loadFromStorage()
      }
    },

    async logout(redirectToLogin = true) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      try {
        const storedRefresh = import.meta.client ? localStorage.getItem('pos_refresh_token') : null
        await $fetch(`${apiBase}/auth/logout`, {
          method: 'POST',
          credentials: 'include',
          body: storedRefresh ? { refresh_token: storedRefresh } : undefined
        })
      } catch {}

      this.token = null
      this.staff = null
      this.user = null
      this.stores = []
      this.current_store = null
      this.store_id = null
      if (import.meta.client) {
        localStorage.removeItem('pos_token')
        localStorage.removeItem('pos_staff')
        localStorage.removeItem('pos_user')
        localStorage.removeItem('pos_stores')
        localStorage.removeItem('pos_store_id')
        localStorage.removeItem('pos_refresh_token')
        if (redirectToLogin) {
          try {
            await navigateTo('/auth/login', { replace: true })
          } catch {
            window.location.href = '/auth/login'
          }
        }
      }
    }
  }
})
