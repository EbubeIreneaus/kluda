import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { db, getStoreDb, type PendingSale, type LocalSale } from '~/utils/db'

export interface ShadowJournalEntry {
  key: string
  sale: PendingSale
  recorded_at: string
}

function getShadowJournal(storeId: string): ShadowJournalEntry[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(`kluda_shadow_journal_${storeId}`)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function addToShadowJournal(storeId: string, sale: PendingSale) {
  if (typeof window === 'undefined') return
  try {
    const list = getShadowJournal(storeId)
    const updated = [
      ...list.filter((e) => e.key !== sale.idempotency_key),
      {
        key: sale.idempotency_key,
        sale,
        recorded_at: new Date().toISOString()
      }
    ].slice(-200)
    localStorage.setItem(`kluda_shadow_journal_${storeId}`, JSON.stringify(updated))
  } catch {}
}

function removeFromShadowJournal(storeId: string, syncedKeys?: string[]) {
  if (typeof window === 'undefined') return
  try {
    if (!syncedKeys || syncedKeys.length === 0) {
      localStorage.removeItem(`kluda_shadow_journal_${storeId}`)
      return
    }
    const list = getShadowJournal(storeId)
    const keySet = new Set(syncedKeys)
    const remaining = list.filter((e) => !keySet.has(e.key))
    if (remaining.length === 0) {
      localStorage.removeItem(`kluda_shadow_journal_${storeId}`)
    } else {
      localStorage.setItem(`kluda_shadow_journal_${storeId}`, JSON.stringify(remaining))
    }
  } catch {}
}

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
      staff: {
        user_id: auth.user?.user_id || "",
        fullname: auth.user?.fullname || ""
      },
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
            staff: {
              user_id: sale.user.user_id,
              fullname: sale.user.fullname
            },
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
    const sub = useSubscription()
    if (sub.isQuotaBlocked.value) {
      throw new Error(sub.quotaBlockReason.value || 'Sales limit reached or offline lease expired')
    }

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
    const storeId = auth.store_id || auth.staff?.store_id
    if (storeId) {
      addToShadowJournal(storeId, newSale)
    }

    const formattedLocalSale = mapPendingToLocalSale(newSale)
    sales.value = [formattedLocalSale, ...sales.value]
    await db.salesCache.put(formattedLocalSale)

    const productStore = useProductsStore()
    await productStore.deductStock(newSale.items)

    syncPendingSales()
  }

  async function syncPendingSales(isManual = false) {
    if (isSyncing.value) return

    if (!isManual && typeof window !== 'undefined' && localStorage.getItem('pos_auto_sync') === 'false') {
      return
    }

    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) return

    isSyncing.value = true
    let totalSyncedCount = 0

    try {
      const activeDb = getStoreDb(storeId)
      let pending = await activeDb.pendingSales.toArray()

      // Detection & Auto-Recovery of deleted IndexedDB offline transactions
      const shadowJournal = getShadowJournal(storeId)
      if (shadowJournal.length > 0) {
        const pendingKeySet = new Set(pending.map((p) => p.idempotency_key))
        const missingFromDb: PendingSale[] = []

        for (const entry of shadowJournal) {
          if (!pendingKeySet.has(entry.key) && entry.sale) {
            missingFromDb.push(entry.sale)
          }
        }

        if (missingFromDb.length > 0) {
          console.warn(
            `[Audit Trail] Detected ${missingFromDb.length} missing/deleted offline sale(s) in IndexedDB. Auto-recovering!`,
            missingFromDb.map((m) => m.idempotency_key)
          )
          await activeDb.pendingSales.bulkPut(missingFromDb)
          pending = await activeDb.pendingSales.toArray()
        }
      }

      if (pending.length > 0) {
        try {
          const res = await api<any>(`/${storeId}/sales`, {
            method: 'POST',
            body: pending
          })

          if (res) {
            const count = (res.synced_keys && Array.isArray(res.synced_keys)) ? res.synced_keys.length : pending.length
            totalSyncedCount += count

            if (res.synced_keys && Array.isArray(res.synced_keys) && res.synced_keys.length > 0) {
              await activeDb.pendingSales.bulkDelete(res.synced_keys)
              removeFromShadowJournal(storeId, res.synced_keys)
            } else if (res.success) {
              await activeDb.pendingSales.clear()
              removeFromShadowJournal(storeId)
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
        }
      }

      if (auth.stores && auth.stores.length > 0) {
        for (const otherStore of auth.stores) {
          if (!otherStore.store_id || otherStore.store_id === storeId) continue
          const otherDb = getStoreDb(otherStore.store_id)
          let otherPending = await otherDb.pendingSales.toArray()
          const otherShadow = getShadowJournal(otherStore.store_id)
          if (otherShadow.length > 0) {
            const otherKeySet = new Set(otherPending.map((p) => p.idempotency_key))
            const otherMissing: PendingSale[] = []
            for (const entry of otherShadow) {
              if (!otherKeySet.has(entry.key) && entry.sale) {
                otherMissing.push(entry.sale)
              }
            }
            if (otherMissing.length > 0) {
              await otherDb.pendingSales.bulkPut(otherMissing)
              otherPending = await otherDb.pendingSales.toArray()
            }
          }
          if (otherPending.length > 0) {
            try {
              const res = await api<any>(`/${otherStore.store_id}/sales`, {
                method: 'POST',
                body: otherPending
              })
              if (res) {
                const count = (res.synced_keys && Array.isArray(res.synced_keys)) ? res.synced_keys.length : otherPending.length
                totalSyncedCount += count

                if (res.synced_keys && Array.isArray(res.synced_keys) && res.synced_keys.length > 0) {
                  await otherDb.pendingSales.bulkDelete(res.synced_keys)
                  removeFromShadowJournal(otherStore.store_id, res.synced_keys)
                } else if (res.success) {
                  await otherDb.pendingSales.clear()
                  removeFromShadowJournal(otherStore.store_id)
                }
              }
            } catch {}
          }
        }
      }

      if (totalSyncedCount > 0 && typeof window !== 'undefined' && localStorage.getItem('pos_offline_alerts') !== 'false') {
        const toast = useToast()
        toast.add({
          title: 'Offline Sales Synced',
          description: `${totalSyncedCount} offline transaction${totalSyncedCount > 1 ? 's' : ''} uploaded to cloud.`,
          color: 'success',
          icon: 'i-lucide-cloud-upload'
        })
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
