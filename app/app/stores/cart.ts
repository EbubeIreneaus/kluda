import { defineStore } from 'pinia'

interface CartItem {
  slug: string
  name: string
  unit_price: number
  quantity: number
  max_discount: number
  barcode_id?: string
}

interface CartState {
  items: CartItem[]
  discount: number
  customerId: string | null
  paymentMethod: 'cash' | 'pos' | 'transfer' | 'online' | 'debt'
  amountReceived: number
  staffNote: string
}

export const useCartStore = defineStore('cart', {
  state: (): CartState => ({
    items: [],
    discount: 0,
    customerId: null,
    paymentMethod: 'cash',
    amountReceived: 0,
    staffNote: ''
  }),

  getters: {
    itemCount: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),

    subtotal: (state) => state.items.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0),

    grandTotal(): number {
      return Math.max(0, this.subtotal - this.discount)
    },

    change(): number {
      return Math.max(0, this.amountReceived - this.grandTotal)
    },

    isEmpty: (state) => state.items.length === 0
  },

  actions: {
    addItem(product: { slug: string, name: string, unit_price: number, max_discount: number, barcode_id?: string }) {
      const existing = this.items.find(item => item.slug === product.slug)
      if (existing) {
        existing.quantity++
      } else {
        this.items.push({
          slug: product.slug,
          name: product.name,
          unit_price: product.unit_price,
          quantity: 1,
          max_discount: product.max_discount,
          barcode_id: product.barcode_id
        })
      }
    },

    removeItem(slug: string) {
      this.items = this.items.filter(item => item.slug !== slug)
    },

    updateQuantity(slug: string, quantity: number) {
      const item = this.items.find(i => i.slug === slug)
      if (item) {
        item.quantity = Math.max(1, quantity)
      }
    },

    clearCart() {
      this.items = []
      this.discount = 0
      this.customerId = null
      this.paymentMethod = 'cash'
      this.amountReceived = 0
      this.staffNote = ''
    }
  }
})
