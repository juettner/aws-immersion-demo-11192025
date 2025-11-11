import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface ArtistData {
  artist_id: string;
  name: string;
  genre: string;
  popularity_score: number;
  total_concerts?: number;
  avg_ticket_sales?: number;
}

interface ArtistPopularityChartProps {
  data: ArtistData[];
  loading?: boolean;
}

const COLORS = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7', '#a29bfe', '#fd79a8'];

const ArtistPopularityChart: React.FC<ArtistPopularityChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <p>Loading artist data...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <p>No artist data available</p>
      </div>
    );
  }

  const chartData = data
    .sort((a, b) => b.popularity_score - a.popularity_score)
    .slice(0, 10)
    .map((artist) => ({
      name: artist.name.length > 20 ? artist.name.substring(0, 20) + '...' : artist.name,
      fullName: artist.name,
      popularity: artist.popularity_score,
      genre: artist.genre,
      concerts: artist.total_concerts || 0,
      avgSales: artist.avg_ticket_sales || 0,
    }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" domain={[0, 100]} />
        <YAxis type="category" dataKey="name" width={90} />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div
                  style={{
                    backgroundColor: 'white',
                    padding: '10px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                  }}
                >
                  <p style={{ margin: 0, fontWeight: 'bold' }}>{data.fullName}</p>
                  <p style={{ margin: '5px 0', fontSize: '0.85rem' }}>Genre: {data.genre}</p>
                  <p style={{ margin: '5px 0', color: '#ff6b6b' }}>
                    Popularity: {data.popularity.toFixed(1)}
                  </p>
                  {data.concerts > 0 && (
                    <p style={{ margin: '5px 0', fontSize: '0.85rem' }}>
                      Total Concerts: {data.concerts}
                    </p>
                  )}
                  {data.avgSales > 0 && (
                    <p style={{ margin: '5px 0', fontSize: '0.85rem' }}>
                      Avg Sales: {Number(data.avgSales).toLocaleString()}
                    </p>
                  )}
                </div>
              );
            }
            return null;
          }}
        />
        <Legend />
        <Bar dataKey="popularity" name="Popularity Score" fill="#ff6b6b">
          {chartData.map((_entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default ArtistPopularityChart;
