export const usePosSocket = () => {
  const config = useRuntimeConfig()
  const auth = useAuthStore()

  const salesStore = useSalesStore()
  const productStore = useProductsStore()
  const customerStore = useCustomerStore()

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let backoffMs = 1_000
  const MAX_BACKOFF = 30_000

  function getWsUrl(): string {
    const rawBase: string = config.public.apiBase as string
    const hostBase = rawBase.replace(/\/api\/v1\/?$/, '').replace(/\/v1\/?$/, '')
    const wsBase = hostBase.replace(/^http/, 'ws')
    const storeId = auth.store_id || auth.staff?.store_id || 'unknown'
    const staffId = auth.staff?.staff_id ?? 'unknown'
    return `${wsBase}/ws/${storeId}/${staffId}`
  }

  function connect() {
    if (!import.meta.client) return
    const storeId = auth.store_id || auth.staff?.store_id
    const staffId = auth.staff?.staff_id
    if (!storeId || !staffId) {
      scheduleReconnect()
      return
    }

    const url = getWsUrl()

    try {
      ws = new WebSocket(url)
    } catch {
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      backoffMs = 1_000
    }

    ws.onmessage = (event: MessageEvent) => {
      let payload: { event: string; data: any }
      try {
        payload = JSON.parse(event.data)
      } catch {
        return
      }

      const { event: evtName, data } = payload

      switch (evtName) {
        case 'add_sale':
          salesStore.fetchSales()
          break
        case 'update_sale':
          salesStore.updateFromWs(data)
          break
        case 'delete_sale':
          salesStore.removeFromWs(data.sale_id)
          break

        case 'add_product':
          productStore.appendFromWs(data)
          break
        case 'update_product':
          productStore.updateFromWs(data)
          break
        case 'delete_product':
          productStore.removeFromWs(data.slug)
          break

        case 'add_customer':
          customerStore.appendCustomerFromWs(data)
          break
        case 'update_customer':
          customerStore.updateCustomerFromWs(data)
          break
        case 'delete_customer':
          customerStore.removeCustomerFromWs(data.customer_id)
          break

        case 'add_debt':
          customerStore.appendDebtFromWs(data)
          break
        case 'update_debt':
          customerStore.updateDebtFromWs(data)
          break
        case 'delete_debt':
          customerStore.removeDebtFromWs(data.debtor_id)
          break

        default:
          break
      }
    }

    ws.onclose = () => {
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      backoffMs = Math.min(backoffMs * 2, MAX_BACKOFF)
      connect()
    }, backoffMs)
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws?.close()
    ws = null
  }

  onMounted(() => connect())
  onUnmounted(() => disconnect())
}
