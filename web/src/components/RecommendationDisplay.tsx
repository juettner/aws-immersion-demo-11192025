import React from 'react';
import './RecommendationDisplay.css';

interface Recommendation {
  concert_id?: string;
  artist_id?: string;
  artist_name: string;
  venue_name: string;
  event_date?: string;
  score: number;
  reason?: string;
  ticket_price?: number;
}

interface RecommendationDisplayProps {
  recommendations: Recommendation[];
  loading?: boolean;
  type?: 'concert' | 'artist' | 'venue';
}

const RecommendationDisplay: React.FC<RecommendationDisplayProps> = ({
  recommendations,
  loading,
}) => {
  if (loading) {
    return (
      <div className="recommendation-loading">
        <p>Loading recommendations...</p>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="recommendation-empty">
        <p>No recommendations available</p>
      </div>
    );
  }

  return (
    <div className="recommendation-display">
      <div className="recommendation-list">
        {recommendations.map((rec, index) => (
          <div key={index} className="recommendation-item">
            <div className="recommendation-rank">#{index + 1}</div>
            <div className="recommendation-content">
              <div className="recommendation-header">
                <h3 className="recommendation-title">{rec.artist_name}</h3>
                <div className="recommendation-score">
                  <span className="score-label">Score:</span>
                  <span className="score-value">{(rec.score * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="recommendation-details">
                <div className="detail-item">
                  <span className="detail-icon">📍</span>
                  <span className="detail-text">{rec.venue_name}</span>
                </div>
                {rec.event_date && (
                  <div className="detail-item">
                    <span className="detail-icon">📅</span>
                    <span className="detail-text">
                      {new Date(rec.event_date).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {rec.ticket_price && (
                  <div className="detail-item">
                    <span className="detail-icon">💵</span>
                    <span className="detail-text">${rec.ticket_price.toFixed(2)}</span>
                  </div>
                )}
              </div>
              {rec.reason && (
                <div className="recommendation-reason">
                  <span className="reason-icon">💡</span>
                  <span className="reason-text">{rec.reason}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecommendationDisplay;
