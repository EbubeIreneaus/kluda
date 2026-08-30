import { ref } from 'vue'

export function useAdminPushNotification() {
  const isSupported = ref(false)
  const isSubscribed = ref(false)
  const isLoading = ref(false)
  const permissionStatus = ref<NotificationPermission>('default')

  const { apiFetch } = useAdminApi()

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
    if ('Notification' in window) {
      permissionStatus.value = Notification.permission
    }
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

  async function subscribe(): Promise<boolean> {
    if (!import.meta.client || !isSupported.value) return false
    isLoading.value = true
    try {
      const permission = await Notification.requestPermission()
      permissionStatus.value = permission
      if (permission !== 'granted') {
        isLoading.value = false
        return false
      }

      const keyRes = await apiFetch<{ public_key: string }>('/admin/notifications/vapid-public-key')
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

      await apiFetch('/admin/notifications/subscribe', {
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

  async function unsubscribe(): Promise<boolean> {
    if (!import.meta.client || !isSupported.value) return false
    isLoading.value = true
    try {
      const registration = await navigator.serviceWorker.ready
      if (registration) {
        const subscription = await registration.pushManager.getSubscription()
        if (subscription) {
          await apiFetch('/admin/notifications/unsubscribe', {
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

  async function sendTestNotification(): Promise<boolean> {
    try {
      const res = await apiFetch<{ success: boolean; sent_to_devices: number }>('/admin/notifications/test', {
        method: 'POST'
      })
      return !!res?.success
    } catch {
      return false
    }
  }

  return {
    isSupported,
    isSubscribed,
    isLoading,
    permissionStatus,
    checkSupportAndStatus,
    subscribe,
    unsubscribe,
    sendTestNotification,
  }
}
