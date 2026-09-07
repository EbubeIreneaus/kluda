// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  ssr: true,

  modules: [
    "@nuxt/eslint",
    "@nuxt/ui",
    "@vueuse/nuxt",
    "@pinia/nuxt",
    "nuxt-echarts",
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
      htmlAttrs: {
        lang: "en",
      },
      title: "Kluda — Free Stock Keeping App & Barcode Scanner for Stores",
      meta: [
        {
          name: "description",
          content:
            "Free stock keeping app and phone camera barcode scanner. Track daily store sales, manage customer debt ledgers, and prevent cashier theft with zero expensive hardware.",
        },
        {
          name: "keywords",
          content:
            "stock keeping app, free app to take stock, free barcode scanning app, free app to track my store sales, retail POS app, store sales tracker, supermarket POS, store inventory tracking",
        },
        { property: "og:site_name", content: "Kluda" },
        { property: "og:type", content: "website" },
        { property: "og:title", content: "Kluda — Free Stock Keeping App & Barcode Scanner for Stores" },
        {
          property: "og:description",
          content:
            "Free stock keeping app and phone camera barcode scanner. Track daily store sales, eliminate cash theft, and take stock with zero expensive hardware.",
        },
        { property: "og:image", content: "https://kluda.app/kluda_icon.jpg" },
        { name: "twitter:card", content: "summary_large_image" },
        { name: "twitter:title", content: "Kluda — Free Stock Keeping App & Barcode Scanner for Stores" },
        {
          name: "twitter:description",
          content:
            "Free stock keeping app and phone camera barcode scanner. Track daily store sales, eliminate cash theft, and take stock with zero expensive hardware.",
        },
        { name: "twitter:image", content: "https://kluda.app/kluda_icon.jpg" },
      ],
      link: [
        { rel: "icon", type: "image/x-icon", href: "/kluda-icons/favicon.ico" },
        {
          rel: "apple-touch-icon",
          type: "image/png",
          href: "/kluda-icons/apple-touch-icon.png",
        },
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        {
          rel: "preconnect",
          href: "https://fonts.gstatic.com",
          crossorigin: "",
        },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap",
        },
      ],
      script: [
        {
          innerHTML: `
            var Tawk_API=Tawk_API||{}, Tawk_LoadStart=new Date();
            (function(){
            var s1=document.createElement("script"),s0=document.getElementsByTagName("script")[0];
            s1.async=true;
            s1.src='https://embed.tawk.to/6a998c98d862ed3449e54d36/1k1jsqdgb';
            s1.charset='UTF-8';
            s1.setAttribute('crossorigin','*');
            s0.parentNode.insertBefore(s1,s0);
            })();
          `,
          type: "text/javascript",
        },
      ],
    },
  },

  css: ["~/assets/css/main.css"],

  runtimeConfig: {
    public: {
      apiBase:
        process.env.NUXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
      posAppUrl: process.env.NUXT_PUBLIC_POS_URL || "http://localhost:3000",
    },
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
});
