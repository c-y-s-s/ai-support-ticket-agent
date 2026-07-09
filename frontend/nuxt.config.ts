export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: false },
  css: ['~/assets/main.css'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000'
    }
  },
  app: {
    head: {
      title: 'SupportFlow AI',
      meta: [
        {
          name: 'description',
          content: 'AI-assisted support ticket workflow with human approval.'
        }
      ]
    }
  },
  typescript: {
    typeCheck: true,
    strict: true
  }
})
