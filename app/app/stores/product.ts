import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { db, type LocalProduct } from '~/utils/db'

export const useProductsStore = defineStore('products', () => {
  const products = ref<LocalProduct[]>([])
  const isInitialized = ref(false)
  const isLoading = ref(false)

  const auth = useAuthStore()
  const { api } = useApi()

  async function fetchProducts(search?: string) {
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) {
      const localItems = await db.products.toArray()
      if (localItems.length > 0) products.value = localItems
      return
    }

    isLoading.value = true
    try {
      const url = search ? `/${storeId}/product?search=${encodeURIComponent(search)}` : `/${storeId}/product`
      const res = await api<any[]>(url)
      if (res && Array.isArray(res)) {
        const mapped: LocalProduct[] = res.map((p: any) => ({
          slug: p.slug,
          name: p.name,
          unit_price: p.unit_price,
          max_discount: p.max_discount || 0,
          barcode_id: p.barcode_id || '',
          quantities: p.quantities ?? 0,
          unit_in: p.unit_in || 'pcs',
          deleted: p.deleted || false,
          description: p.description || ''
        }))

        products.value = mapped
        await db.products.clear()
        if (mapped.length > 0) {
          await db.products.bulkPut(mapped)
        }
      }
    } catch (err: any) {
      const statusCode = err?.response?.status ?? err?.statusCode ?? err?.status
      if (statusCode === 401 || statusCode === 403 || statusCode === 422) {
        return
      }
      const localItems = await db.products.toArray()
      if (localItems.length > 0) {
        products.value = localItems
      }
    } finally {
      isLoading.value = false
    }
  }

  async function init() {
    const cached = await db.products.toArray()
    if (cached.length > 0) {
      products.value = cached
    }

    if (import.meta.client && window.navigator.onLine) {
      await fetchProducts()
    }
    isInitialized.value = true
  }

  async function deductStock(items: { stock_slug?: string; slug?: string; quantities?: number; qty?: number }[]) {
    for (const item of items) {
      const slug = item.stock_slug || item.slug
      const qty = item.quantities ?? item.qty ?? 0
      if (!slug || qty <= 0) continue

      const prod = products.value.find(p => p.slug === slug)
      if (prod) {
        prod.quantities = Math.max(0, prod.quantities - qty)
        await db.products.put(JSON.parse(JSON.stringify(prod)))
      }
    }
  }

  async function addProduct(productData: Partial<LocalProduct>) {
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) throw new Error('No store ID')

    try {
      const res = await api<any>(`/${storeId}/product`, {
        method: 'POST',
        body: productData
      })

      if (res) {
        const newProduct: LocalProduct = {
          slug: res.slug,
          name: res.name,
          unit_price: res.unit_price,
          max_discount: res.max_discount || 0,
          barcode_id: res.barcode_id || '',
          quantities: res.quantities ?? 0,
          unit_in: res.unit_in || 'pcs',
          deleted: res.deleted || false,
          description: res.description || ''
        }

        products.value.unshift(newProduct)
        await db.products.put(newProduct)
        return newProduct
      }
    } catch (err) {
      throw err
    }
  }

  async function updateProduct(slug: string, updateData: Partial<LocalProduct>) {
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) throw new Error('No store ID')

    try {
      const res = await api<any>(`/${storeId}/product/${slug}`, {
        method: 'PUT',
        body: updateData
      })

      if (res) {
        const idx = products.value.findIndex(p => p.slug === slug)
        const updatedProduct: LocalProduct = {
          slug: res.slug || slug,
          name: res.name || updateData.name || '',
          unit_price: res.unit_price ?? updateData.unit_price ?? 0,
          max_discount: res.max_discount ?? updateData.max_discount ?? 0,
          barcode_id: res.barcode_id ?? updateData.barcode_id ?? '',
          quantities: res.quantities ?? updateData.quantities ?? 0,
          unit_in: res.unit_in ?? updateData.unit_in ?? 'pcs',
          deleted: res.deleted ?? updateData.deleted ?? false,
          description: res.description ?? updateData.description ?? ''
        }

        if (idx !== -1) {
          products.value[idx] = updatedProduct
        }
        await db.products.put(updatedProduct)
        return updatedProduct
      }
    } catch (err) {
      throw err
    }
  }

  async function deleteProduct(slug: string) {
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) throw new Error('No store ID')

    try {
      await api(`/${storeId}/product/${slug}`, {
        method: 'DELETE'
      })

      products.value = products.value.filter(p => p.slug !== slug)
      await db.products.delete(slug)
    } catch (err) {
      throw err
    }
  }

  function getByBarcode(barcode: string): LocalProduct | undefined {
    if (!barcode) return undefined
    const clean = barcode.trim().toLowerCase()
    return products.value.find(p => p.barcode_id && p.barcode_id.trim().toLowerCase() === clean)
  }

  const productCount = computed(() => products.value.filter(p => !p.deleted).length)
  const lowStockProducts = computed(() => products.value.filter(p => !p.deleted && p.quantities <= 10))

  async function appendFromWs(raw: any) {
    const product: LocalProduct = {
      slug: raw.slug,
      name: raw.name,
      unit_price: raw.unit_price,
      max_discount: raw.max_discount || 0,
      barcode_id: raw.barcode_id || '',
      quantities: raw.quantities ?? 0,
      unit_in: raw.unit_in || 'pcs',
      deleted: raw.deleted || false,
      description: raw.description || ''
    }
    const exists = products.value.some(p => p.slug === product.slug)
    if (!exists) {
      products.value.unshift(product)
      await db.products.put(product)
    }
  }

  async function updateFromWs(raw: any) {
    const product: LocalProduct = {
      slug: raw.slug,
      name: raw.name,
      unit_price: raw.unit_price,
      max_discount: raw.max_discount || 0,
      barcode_id: raw.barcode_id || '',
      quantities: raw.quantities ?? 0,
      unit_in: raw.unit_in || 'pcs',
      deleted: raw.deleted || false,
      description: raw.description || ''
    }
    const idx = products.value.findIndex(p => p.slug === product.slug)
    if (idx !== -1) {
      products.value[idx] = product
    } else {
      products.value.unshift(product)
    }
    await db.products.put(product)
  }

  async function removeFromWs(slug: string) {
    products.value = products.value.filter(p => p.slug !== slug)
    await db.products.delete(slug)
  }

  init()

  return {
    products,
    isInitialized,
    isLoading,
    productCount,
    lowStockProducts,
    fetchProducts,
    addProduct,
    updateProduct,
    deleteProduct,
    getByBarcode,
    deductStock,
    appendFromWs,
    updateFromWs,
    removeFromWs,
    init
  }
})

export const useProductStore = useProductsStore
