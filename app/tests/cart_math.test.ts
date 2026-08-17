import { describe, it, expect } from 'vitest'

function calculateCartTotals(
  items: { unit_price: number; qty: number; max_discount?: number }[],
  requestedDiscount: number,
  amountReceived: number
) {
  const subtotal = items.reduce((sum, item) => sum + Math.round(item.unit_price * item.qty), 0)
  const totalMaxDiscountAllowed = items.reduce((sum, item) => sum + ((item.max_discount || 0) * item.qty), 0)
  const appliedDiscount = Math.min(Math.max(0, requestedDiscount), totalMaxDiscountAllowed, subtotal)
  const finalTotal = Math.max(0, subtotal - appliedDiscount)
  const change = Math.max(0, amountReceived - finalTotal)

  return {
    subtotal,
    appliedDiscount,
    finalTotal,
    change,
    isFullyPaid: amountReceived >= finalTotal
  }
}

describe('POS Cart Math & Pricing Logic', () => {
  it('calculates integer item quantities accurately in kobo', () => {
    const items = [
      { unit_price: 250000, qty: 2 },
      { unit_price: 180000, qty: 3 }
    ]
    const result = calculateCartTotals(items, 0, 1100000)

    expect(result.subtotal).toBe(1040000)
    expect(result.finalTotal).toBe(1040000)
    expect(result.change).toBe(60000)
    expect(result.isFullyPaid).toBe(true)
  })

  it('calculates decimal quantities accurately for weighted/measured goods', () => {
    const items = [
      { unit_price: 100000, qty: 1.5 },
      { unit_price: 200000, qty: 0.25 }
    ]
    const result = calculateCartTotals(items, 0, 200000)

    expect(result.subtotal).toBe(200000)
    expect(result.finalTotal).toBe(200000)
    expect(result.change).toBe(0)
    expect(result.isFullyPaid).toBe(true)
  })

  it('caps discount at total allowed max discount', () => {
    const items = [
      { unit_price: 500000, qty: 1, max_discount: 50000 },
      { unit_price: 300000, qty: 2, max_discount: 20000 }
    ]
    const result = calculateCartTotals(items, 200000, 1100000)

    expect(result.subtotal).toBe(1100000)
    expect(result.appliedDiscount).toBe(90000)
    expect(result.finalTotal).toBe(1010000)
    expect(result.change).toBe(90000)
  })

  it('prevents negative discount inputs and over-discounting beyond subtotal', () => {
    const items = [{ unit_price: 100000, qty: 1, max_discount: 150000 }]
    const negativeDiscount = calculateCartTotals(items, -50000, 100000)
    expect(negativeDiscount.appliedDiscount).toBe(0)
    expect(negativeDiscount.finalTotal).toBe(100000)

    const overDiscount = calculateCartTotals(items, 500000, 100000)
    expect(overDiscount.appliedDiscount).toBe(100000)
    expect(overDiscount.finalTotal).toBe(0)
  })
})
