import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface CartItem {
  slug: string
  name: string
  unit_price: number
  quantity: number
  max_discount: number
  barcode_id?: string
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const discount = ref(0)
  const customerId = ref<string | null>(null)
  const paymentMethod = ref<'cash' | 'pos' | 'transfer' | 'online' | 'debt'>('cash')
  const amountReceived = ref(0)
  const staffNote = ref('')

  const itemCount = computed(() => items.value.reduce((sum, item) => sum + item.quantity, 0))
  const subtotal = computed(() => items.value.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0))
  const grandTotal = computed(() => Math.max(0, subtotal.value - discount.value))
  const change = computed(() => Math.max(0, amountReceived.value - grandTotal.value))
  const isEmpty = computed(() => items.value.length === 0)

  function addItem(product: { slug: string, name: string, unit_price: number, max_discount?: number, barcode_id?: string }) {
    const existing = items.value.find(item => item.slug === product.slug)
    if (existing) {
      existing.quantity++
    } else {
      items.value.push({
        slug: product.slug,
        name: product.name,
        unit_price: product.unit_price,
        quantity: 1,
        max_discount: product.max_discount || 0,
        barcode_id: product.barcode_id
      })
    }
  }

  function removeItem(slug: string) {
    items.value = items.value.filter(item => item.slug !== slug)
  }

  function updateQuantity(slug: string, quantity: number) {
    const item = items.value.find(i => i.slug === slug)
    if (item) {
      item.quantity = Math.max(1, quantity)
    }
  }

  function clearCart() {
    items.value = []
    discount.value = 0
    customerId.value = null
    paymentMethod.value = 'cash'
    amountReceived.value = 0
    staffNote.value = ''
  }

  return {
    items,
    discount,
    customerId,
    paymentMethod,
    amountReceived,
    staffNote,
    itemCount,
    subtotal,
    grandTotal,
    change,
    isEmpty,
    addItem,
    removeItem,
    updateQuantity,
    clearCart
  }
})
