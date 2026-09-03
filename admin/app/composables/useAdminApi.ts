export function useAdminApi() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  async function apiFetch<T>(endpoint: string, options: Parameters<typeof $fetch>[1] = {}): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
    const fullUrl = `${apiBase}${cleanEndpoint}`

    try {
      return await $fetch<T>(fullUrl, {
        credentials: 'include',
        headers: {
          Accept: 'application/json',
          ...options.headers
        },
        ...options
      })
    } catch (err: any) {
      if (err?.data && err.data.detail !== undefined) {
        err.data.detail = getErrorMessage(err)
      }
      throw err
    }
  }

  return {
    apiFetch,
    apiBase
  }
}
