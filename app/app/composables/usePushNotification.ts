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
        const registration = await navigator.serviceWorker.ready
        if (registration) {
          const subscription = await registration.pushManager.getSubscription()
          isSubscribed.value = !!subscription
        }
      } catch {
        isSubscribed.value = false
      }
    }
  }

  async function subscribe() {
    if (!import.meta.client || !isSupported.value) return false
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) return false

    isLoading.value = true
    try {
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        isLoading.value = false
        return false
      }

      const keyRes = await api<{ public_key: string }>(`/${storeId}/notifications/vapid-public-key`)
      if (!keyRes?.public_key) {
        isLoading.value = false
        return false
      }

      const registration = await navigator.serviceWorker.ready

      const convertedVapidKey = urlBase64ToUint8Array(keyRes.public_key)
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedVapidKey
      })

      await api(`/${storeId}/notifications/subscribe`, {
        method: 'POST',
        body: subscription.toJSON()
      })

      isSubscribed.value = true
      return true
    } catch {
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function unsubscribe() {
    if (!import.meta.client || !isSupported.value) return false
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) return false

    isLoading.value = true
    try {
      const registration = await navigator.serviceWorker.ready
      if (registration) {
        const subscription = await registration.pushManager.getSubscription()
        if (subscription) {
          await api(`/${storeId}/notifications/unsubscribe`, {
            method: 'POST',
            body: subscription.toJSON()
          })
          await subscription.unsubscribe()
        }
      }
      isSubscribed.value = false
      return true
    } catch {
      return false
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
    subscribe,
    unsubscribe,
    checkSupportAndStatus
  }
}
