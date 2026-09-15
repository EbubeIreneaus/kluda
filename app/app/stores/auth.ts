import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { getTerminalUnlockProof } from '~/composables/usePinAuth'

export interface StoreItem {
  store_id: string
  name: string
  category?: string
  address?: string
  phone?: string
  website?: string
  role: string
  is_owner: boolean
  display_name?: string
  permission: string[]
  owner_subscription?: any
  owner_name?: string
}

export interface User {
  user_id: string
  fullname: string
  email: string
  phone?: string
  role: string
  permission: string[]
  status: string
  has_pin: boolean
  pin_hash?: string | null
  pin_salt?: string | null
  store_id?: string | null
  created_at?: string | null
  last_login?: string | null
  current_subscription?: any
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)
  const stores = ref<StoreItem[]>([])
  const store_id = ref<string | null>(null)
  const current_store = ref<StoreItem | null>(null)

  // Getters
  const isLoggedIn = computed(() => !!user.value)
  const isOwner = computed(() => {
    return Boolean(current_store.value?.is_owner || current_store.value?.role === 'owner' || user.value?.role === 'owner')
  })
  const fullName = computed(() => user.value?.fullname || user.value?.email || '')
  const initials = computed(() => {
    if (!user.value?.fullname) return '?'
    const parts = user.value.fullname.trim().split(/\s+/)
    return `${parts[0]?.[0] || ''}${parts[1]?.[0] || ''}`.toUpperCase() || '?'
  })

  function hasPermission(perm: string): boolean {
    if (!user.value) return false
    if (isOwner.value) return true
    const perms = current_store.value?.permission || user.value.permission || []
    return perms.includes('manage:all') || perms.includes(perm)
  }

  // Actions
  function setAuth(
    newToken: string,
    userData: any,
    targetStoreId?: string,
    refreshToken?: string,
    storesList?: StoreItem[]
  ) {
    token.value = newToken || 'cookie_session'

    if (storesList) {
      stores.value = storesList
    } else if (userData?.stores) {
      stores.value = userData.stores
    }

    const chosenStoreId = targetStoreId || userData?.store_id || stores.value[0]?.store_id || null
    store_id.value = chosenStoreId
    current_store.value = stores.value.find(s => s.store_id === chosenStoreId) || stores.value[0] || null

    const role = current_store.value?.role || userData?.role || 'staff'
    const permission = current_store.value?.permission || userData?.permission || (role === 'owner' ? ['manage:all'] : [])

    user.value = {
      user_id: String(userData?.user_id),
      fullname: userData?.fullname || '',
      email: userData?.email || '',
      phone: userData?.phone || undefined,
      role,
      permission: Array.isArray(permission) ? permission : [permission],
      status: userData?.status || 'active',
      has_pin: Boolean(userData?.has_pin || userData?.pin_hash),
      pin_hash: userData?.pin_hash ?? user.value?.pin_hash ?? null,
      pin_salt: userData?.pin_salt ?? user.value?.pin_salt ?? null,
      store_id: chosenStoreId,
      created_at: userData?.created_at || null
    }

    if (import.meta.client) {
      localStorage.setItem('pos_token', token.value)
      localStorage.setItem('pos_user', JSON.stringify(user.value))
      localStorage.setItem('pos_stores', JSON.stringify(stores.value))
      if (chosenStoreId) {
        localStorage.setItem('pos_store_id', chosenStoreId)
      }
      if (refreshToken) {
        localStorage.setItem('pos_refresh_token', refreshToken)
      }
    }
  }

  function switchStore(targetStoreId: string) {
    if (!targetStoreId || targetStoreId === store_id.value) return
    store_id.value = targetStoreId
    current_store.value = stores.value.find(s => s.store_id === targetStoreId) || null
    if (user.value && current_store.value) {
      user.value.role = current_store.value.role
      user.value.permission = current_store.value.permission
      user.value.store_id = targetStoreId
    }
    if (import.meta.client) {
      localStorage.setItem('pos_store_id', targetStoreId)
      if (user.value) {
        localStorage.setItem('pos_user', JSON.stringify(user.value))
      }
      window.location.reload()
    }
  }

  function loadFromStorage() {
    if (!import.meta.client) return
    token.value = localStorage.getItem('pos_token')
    const userJson = localStorage.getItem('pos_user')
    const storesJson = localStorage.getItem('pos_stores')

    user.value = userJson ? JSON.parse(userJson) : null
    stores.value = storesJson ? JSON.parse(storesJson) : []

    const storedStoreId = localStorage.getItem('pos_store_id') || user.value?.store_id || stores.value[0]?.store_id || null
    store_id.value = storedStoreId
    current_store.value = stores.value.find(s => s.store_id === storedStoreId) || stores.value[0] || null
  }

  let refreshPromise: Promise<boolean> | null = null

  async function refreshToken(): Promise<boolean> {
    if (refreshPromise) return refreshPromise

    const config = useRuntimeConfig()
    const apiBase = config.public.apiBase

    refreshPromise = (async () => {
      try {
        const storedRefresh = import.meta.client ? localStorage.getItem('pos_refresh_token') : null
        const pinProof = getTerminalUnlockProof()
        const refreshRes = await $fetch<any>(`${apiBase}/auth/refresh-token`, {
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

        if (refreshRes?.success) {
          setAuth(
            refreshRes.access_token || token.value || '',
            refreshRes.user,
            refreshRes.store_id || store_id.value || undefined,
            refreshRes.refresh_token,
            refreshRes.stores
          )
          return true
        }
        return false
      } catch (refreshErr: any) {
        const status = refreshErr?.response?.status ?? refreshErr?.statusCode ?? refreshErr?.status
        if (status === 401 || status === 403) {
          await logout(true)
        }
        return false
      } finally {
        refreshPromise = null
      }
    })()

    return refreshPromise
  }

  async function fetchMe() {
    if (import.meta.client && typeof navigator !== 'undefined' && !navigator.onLine) {
      loadFromStorage()
      return
    }

    const config = useRuntimeConfig()
    const apiBase = config.public.apiBase
    try {
      const res = await $fetch<any>(`${apiBase}/auth/me`, {
        credentials: 'include',
        headers: token.value ? { Authorization: `Bearer ${token.value}` } : {}
      })
      if (res) {
        setAuth(token.value || '', res, store_id.value || res.store_id, undefined, res.stores)
      }
    } catch (err: any) {
      const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
      if (statusCode === 401) {
        const ok = await refreshToken()
        if (ok) {
          try {
            const meRes = await $fetch<any>(`${apiBase}/auth/me`, {
              credentials: 'include',
              headers: token.value ? { Authorization: `Bearer ${token.value}` } : {}
            })
            if (meRes) {
              setAuth(token.value || '', meRes, store_id.value || meRes.store_id, undefined, meRes.stores)
              return
            }
          } catch {}
        }
      }
      loadFromStorage()
    }
  }

  async function logout(redirectToLogin = true) {
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

    token.value = null
    user.value = null
    stores.value = []
    current_store.value = null
    store_id.value = null

    if (import.meta.client) {
      localStorage.removeItem('pos_token')
      localStorage.removeItem('pos_user')
      localStorage.removeItem('pos_staff')
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

  return {
    // State
    token,
    user,
    stores,
    store_id,
    current_store,

    // Getters
    isLoggedIn,
    isOwner,
    fullName,
    initials,
    hasPermission,

    // Actions
    setAuth,
    switchStore,
    loadFromStorage,
    refreshToken,
    fetchMe,
    logout
  }
})
