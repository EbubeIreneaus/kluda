/**
 * Format kobo/cent integer to currency string
 * e.g. 150000 → ₦1,500.00
 */
export function useFormatCurrency() {
  const format = (amountInKobo: number, currency = '₦'): string => {
    const naira = amountInKobo / 100
    return `${currency}${naira.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatCompact = (amountInKobo: number, currency = '₦'): string => {
    const naira = amountInKobo / 100
    if (naira >= 1_000_000) return `${currency}${(naira / 1_000_000).toFixed(1)}M`
    if (naira >= 1_000) return `${currency}${(naira / 1_000).toFixed(1)}K`
    return `${currency}${naira.toFixed(0)}`
  }

  return { format, formatCompact }
}
