/**
 * StatusBadge Component
 * Displays status with icon and color coding
 */

import React from 'react';
import { CheckCircle2, AlertCircle, Clock, Loader } from 'lucide-react';

export default function StatusBadge({
  status, // 'success', 'error', 'warning', 'pending', 'loading'
  label = '',
  size = 'md',
  animated = true,
}) {
  const sizeMap = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };

  const iconSizeMap = {
    sm: 16,
    md: 16,
    lg: 20,
  };

  const statusConfig = {
    success: {
      bg: 'bg-green-100 dark:bg-green-950',
      text: 'text-green-800 dark:text-green-200',
      icon: CheckCircle2,
      color: '#22c55e',
      ariaLabel: 'Status: Success',
    },
    error: {
      bg: 'bg-red-100 dark:bg-red-950',
      text: 'text-red-800 dark:text-red-200',
      icon: AlertCircle,
      color: '#ef4444',
      ariaLabel: 'Status: Error',
    },
    warning: {
      bg: 'bg-amber-100 dark:bg-amber-950',
      text: 'text-amber-800 dark:text-amber-200',
      icon: AlertCircle,
      color: '#f59e0b',
      ariaLabel: 'Status: Warning',
    },
    pending: {
      bg: 'bg-slate-100 dark:bg-slate-800',
      text: 'text-slate-800 dark:text-slate-200',
      icon: Clock,
      color: '#64748b',
      ariaLabel: 'Status: Pending',
    },
    loading: {
      bg: 'bg-blue-100 dark:bg-blue-950',
      text: 'text-blue-800 dark:text-blue-200',
      icon: Loader,
      color: '#3b82f6',
      ariaLabel: 'Status: Loading',
    },
  };

  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;
  const displayLabel = label || status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <div
      className={`
        ${sizeMap[size]}
        ${config.bg} ${config.text}
        rounded-full inline-flex items-center gap-1.5 font-medium
        transition-all duration-200
      `}
      role="status"
      aria-label={`${config.ariaLabel}${label ? ': ' + label : ''}`}
      aria-busy={status === 'loading'}
    >
      <Icon
        size={iconSizeMap[size]}
        className={animated && status === 'loading' ? 'animate-spin' : ''}
        aria-hidden="true"
      />
      <span>{displayLabel}</span>
    </div>
  );
}

// ==================== VARIANTS ====================

/**
 * StatusDot Component
 * Simple colored dot for status indication
 */
export function StatusDot({ status, size = 'md', animated = false }) {
  const sizeMap = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };

  const colorMap = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    warning: 'bg-amber-500',
    pending: 'bg-slate-500',
    loading: 'bg-blue-500',
  };

  const color = colorMap[status] || colorMap.pending;

  return (
    <div
      className={`
        ${sizeMap[size]}
        ${color}
        rounded-full
        ${animated ? 'animate-pulse' : ''}
      `}
      title={status}
    />
  );
}

/**
 * StatusIndicator Component
 * Dot with label and optional tooltip
 */
export function StatusIndicator({ status, label = '', tooltip = '' }) {
  return (
    <div className="flex items-center gap-2" title={tooltip}>
      <StatusDot status={status} size="sm" animated={status === 'loading'} />
      <span className="text-sm text-slate-300">{label || status}</span>
    </div>
  );
}

/**
 * FinancialStatusBadge Component
 * Status badge for trading signals (BUY, SELL, HOLD)
 */
export function FinancialStatusBadge({ signal, confidence = null }) {
  const signalConfig = {
    BUY: {
      bg: 'bg-green-100 dark:bg-green-950',
      text: 'text-green-800 dark:text-green-200',
      emoji: '🟢',
      label: 'BUY',
    },
    SELL: {
      bg: 'bg-red-100 dark:bg-red-950',
      text: 'text-red-800 dark:text-red-200',
      emoji: '🔴',
      label: 'SELL',
    },
    HOLD: {
      bg: 'bg-amber-100 dark:bg-amber-950',
      text: 'text-amber-800 dark:text-amber-200',
      emoji: '🟡',
      label: 'HOLD',
    },
  };

  const config = signalConfig[signal] || signalConfig.HOLD;

  return (
    <div
      className={`
        ${config.bg} ${config.text}
        px-4 py-2 rounded-lg font-semibold text-sm inline-flex items-center gap-2
      `}
    >
      <span>{config.emoji}</span>
      <span>{config.label}</span>
      {confidence && (
        <span className="ml-2 text-xs opacity-75">
          ({(confidence * 100).toFixed(0)}%)
        </span>
      )}
    </div>
  );
}
