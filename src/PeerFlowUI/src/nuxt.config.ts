// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  ssr: false,

  runtimeConfig: {
    public: {
      authApiUrl: "http://192.168.72.52:30010",
      peerflowApiUrl: "http://192.168.72.52:30060",
      fileStorageUrl: "http://192.168.72.52:30031",
    }
  },

  typescript: {
    shim: false
  },

  build: {
    transpile: ["vuetify"],
  },

  vite: {
    define: {
      "process.env.DEBUG": false,
    },
    server: {
      watch: {
        usePolling: true,
        interval: 1000,
      },
    }
  },

  nitro: {
    serveStatic: true,
  },

  devServerHandlers: [],

  hooks: {
  },

  compatibilityDate: "2025-04-15",
  modules: ["@pinia/nuxt"],
})