/**
 * LoadingSpinner Component
 * Shows loading state with spinner animation
 */

import React from 'react';

export default function LoadingSpinner({
  size = 'md',
  text = 'Loading...',
  fullPage = false,
}) {
  const sizeMap = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };

  const textSizeMap = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center gap-3">
      {/* Spinner Animation */}
      <div className={`${sizeMap[size]} relative`}>
        <div
          className="absolute inset-0 rounded-full border-2 border-slate-700"
          aria-hidden="true"
        />
        <div
          className="absolute inset-0 rounded-full border-2 border-transparent border-t-blue-500 animate-spin"
          aria-hidden="true"
        />
      </div>

      {/* Loading Text */}
      {text && (
        <p className={`${textSizeMap[size]} text-slate-400 font-medium`}>
          {text}
        </p>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
        {spinner}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center p-8">
      {spinner}
    </div>
  );
}

// ==================== VARIANTS ====================

/**
 * InlineLoading Component
 * Compact loading indicator for inline use
 */
export function InlineLoading({ size = 'sm' }) {
  const sizeMap = {
    sm: 'w-4 h-4 border border-slate-600 border-t-blue-500',
    md: 'w-5 h-5 border-2 border-slate-600 border-t-blue-500',
  };

  return (
    <div
      className={`${sizeMap[size]} rounded-full animate-spin inline-block`}
      aria-label="Loading"
    />
  );
}

/**
 * Skeleton Loading Component
 * Shows placeholder while loading
 */
export function Skeleton({ className = '', children }) {
  return (
    <div className={`bg-slate-700 animate-pulse rounded ${className}`}>
      {children}
    </div>
  );
}
