export default defineNuxtConfig({
  ssr: false,

  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@vueuse/nuxt',
    'nuxt-qrcode',
    '@pinia/nuxt'
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000'
    }
  },

  routeRules: {
    '/': { redirect: '/dashboard' },
    '/dashboard/**': { ssr: false }
  },

  compatibilityDate: '2026-06-30',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },

  devServer: {
    host: '0.0.0.0'
  },

  vite: {
    server: {
      allowedHosts: true
    }
  }
})