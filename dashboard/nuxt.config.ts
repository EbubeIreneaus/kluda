export default defineNuxtConfig({
  ssr: false,

  modules: [
    "@nuxt/eslint",
    "@nuxt/ui",
    "@vueuse/nuxt",
    "nuxt-qrcode",
    "@pinia/nuxt",
    "@vite-pwa/nuxt",
  ],

  devtools: {
    enabled: true,
  },

  app: {
    head: {
      link: [
        { rel: "icon", type: "image/x-icon", href: "/favicon.svg" }
      ]
    }
  },

  css: ["~/assets/css/main.css"],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_URL || "http://localhost:8000",
    },
  },

  routeRules: {
    "/": { redirect: "/dashboard" },
    "/dashboard/**": { ssr: false },
  },

  compatibilityDate: "2026-06-30",

  eslint: {
    config: {
      stylistic: {
        commaDangle: "never",
        braceStyle: "1tbs",
      },
    },
  },

  devServer: {
    host: "0.0.0.0",
  },

  vite: {
    server: {
      allowedHosts: true,
    },
  },
  pwa: {
    registerType: "prompt",
    includeAssets: ["favicon.svg", "splash.png", "robots.txt"],
    manifest: {
      name: "Retail POS System",
      short_name: "Retail POS",
      display: "standalone",
      start_url: "/",
      description: "Point of Sale system for Retail Businesses",
      theme_color: "#1e293b",
      background_color: "#0f172a",
      icons: [
        {
          src: "/pwa-64x64.png",
          sizes: "64x64",
          type: "image/png",
        },
        {
          src: "/pwa-192x192.png",
          sizes: "192x192",
          type: "image/png",
        },
        {
          src: "/pwa-512x512.png",
          sizes: "512x512",
          type: "image/png",
          purpose: "any maskable",
        },
      ],
    },
    workbox: {
      navigateFallback: "/",
      navigateFallbackDenylist: [/^\/api/],
      globPatterns: ["**/*.{js,css,html,png,svg,ico,woff,woff2}"],
      cleanupOutdatedCaches: true,
      skipWaiting: false,
      clientsClaim: false,
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/,
          handler: "CacheFirst",
          options: {
            cacheName: "fonts-cache",
            expiration: {
              maxEntries: 5,
              maxAgeSeconds: 60 * 60 * 24 * 365,
            },
          },
        }
      ],
    },
    devOptions: {
      enabled: true,
    },
  },
});