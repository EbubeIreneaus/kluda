import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { db, type PendingSale, type LocalSale } from '~/utils/db'

export const useSalesStore = defineStore('sales', () => {
  const sales = ref<LocalSale[]>([])
  const isInitialized = ref(false)
  const isSyncing = ref(false)
  const isOnline = useOnline()

  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase
  const auth = useAuthStore()

  function mapPendingToLocalSale(pendingSale: PendingSale): LocalSale {
    const subtotalKobo = pendingSale.items.reduce((sum, item) => sum + (item.amount * item.quantities), 0)
    const totalKobo = Math.max(0, subtotalKobo - pendingSale.discount)

    const dateObj = new Date(pendingSale.created_at)
    const yyyy = dateObj.getFullYear()
    const mm = String(dateObj.getMonth() + 1).padStart(2, '0')
    const dd = String(dateObj.getDate()).padStart(2, '0')
    const hh = String(dateObj.getHours()).padStart(2, '0')
    const min = String(dateObj.getMinutes()).padStart(2, '0')
    const dateFormatted = `${yyyy}-${mm}-${dd} ${hh}:${min}`

    return {
      sale_id: 'SYNCING',
      full_sale_id: pendingSale.idempotency_key,
      idempotency_key: pendingSale.idempotency_key,
      date: dateFormatted,
      customer: pendingSale.customer_id ? 'Linked Customer' : 'Walk-in',
      items: pendingSale.items.map((item) => ({
        name: item.stock_slug,
        qty: item.quantities,
        price: item.amount // in Kobo
      })),
      total: totalKobo, // in Kobo
      method: pendingSale.payment_method,
      status: pendingSale.status || 'pending',
      staff: 'Admin Staff',
      note: pendingSale.staff_note || ''
    }
  }

  async function fetchSales() {
    try {
      const headers: Record<string, string> = {}
      if (auth.token) {
        headers['Authorization'] = `Bearer ${auth.token}`
      }

      const today = new Date().toISOString().split('T')[0]
      const response = await $fetch<any>(`${apiBase}/sales?sale_date=${today}`, { headers })
      
      let serverSales: LocalSale[] = []
      if (response && response.items) {
        serverSales = response.items.map((sale: any) => {
          const subtotalKobo = sale.items.reduce((sum: number, item: any) => sum + (item.amount * item.quantities), 0)
          const totalKobo = Math.max(0, subtotalKobo - sale.discount)

          const dateObj = new Date(sale.created_at)
          const yyyy = dateObj.getFullYear()
          const mm = String(dateObj.getMonth() + 1).padStart(2, '0')
          const dd = String(dateObj.getDate()).padStart(2, '0')
          const hh = String(dateObj.getHours()).padStart(2, '0')
          const min = String(dateObj.getMinutes()).padStart(2, '0')
          const dateFormatted = `${yyyy}-${mm}-${dd} ${hh}:${min}`

          return {
            sale_id: sale.sale_id.substring(0, 8).toUpperCase(),
            full_sale_id: sale.sale_id,
            idempotency_key: sale.idempotency_key,
            date: dateFormatted,
            customer: sale.customer ? sale.customer.fullname : null,
            items: sale.items.map((item: any) => ({
              name: item.stock?.name || item.stock_slug,
              qty: item.quantities,
              price: item.amount // already in Kobo
            })),
            total: totalKobo, // in Kobo
            method: sale.payment_method,
            status: sale.status,
            staff: 'Admin Staff',
            note: sale.staff_note || ''
          }
        })
      }

      // Read local pending sales that have NOT yet synced to server
      const pending = await db.pendingSales.toArray()
      const serverKeySet = new Set(serverSales.map(s => s.idempotency_key))
      
      // Keep any pending sales not yet returned by the server
      const pendingAsLocal = pending
        .filter(p => !serverKeySet.has(p.idempotency_key))
        .map(mapPendingToLocalSale)

      // Merged list: pending sales at the top, followed by server sales
      const mergedSales = [...pendingAsLocal, ...serverSales]

      sales.value = mergedSales
      await db.salesCache.clear()
      if (mergedSales.length > 0) {
        await db.salesCache.bulkPut(mergedSales)
      }
    } catch (err) {
      console.warn('Failed to fetch sales from API, using cached sales from IndexedDB:', err)
      const cached = await db.salesCache.toArray()
      if (cached.length > 0) {
        sales.value = cached
      }
    }
  }

  async function init() {
    // 1. Immediately load local cache and any unsynced pending sales
    const cached = await db.salesCache.toArray()
    const pending = await db.pendingSales.toArray()

    const cachedKeySet = new Set(cached.map(s => s.idempotency_key))
    const pendingUncached = pending
      .filter(p => !cachedKeySet.has(p.idempotency_key))
      .map(mapPendingToLocalSale)

    const initialMerged = [...pendingUncached, ...cached]
    if (initialMerged.length > 0) {
      sales.value = initialMerged
    }

    // 2. If online, fetch and sync
    if (isOnline.value) {
      await fetchSales()
      await syncPendingSales()
    }
  }

  async function addSale(saleData: Omit<PendingSale, 'created_at'>) {
    const newSale: PendingSale = {
      ...saleData,
      created_at: new Date().toISOString()
    }

    // Save to IndexedDB (Dexie)
    await db.pendingSales.add(newSale)

    const formattedLocalSale = mapPendingToLocalSale(newSale)

    sales.value.unshift(formattedLocalSale)
    await db.salesCache.put(formattedLocalSale)

    // Optimistically deduct local stock immediately (0ms) in memory and IndexedDB
    const productStore = useProductsStore()
    await productStore.deductStock(newSale.items)

    syncPendingSales()
  }

  async function syncPendingSales() {
    if (isSyncing.value) return

    try {
      const headers: Record<string, string> = {}
      if (auth.token) {
        headers['Authorization'] = `Bearer ${auth.token}`
      }
      const pingRes = await $fetch<any>(`${apiBase}/sales/ping`, { headers })
      if (!pingRes || !pingRes.db_connected) {
        return
      }
    } catch (err) {
      console.warn('Backend database is currently offline:', err)
      return
    }

    // 2. Fetch pending local sales
    const pending = await db.pendingSales.toArray()
    if (pending.length === 0) return

    isSyncing.value = true

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (auth.token) {
        headers['Authorization'] = `Bearer ${auth.token}`
      }

      const res = await $fetch<any>(`${apiBase}/sales/`, {
        method: 'POST',
        headers,
        body: pending
      })

      if (res) {
        if (res.synced_keys && Array.isArray(res.synced_keys) && res.synced_keys.length > 0) {
          await db.pendingSales.bulkDelete(res.synced_keys)
        } else if (res.success) {
          await db.pendingSales.clear()
        }

        if (res.failed && res.failed.length > 0) {
          console.warn('Some pending sales failed to sync:', res.failed)
        }

        await fetchSales()
        const productStore = useProductsStore()
        await productStore.fetchProducts()
      }
    } catch (err) {
      console.error('Failed to batch sync pending sales:', err)
    } finally {
      isSyncing.value = false
    }
  }

  // Watch online status: trigger sync when we come back online
  watch(isOnline, (online) => {
    if (online) {
      syncPendingSales()
    }
  })

  // Auto-initialize when store is instantiated
  init()

  // ── WebSocket helpers ────────────────────────────────────────────────────

  async function appendSaleFromWs(sale: LocalSale) {
    // Avoid duplicates
    const exists = sales.value.some(s => s.idempotency_key === sale.idempotency_key)
    if (!exists) {
      sales.value.unshift(sale)
      await db.salesCache.put(sale)
    }
  }

  async function updateFromWs(sale: LocalSale) {
    const idx = sales.value.findIndex(s => s.full_sale_id === sale.full_sale_id)
    if (idx !== -1) {
      sales.value[idx] = sale
    } else {
      sales.value.unshift(sale)
    }
    await db.salesCache.put(sale)
  }

  async function removeFromWs(saleId: string) {
    sales.value = sales.value.filter(s => s.full_sale_id !== saleId)
    await db.salesCache.delete(saleId)
  }

  return {
    sales,
    isInitialized,
    isSyncing,
    isOnline,
    fetchSales,
    addSale,
    syncPendingSales,
    appendSaleFromWs,
    updateFromWs,
    removeFromWs,
    init
  }
})
