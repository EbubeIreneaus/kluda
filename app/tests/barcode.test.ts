import { describe, it, expect } from 'vitest'

interface MockProduct {
  slug: string
  name: string
  barcode_id: string
}

function findProductByBarcode(products: MockProduct[], barcode: string): MockProduct | undefined {
  if (!barcode) return undefined
  const clean = barcode.trim().toLowerCase()
  return products.find(p => p.barcode_id && p.barcode_id.trim().toLowerCase() === clean)
}

describe('Barcode Matching Logic', () => {
  const inventory: MockProduct[] = [
    { slug: 'coca-cola-50cl', name: 'Coca Cola 50cl', barcode_id: '5449000000996' },
    { slug: 'golden-morn-500g', name: 'Golden Morn 500g', barcode_id: 'GM-500-NG' },
    { slug: 'no-barcode-item', name: 'Local Bread', barcode_id: '' }
  ]

  it('matches exact barcode strings', () => {
    const found = findProductByBarcode(inventory, '5449000000996')
    expect(found).toBeDefined()
    expect(found?.name).toBe('Coca Cola 50cl')
  })

  it('matches barcode with leading/trailing whitespace and differing case', () => {
    const found = findProductByBarcode(inventory, '  gm-500-ng  ')
    expect(found).toBeDefined()
    expect(found?.slug).toBe('golden-morn-500g')
  })

  it('returns undefined for non-existent barcodes or empty input', () => {
    expect(findProductByBarcode(inventory, '9999999999999')).toBeUndefined()
    expect(findProductByBarcode(inventory, '')).toBeUndefined()
    expect(findProductByBarcode(inventory, '   ')).toBeUndefined()
  })
})
