export default defineNuxtRouteMiddleware(async (to) => {
  const { adminUser, isLoaded, fetchMe } = useAdminAuth()

  if (!isLoaded.value) {
    await fetchMe()
  }

  const isAuthRoute = to.path === '/login' || to.path === '/forgot-password' || to.path === '/reset-password'

  if (!adminUser.value && !isAuthRoute) {
    return navigateTo('/login')
  }

  if (adminUser.value && isAuthRoute) {
    return navigateTo('/')
  }
})
