import { ref } from 'vue'

export function usePushNotification() {
  const isSupported = ref(false)
  const isSubscribed = ref(false)
  const isLoading = ref(false)

  const auth = useAuthStore()
  const { api } = useApi()

  function urlBase64ToUint8Array(base64String: string) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i)
    }
    return outputArray
  }

  async function checkSupportAndStatus() {
    if (!import.meta.client) return
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      isSupported.value = true
      try {
        let registration = await navigator.serviceWorker.getRegistration()
        if (!registration && 'ready' in navigator.serviceWorker) {
          registration = await navigator.serviceWorker.ready
        }
        if (registration) {
          const subscription = await registration.pushManager.getSubscription()
          isSubscribed.value = !!subscription
        }
      } catch {
        isSubscribed.value = false
      }
    }
  }

  async function subscribe(): Promise<{ success: boolean; message?: string }> {
    if (!import.meta.client || !isSupported.value) {
      return { success: false, message: 'Push notifications are not supported on this browser' }
    }
    const storeId = auth.store_id || auth.staff?.store_id || (import.meta.client ? localStorage.getItem('pos_store_id') : null)
    if (!storeId) {
      return { success: false, message: 'Store identification missing. Please re-login.' }
    }

    isLoading.value = true
    try {
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        isLoading.value = false
        return { success: false, message: 'Notification permission was denied.' }
      }

      const keyRes = await api<{ public_key: string }>(`/${storeId}/notifications/vapid-public-key`)
      if (!keyRes?.public_key) {
        isLoading.value = false
        return { success: false, message: 'Could not fetch notification encryption key from server.' }
      }

      let registration = await navigator.serviceWorker.getRegistration()
      if (!registration) {
        registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' })
      }
      const activeReg = registration || (await navigator.serviceWorker.ready)
      if (!activeReg?.pushManager) {
        isLoading.value = false
        return { success: false, message: 'Service worker push manager is initializing. Please try again.' }
      }

      const convertedVapidKey = urlBase64ToUint8Array(keyRes.public_key)
      const subscription = await activeReg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedVapidKey
      })

      const res = await api<{ success?: boolean; message?: string }>(`/${storeId}/notifications/subscribe`, {
        method: 'POST',
        body: subscription.toJSON()
      })

      isSubscribed.value = true
      return { success: true, message: res?.message || 'Subscribed successfully' }
    } catch (err: any) {
      return { success: false, message: err?.data?.detail || err?.message || 'Failed to register push subscription' }
    } finally {
      isLoading.value = false
    }
  }

  async function unsubscribe(): Promise<{ success: boolean; message?: string }> {
    if (!import.meta.client || !isSupported.value) {
      return { success: false, message: 'Push notifications not supported' }
    }
    const storeId = auth.store_id || auth.staff?.store_id || (import.meta.client ? localStorage.getItem('pos_store_id') : null)
    if (!storeId) return { success: false, message: 'Store not found' }

    isLoading.value = true
    try {
      let registration = await navigator.serviceWorker.getRegistration()
      if (!registration && 'ready' in navigator.serviceWorker) {
        registration = await navigator.serviceWorker.ready
      }
      if (registration) {
        const subscription = await registration.pushManager.getSubscription()
        if (subscription) {
          try {
            await api(`/${storeId}/notifications/unsubscribe`, {
              method: 'POST',
              body: subscription.toJSON()
            })
          } catch {
            // ignore backend delete error
          }
          await subscription.unsubscribe()
        }
      }
      isSubscribed.value = false
      return { success: true, message: 'Unsubscribed successfully' }
    } catch (err: any) {
      return { success: false, message: err?.message || 'Failed to unsubscribe' }
    } finally {
      isLoading.value = false
    }
  }

  if (import.meta.client) {
    checkSupportAndStatus()
  }

  return {
    isSupported,
    isSubscribed,
    isLoading,
    checkSupportAndStatus,
    subscribe,
    unsubscribe,
  }
}
