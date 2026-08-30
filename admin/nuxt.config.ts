import process from 'node:process'

export default defineNuxtConfig({
  ssr: false,

  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@vueuse/nuxt',
    '@vite-pwa/nuxt',
    'nuxt-echarts'
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1',
      domainName: process.env.NUXT_PUBLIC_DOMAIN_NAME || 'localhost:3000'
    }
  },

  pwa: {
    registerType: 'prompt',
    includeAssets: ['favicon.ico', 'favicon.svg', 'apple-touch-icon.png', 'splash.png', 'robots.txt', 'custom-sw.js'],
    manifest: {
      name: 'Kluda Platform Admin',
      short_name: 'Kluda Admin',
      description: 'Kluda Platform Operations & Control Center',
      theme_color: '#09090b',
      background_color: '#09090b',
      display: 'standalone',
      orientation: 'portrait',
      start_url: '/',
      icons: [
        {
          src: '/pwa-64x64.png',
          sizes: '64x64',
          type: 'image/png'
        },
        {
          src: '/pwa-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: '/pwa-512x512.png',
          sizes: '512x512',
          type: 'image/png',
          purpose: 'any maskable'
        }
      ]
    },
    workbox: {
      importScripts: ['/custom-sw.js'],
      navigateFallback: '/',
      navigateFallbackDenylist: [/^\/api/],
      globPatterns: ['**/*.{js,css,html,png,svg,ico,woff,woff2}'],
      cleanupOutdatedCaches: true,
      skipWaiting: false,
      clientsClaim: false,
      runtimeCaching: [
        {
          urlPattern: /\/_nuxt\/.*/i,
          handler: 'CacheFirst',
          options: {
            cacheName: 'admin-nuxt-assets',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 * 24 * 30
            }
          }
        },
        {
          urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/i,
          handler: 'StaleWhileRevalidate',
          options: {
            cacheName: 'admin-images-cache',
            expiration: {
              maxEntries: 60,
              maxAgeSeconds: 60 * 60 * 24 * 30
            }
          }
        }
      ]
    },
    devOptions: {
      enabled: true,
      type: 'classic'
    },
    client: {
      installPrompt: true
    }
  },

  compatibilityDate: '2026-06-30'
})