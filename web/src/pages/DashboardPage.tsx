import React, { useState } from 'react';
import {
  VenuePopularityChart,
  TicketSalesPredictionChart,
  ArtistPopularityChart,
  RecommendationDisplay,
  Loading,
} from '../components';
import {
  useVenuePopularity,
  useTopArtists,
  useRecommendations,
  useRefreshAnalytics,
  useBatchPredictions,
} from '../hooks/useAnalytics';
import './DashboardPage.css';

type DashboardView = 'overview' | 'venues' | 'artists' | 'predictions';

interface DateRange {
  startDate: string;
  endDate: string;
}

const DashboardPage: React.FC = () => {
  const [activeView, setActiveView] = useState<DashboardView>('overview');
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: '',
    endDate: '',
  });

  // Fetch analytics data
  const {
    data: venueData,
    isLoading: venueLoading,
    error: venueError,
  } = useVenuePopularity({ top_n: 10, min_events: 5 });

  const {
    data: artistData,
    isLoading: artistLoading,
    error: artistError,
  } = useTopArtists(10);

  const {
    data: recommendationData,
    isLoading: recommendationLoading,
    error: recommendationError,
  } = useRecommendations({ top_n: 10 });

  // Sample predictions for dashboard
  const samplePredictions = [
    { artist_id: 'artist_1', venue_id: 'venue_1', event_date: '2025-12-01' },
    { artist_id: 'artist_2', venue_id: 'venue_2', event_date: '2025-12-15' },
    { artist_id: 'artist_3', venue_id: 'venue_3', event_date: '2026-01-10' },
  ];

  const {
    data: predictionData,
    isLoading: predictionLoading,
    error: predictionError,
  } = useBatchPredictions(samplePredictions);

  const refreshAnalytics = useRefreshAnalytics();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshAnalytics();
    } catch (error) {
      console.error('Failed to refresh analytics:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleDateChange = (field: keyof DateRange, value: string) => {
    setDateRange(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <div className="dashboard-controls">
          <button
            className={`refresh-button ${isRefreshing ? 'refreshing' : ''}`}
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <span className={`refresh-icon ${isRefreshing ? 'spinning' : ''}`}>
              ↻
            </span>
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      <nav className="dashboard-nav">
        <button
          className={`nav-tab ${activeView === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveView('overview')}
        >
          Overview
        </button>
        <button
          className={`nav-tab ${activeView === 'venues' ? 'active' : ''}`}
          onClick={() => setActiveView('venues')}
        >
          Venues
        </button>
        <button
          className={`nav-tab ${activeView === 'artists' ? 'active' : ''}`}
          onClick={() => setActiveView('artists')}
        >
          Artists
        </button>
        <button
          className={`nav-tab ${activeView === 'predictions' ? 'active' : ''}`}
          onClick={() => setActiveView('predictions')}
        >
          Predictions
        </button>
      </nav>

      <div className="filter-panel">
        <div className="filter-group">
          <label htmlFor="start-date">Start Date</label>
          <input
            id="start-date"
            type="date"
            value={dateRange.startDate}
            onChange={(e) => handleDateChange('startDate', e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label htmlFor="end-date">End Date</label>
          <input
            id="end-date"
            type="date"
            value={dateRange.endDate}
            onChange={(e) => handleDateChange('endDate', e.target.value)}
          />
        </div>
      </div>

      <div className="dashboard-content">
        {activeView === 'overview' && (
          <>
            <div className="dashboard-widget">
              <div className="widget-header">
                <h2>Venue Popularity</h2>
                {venueError && (
                  <span className="widget-info" style={{ color: 'red' }}>
                    Error loading data
                  </span>
                )}
              </div>
              <div className="widget-content">
                {venueLoading ? (
                  <Loading />
                ) : (
                  <VenuePopularityChart
                    data={venueData?.venues || []}
                    loading={venueLoading}
                  />
                )}
              </div>
            </div>
            <div className="dashboard-widget">
              <div className="widget-header">
                <h2>Ticket Sales Predictions</h2>
                {predictionError && (
                  <span className="widget-info" style={{ color: 'red' }}>
                    Error loading data
                  </span>
                )}
              </div>
              <div className="widget-content">
                {predictionLoading ? (
                  <Loading />
                ) : (
                  <TicketSalesPredictionChart
                    data={predictionData || []}
                    loading={predictionLoading}
                  />
                )}
              </div>
            </div>
            <div className="dashboard-widget">
              <div className="widget-header">
                <h2>Artist Popularity</h2>
                {artistError && (
                  <span className="widget-info" style={{ color: 'red' }}>
                    Error loading data
                  </span>
                )}
              </div>
              <div className="widget-content">
                {artistLoading ? (
                  <Loading />
                ) : (
                  <ArtistPopularityChart data={artistData || []} loading={artistLoading} />
                )}
              </div>
            </div>
            <div className="dashboard-widget">
              <div className="widget-header">
                <h2>Recommendations</h2>
                {recommendationError && (
                  <span className="widget-info" style={{ color: 'red' }}>
                    Error loading data
                  </span>
                )}
              </div>
              <div className="widget-content">
                {recommendationLoading ? (
                  <Loading />
                ) : (
                  <RecommendationDisplay
                    recommendations={recommendationData?.recommendations || []}
                    loading={recommendationLoading}
                  />
                )}
              </div>
            </div>
          </>
        )}

        {activeView === 'venues' && (
          <div className="dashboard-widget">
            <div className="widget-header">
              <h2>Venue Analytics</h2>
              {venueError && (
                <span className="widget-info" style={{ color: 'red' }}>
                  Error loading data
                </span>
              )}
            </div>
            <div className="widget-content">
              {venueLoading ? (
                <Loading />
              ) : (
                <VenuePopularityChart data={venueData?.venues || []} loading={venueLoading} />
              )}
            </div>
          </div>
        )}

        {activeView === 'artists' && (
          <div className="dashboard-widget">
            <div className="widget-header">
              <h2>Artist Analytics</h2>
              {artistError && (
                <span className="widget-info" style={{ color: 'red' }}>
                  Error loading data
                </span>
              )}
            </div>
            <div className="widget-content">
              {artistLoading ? (
                <Loading />
              ) : (
                <ArtistPopularityChart data={artistData || []} loading={artistLoading} />
              )}
            </div>
          </div>
        )}

        {activeView === 'predictions' && (
          <div className="dashboard-widget">
            <div className="widget-header">
              <h2>Prediction Analytics</h2>
              {predictionError && (
                <span className="widget-info" style={{ color: 'red' }}>
                  Error loading data
                </span>
              )}
            </div>
            <div className="widget-content">
              {predictionLoading ? (
                <Loading />
              ) : (
                <TicketSalesPredictionChart
                  data={predictionData || []}
                  loading={predictionLoading}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
