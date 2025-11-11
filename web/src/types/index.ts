// Core domain types
export interface Artist {
  artist_id: string;
  name: string;
  genre: string[];
  popularity_score: number;
  formation_date?: string;
  members: string[];
  spotify_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Venue {
  venue_id: string;
  name: string;
  location: Location;
  capacity: number;
  venue_type: string;
  amenities: string[];
  ticketmaster_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Location {
  city: string;
  state: string;
  country: string;
  latitude?: number;
  longitude?: number;
}

export interface Concert {
  concert_id: string;
  artist_id: string;
  venue_id: string;
  event_date: string;
  ticket_prices: Record<string, number>;
  total_attendance?: number;
  revenue?: number;
  status: 'scheduled' | 'completed' | 'cancelled';
  created_at: string;
  updated_at: string;
}

export interface TicketSale {
  sale_id: string;
  concert_id: string;
  price_tier: string;
  quantity: number;
  unit_price: number;
  purchase_timestamp: string;
  customer_segment: string;
  created_at: string;
}

// Analytics types
export interface VenuePopularity {
  venue_id: string;
  popularity_rank: number;
  avg_attendance_rate: number;
  revenue_per_event: number;
  booking_frequency: number;
  calculated_at: string;
}

export interface PredictionResult {
  prediction_id: string;
  model_type: string;
  input_features: Record<string, unknown>;
  predicted_value: number;
  confidence_score: number;
  prediction_date: string;
  actual_value?: number;
}

export interface Recommendation {
  id: string;
  type: 'artist' | 'concert' | 'venue';
  item_id: string;
  score: number;
  reason: string;
}

// Chatbot types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  data?: unknown;
  visualization?: string;
}

export interface ChatResponse {
  message: ChatMessage;
  session_id: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
