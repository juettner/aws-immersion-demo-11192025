// Environment configuration
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api',
  chatbotApiUrl: import.meta.env.VITE_CHATBOT_API_URL || 'http://localhost:3000/api/chat',
  analyticsApiUrl:
    import.meta.env.VITE_ANALYTICS_API_URL || 'http://localhost:3000/api/analytics',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const;

export default config;
