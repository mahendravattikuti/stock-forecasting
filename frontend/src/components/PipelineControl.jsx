import React, { useState, useEffect } from 'react';
import { Play, Square, RefreshCw, Settings } from 'lucide-react';
import { usePipelineStatus } from '../hooks/usePipelineStatus';
import { api } from '../services/api';
import { Card, LoadingSpinner, ErrorAlert, StatusBadge, ConfirmModal } from './ui';
import LogViewer from './LogViewer';
import ConfigurationEditor from './ConfigurationEditor';

/**
 * PipelineControl Component
 * 
 * Main interface for controlling the stock prediction pipeline.
 * Features real-time status monitoring, log streaming, and configuration management.
 * 
 * @component
 * @returns {React.ReactNode} Pipeline control interface
 */
export default function PipelineControl() {
  const [isRunning, setIsRunning] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);
  const [error, setError] = useState(null);

  // Auto-refresh pipeline status every 5 seconds
  const { status: pipelineStatus, loading: statusLoading, error: statusError, refresh } = usePipelineStatus({
    autoRefresh: true,
    refreshInterval: 5000,
    onStatusChange: (oldStatus, newStatus) => {
      if (newStatus === 'idle') setIsRunning(false);
      if (newStatus === 'running') setIsRunning(true);
    },
  });

  // Handle start pipeline with confirmation
  const handleStartPipeline = async () => {
    try {
      setConfirmAction('start');
      setShowConfirm(true);
    } catch (err) {
      setError(err);
    }
  };

  // Confirm start pipeline
  const confirmStartPipeline = async () => {
    try {
      setError(null);
      await api.startPipeline();
      setIsRunning(true);
      await refresh();
      setShowConfirm(false);
    } catch (err) {
      setError(err);
      setShowConfirm(false);
    }
  };

  // Handle stop pipeline with confirmation
  const handleStopPipeline = async () => {
    try {
      setConfirmAction('stop');
      setShowConfirm(true);
    } catch (err) {
      setError(err);
    }
  };

  // Confirm stop pipeline
  const confirmStopPipeline = async () => {
    try {
      setError(null);
      await api.stopPipeline();
      setIsRunning(false);
      await refresh();
      setShowConfirm(false);
    } catch (err) {
      setError(err);
      setShowConfirm(false);
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'loading';
      case 'stopped':
      case 'idle':
        return 'pending';
      case 'error':
        return 'error';
      default:
        return 'pending';
    }
  };

  // Get status display text
  const getStatusText = (status) => {
    switch (status) {
      case 'running':
        return 'Pipeline Running';
      case 'completed':
        return 'Pipeline Completed';
      case 'stopped':
        return 'Pipeline Stopped';
      case 'idle':
        return 'Ready to Run';
      case 'error':
        return 'Pipeline Error';
      default:
        return 'Unknown Status';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Status */}
      <Card>
        <Card.Header
          title="Pipeline Control"
          subtitle="Manage and monitor the stock prediction pipeline"
          action={
            <div className="flex items-center gap-2">
              {statusLoading ? (
                <span className="text-xs text-slate-500">Updating...</span>
              ) : (
                <StatusBadge
                  status={getStatusColor(pipelineStatus?.state || 'idle')}
                  label={getStatusText(pipelineStatus?.state || 'idle')}
                  size="sm"
                />
              )}
            </div>
          }
        />
        <Card.Body>
          {/* Error Alert */}
          {error && (
            <div className="mb-4">
              <ErrorAlert
                title="Pipeline Error"
                message={error.message}
                onRetry={refresh}
              />
            </div>
          )}

          {/* Status Error */}
          {statusError && (
            <div className="mb-4">
              <ErrorAlert
                title="Status Update Failed"
                message={statusError.message}
                onRetry={refresh}
              />
            </div>
          )}

          {/* Control Buttons */}
          <div className="flex gap-3 flex-wrap">
            <button
              onClick={handleStartPipeline}
              disabled={isRunning || statusLoading}
              className="flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Start the prediction pipeline"
            >
              <Play size={18} />
              Start Pipeline
            </button>

            {isRunning && (
              <button
                onClick={handleStopPipeline}
                className="flex items-center gap-2 px-6 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
                title="Stop the running pipeline"
              >
                <Square size={18} />
                Stop Pipeline
              </button>
            )}

            <button
              onClick={refresh}
              disabled={statusLoading}
              className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              title="Refresh pipeline status"
            >
              <RefreshCw size={18} className={statusLoading ? 'animate-spin' : ''} />
              Refresh Status
            </button>

            <button
              onClick={() => setShowConfig(!showConfig)}
              className="flex items-center gap-2 px-6 py-2.5 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
              title="Edit pipeline configuration"
            >
              <Settings size={18} />
              Configuration
            </button>
          </div>

          {/* Status Details */}
          {pipelineStatus && (
            <div className="mt-4 p-4 bg-slate-100 dark:bg-slate-800 rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-slate-600 dark:text-slate-400">State</p>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {pipelineStatus.state || 'unknown'}
                  </p>
                </div>
                <div>
                  <p className="text-slate-600 dark:text-slate-400">Last Updated</p>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {new Date(pipelineStatus.timestamp).toLocaleString()}
                  </p>
                </div>
                {pipelineStatus.progress !== undefined && (
                  <div>
                    <p className="text-slate-600 dark:text-slate-400">Progress</p>
                    <p className="font-semibold text-slate-900 dark:text-white">
                      {(pipelineStatus.progress * 100).toFixed(0)}%
                    </p>
                  </div>
                )}
                {pipelineStatus.duration && (
                  <div>
                    <p className="text-slate-600 dark:text-slate-400">Duration</p>
                    <p className="font-semibold text-slate-900 dark:text-white">
                      {pipelineStatus.duration}s
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Configuration Editor */}
      {showConfig && (
        <ConfigurationEditor onClose={() => setShowConfig(false)} />
      )}

      {/* Log Viewer */}
      <LogViewer isRunning={isRunning} />

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={showConfirm}
        title={
          confirmAction === 'start'
            ? 'Start Pipeline?'
            : 'Stop Pipeline?'
        }
        message={
          confirmAction === 'start'
            ? 'This will start the stock prediction pipeline. This may take several minutes.'
            : 'Are you sure you want to stop the running pipeline? Progress will be lost.'
        }
        confirmText={confirmAction === 'start' ? 'Start' : 'Stop'}
        cancelText="Cancel"
        type={confirmAction === 'start' ? 'warning' : 'danger'}
        onConfirm={
          confirmAction === 'start'
            ? confirmStartPipeline
            : confirmStopPipeline
        }
        onCancel={() => setShowConfirm(false)}
      />
    </div>
  );
}
