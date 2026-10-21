import React, { useState, useEffect } from 'react';
import { Trash2, Download, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, FinancialStatusBadge } from './ui';

const STORAGE_KEY = 'stock_predictions_history';
const MAX_HISTORY = 50;

/**
 * PredictionHistory Component
 * 
 * Displays prediction history with localStorage persistence.
 * Allows filtering by symbol and recommendation.
 * Supports CSV export functionality.
 * 
 * @component
 * @param {Array} props.predictions - Real-time predictions to add to history
 * @returns {React.ReactNode} Prediction history display
 */
export function PredictionHistory({ predictions = [] }) {
  const [history, setHistory] = useState([]);
  const [filterSymbol, setFilterSymbol] = useState('');
  const [filteredHistory, setFilteredHistory] = useState([]);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setHistory(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse prediction history:', e);
      }
    }
  }, []);

  // Add new predictions to history
  useEffect(() => {
    if (predictions && predictions.length > 0) {
      setHistory((prev) => {
        const updated = [
          {
            ...predictions,
            id: Date.now(),
            timestamp: new Date().toISOString(),
          },
          ...prev,
        ].slice(0, MAX_HISTORY);

        // Persist to localStorage
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        } catch (e) {
          console.error('Failed to save prediction history:', e);
        }

        return updated;
      });
    }
  }, [predictions]);

  // Filter history
  useEffect(() => {
    let filtered = history;
    if (filterSymbol) {
      filtered = history.filter((p) =>
        p.symbol?.includes(filterSymbol.toUpperCase())
      );
    }
    setFilteredHistory(filtered);
  }, [history, filterSymbol]);

  const clearHistory = () => {
    if (window.confirm('Are you sure you want to clear all prediction history?')) {
      setHistory([]);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const exportAsCSV = () => {
    const headers = [
      'Symbol',
      'Recommendation',
      'Confidence',
      'Current Price',
      'Predicted Price',
      'Change %',
      'Timestamp',
    ];

    const rows = filteredHistory.map((p) => [
      p.symbol,
      p.recommendation,
      (p.confidence * 100).toFixed(1),
      p.current_price?.toFixed(2) || 'N/A',
      p.predicted_price?.toFixed(2) || 'N/A',
      p.predicted_change?.toFixed(2) || 'N/A',
      new Date(p.timestamp).toLocaleString(),
    ]);

    const csv = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `predictions_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const getRecommendationIcon = (rec) => {
    switch (rec) {
      case 'BUY':
        return <TrendingUp size={16} className="text-green-600" />;
      case 'SELL':
        return <TrendingDown size={16} className="text-red-600" />;
      case 'HOLD':
        return <Minus size={16} className="text-amber-600" />;
      default:
        return null;
    }
  };

  const getUniqueSymbols = () => {
    return [...new Set(history.map((p) => p.symbol))].sort();
  };

  if (history.length === 0) {
    return (
      <Card>
        <Card.Header title="Prediction History" />
        <Card.Body>
          <p className="text-slate-600 dark:text-slate-400 text-center py-8">
            No predictions yet. Make a prediction to see history here.
          </p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card>
      <Card.Header
        title="Prediction History"
        subtitle={`${history.length} predictions stored locally`}
        action={
          <div className="flex gap-2">
            <button
              onClick={exportAsCSV}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors text-slate-600 dark:text-slate-400"
              title="Export as CSV"
            >
              <Download size={18} />
            </button>
            <button
              onClick={clearHistory}
              className="p-2 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors text-red-600 dark:text-red-400"
              title="Clear history"
            >
              <Trash2 size={18} />
            </button>
          </div>
        }
      />
      <Card.Body>
        {/* Filter Section */}
        <div className="mb-4">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 block">
            Filter by Symbol
          </label>
          <select
            value={filterSymbol}
            onChange={(e) => setFilterSymbol(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 transition-all"
          >
            <option value="">All Symbols</option>
            {getUniqueSymbols().map((sym) => (
              <option key={sym} value={sym}>
                {sym}
              </option>
            ))}
          </select>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
          <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg border border-green-200 dark:border-green-800">
            <p className="text-green-800 dark:text-green-200">BUY Signals</p>
            <p className="text-xl font-bold text-green-600 dark:text-green-400">
              {filteredHistory.filter((p) => p.recommendation === 'BUY').length}
            </p>
          </div>
          <div className="bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg border border-amber-200 dark:border-amber-800">
            <p className="text-amber-800 dark:text-amber-200">HOLD Signals</p>
            <p className="text-xl font-bold text-amber-600 dark:text-amber-400">
              {filteredHistory.filter((p) => p.recommendation === 'HOLD').length}
            </p>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-200 dark:border-red-800">
            <p className="text-red-800 dark:text-red-200">SELL Signals</p>
            <p className="text-xl font-bold text-red-600 dark:text-red-400">
              {filteredHistory.filter((p) => p.recommendation === 'SELL').length}
            </p>
          </div>
        </div>

        {/* History Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2 text-left font-semibold text-slate-700 dark:text-slate-300">
                  Symbol
                </th>
                <th className="px-4 py-2 text-left font-semibold text-slate-700 dark:text-slate-300">
                  Signal
                </th>
                <th className="px-4 py-2 text-right font-semibold text-slate-700 dark:text-slate-300">
                  Confidence
                </th>
                <th className="px-4 py-2 text-right font-semibold text-slate-700 dark:text-slate-300">
                  Current Price
                </th>
                <th className="px-4 py-2 text-right font-semibold text-slate-700 dark:text-slate-300">
                  Predicted
                </th>
                <th className="px-4 py-2 text-right font-semibold text-slate-700 dark:text-slate-300">
                  Change
                </th>
                <th className="px-4 py-2 text-left font-semibold text-slate-700 dark:text-slate-300">
                  Time
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((prediction) => (
                <tr
                  key={prediction.id}
                  className="border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                  <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                    {prediction.symbol}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getRecommendationIcon(prediction.recommendation)}
                      <FinancialStatusBadge
                        signal={prediction.recommendation}
                        confidence={prediction.confidence}
                      />
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600 dark:text-slate-400">
                    {(prediction.confidence * 100).toFixed(1)}%
                  </td>
                  <td className="px-4 py-3 text-right text-slate-900 dark:text-white font-medium">
                    ${prediction.current_price?.toFixed(2) || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-900 dark:text-white font-medium">
                    ${prediction.predicted_price?.toFixed(2) || 'N/A'}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-medium ${
                      prediction.predicted_change >= 0
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {prediction.predicted_change >= 0 ? '↑' : '↓'}
                    {Math.abs(prediction.predicted_change).toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                    {new Date(prediction.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredHistory.length === 0 && (
          <p className="text-center text-slate-600 dark:text-slate-400 py-4">
            No predictions matching filter.
          </p>
        )}
      </Card.Body>
    </Card>
  );
}

export default PredictionHistory;
