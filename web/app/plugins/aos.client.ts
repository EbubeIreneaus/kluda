import AOS from 'aos'
import 'aos/dist/aos.css'

export default defineNuxtPlugin((nuxtApp) => {
  if (import.meta.client) {
    nuxtApp.hook('app:mounted', () => {
      AOS.init({
        once: true,
        duration: 600,
        easing: 'ease-out-cubic',
        offset: 40
      })
    })

    const router = useRouter()
    router.afterEach(() => {
      nextTick(() => {
        AOS.refreshHard()
      })
    })
  }
})
