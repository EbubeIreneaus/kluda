import { ref } from 'vue'

export function usePushNotification() {
  const isSupported = ref(false)
  const isSubscribed = ref(false)
  const isLoading = ref(false)

  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase
  const ownerStore = useOwnerStore()

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
        const registration = await navigator.serviceWorker.getRegistration('/custom-sw.js')
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
    const token = ownerStore.token
    if (!token) return false

    isLoading.value = true
    try {
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        isLoading.value = false
        return false
      }

      const keyRes = await $fetch<{ public_key: string }>(`${apiBase}/api/v1/notifications/vapid-public-key`)
      if (!keyRes?.public_key) {
        isLoading.value = false
        return false
      }

      const registration = await navigator.serviceWorker.register('/custom-sw.js')
      await navigator.serviceWorker.ready

      const convertedVapidKey = urlBase64ToUint8Array(keyRes.public_key)
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedVapidKey
      })

      await $fetch(`${apiBase}/api/v1/notifications/subscribe`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
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
    const token = ownerStore.token
    if (!token) return false

    isLoading.value = true
    try {
      const registration = await navigator.serviceWorker.getRegistration('/custom-sw.js')
      if (registration) {
        const subscription = await registration.pushManager.getSubscription()
        if (subscription) {
          await $fetch(`${apiBase}/api/v1/notifications/unsubscribe`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
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
