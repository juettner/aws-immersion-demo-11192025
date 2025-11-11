import { useQuery, useMutation, type UseQueryOptions, type UseMutationOptions } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { apiRequest } from '../services/api';

// Custom hook for GET requests
export function useApiQuery<T>(
  queryKey: string[],
  client: AxiosInstance,
  url: string,
  options?: Omit<UseQueryOptions<T, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<T, Error>({
    queryKey,
    queryFn: () => apiRequest<T>(client, { method: 'GET', url }),
    ...options,
  });
}

// Custom hook for POST/PUT/DELETE requests
export function useApiMutation<TData, TVariables>(
  client: AxiosInstance,
  method: 'POST' | 'PUT' | 'DELETE',
  url: string,
  options?: UseMutationOptions<TData, Error, TVariables>
) {
  return useMutation<TData, Error, TVariables>({
    mutationFn: (variables) =>
      apiRequest<TData>(client, {
        method,
        url,
        data: variables,
      }),
    ...options,
  });
}
