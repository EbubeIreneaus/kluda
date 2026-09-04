export default defineNuxtConfig({
  ssr: false,

  modules: [
    "@nuxt/eslint",
    "@nuxt/ui",
    "@vueuse/nuxt",
    "nuxt-qrcode",
    "@pinia/nuxt",
    "@vite-pwa/nuxt"
  ],

  devtools: {
    enabled: true,
  },

  colorMode: {
    preference: "system",
    fallback: "light",
    classSuffix: "",
  },

  app: {
    head: {
      link: [
        {
          rel: "icon",
          type: "image/x-icon",
          href: "/kluda-icons/favicon.ico",
        },
        {
          rel: "apple-touch-icon",
          type: "image/png",
          href: "/kluda-icons/apple-touch-icon.png",
        },
      ],
    },
  },

  css: ["~/assets/css/main.css"],

  runtimeConfig: {
    public: {
      apiBase:
        process.env.NUXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
      webDashboardUrl:
        process.env.NUXT_PUBLIC_WEB_URL || "http://localhost:3001",
    },
  },

  routeRules: {
    "/**": { ssr: false },
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

  vite: {
    server: {
      allowedHosts: true,
    },
  },
  pwa: {
    registerType: "prompt",
    includeAssets: [
      "kluda-icons/favicon-32x32.png",
      "kluda-icons/apple-touch-icon.png",
      "kluda-icons/favicon.ico",
      "kluda-icons/64x64.png",
      "kluda-icons/192x192.png",
      "kluda-icons/512x512.png",
      "robots.txt",
      "custom-sw.js",
    ],
    manifest: {
      name: "Kluda",
      short_name: "Kluda",
      display: "standalone",
      start_url: "/",
      description: "Sell Faster, Track Everything",
      theme_color: "#09090b",
      background_color: "#09090b",
      icons: [
        {
          src: "/kluda-icons/64x64.png",
          sizes: "64x64",
          type: "image/png",
        },
        {
          src: "/kluda-icons/192x192.png",
          sizes: "192x192",
          type: "image/png",
        },
        {
          src: "/kluda-icons/512x512.png",
          sizes: "512x512",
          type: "image/png",
          purpose: "any maskable",
        },
      ],
    },
    devOptions: {
      enabled: true,
      type: "classic",
    },
    workbox: {
      importScripts: ["/custom-sw.js"],
      navigateFallback: "/",
      navigateFallbackDenylist: [/^\/api/],
      globPatterns: ["**/*.{js,css,html,png,svg,ico,woff,woff2}"],
      globIgnores: ["**/200.html", "**/200/**", "**/404.html", "**/404/**"],
      cleanupOutdatedCaches: true,
      skipWaiting: false,
      clientsClaim: false,
      runtimeCaching: [
        {
          urlPattern: /\/_nuxt\/.*/i,
          handler: "CacheFirst",
          options: {
            cacheName: "nuxt-assets-cache",
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 * 24 * 30,
            },
            cacheableResponse: {
              statuses: [0, 200],
            },
          },
        },
        {
          urlPattern: ({ request }) => request.mode === "navigate",
          handler: "NetworkFirst",
          options: {
            cacheName: "pages-cache",
            networkTimeoutSeconds: 3,
            cacheableResponse: {
              statuses: [0, 200],
            },
          },
        },
        {
          urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/,
          handler: "CacheFirst",
          options: {
            cacheName: "fonts-cache",
            expiration: {
              maxEntries: 10,
              maxAgeSeconds: 60 * 60 * 24 * 365,
            },
          },
        },
      ],
    }
  }
});