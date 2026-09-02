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
        fetchUrl.includes("/auth/refresh-token") ||
        fetchUrl.includes("/auth/login") ||
        fetchUrl.includes("/auth/logout") ||
        fetchUrl.includes("/staff/auth/");

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
