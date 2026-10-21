/**
 * ErrorAlert Component
 * Displays error messages with recovery options
 */

import React from 'react';
import { AlertCircle, X } from 'lucide-react';

export default function ErrorAlert({
  title = 'Error',
  message,
  onClose = null,
  onRetry = null,
  variant = 'danger', // 'danger', 'warning', 'info'
}) {
  const variantStyles = {
    danger: {
      container: 'bg-red-50 border border-red-300',
      icon: 'text-red-600',
      title: 'text-red-900',
      message: 'text-red-800',
      button: 'text-red-700 hover:text-red-900 hover:bg-red-100',
    },
    warning: {
      container: 'bg-amber-50 border border-amber-300',
      icon: 'text-amber-600',
      title: 'text-amber-900',
      message: 'text-amber-800',
      button: 'text-amber-700 hover:text-amber-900 hover:bg-amber-100',
    },
    info: {
      container: 'bg-blue-50 border border-blue-300',
      icon: 'text-blue-600',
      title: 'text-blue-900',
      message: 'text-blue-800',
      button: 'text-blue-700 hover:text-blue-900 hover:bg-blue-100',
    },
  };

  const style = variantStyles[variant];

  return (
    <div className={`${style.container} rounded-lg p-4 flex gap-3`}>
      {/* Icon */}
      <div className="flex-shrink-0">
        <AlertCircle className={`w-5 h-5 ${style.icon}`} />
      </div>

      {/* Content */}
      <div className="flex-1">
        <h3 className={`font-semibold text-sm ${style.title}`}>{title}</h3>
        {message && <p className={`mt-1 text-sm ${style.message}`}>{message}</p>}
      </div>

      {/* Actions */}
      <div className="flex-shrink-0 flex gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className={`px-3 py-1 text-sm font-medium rounded transition-colors ${style.button}`}
          >
            Retry
          </button>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className={`p-1 rounded transition-colors ${style.button}`}
            aria-label="Close error"
          >
            <X size={18} />
          </button>
        )}
      </div>
    </div>
  );
}

// ==================== VARIANTS ====================

/**
 * DarkErrorAlert Component
 * Error alert styled for dark backgrounds (like our dashboard)
 */
export function DarkErrorAlert({
  title = 'Error',
  message,
  onClose = null,
  onRetry = null,
  icon: Icon = AlertCircle,
}) {
  return (
    <div className="bg-red-950 border border-red-700 rounded-lg p-4 flex gap-3">
      {/* Icon */}
      <div className="flex-shrink-0">
        <Icon className="w-5 h-5 text-red-400" />
      </div>

      {/* Content */}
      <div className="flex-1">
        <h3 className="font-semibold text-sm text-red-200">{title}</h3>
        {message && <p className="mt-1 text-sm text-red-300">{message}</p>}
      </div>

      {/* Actions */}
      <div className="flex-shrink-0 flex gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-3 py-1 text-sm font-medium text-red-200 hover:text-red-100 hover:bg-red-900 rounded transition-colors"
          >
            Retry
          </button>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 text-red-200 hover:text-red-100 hover:bg-red-900 rounded transition-colors"
            aria-label="Close error"
          >
            <X size={18} />
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * InlineError Component
 * Error message for inline display (in forms, etc.)
 */
export function InlineError({ message, icon: Icon = AlertCircle }) {
  if (!message) return null;

  return (
    <div className="flex items-center gap-2 text-red-500 text-sm">
      {Icon && <Icon size={16} />}
      <span>{message}</span>
    </div>
  );
}
