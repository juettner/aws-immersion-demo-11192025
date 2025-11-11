import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface PredictionData {
  artist_name: string;
  venue_name: string;
  event_date: string;
  predicted_sales: number;
  confidence: number;
  actual_sales?: number;
}

interface TicketSalesPredictionChartProps {
  data: PredictionData[];
  loading?: boolean;
}

const TicketSalesPredictionChart: React.FC<TicketSalesPredictionChartProps> = ({
  data,
  loading,
}) => {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <p>Loading prediction data...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <p>No prediction data available</p>
      </div>
    );
  }

  const chartData = data.map((prediction, index) => ({
    index: index + 1,
    event: `${prediction.artist_name} @ ${prediction.venue_name}`,
    predicted: prediction.predicted_sales,
    actual: prediction.actual_sales || null,
    confidence: (prediction.confidence * 100).toFixed(0),
    date: prediction.event_date,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="index" label={{ value: 'Event', position: 'insideBottom', offset: -5 }} />
        <YAxis label={{ value: 'Ticket Sales', angle: -90, position: 'insideLeft' }} />
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
                    maxWidth: '300px',
                  }}
                >
                  <p style={{ margin: 0, fontWeight: 'bold', fontSize: '0.9rem' }}>
                    {data.event}
                  </p>
                  <p style={{ margin: '5px 0', fontSize: '0.85rem' }}>Date: {data.date}</p>
                  <p style={{ margin: '5px 0', color: '#8884d8' }}>
                    Predicted: {Number(data.predicted).toLocaleString()} tickets
                  </p>
                  {data.actual && (
                    <p style={{ margin: '5px 0', color: '#82ca9d' }}>
                      Actual: {Number(data.actual).toLocaleString()} tickets
                    </p>
                  )}
                  <p style={{ margin: '5px 0', color: '#ffc658' }}>
                    Confidence: {data.confidence}%
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="predicted"
          name="Predicted Sales"
          stroke="#8884d8"
          strokeWidth={2}
          dot={{ r: 4 }}
        />
        {chartData.some((d) => d.actual) && (
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Sales"
            stroke="#82ca9d"
            strokeWidth={2}
            dot={{ r: 4 }}
          />
        )}
        <ReferenceLine y={0} stroke="#666" />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default TicketSalesPredictionChart;
