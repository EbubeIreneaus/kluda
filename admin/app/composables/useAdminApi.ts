export function useAdminApi() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  async function apiFetch<T>(endpoint: string, options: Parameters<typeof $fetch>[1] = {}): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
    const fullUrl = `${apiBase}${cleanEndpoint}`

    return $fetch<T>(fullUrl, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...options.headers
      },
      ...options
    })
  }

  return {
    apiFetch,
    apiBase
  }
}
