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

  constructor() {
    super('RetailPOS_DB')
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

export const db = new POSDatabase()

