/**
 * Kluda ESC/POS Thermal Receipt Binary Builder
 * Compatible with standard 58mm and 80mm thermal receipt printers.
 */

export interface ReceiptItem {
  name: string
  quantity: number
  unit_price: number
  total: number
}

export interface ReceiptData {
  storeName: string
  storeAddress?: string
  storePhone?: string
  receiptNumber: string
  date: string
  cashierName?: string
  customerName?: string
  paymentMethod: string
  items: ReceiptItem[]
  subtotal: number
  discount?: number
  tax?: number
  total: number
  footerNote?: string
}

export function sanitizeAscii(str: string): string {
  if (!str) return ''
  return str
    .replace(/₦/g, 'NGN ')
    .replace(/[‘’‚‛]/g, "'")
    .replace(/[“”„‟]/g, '"')
    .replace(/[–—―]/g, '-')
    .replace(/…/g, '...')
    .replace(/[•·]/g, '*')
    .normalize('NFKD')
    .replace(/[^\x00-\x7F]/g, '')
}

export class EscPosBuilder {
  private buffer: number[] = []
  private encoder = new TextEncoder()
  public lineWidth: number // 32 chars for 58mm, 48 chars for 80mm

  constructor(paperWidth: '58mm' | '80mm' = '58mm') {
    this.lineWidth = paperWidth === '80mm' ? 48 : 32
    this.init()
  }

  /** Reset and initialize printer */
  init(): this {
    this.buffer.push(0x1b, 0x40)
    return this
  }

  /** Align text: 0 = Left, 1 = Center, 2 = Right */
  align(alignment: 'left' | 'center' | 'right'): this {
    const val = alignment === 'center' ? 1 : alignment === 'right' ? 2 : 0
    this.buffer.push(0x1b, 0x61, val)
    return this
  }

  /** Toggle bold font */
  bold(enable = true): this {
    this.buffer.push(0x1b, 0x45, enable ? 1 : 0)
    return this
  }

  /** Character size scaling */
  size(mode: 'normal' | 'double-height' | 'double-width' | 'large'): this {
    let val = 0x00
    if (mode === 'double-height') val = 0x01
    else if (mode === 'double-width') val = 0x10
    else if (mode === 'large') val = 0x11
    this.buffer.push(0x1d, 0x21, val)
    return this
  }

  /** Feed lines */
  feed(lines = 1): this {
    for (let i = 0; i < lines; i++) {
      this.buffer.push(0x0a)
    }
    return this
  }

  /** Feed paper and cut (partial cut) */
  cut(): this {
    this.feed(3)
    this.buffer.push(0x1d, 0x56, 0x41, 0x03)
    return this
  }

  /** Write raw text, ensuring ASCII safe characters for thermal hardware */
  text(str: string): this {
    const sanitized = sanitizeAscii(str)
    const bytes = this.encoder.encode(sanitized)
    for (let i = 0; i < bytes.length; i++) {
      this.buffer.push(bytes[i])
    }
    return this
  }

  /** Write text and append a line break */
  line(str = ''): this {
    this.text(str)
    this.buffer.push(0x0a)
    return this
  }

  /** Write a horizontal divider line */
  divider(char = '-'): this {
    this.line(char.repeat(this.lineWidth))
    return this
  }

  /**
   * Print a two-column row with left and right alignment.
   * e.g. "Subtotal"                  "NGN 5,000"
   */
  row(left: string, right: string): this {
    const cleanLeft = sanitizeAscii(left)
    const cleanRight = sanitizeAscii(right)
    const totalLen = cleanLeft.length + cleanRight.length

    if (totalLen <= this.lineWidth) {
      const spaces = ' '.repeat(this.lineWidth - totalLen)
      this.line(cleanLeft + spaces + cleanRight)
    } else {
      // If left text is too wide, print left on its own line and right indented
      this.line(cleanLeft)
      const spaces = ' '.repeat(Math.max(0, this.lineWidth - cleanRight.length))
      this.line(spaces + cleanRight)
    }
    return this
  }

  /**
   * Print a three-column item row.
   * Item Name (truncated or line-wrapped)
   * Qty x Price                  Total
   */
  itemRow(name: string, qty: number, unitPrice: number, total: number): this {
    const totalStr = `NGN ${total.toLocaleString()}`
    const qtyPriceStr = `${qty} x ${unitPrice.toLocaleString()}`

    // Print item name first if it takes too much space
    if (name.length > this.lineWidth - 14) {
      this.line(name)
      this.row(`  ${qtyPriceStr}`, totalStr)
    } else {
      this.row(`${name} (${qty})`, totalStr)
    }
    return this
  }

  /** Return the raw Uint8Array byte buffer ready for Bluetooth/USB transmission */
  build(): Uint8Array {
    return new Uint8Array(this.buffer)
  }
}

/**
 * Generate a complete, formatted receipt byte buffer from ReceiptData.
 */
export function buildReceiptPayload(data: ReceiptData, paperWidth: '58mm' | '80mm' = '58mm'): Uint8Array {
  const p = new EscPosBuilder(paperWidth)

  // 1. Header (Centered, Bold, Double Size for Store Name)
  p.align('center')
  p.size('large')
  p.bold(true)
  p.line(data.storeName || 'KLUDA RETAIL')
  p.size('normal')
  p.bold(false)

  if (data.storeAddress) {
    p.line(data.storeAddress)
  }
  if (data.storePhone) {
    p.line(`Tel: ${data.storePhone}`)
  }

  p.feed(1)
  p.divider('=')

  // 2. Receipt Info
  p.align('left')
  p.row('Receipt #:', data.receiptNumber || 'REC-' + Date.now().toString().slice(-6))
  p.row('Date:', data.date || new Date().toLocaleString())
  if (data.cashierName) {
    p.row('Cashier:', data.cashierName)
  }
  if (data.customerName) {
    p.row('Customer:', data.customerName)
  }

  p.divider('-')

  // 3. Line Items
  p.bold(true)
  p.row('ITEM (QTY)', 'AMOUNT')
  p.bold(false)
  p.divider('-')

  for (const item of data.items) {
    p.itemRow(item.name, item.quantity, item.unit_price, item.total)
  }

  p.divider('-')

  // 4. Financial Totals
  p.row('Subtotal:', `NGN ${data.subtotal.toLocaleString()}`)
  if (data.discount && data.discount > 0) {
    p.row('Discount:', `-NGN ${data.discount.toLocaleString()}`)
  }
  if (data.tax && data.tax > 0) {
    p.row('VAT / Tax:', `NGN ${data.tax.toLocaleString()}`)
  }

  p.divider('=')
  p.size('double-height')
  p.bold(true)
  p.row('TOTAL:', `NGN ${data.total.toLocaleString()}`)
  p.size('normal')
  p.bold(false)
  p.divider('=')

  // 5. Payment Details
  p.row('Payment Method:', (data.paymentMethod || 'Cash').toUpperCase())
  p.row('Status:', 'PAID')

  p.feed(1)

  // 6. Footer
  p.align('center')
  p.line(data.footerNote || 'Thank you for your business!')
  p.line('Powered by Kluda POS')

  // 7. Cut paper
  p.cut()

  return p.build()
}

/**
 * Generate a diagnostic test print slip to verify printer connection & alignment.
 */
export function buildTestPrintPayload(paperWidth: '58mm' | '80mm' = '58mm'): Uint8Array {
  const p = new EscPosBuilder(paperWidth)

  p.align('center')
  p.size('large')
  p.bold(true)
  p.line('KLUDA POS')
  p.size('normal')
  p.bold(false)
  p.line('Hardware Diagnostics Slip')
  p.line(new Date().toLocaleString())
  p.divider('=')

  p.align('left')
  p.row('Printer Width:', paperWidth)
  p.row('Columns:', `${p.lineWidth} chars/line`)
  p.row('Interface:', 'ESC/POS Direct')
  p.row('Connection:', 'SUCCESSFUL (OK)')
  p.divider('-')

  p.align('center')
  p.bold(true)
  p.line('TEST PRINT VERIFIED')
  p.bold(false)
  p.line('If this slip is readable, your printer is ready for instant checkout printing.')
  p.cut()

  return p.build()
}
