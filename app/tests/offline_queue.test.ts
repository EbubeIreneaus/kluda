import { describe, it, expect, beforeEach } from 'vitest'
import { db, type PendingSale, type LocalSale } from '../app/utils/db'

describe('Offline Sales Queue & Deduplication', () => {
  beforeEach(async () => {
    await db.pendingSales.clear()
    await db.salesCache.clear()
    await db.products.clear()
  })

  it('queues a pending sale into IndexedDB with idempotency key', async () => {
    const idempotencyKey = '550e8400-e29b-41d4-a716-446655440000'
    const pendingSale: PendingSale = {
      idempotency_key: idempotencyKey,
      items: [{ stock_slug: 'milo-500g', quantities: 2, amount: 250000 }],
      discount: 0,
      payment_method: 'cash',
      amount_recived: 500000,
      created_at: new Date().toISOString(),
      status: 'completed'
    }

    await db.pendingSales.add(pendingSale)
    const stored = await db.pendingSales.toArray()

    expect(stored.length).toBe(1)
    expect(stored[0].idempotency_key).toBe(idempotencyKey)
    expect(stored[0].items[0].stock_slug).toBe('milo-500g')
  })

  it('prunes successfully synced sales by idempotency keys', async () => {
    const key1 = '11111111-1111-1111-1111-111111111111'
    const key2 = '22222222-2222-2222-2222-222222222222'

    await db.pendingSales.bulkAdd([
      {
        idempotency_key: key1,
        items: [{ stock_slug: 'item-1', quantities: 1, amount: 100000 }],
        discount: 0,
        payment_method: 'cash',
        amount_recived: 100000,
        created_at: new Date().toISOString(),
        status: 'completed'
      },
      {
        idempotency_key: key2,
        items: [{ stock_slug: 'item-2', quantities: 1, amount: 200000 }],
        discount: 0,
        payment_method: 'pos',
        amount_recived: 200000,
        created_at: new Date().toISOString(),
        status: 'completed'
      }
    ])

    const beforeSync = await db.pendingSales.toArray()
    expect(beforeSync.length).toBe(2)

    const syncedKeys = [key1]
    await db.pendingSales.bulkDelete(syncedKeys)

    const afterSync = await db.pendingSales.toArray()
    expect(afterSync.length).toBe(1)
    expect(afterSync[0].idempotency_key).toBe(key2)
  })

  it('updates local product stock quantity in IndexedDB cache', async () => {
    await db.products.add({
      slug: 'item-1',
      name: 'Item 1',
      unit_price: 100000,
      max_discount: 0,
      barcode_id: '123456',
      quantities: 10,
      unit_in: 'pcs',
      deleted: false,
      description: ''
    })

    const prod = await db.products.get('item-1')
    expect(prod).toBeDefined()
    expect(prod?.quantities).toBe(10)

    if (prod) {
      prod.quantities = Math.max(0, prod.quantities - 3)
      await db.products.put(prod)
    }

    const updated = await db.products.get('item-1')
    expect(updated?.quantities).toBe(7)
  })
})
