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

  async function getReadyRegistration(): Promise<ServiceWorkerRegistration | null> {
    if (!('serviceWorker' in navigator)) return null
    let reg = await navigator.serviceWorker.getRegistration()
    if (!reg) {
      reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' })
    }

    if (reg.active && reg.active.state === 'activated') {
      return reg
    }

    const readyReg = await navigator.serviceWorker.ready
    if (readyReg.active && readyReg.active.state === 'activated') {
      return readyReg
    }

    const candidate = readyReg || reg
    const worker = candidate.installing || candidate.waiting || candidate.active
    if (worker && worker.state !== 'activated') {
      await new Promise<void>((resolve) => {
        const onState = () => {
          if (worker.state === 'activated') {
            worker.removeEventListener('statechange', onState)
            resolve()
          }
        }
        worker.addEventListener('statechange', onState)
        setTimeout(resolve, 2500)
      })
    }

    return (await navigator.serviceWorker.ready) || candidate
  }

  async function checkSupportAndStatus() {
    if (!import.meta.client) return
    if ('Notification' in window) {
      permissionStatus.value = Notification.permission
    }
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      isSupported.value = true
      try {
        const registration = await getReadyRegistration()
        if (registration?.pushManager) {
          const subscription = await registration.pushManager.getSubscription()
          isSubscribed.value = !!subscription
        }
      } catch {
        isSubscribed.value = false
      }
    }
  }

  async function subscribe(): Promise<{ success: boolean; message?: string }> {
    if (!import.meta.client) {
      return { success: false, message: 'Browser environment required.' }
    }
    if (!('Notification' in window)) {
      return { success: false, message: 'Your browser does not support push notifications.' }
    }
    if (!('serviceWorker' in navigator)) {
      return { success: false, message: 'Your browser does not support service workers.' }
    }

    isLoading.value = true
    try {
      const permission = await Notification.requestPermission()
      permissionStatus.value = permission
      if (permission !== 'granted') {
        isLoading.value = false
        return {
          success: false,
          message: permission === 'denied'
            ? 'Notification permissions are blocked in your browser settings. Please allow notifications for this site.'
            : 'Notification permission request was dismissed.'
        }
      }

      const activeReg = await getReadyRegistration()
      if (!activeReg || !activeReg.pushManager) {
        isLoading.value = false
        return { success: false, message: 'Service worker is activating. Please try again in a moment.' }
      }

      if (!activeReg.active) {
        await new Promise(r => setTimeout(r, 600))
      }

      const keyRes = await apiFetch<{ public_key: string }>('/admin/notifications/vapid-public-key')
      if (!keyRes?.public_key) {
        isLoading.value = false
        return { success: false, message: 'Failed to retrieve notification keys from the server.' }
      }

      const convertedVapidKey = urlBase64ToUint8Array(keyRes.public_key)
      const subscription = await activeReg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedVapidKey
      })

      const res = await apiFetch<{ success?: boolean; message?: string }>('/admin/notifications/subscribe', {
        method: 'POST',
        body: subscription.toJSON()
      })

      isSubscribed.value = true
      return { success: true, message: res?.message || 'Notifications enabled successfully!' }
    } catch (err: any) {
      return { success: false, message: err?.data?.detail || err?.message || 'Failed to enable notifications.' }
    } finally {
      isLoading.value = false
    }
  }

  async function unsubscribe(): Promise<{ success: boolean; message?: string }> {
    if (!import.meta.client) return { success: false, message: 'Browser environment required.' }
    isLoading.value = true
    try {
      const registration = await navigator.serviceWorker.ready
      if (registration) {
        const subscription = await registration.pushManager.getSubscription()
        if (subscription) {
          try {
            await apiFetch('/admin/notifications/unsubscribe', {
              method: 'POST',
              body: subscription.toJSON()
            })
          } catch {
            // ignore
          }
          await subscription.unsubscribe()
        }
      }
      isSubscribed.value = false
      return { success: true, message: 'Notifications disabled successfully.' }
    } catch (err: any) {
      return { success: false, message: err?.message || 'Failed to unsubscribe.' }
    } finally {
      isLoading.value = false
    }
  }

  async function sendTestNotification(): Promise<{ success: boolean; message?: string }> {
    try {
      const res = await apiFetch<{ success: boolean; sent_to_devices: number }>('/admin/notifications/test', {
        method: 'POST'
      })
      if (res?.success) {
        return {
          success: true,
          message: res.sent_to_devices > 0
            ? `Test alert sent to ${res.sent_to_devices} device(s).`
            : 'No active device subscriptions found for this account.'
        }
      }
      return { success: false, message: 'Failed to send test notification.' }
    } catch (err: any) {
      return { success: false, message: err?.data?.detail || err?.message || 'Failed to send test notification.' }
    }
  }

  if (import.meta.client) {
    checkSupportAndStatus()
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
