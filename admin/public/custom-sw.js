self.addEventListener('push', function (event) {
  if (!event.data) return
  try {
    const payload = event.data.json()
    const title = payload.title || 'Kluda'
    const options = {
      body: payload.body || '',
      icon: '/pwa-192x192.png',
      badge: '/favicon.svg',
      data: payload.data || {},
      vibrate: [100, 50, 100]
    }
    event.waitUntil(self.registration.showNotification(title, options))
  } catch {
    event.waitUntil(
      self.registration.showNotification('Kluda', {
        body: event.data.text(),
        icon: '/pwa-192x192.png'
      })
    )
  }
})

self.addEventListener('notificationclick', function (event) {
  event.notification.close()
  const targetUrl = event.notification.data?.url || '/'
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i]
        if (client.url === targetUrl && 'focus' in client) {
          return client.focus()
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl)
      }
    })
  )
})
