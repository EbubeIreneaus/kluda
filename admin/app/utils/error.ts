/**
 * Extracts a human-readable error message from API/Fetch errors.
 * Handles FastAPI 422 validation error arrays, standard error responses, and fallbacks.
 * Prevents "[object Object]" from ever appearing in dialogs or toasts.
 */
export function getErrorMessage(err: any, fallback = 'An unexpected error occurred'): string {
  if (!err) return fallback

  const detail = err?.data?.detail ?? err?.response?._data?.detail ?? err?.detail

  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim()
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item: any) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const field = Array.isArray(item.loc) && item.loc.length > 0 ? item.loc[item.loc.length - 1] : ''
          const msg = item.msg || item.message || JSON.stringify(item)
          return field && field !== 'body' ? `${field}: ${msg}` : msg
        }
        return String(item)
      })
      .filter(Boolean)
      .join(', ')
  }

  if (detail && typeof detail === 'object') {
    if (typeof detail.message === 'string' && detail.message.trim()) return detail.message.trim()
    if (typeof detail.msg === 'string' && detail.msg.trim()) return detail.msg.trim()
  }

  if (typeof err?.data?.message === 'string' && err.data.message.trim()) {
    return err.data.message.trim()
  }

  if (typeof err?.message === 'string' && err.message.trim()) {
    return err.message.trim()
  }

  return fallback
}
