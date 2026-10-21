import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * FinancialChart Component
 * 
 * Displays historical vs predicted prices side-by-side on a line chart.
 * Features confidence levels and custom tooltips.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Array<Object>} props.data - Chart data array
 * @param {string} props.data[].date - Date of the data point
 * @param {number} props.data[].historical - Historical/actual price
 * @param {number} props.data[].predicted - Model predicted price
 * @param {number} [props.data[].confidence] - Prediction confidence (0-1)
 * @param {number} [props.height] - Chart height in pixels (default 400)
 * @returns {React.ReactNode} Responsive financial chart
 */
export function FinancialChart({ data = [], height = 400 }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-500">
        <p>No data available</p>
      </div>
    );
  }

  /**
   * Custom Tooltip Component
   * Displays formatted price and confidence information on hover
   */
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;

    const data = payload[0]?.payload;

    return (
      <div className="bg-white dark:bg-slate-800 p-3 rounded shadow-lg border border-slate-200 dark:border-slate-700">
        <p className="font-semibold text-slate-900 dark:text-white">{data.date}</p>
        {data.historical !== undefined && (
          <p className="text-cyan-600 dark:text-cyan-400 text-sm">
            Historical: ${data.historical.toFixed(2)}
          </p>
        )}
        {data.predicted !== undefined && (
          <p className="text-amber-600 dark:text-amber-400 text-sm">
            Predicted: ${data.predicted.toFixed(2)}
          </p>
        )}
        {data.confidence !== undefined && (
          <p className="text-green-600 dark:text-green-400 text-sm">
            Confidence: {(data.confidence * 100).toFixed(1)}%
          </p>
        )}
        {data.historical !== undefined && data.predicted !== undefined && (
          <p className="text-slate-600 dark:text-slate-400 text-sm">
            Error: ${Math.abs(data.historical - data.predicted).toFixed(2)}
          </p>
        )}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={data}
        margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#e5e7eb"
          className="dark:stroke-slate-700"
        />
        <XAxis
          dataKey="date"
          stroke="#6b7280"
          className="dark:stroke-slate-500"
          style={{ fontSize: '0.875rem' }}
        />
        <YAxis
          stroke="#6b7280"
          className="dark:stroke-slate-500"
          style={{ fontSize: '0.875rem' }}
          label={{ value: 'Price ($)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ paddingTop: '1rem' }}
          iconType="line"
        />

        {/* Historical/Actual Price Line */}
        <Line
          type="monotone"
          dataKey="historical"
          stroke="#06b6d4"
          name="Historical Price"
          strokeWidth={2.5}
          dot={false}
          isAnimationActive={true}
          animationDuration={500}
        />

        {/* Predicted Price Line */}
        <Line
          type="monotone"
          dataKey="predicted"
          stroke="#f59e0b"
          name="Predicted Price"
          strokeWidth={2.5}
          strokeDasharray="5 5"
          dot={false}
          isAnimationActive={true}
          animationDuration={500}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default FinancialChart;
