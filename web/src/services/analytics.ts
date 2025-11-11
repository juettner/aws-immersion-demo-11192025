import { analyticsClient, apiRequest } from './api';

// Types
export interface VenuePopularity {
  venue_id: string;
  name: string;
  popularity_rank: number;
  avg_attendance_rate: number;
  revenue_per_event: number;
  booking_frequency: number;
}

export interface TicketSalesPrediction {
  artist_name: string;
  venue_name: string;
  event_date: string;
  predicted_sales: number;
  confidence: number;
  actual_sales?: number;
}

export interface ArtistPopularity {
  artist_id: string;
  name: string;
  genre: string;
  popularity_score: number;
  total_concerts?: number;
  avg_ticket_sales?: number;
}

export interface Recommendation {
  concert_id?: string;
  artist_id?: string;
  artist_name: string;
  venue_name: string;
  event_date?: string;
  score: number;
  reason?: string;
  ticket_price?: number;
}

export interface VenuePopularityRequest {
  top_n?: number;
  min_events?: number;
}

export interface VenuePopularityResponse {
  venues: VenuePopularity[];
  total_venues: number;
  timestamp: string;
}

export interface TicketSalesPredictionRequest {
  artist_id: string;
  venue_id: string;
  event_date?: string;
  ticket_price?: number;
}

export interface TicketSalesPredictionResponse {
  predicted_sales: number;
  confidence: number;
  features_used: Record<string, unknown>;
  timestamp: string;
}

export interface RecommendationRequest {
  user_id?: string;
  artist_preferences?: string[];
  location?: string;
  top_n?: number;
}

export interface RecommendationResponse {
  recommendations: Recommendation[];
  total_recommendations: number;
  recommendation_type: string;
  timestamp: string;
}

interface VenueDetails {
  venue_id: string;
  name: string;
  city: string;
  state: string;
  capacity: number;
  venue_type: string;
}

interface ArtistDetails {
  artist_id: string;
  name: string;
  genre: string;
  popularity_score: number;
}

// Analytics Service
class AnalyticsService {
  /**
   * Get venue popularity rankings
   */
  async getVenuePopularity(
    params: VenuePopularityRequest = {}
  ): Promise<VenuePopularityResponse> {
    return apiRequest<VenuePopularityResponse>(analyticsClient, {
      method: 'POST',
      url: '/ml/venues/popularity',
      data: {
        top_n: params.top_n || 10,
        min_events: params.min_events || 5,
      },
    });
  }

  /**
   * Predict ticket sales for a concert
   */
  async predictTicketSales(
    params: TicketSalesPredictionRequest
  ): Promise<TicketSalesPredictionResponse> {
    return apiRequest<TicketSalesPredictionResponse>(analyticsClient, {
      method: 'POST',
      url: '/ml/tickets/predict',
      data: params,
    });
  }

  /**
   * Get concert recommendations
   */
  async getRecommendations(
    params: RecommendationRequest = {}
  ): Promise<RecommendationResponse> {
    return apiRequest<RecommendationResponse>(analyticsClient, {
      method: 'POST',
      url: '/ml/recommendations',
      data: {
        user_id: params.user_id,
        artist_preferences: params.artist_preferences,
        location: params.location,
        top_n: params.top_n || 10,
      },
    });
  }

  /**
   * Get venue details by ID
   */
  async getVenueDetails(venueId: string): Promise<VenueDetails> {
    return apiRequest<VenueDetails>(analyticsClient, {
      method: 'GET',
      url: `/ml/venues/${venueId}`,
    });
  }

  /**
   * Get artist details by ID
   */
  async getArtistDetails(artistId: string): Promise<ArtistDetails> {
    return apiRequest<ArtistDetails>(analyticsClient, {
      method: 'GET',
      url: `/ml/artists/${artistId}`,
    });
  }

  /**
   * Get top artists by popularity
   */
  async getTopArtists(limit: number = 10): Promise<ArtistPopularity[]> {
    // This would typically call a backend endpoint
    // For now, we'll return mock data structure
    return apiRequest<ArtistPopularity[]>(analyticsClient, {
      method: 'GET',
      url: `/ml/artists/top?limit=${limit}`,
    });
  }

  /**
   * Get multiple predictions for dashboard
   */
  async getBatchPredictions(
    predictions: TicketSalesPredictionRequest[]
  ): Promise<TicketSalesPrediction[]> {
    const results = await Promise.all(
      predictions.map(async (pred) => {
        try {
          const response = await this.predictTicketSales(pred);
          return {
            artist_name: pred.artist_id, // Would be resolved from backend
            venue_name: pred.venue_id, // Would be resolved from backend
            event_date: pred.event_date || new Date().toISOString(),
            predicted_sales: response.predicted_sales,
            confidence: response.confidence,
          };
        } catch (error) {
          console.error('Prediction failed:', error);
          return null;
        }
      })
    );

    return results.filter((r): r is TicketSalesPrediction => r !== null);
  }

  /**
   * Check ML services health
   */
  async checkHealth(): Promise<Record<string, string>> {
    return apiRequest<Record<string, string>>(analyticsClient, {
      method: 'GET',
      url: '/ml/health',
    });
  }
}

export const analyticsService = new AnalyticsService();
export default analyticsService;
