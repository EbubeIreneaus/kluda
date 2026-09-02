export const useApi = () => {
  async function api<T extends Record<string, any>>(
    url: string,
    options: Parameters<typeof $fetch>[1] = {},
  ): Promise<T> {
    const config = useRuntimeConfig();
    const auth = useAuthStore();
    const fetchUrl = url.startsWith("http")
      ? url
      : `${config.public.apiBase}${url}`;

    const requestOptions: Parameters<typeof $fetch>[1] = {
      credentials: "include",
      ...options,
      headers: {
        ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
        ...(options.headers as Record<string, string>),
      },
    };

    try {
      return await $fetch<T>(fetchUrl, requestOptions);
    } catch (error: any) {
      const statusCode =
        error?.response?.status ?? error?.statusCode ?? error?.status;
      const isRefreshOrAuthUrl =
        fetchUrl.includes("/staff/auth/refresh-token") ||
        fetchUrl.includes("/staff/auth/login") ||
        fetchUrl.includes("/staff/auth/logout");

      if (statusCode === 401 && !isRefreshOrAuthUrl) {
        const refreshed = await auth.refreshToken();
        if (refreshed) {
          return await $fetch<T>(fetchUrl, {
            ...requestOptions,
            headers: {
              ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
              ...(options.headers as Record<string, string>),
            },
          });
        }
      }
      throw error;
    }
  }

  return { api };
};
