export default defineNuxtPlugin(() => {
  if (typeof window === 'undefined') return

  try {
    const urlParams = new URLSearchParams(window.location.search)

    // 1. Preserve referral code across browser and standalone PWA
    const ref = urlParams.get('ref') || urlParams.get('refcode') || urlParams.get('referral_code')
    if (ref) {
      localStorage.setItem('kluda_saved_ref', ref.trim())
      document.cookie = `kluda_saved_ref=${encodeURIComponent(ref.trim())}; path=/; max-age=2592000; SameSite=Lax`
    }

    // 2. Preserve selected subscription plan
    const plan = urlParams.get('plan')
    if (plan) {
      localStorage.setItem('kluda_saved_plan', plan.trim())
      document.cookie = `kluda_saved_plan=${encodeURIComponent(plan.trim())}; path=/; max-age=2592000; SameSite=Lax`
    }

    // 3. Preserve trial intent flag
    const trial = urlParams.get('trial')
    if (trial !== null) {
      localStorage.setItem('kluda_saved_trial', trial.trim())
      document.cookie = `kluda_saved_trial=${encodeURIComponent(trial.trim())}; path=/; max-age=2592000; SameSite=Lax`
    }

    // 4. Preserve general query map in case of redirection in middleware
    const allQueries: Record<string, string> = {}
    urlParams.forEach((val, key) => {
      allQueries[key] = val
    })
    if (Object.keys(allQueries).length > 0) {
      const existing = JSON.parse(localStorage.getItem('kluda_saved_queries') || '{}')
      const merged = { ...existing, ...allQueries }
      localStorage.setItem('kluda_saved_queries', JSON.stringify(merged))
      document.cookie = `kluda_saved_queries=${encodeURIComponent(JSON.stringify(merged))}; path=/; max-age=2592000; SameSite=Lax`
    }
  } catch (err) {
    console.warn('Could not persist onboarding query params:', err)
  }
})
