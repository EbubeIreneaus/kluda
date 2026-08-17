import Dexie, { type Table } from 'dexie'

export interface PendingSaleItem {
  stock_slug: string
  amount: number      // in kobo (stored integer)
  quantities: number
}

export interface PendingSale {
  idempotency_key: string
  items: PendingSaleItem[]
  discount: number    // in kobo (stored integer)
  customer_id: string | null
  payment_method: 'cash' | 'pos' | 'debt' | 'transfer' | 'online'
  amount_recived: number // in kobo (stored integer)
  staff_note: string | null
  status: 'pending' | 'completed' | 'cancelled'
  created_at: string
}

export interface LocalProduct {
  slug: string
  name: string
  unit_price: number    // in kobo
  max_discount: number  // in kobo
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
  customer_id:string
  amount: number
  note: string
  status: string
  created_at: string
}


export interface LocalSale {
  sale_id: string
  full_sale_id: string
  idempotency_key: string
  date: string
  customer: string | null
  items: Array<{ name: string; qty: number; price: number }>
  total: number // in kobo
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

  constructor() {
    // ⚠️ Renamed from 'POSDatabase' — the old DB had a broken migration
    // (primary key rename from idompotency_key → idempotency_key).
    // Dexie cannot change a PK in-place, so we start fresh with a new name.
    // The old 'POSDatabase' is left dormant in the browser; it causes no harm.
    super('RetailPOS_DB')
    this.version(1).stores({
      pendingSales: 'idempotency_key, created_at',
      products:     'slug, name, barcode_id',
      customers:    'customer_id, fullname, phone',
      salesCache:   'sale_id, date',
      debtors:      'debtor_id',
    })
  }
}

export const db = new POSDatabase()

