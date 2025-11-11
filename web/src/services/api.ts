import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios';
import config from '../config/env';

// Create axios instance with default config
const createApiClient = (baseURL: string): AxiosInstance => {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Handle unauthorized access
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return client;
};

// API clients
export const apiClient = createApiClient(config.apiBaseUrl);
export const chatbotClient = createApiClient(config.chatbotApiUrl);
export const analyticsClient = createApiClient(config.analyticsApiUrl);

// Generic API request wrapper
export async function apiRequest<T>(
  client: AxiosInstance,
  config: AxiosRequestConfig
): Promise<T> {
  try {
    const response: AxiosResponse<T> = await client.request(config);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message);
    }
    throw error;
  }
}

export default apiClient;
