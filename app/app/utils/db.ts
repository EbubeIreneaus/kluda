import Dexie, { type Table } from 'dexie'

export interface PendingSaleItem {
  stock_slug: string
  amount: number
  quantities: number
}

export interface PendingSale {
  idempotency_key: string
  items: PendingSaleItem[]
  discount: number
  customer_id: string | null
  payment_method: 'cash' | 'pos' | 'debt' | 'transfer' | 'online'
  amount_recived: number
  staff_note: string | null
  status: 'pending' | 'completed' | 'cancelled'
  created_at: string
}

export interface LocalProduct {
  slug: string
  name: string
  unit_price: number
  max_discount: number
  barcode_id: string
  quantities: number
  unit_in: string
  deleted: boolean
  sku?: string
  description?: string
}

export interface LocalCustomer {
  customer_id: string
  fullname: string
  email: string
  phone: string
  address: string
  status: string
  created_at: string
}

export interface LocalDebtor {
  debtor_id: string
  customer_name: string
  customer_id: string
  amount: number
  note: string
  status: string
  created_at: string
}

export interface LocalStaffMember {
  staff_id: string
  first_name: string
  last_name: string
  role: string
  email: string
  permission: string[]
  pin_hash: string | null
  pin_salt: string | null
  has_pin: boolean
  status: string
}

export interface LocalSale {
  sale_id: string
  full_sale_id: string
  idempotency_key: string
  date: string
  customer: string | null
  items: Array<{ name: string; qty: number; price: number }>
  total: number
  method: string
  status: string
  staff: string
  note: string
}

export class POSDatabase extends Dexie {
  pendingSales!: Table<PendingSale, string>
  products!: Table<LocalProduct, string>
  customers!: Table<LocalCustomer, string>
  salesCache!: Table<LocalSale, string>
  debtors!: Table<LocalDebtor, string>
  staffMembers!: Table<LocalStaffMember, string>

  constructor(dbName = 'RetailPOS_DB') {
    super(dbName)
    this.version(1).stores({
      pendingSales: 'idempotency_key, created_at',
      products:     'slug, name, barcode_id',
      customers:    'customer_id, fullname, phone',
      salesCache:   'sale_id, date',
      debtors:      'debtor_id',
    })
    this.version(2).stores({
      pendingSales: 'idempotency_key, created_at',
      products:     'slug, name, barcode_id',
      customers:    'customer_id, fullname, phone',
      salesCache:   'sale_id, date',
      debtors:      'debtor_id',
      staffMembers: 'staff_id, role',
    })
  }
}

const dbInstances = new Map<string, POSDatabase>()

export function getStoreDb(storeId?: string | null): POSDatabase {
  let resolvedId = storeId
  if (!resolvedId && typeof window !== 'undefined' && window.localStorage) {
    resolvedId = window.localStorage.getItem('pos_store_id') || 'default'
  }
  const safeId = resolvedId || 'default'
  const dbName = `RetailPOS_DB_${safeId}`

  let instance = dbInstances.get(dbName)
  if (!instance) {
    instance = new POSDatabase(dbName)
    dbInstances.set(dbName, instance)
  }
  return instance
}

export async function deleteStoreDb(storeId: string): Promise<void> {
  const dbName = `RetailPOS_DB_${storeId}`
  const existing = dbInstances.get(dbName)
  if (existing) {
    existing.close()
    dbInstances.delete(dbName)
  }
  await Dexie.delete(dbName)
}

export const db: POSDatabase = new Proxy({} as POSDatabase, {
  get(_target, prop) {
    const activeDb = getStoreDb()
    const value = (activeDb as any)[prop]
    if (typeof value === 'function') {
      return value.bind(activeDb)
    }
    return value
  }
})
