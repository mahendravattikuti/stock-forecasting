/**
 * MetricCard Component
 * Displays a key performance metric with icon, label, and value
 */

import React from 'react';
import { TOKENS } from '../../theme/tokens';

export default function MetricCard({
  icon: Icon,
  label,
  value,
  unit = '',
  color = 'primary',
  trend = null, // 'up', 'down', or null
  trendValue = null, // percentage or value to display
  loading = false,
  onClick = null,
  tooltip = null,
}) {
  const colorMap = {
    primary: 'bg-blue-600 text-blue-50',
    success: 'bg-green-600 text-green-50',
    warning: 'bg-amber-600 text-amber-50',
    danger: 'bg-red-600 text-red-50',
    purple: 'bg-purple-600 text-purple-50',
  };

  const trendColorMap = {
    up: 'text-green-500',
    down: 'text-red-500',
  };

  return (
    <div
      className={`
        bg-slate-800 border border-slate-700 rounded-lg p-6
        hover:border-slate-600 transition-all duration-200
        ${onClick ? 'cursor-pointer hover:shadow-md' : ''}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
      title={tooltip}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          {/* Label */}
          <p className="text-slate-400 text-sm font-medium">{label}</p>

          {/* Value */}
          {loading ? (
            <div className="mt-2 h-8 bg-slate-700 rounded animate-pulse" />
          ) : (
            <div className="flex items-baseline gap-2 mt-2">
              <p className="text-3xl font-bold text-white">{value}</p>
              {unit && <p className="text-slate-400 text-sm font-medium">{unit}</p>}
            </div>
          )}

          {/* Trend Indicator */}
          {trend && trendValue !== null && !loading && (
            <div className={`flex items-center gap-1 mt-2 ${trendColorMap[trend]}`}>
              <span className="text-sm font-medium">
                {trend === 'up' ? '↑' : '↓'} {trendValue}
              </span>
            </div>
          )}
        </div>

        {/* Icon */}
        {!loading && Icon && (
          <div className={`p-3 rounded-lg ${colorMap[color]}`}>
            <Icon size={24} />
          </div>
        )}
      </div>
    </div>
  );
}

// ==================== VARIANTS ====================

/**
 * MetricGrid Component
 * Layout multiple metric cards in a responsive grid
 */
export function MetricGrid({ metrics, loading = false, columns = 4 }) {
  const colClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={`grid ${colClass[columns]} gap-4`}>
      {metrics.map((metric, idx) => (
        <MetricCard key={idx} {...metric} loading={loading} />
      ))}
    </div>
  );
}
