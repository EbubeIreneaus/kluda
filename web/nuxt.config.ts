// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  ssr: false,

  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@vueuse/nuxt',
    '@pinia/nuxt',
    'nuxt-echarts'
  ],

  devtools: {
    enabled: true
  },

  colorMode: {
    preference: 'system',
    fallback: 'light',
    classSuffix: ''
  },

  app: {
    head: {
      title: 'RetailPOS — The Offline-First Multi-Store POS Platform',
      meta: [
        { name: 'description', content: 'Turn any smartphone, tablet, or laptop into a fast, offline-ready retail POS with instant camera barcode scanning, customer ledgers, and real-time multi-register mesh.' }
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap' }
      ]
    }
  },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
      posAppUrl: process.env.NUXT_PUBLIC_POS_URL || 'http://localhost:3000'
    }
  },

  routeRules: {
    '/**': { ssr: false }
  },

  compatibilityDate: '2026-06-30',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})