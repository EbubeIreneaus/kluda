export function useOnboardingParams() {
  const route = useRoute()

  function getCookie(name: string): string {
    if (typeof document === 'undefined') return ''
    const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'))
    return match && match[3] ? decodeURIComponent(match[3]) : ''
  }

  function getSavedReferralCode(): string {
    const fromRoute = (route.query.ref || route.query.refcode || route.query.referral_code) as string
    if (fromRoute) return fromRoute.trim()

    if (typeof window !== 'undefined') {
      const fromLocal = localStorage.getItem('kluda_saved_ref')
      if (fromLocal) return fromLocal.trim()
      const fromCookie = getCookie('kluda_saved_ref')
      if (fromCookie) return fromCookie.trim()
    }
    return ''
  }

  function getSavedPlan(): string {
    const fromRoute = route.query.plan as string
    if (fromRoute) return fromRoute.trim().toLowerCase()

    if (typeof window !== 'undefined') {
      const fromLocal = localStorage.getItem('kluda_saved_plan')
      if (fromLocal) return fromLocal.trim().toLowerCase()
      const fromCookie = getCookie('kluda_saved_plan')
      if (fromCookie) return fromCookie.trim().toLowerCase()
    }
    return ''
  }

  function getSavedTrial(): boolean {
    const fromRoute = route.query.trial as string
    if (fromRoute !== undefined) return fromRoute === 'true' || fromRoute === '1'

    if (typeof window !== 'undefined') {
      const fromLocal = localStorage.getItem('kluda_saved_trial')
      if (fromLocal !== null) return fromLocal === 'true' || fromLocal === '1'
      const fromCookie = getCookie('kluda_saved_trial')
      if (fromCookie) return fromCookie === 'true' || fromCookie === '1'
    }
    return false
  }

  function clearSavedOnboardingParams(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem('kluda_saved_ref')
    localStorage.removeItem('kluda_saved_plan')
    localStorage.removeItem('kluda_saved_trial')
    localStorage.removeItem('kluda_saved_queries')
    document.cookie = 'kluda_saved_ref=; path=/; max-age=0'
    document.cookie = 'kluda_saved_plan=; path=/; max-age=0'
    document.cookie = 'kluda_saved_trial=; path=/; max-age=0'
    document.cookie = 'kluda_saved_queries=; path=/; max-age=0'
  }

  return {
    getSavedReferralCode,
    getSavedPlan,
    getSavedTrial,
    clearSavedOnboardingParams
  }
}
