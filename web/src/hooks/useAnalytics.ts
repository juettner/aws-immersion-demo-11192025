import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import analyticsService from '../services/analytics';
import type {
  VenuePopularityRequest,
  TicketSalesPredictionRequest,
  RecommendationRequest,
} from '../services/analytics';

// Query keys
export const analyticsKeys = {
  all: ['analytics'] as const,
  venuePopularity: (params?: VenuePopularityRequest) =>
    [...analyticsKeys.all, 'venue-popularity', params] as const,
  predictions: (params?: TicketSalesPredictionRequest[]) =>
    [...analyticsKeys.all, 'predictions', params] as const,
  recommendations: (params?: RecommendationRequest) =>
    [...analyticsKeys.all, 'recommendations', params] as const,
  venueDetails: (venueId: string) => [...analyticsKeys.all, 'venue', venueId] as const,
  artistDetails: (artistId: string) => [...analyticsKeys.all, 'artist', artistId] as const,
  topArtists: (limit?: number) => [...analyticsKeys.all, 'top-artists', limit] as const,
  health: () => [...analyticsKeys.all, 'health'] as const,
};

/**
 * Hook to fetch venue popularity rankings
 */
export function useVenuePopularity(params?: VenuePopularityRequest) {
  return useQuery({
    queryKey: analyticsKeys.venuePopularity(params),
    queryFn: () => analyticsService.getVenuePopularity(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

/**
 * Hook to predict ticket sales
 */
export function useTicketSalesPrediction() {
  return useMutation({
    mutationFn: (predictionParams: TicketSalesPredictionRequest) =>
      analyticsService.predictTicketSales(predictionParams),
  });
}

/**
 * Hook to fetch batch predictions
 */
export function useBatchPredictions(predictions?: TicketSalesPredictionRequest[]) {
  return useQuery({
    queryKey: analyticsKeys.predictions(predictions),
    queryFn: () => analyticsService.getBatchPredictions(predictions || []),
    enabled: !!predictions && predictions.length > 0,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Hook to fetch concert recommendations
 */
export function useRecommendations(params?: RecommendationRequest) {
  return useQuery({
    queryKey: analyticsKeys.recommendations(params),
    queryFn: () => analyticsService.getRecommendations(params),
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Hook to fetch venue details
 */
export function useVenueDetails(venueId: string) {
  return useQuery({
    queryKey: analyticsKeys.venueDetails(venueId),
    queryFn: () => analyticsService.getVenueDetails(venueId),
    enabled: !!venueId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to fetch artist details
 */
export function useArtistDetails(artistId: string) {
  return useQuery({
    queryKey: analyticsKeys.artistDetails(artistId),
    queryFn: () => analyticsService.getArtistDetails(artistId),
    enabled: !!artistId,
    staleTime: 10 * 60 * 1000,
  });
}

/**
 * Hook to fetch top artists
 */
export function useTopArtists(limit: number = 10) {
  return useQuery({
    queryKey: analyticsKeys.topArtists(limit),
    queryFn: () => analyticsService.getTopArtists(limit),
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Hook to check ML services health
 */
export function useAnalyticsHealth() {
  return useQuery({
    queryKey: analyticsKeys.health(),
    queryFn: () => analyticsService.checkHealth(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

/**
 * Hook to refresh all analytics data
 */
export function useRefreshAnalytics() {
  const queryClient = useQueryClient();

  return () => {
    return queryClient.invalidateQueries({
      queryKey: analyticsKeys.all,
    });
  };
}
