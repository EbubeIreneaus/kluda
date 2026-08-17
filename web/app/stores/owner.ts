import { defineStore } from 'pinia'

export interface OwnerUser {
  user_id: string
  fullname: string
  email: string
  phone?: string
  status: string
  created_at: string
}

export interface StoreItem {
  store_id: string
  name: string
  category: string
  address?: string
  phone?: string
  website?: string
  status: string
  created_at: string
}

export interface StoreStaff {
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
  last_login?: string
  created_at: string
}

interface OwnerState {
  token: string | null
  user: OwnerUser | null
  stores: StoreItem[]
  selectedStoreId: string | null
  staffs: StoreStaff[]
  isLoading: boolean
}

export const useOwnerStore = defineStore('owner',  {
  state: (): OwnerState => ({
    token: null,
    user: null,
    stores: [],
    selectedStoreId: null,
    staffs: [],
    isLoading: false
  }),

  getters: {
    isLoggedIn: (state) => !!state.user || !!state.token,
    activeStores: (state) => state.stores.filter(s => s.status !== 'deleted'),
    selectedStore: (state) => state.stores.find(s => s.store_id === state.selectedStoreId) || state.stores[0] || null,
    initials: (state) => {
      if (!state.user?.fullname) return 'OP'
      const parts = state.user.fullname.trim().split(' ')
      if (parts && parts.length >= 2) {
        return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
      }
      return state.user.fullname.substring(0, 2).toUpperCase()
    }
  },

  actions: {
    setAuth(token: string, user: OwnerUser) {
      this.token = token || 'cookie_session'
      this.user = user
      if (import.meta.client) {
        localStorage.setItem('owner_token', token || 'cookie_session')
        localStorage.setItem('owner_user', JSON.stringify(user))
      }
    },

    loadFromStorage() {
      if (import.meta.client) {
        this.token = localStorage.getItem('owner_token')
        const userJson = localStorage.getItem('owner_user')
        this.user = (userJson && userJson != "undefined" && userJson != "null") ? JSON.parse(userJson) : null
        this.selectedStoreId = localStorage.getItem('owner_selected_store') || null
      }
    },

    selectStore(storeId: string) {
      this.selectedStoreId = storeId
      if (import.meta.client) {
        localStorage.setItem('owner_selected_store', storeId)
      }
    },

    async fetchMe() {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      try {
        const res = await $fetch<OwnerUser>(`${apiBase}/auth/me`, {
          credentials: 'include',
          headers: this.token && this.token !== 'cookie_session' ? { Authorization: `Bearer ${this.token}` } : {}
        })
        if (res) {
          this.user = res
          if (import.meta.client) {
            localStorage.setItem('owner_user', JSON.stringify(res))
          }
        }
      } catch (err: any) {
        const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
        if (statusCode === 401) {
          try {
            const refreshRes = await $fetch<{ success: boolean; user?: OwnerUser; access_token?: string }>(
              `${apiBase}/auth/refresh-token`,
              { method: 'POST', credentials: 'include' }
            )
            if (refreshRes && refreshRes.success && refreshRes.user) {
              this.setAuth(refreshRes.access_token || '', refreshRes.user)
              return
            }
          } catch {
            await this.logout(false)
          }
        }
      }
    },

    async fetchStores() {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      this.isLoading = true
      try {
        const res = await $fetch<StoreItem[]>(`${apiBase}/store`, {
          credentials: 'include',
          headers: this.token && this.token !== 'cookie_session' ? { Authorization: `Bearer ${this.token}` } : {}
        })
        if (Array.isArray(res)) {
          this.stores = res
          if (!this.selectedStoreId && res.length > 0) {
            this.selectStore(res[0].store_id)
          }
        }
        return res
      } finally {
        this.isLoading = false
      }
    },

    async createStore(data: { name: string; category: string; address: string; phone?: string; website?: string }) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      const res = await $fetch<StoreItem>(`${apiBase}/store`, {
        method: 'POST',
        credentials: 'include',
        headers: this.token && this.token !== 'cookie_session' ? { Authorization: `Bearer ${this.token}` } : {},
        body: data
      })
      if (res) {
        this.stores.push(res)
        this.selectStore(res.store_id)
      }
      return res
    },

    async updateStore(storeId: string, data: Partial<StoreItem>) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      const res = await $fetch<StoreItem>(`${apiBase}/store/${storeId}`, {
        method: 'PUT',
        credentials: 'include',
        headers: this.token && this.token !== 'cookie_session' ? { Authorization: `Bearer ${this.token}` } : {},
        body: data
      })
      await this.fetchStores()
      return res
    },

    async fetchStaffs(storeId?: string) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      const targetStoreId = storeId || this.selectedStoreId
      if (!targetStoreId) return []

      try {
        const res = await $fetch<StoreStaff[]>(`${apiBase}/staff/?store_id=${targetStoreId}`, {
          credentials: 'include',
          headers: this.token && this.token !== 'cookie_session' ? { Authorization: `Bearer ${this.token}` } : {}
        })
        if (Array.isArray(res)) {
          this.staffs = res
        }
        return res
      } catch (e) {
        console.error('Failed to fetch staff:', e)
        return []
      }
    },

    async createStaff(storeId: string, staffData: {
      first_name: string
      last_name: string
      other_name?: string
      role: string
      email: string
      phone?: string
      password: string
      permission: string[]
      status?: string
    }) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      const res = await $fetch<StoreStaff>(`${apiBase}/staff/${storeId}?store_id=${storeId}`, {
        method: 'POST',
        credentials: 'include',
        headers: this.token && this.token !== 'cookie_session' ? { Authorization: `Bearer ${this.token}` } : {},
        body: staffData
      })
      await this.fetchStaffs(storeId)
      return res
    },

    async updateStaff(staffId: string, storeId: string, data: Partial<StoreStaff>) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      const res = await $fetch<StoreStaff>(`${apiBase}/staff/${staffId}?store_id=${storeId}`, {
        method: 'PUT',
        credentials: 'include',
        headers: this.token && this.token !== 'cookie_session' ? { Authorization: `Bearer ${this.token}` } : {},
        body: data
      })
      await this.fetchStaffs(storeId)
      return res
    },

    async revokeStaffAccess(staffId: string, storeId: string) {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      return await $fetch(`${apiBase}/staff/revoke-access?target_staff_id=${staffId}&store_id=${storeId}`, {
        method: 'POST',
        credentials: 'include',
        headers: this.token && this.token !== 'cookie_session' ? { Authorization: `Bearer ${this.token}` } : {}
      })
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
        // Proceed anyway
      }

      this.token = null
      this.user = null
      this.stores = []
      this.staffs = []
      this.selectedStoreId = null

      if (import.meta.client) {
        localStorage.removeItem('owner_token')
        localStorage.removeItem('owner_user')
        localStorage.removeItem('owner_selected_store')
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
