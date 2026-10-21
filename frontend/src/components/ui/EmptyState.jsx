/**
 * EmptyState Component
 * Display when no data is available
 */

import React from 'react';
import { Database, Search, TrendingUp } from 'lucide-react';

export default function EmptyState({
  title = 'No data available',
  description = 'There is no data to display right now.',
  icon: Icon = Database,
  action = null, // { label: 'string', onClick: function }
  size = 'md',
}) {
  const sizeMap = {
    sm: {
      container: 'py-6',
      icon: 32,
      title: 'text-lg',
      description: 'text-sm',
    },
    md: {
      container: 'py-12',
      icon: 48,
      title: 'text-2xl',
      description: 'text-base',
    },
    lg: {
      container: 'py-20',
      icon: 64,
      title: 'text-3xl',
      description: 'text-lg',
    },
  };

  const sizing = sizeMap[size];

  return (
    <div className={`${sizing.container} flex flex-col items-center justify-center gap-4 text-center`}>
      {/* Icon */}
      <div className="p-4 bg-slate-700 rounded-full text-slate-400">
        <Icon size={sizing.icon} />
      </div>

      {/* Title */}
      <h3 className={`${sizing.title} font-semibold text-white`}>{title}</h3>

      {/* Description */}
      <p className={`${sizing.description} text-slate-400 max-w-md`}>{description}</p>

      {/* Action Button */}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

// ==================== VARIANTS ====================

/**
 * NoResultsState Component
 * For search/filter results
 */
export function NoResultsState({ query = '', onReset = null }) {
  return (
    <EmptyState
      title="No results found"
      description={query ? `No results for "${query}". Try a different search term.` : 'Try adjusting your filters or search.'}
      icon={Search}
      action={onReset ? { label: 'Reset search', onClick: onReset } : null}
      size="md"
    />
  );
}

/**
 * NoPredictionsState Component
 * For prediction history
 */
export function NoPredictionsState({ onStart = null }) {
  return (
    <EmptyState
      title="No predictions yet"
      description="Make your first stock prediction to get started."
      icon={TrendingUp}
      action={onStart ? { label: 'Make a prediction', onClick: onStart } : null}
      size="md"
    />
  );
}

/**
 * NoDataState Component
 * Generic no data state
 */
export function NoDataState({ message = 'No data available', action = null }) {
  return (
    <EmptyState
      title="No data"
      description={message}
      icon={Database}
      action={action}
      size="md"
    />
  );
}
