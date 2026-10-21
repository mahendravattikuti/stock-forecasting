import React, { useState, useEffect, useRef } from 'react';
import { Download, Copy, Trash2, Pause, Play } from 'lucide-react';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { Card, LoadingSpinner } from './ui';

/**
 * LogViewer Component
 * 
 * Displays real-time execution logs from the pipeline.
 * Features auto-scroll, filtering, export, and search capabilities.
 * 
 * @component
 * @param {boolean} props.isRunning - Whether pipeline is currently running
 * @returns {React.ReactNode} Log viewer interface
 */
export function LogViewer({ isRunning = false }) {
  const [logs, setLogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const [logFilter, setLogFilter] = useState('all'); // 'all', 'info', 'error', 'success'
  const logsEndRef = useRef(null);
  const logsContainerRef = useRef(null);

  // Fetch logs from API
  const { data: fetchedLogs, loading, refetch } = useFetch(
    () => api.getExecutionLogs(100),
    { cache: false }
  );

  // Update logs when fetched
  useEffect(() => {
    if (fetchedLogs && fetchedLogs.logs) {
      // Parse logs from API response
      const parsedLogs = fetchedLogs.logs.map((log) => {
        // Determine log level from message
        let level = 'info';
        if (
          log.includes('error') ||
          log.includes('Error') ||
          log.includes('ERROR')
        ) {
          level = 'error';
        } else if (
          log.includes('success') ||
          log.includes('✓') ||
          log.includes('completed')
        ) {
          level = 'success';
        } else if (
          log.includes('warning') ||
          log.includes('Warning')
        ) {
          level = 'warning';
        }

        return {
          id: Math.random(),
          message: log,
          level,
          timestamp: new Date().toLocaleTimeString(),
        };
      });
      setLogs(parsedLogs);
    }
  }, [fetchedLogs]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (isAutoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isAutoScroll]);

  // Auto-refresh logs while running
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      refetch();
    }, 2000); // Refresh every 2 seconds

    return () => clearInterval(interval);
  }, [isRunning, refetch]);

  // Filter logs
  const filteredLogs = logs.filter((log) => {
    const matchesFilter =
      logFilter === 'all' || log.level === logFilter;
    const matchesSearch =
      log.message.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  // Get log colors
  const getLogColor = (level) => {
    switch (level) {
      case 'error':
        return 'text-red-600 dark:text-red-400';
      case 'success':
        return 'text-green-600 dark:text-green-400';
      case 'warning':
        return 'text-amber-600 dark:text-amber-400';
      default:
        return 'text-slate-600 dark:text-slate-400';
    }
  };

  const getLevelBadge = (level) => {
    const badges = {
      error: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
      success: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
      warning: 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200',
      info: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
    };
    return badges[level] || badges.info;
  };

  // Export logs as text
  const exportLogs = () => {
    const text = filteredLogs
      .map((log) => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`)
      .join('\n');

    const blob = new Blob([text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pipeline_logs_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  // Copy logs to clipboard
  const copyToClipboard = () => {
    const text = filteredLogs
      .map((log) => `[${log.timestamp}] ${log.message}`)
      .join('\n');

    navigator.clipboard.writeText(text).then(() => {
      alert('Logs copied to clipboard!');
    });
  };

  return (
    <Card>
      <Card.Header
        title="Execution Logs"
        subtitle={`${filteredLogs.length} / ${logs.length} logs`}
        action={
          <div className="flex gap-2">
            <button
              onClick={() => setIsAutoScroll(!isAutoScroll)}
              className={`p-2 rounded transition-colors ${
                isAutoScroll
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400'
                  : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400'
              }`}
              title={isAutoScroll ? 'Disable auto-scroll' : 'Enable auto-scroll'}
            >
              {isAutoScroll ? <Pause size={18} /> : <Play size={18} />}
            </button>
            <button
              onClick={copyToClipboard}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors text-slate-600 dark:text-slate-400"
              title="Copy logs to clipboard"
            >
              <Copy size={18} />
            </button>
            <button
              onClick={exportLogs}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors text-slate-600 dark:text-slate-400"
              title="Export logs as file"
            >
              <Download size={18} />
            </button>
            <button
              onClick={() => setLogs([])}
              className="p-2 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors text-red-600 dark:text-red-400"
              title="Clear logs"
            >
              <Trash2 size={18} />
            </button>
          </div>
        }
      />
      <Card.Body>
        {/* Search and Filter */}
        <div className="mb-4 flex gap-3 flex-wrap">
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 min-w-[200px] px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 transition-all"
          />
          <select
            value={logFilter}
            onChange={(e) => setLogFilter(e.target.value)}
            className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 transition-all"
          >
            <option value="all">All Levels</option>
            <option value="info">Info</option>
            <option value="success">Success</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>

        {/* Loading State */}
        {loading && logs.length === 0 && (
          <LoadingSpinner message="Loading logs..." size="sm" />
        )}

        {/* Logs Display */}
        <div
          ref={logsContainerRef}
          className="bg-slate-900 dark:bg-black rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm space-y-1 border border-slate-300 dark:border-slate-700"
        >
          {filteredLogs.length === 0 ? (
            <p className="text-slate-500">
              {logs.length === 0
                ? 'No logs yet. Run the pipeline to see logs here.'
                : 'No logs match the current filter.'}
            </p>
          ) : (
            <>
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex gap-3 items-start hover:bg-slate-800 dark:hover:bg-slate-800 px-2 py-1 rounded transition-colors"
                >
                  <span className="text-slate-600 dark:text-slate-500 flex-shrink-0">
                    {log.timestamp}
                  </span>
                  <span
                    className={`${getLevelBadge(log.level)} px-2 py-0.5 rounded text-xs font-semibold flex-shrink-0`}
                  >
                    {log.level.toUpperCase()}
                  </span>
                  <span className={`${getLogColor(log.level)} flex-1`}>
                    {log.message}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </>
          )}
        </div>

        {/* Log Stats */}
        <div className="mt-4 grid grid-cols-4 gap-2 text-xs">
          <div className="bg-blue-100 dark:bg-blue-900 p-2 rounded">
            <p className="text-blue-800 dark:text-blue-200 font-semibold">
              {logs.filter((l) => l.level === 'info').length}
            </p>
            <p className="text-blue-700 dark:text-blue-300">Info</p>
          </div>
          <div className="bg-green-100 dark:bg-green-900 p-2 rounded">
            <p className="text-green-800 dark:text-green-200 font-semibold">
              {logs.filter((l) => l.level === 'success').length}
            </p>
            <p className="text-green-700 dark:text-green-300">Success</p>
          </div>
          <div className="bg-amber-100 dark:bg-amber-900 p-2 rounded">
            <p className="text-amber-800 dark:text-amber-200 font-semibold">
              {logs.filter((l) => l.level === 'warning').length}
            </p>
            <p className="text-amber-700 dark:text-amber-300">Warning</p>
          </div>
          <div className="bg-red-100 dark:bg-red-900 p-2 rounded">
            <p className="text-red-800 dark:text-red-200 font-semibold">
              {logs.filter((l) => l.level === 'error').length}
            </p>
            <p className="text-red-700 dark:text-red-300">Error</p>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
}

export default LogViewer;
