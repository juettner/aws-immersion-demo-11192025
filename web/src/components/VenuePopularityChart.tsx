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

interface VenueData {
  venue_id: string;
  name: string;
  popularity_rank: number;
  avg_attendance_rate: number;
  revenue_per_event: number;
  booking_frequency: number;
}

interface VenuePopularityChartProps {
  data: VenueData[];
  loading?: boolean;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#8dd1e1', '#d084d0', '#a4de6c'];

const VenuePopularityChart: React.FC<VenuePopularityChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <p>Loading venue data...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <p>No venue data available</p>
      </div>
    );
  }

  const chartData = data.map((venue) => ({
    name: venue.name.length > 20 ? venue.name.substring(0, 20) + '...' : venue.name,
    fullName: venue.name,
    attendanceRate: (venue.avg_attendance_rate * 100).toFixed(1),
    revenue: venue.revenue_per_event,
    bookings: venue.booking_frequency,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
        <YAxis />
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
                  <p style={{ margin: '5px 0', color: '#8884d8' }}>
                    Attendance Rate: {data.attendanceRate}%
                  </p>
                  <p style={{ margin: '5px 0', color: '#82ca9d' }}>
                    Revenue: ${Number(data.revenue).toLocaleString()}
                  </p>
                  <p style={{ margin: '5px 0', color: '#ffc658' }}>
                    Bookings: {data.bookings}
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Legend />
        <Bar dataKey="attendanceRate" name="Attendance Rate (%)" fill="#8884d8">
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default VenuePopularityChart;
