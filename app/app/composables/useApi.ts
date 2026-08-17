let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

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
        fetchUrl.includes("/staff/auth/login");

      if (statusCode === 401 && !isRefreshOrAuthUrl) {
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = (async () => {
            try {
              const res = await $fetch<{
                success: boolean;
                staff?: any;
                access_token?: string;
                store_id?: string;
              }>(`${config.public.apiBase}/staff/auth/refresh-token`, {
                method: "POST",
                credentials: "include",
              });
              if (res && res.success && res.staff) {
                auth.setAuth(
                  res.access_token || auth.token || "",
                  res.staff,
                  (res.store_id || auth.store_id) as string
                );
                return true;
              }
              return false;
            } catch {
              return false;
            } finally {
              isRefreshing = false;
              refreshPromise = null;
            }
          })();
        }

        const refreshed = await refreshPromise;
        if (refreshed) {
          return await $fetch<T>(fetchUrl, {
            ...requestOptions,
            headers: {
              ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
              ...(options.headers as Record<string, string>),
            },
          });
        } else {
          await auth.logout(true);
        }
      } else if (statusCode === 403) {
        await auth.logout(true);
      }
      throw error;
    }
  }

  return { api };
};
