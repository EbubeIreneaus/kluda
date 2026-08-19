import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { db, type PendingSale, type LocalSale } from '~/utils/db'

export const useSalesStore = defineStore('sales', () => {
  const sales = ref<LocalSale[]>([])
  const isInitialized = ref(false)
  const isSyncing = ref(false)
  const isOnline = useOnline()

  const auth = useAuthStore()
  const { api } = useApi()

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
        price: item.amount
      })),
      total: totalKobo,
      method: pendingSale.payment_method,
      status: pendingSale.status || 'pending',
      staff: 'Admin Staff',
      note: pendingSale.staff_note || ''
    }
  }

  async function fetchSales() {
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) {
      const cached = await db.salesCache.toArray()
      if (cached.length > 0) sales.value = cached
      return
    }

    try {
      const today = new Date().toISOString().split('T')[0]
      const response = await api<any>(`/${storeId}/sales?sale_date=${today}`)
      
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
              price: item.amount
            })),
            total: totalKobo,
            method: sale.payment_method,
            status: sale.status,
            staff: 'Admin Staff',
            note: sale.staff_note || ''
          }
        })
      }

      const pending = await db.pendingSales.toArray()
      const serverKeySet = new Set(serverSales.map(s => s.idempotency_key))
      
      const pendingAsLocal = pending
        .filter(p => !serverKeySet.has(p.idempotency_key))
        .map(mapPendingToLocalSale)

      const mergedSales = [...pendingAsLocal, ...serverSales]

      sales.value = mergedSales
      await db.salesCache.clear()
      if (mergedSales.length > 0) {
        await db.salesCache.bulkPut(mergedSales)
      }
    } catch (err: any) {
      const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
      if (statusCode === 401 || statusCode === 403 || statusCode === 422) {
        return
      }
      const cached = await db.salesCache.toArray()
      if (cached.length > 0) {
        sales.value = cached
      }
    }
  }

  async function init() {
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

    if (import.meta.client && window.navigator.onLine) {
      await fetchSales()
      syncPendingSales()
    }
    isInitialized.value = true
  }

  async function recordSale(payload: {
    items: { stock_slug: string; quantities: number; amount: number }[]
    discount: number
    payment_method: 'cash' | 'pos' | 'debt' | 'transfer' | 'online'
    amount_recived: number
    customer_id?: string | null
    staff_note?: string | null
    idempotency_key?: string
    status?: string
  }) {
    const newSale: PendingSale = {
      idempotency_key: payload.idempotency_key || crypto.randomUUID(),
      items: payload.items,
      discount: payload.discount,
      payment_method: payload.payment_method,
      amount_recived: payload.amount_recived,
      customer_id: payload.customer_id || null,
      staff_note: payload.staff_note || null,
      created_at: new Date().toISOString(),
      status: 'completed'
    }

    await db.pendingSales.add(newSale)

    const formattedLocalSale = mapPendingToLocalSale(newSale)
    sales.value = [formattedLocalSale, ...sales.value]
    await db.salesCache.put(formattedLocalSale)

    const productStore = useProductsStore()
    await productStore.deductStock(newSale.items)

    syncPendingSales()
  }

  async function syncPendingSales() {
    if (isSyncing.value) return

    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) return

    try {
      const pingRes = await api<any>(`/${storeId}/sales/ping`)
      if (!pingRes || !pingRes.db_connected) {
        return
      }
    } catch (err: any) {
      const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
      if (statusCode === 401 || statusCode === 403 || statusCode === 422) {
        return
      }
      return
    }

    const pending = await db.pendingSales.toArray()
    if (pending.length === 0) return

    isSyncing.value = true

    try {
      const res = await api<any>(`/${storeId}/sales`, {
        method: 'POST',
        body: pending
      })

      if (res) {
        if (res.synced_keys && Array.isArray(res.synced_keys) && res.synced_keys.length > 0) {
          await db.pendingSales.bulkDelete(res.synced_keys)
        } else if (res.success) {
          await db.pendingSales.clear()
        }

        await fetchSales()
        const productStore = useProductsStore()
        await productStore.fetchProducts()
      }
    } catch (err: any) {
      const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
      if (statusCode === 401 || statusCode === 403 || statusCode === 422) {
        return
      }
    } finally {
      isSyncing.value = false
    }
  }

  watch(isOnline, (online) => {
    if (online) {
      syncPendingSales()
    }
  })

  async function appendSaleFromWs(sale: LocalSale) {
    const existingIdx = sales.value.findIndex(s => s.idempotency_key === sale.idempotency_key || s.full_sale_id === sale.full_sale_id)
    if (existingIdx === -1) {
      sales.value = [sale, ...sales.value]
      await db.salesCache.put(sale)
    }
  }

  async function updateFromWs(sale: LocalSale) {
    const existingIdx = sales.value.findIndex(s => s.idempotency_key === sale.idempotency_key || s.full_sale_id === sale.full_sale_id)
    if (existingIdx !== -1) {
      sales.value[existingIdx] = { ...sales.value[existingIdx], ...sale }
      await db.salesCache.put(sales.value[existingIdx]!)
    }
  }

  async function removeFromWs(saleId: string) {
    const existingIdx = sales.value.findIndex(s => s.sale_id === saleId || s.full_sale_id === saleId)
    if (existingIdx !== -1) {
      const removed = sales.value.splice(existingIdx, 1)[0]
      if (removed) {
        await db.salesCache.delete(removed.idempotency_key)
      }
    }
  }

  return {
    sales,
    isInitialized,
    isSyncing,
    init,
    fetchSales,
    recordSale,
    addSale: recordSale,
    syncPendingSales,
    appendSaleFromWs,
    updateFromWs,
    removeFromWs
  }
})
