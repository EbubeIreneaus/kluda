export interface ProductItem {
  slug: string;
  name: string;
  barcode_id: string;
  price: number;
  cost_price: number;
  quantity: number;
  unit: string;
  status: 'active' | 'inactive';
  description: string;
}

export const UNIT_OPTIONS = [
  { label: 'Piece (pcs)', value: 'piece' },
  { label: 'Sachet', value: 'sachet' },
  { label: 'Pack', value: 'pack' },
  { label: 'Carton', value: 'carton' },
  { label: 'Kilogram (kg)', value: 'kg' },
  { label: 'Gram (g)', value: 'g' },
  { label: 'Litre (L)', value: 'litre' },
  { label: 'Millilitre (ml)', value: 'ml' },
  { label: 'Dozen', value: 'dozen' },
  { label: 'Bag', value: 'bag' },
] as const;

export const REASON_OPTIONS = [
  { value: 'restock', label: 'Restock / New Shipment' },
  { value: 'return', label: 'Customer Return' },
  { value: 'damage', label: 'Damaged / Expired' },
  { value: 'adjustment', label: 'Stock Audit / Adjustment' },
] as const;

export function getStockBadge(qty: number) {
  if (qty <= 0) return { label: 'Out of stock', color: 'error' as const };
  if (qty <= 10) return { label: 'Low stock', color: 'warning' as const };
  return { label: 'In stock', color: 'success' as const };
}
