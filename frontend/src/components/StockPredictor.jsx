import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { usePrediction } from '../hooks/usePrediction';
import { Card, LoadingSpinner, ErrorAlert, FinancialStatusBadge, EmptyState } from './ui';
import StockSearch from './StockSearch';
import PredictionHistory from './PredictionHistory';
import TechnicalIndicators from './TechnicalIndicators';

/**
 * StockPredictor Component
 * 
 * Main stock prediction interface with:
 * - Real-time API integration via usePrediction hook
 * - Autocomplete search with StockSearch component
 * - Prediction history with localStorage persistence
 * - Technical indicators display
 * 
 * @component
 * @returns {React.ReactNode} Stock predictor UI
 */
export default function StockPredictor() {
  const [searchValue, setSearchValue] = useState('');
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  // Use prediction hook for API calls
  const { data: prediction, loading, error, predict, clearError } = usePrediction();

  // Handle stock selection from search
  const handleSelectStock = async (stock) => {
    setSearchValue(stock.symbol);
    await predict(stock.symbol);
  };

  // Handle manual search submission
  const handleSearch = async () => {
    if (searchValue.trim()) {
      await predict(searchValue.toUpperCase());
    }
  };

  // Update selected prediction when new prediction arrives
  useEffect(() => {
    if (prediction) {
      setSelectedPrediction(prediction);
    }
  }, [prediction]);

  // Render recommendation icon
  const getRecommendationIcon = (rec) => {
    switch (rec) {
      case 'BUY':
        return <TrendingUp size={24} />;
      case 'SELL':
        return <TrendingDown size={24} />;
      case 'HOLD':
        return <Minus size={24} />;
      default:
        return null;
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.6) return 'bg-amber-500';
    return 'bg-orange-500';
  };

  const getRecommendationMessage = (rec) => {
    const messages = {
      BUY: 'Technical indicators suggest bullish momentum. Stock showing positive trends with predicted upward movement.',
      SELL: 'Technical indicators suggest bearish momentum. Stock showing negative trends with predicted downward movement.',
      HOLD: 'Technical indicators suggest neutral momentum. Stock showing mixed signals - maintain current position.',
    };
    return messages[rec] || 'No signal available';
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Search Section */}
      <Card>
        <Card.Header
          title="Real-Time Stock Prediction"
          subtitle="Enter a stock symbol to get AI-powered predictions"
        />
        <Card.Body>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <div className="flex-1 min-w-0">
              <StockSearch
                value={searchValue}
                onChange={setSearchValue}
                onSelect={handleSelectStock}
                loading={loading}
                suggestions={suggestions}
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading || !searchValue.trim()}
              className="w-full sm:w-auto px-4 sm:px-6 py-2.5 bg-blue-600 hover:bg-blue-700 dark:hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm sm:text-base"
            >
              {loading ? (
                <>
                  <span className="inline-block animate-spin">⟳</span>
                  <span className="hidden sm:inline">Predicting...</span>
                  <span className="sm:hidden">Wait...</span>
                </>
              ) : (
                'Predict'
              )}
            </button>
          </div>

          {error && (
            <div className="mt-3">
              <ErrorAlert
                title="Prediction Failed"
                message={error.message}
                onRetry={handleSearch}
                variant="danger"
              />
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Loading State */}
      {loading && (
        <LoadingSpinner
          message="Analyzing stock data and generating prediction..."
          size="md"
        />
      )}

      {/* Current Prediction */}
      {selectedPrediction && !loading && (
        <Card
          className={`border-2 ${
            selectedPrediction.recommendation === 'BUY'
              ? 'border-green-500 bg-green-50 dark:bg-green-950'
              : selectedPrediction.recommendation === 'SELL'
                ? 'border-red-500 bg-red-50 dark:bg-red-950'
                : 'border-amber-500 bg-amber-50 dark:bg-amber-950'
          }`}
        >
          <Card.Header
            title={`${selectedPrediction.symbol} - Prediction Result`}
            subtitle={`Current Price: $${selectedPrediction.current_price?.toFixed(2) || 'N/A'}`}
          />
          <Card.Body className="space-y-4 sm:space-y-6">
            {/* Main Prediction Display - Responsive Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-6">
              {/* Recommendation */}
              <div className="text-center col-span-1">
                <div className="text-3xl sm:text-5xl mb-1 sm:mb-2 opacity-75">
                  {getRecommendationIcon(selectedPrediction.recommendation)}
                </div>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mb-1">
                  Recommendation
                </p>
                <FinancialStatusBadge
                  signal={selectedPrediction.recommendation}
                  confidence={selectedPrediction.confidence}
                />
              </div>

              {/* Predicted Price */}
              <div>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mb-1">
                  Predicted Next Day
                </p>
                <p className="text-xl sm:text-3xl font-bold text-slate-900 dark:text-white">
                  ${selectedPrediction.predicted_price?.toFixed(2) || 'N/A'}
                </p>
                <p className="text-base sm:text-lg font-semibold mt-1 sm:mt-2">
                  {selectedPrediction.predicted_change >= 0 ? '📈' : '📉'}
                  <span className="ml-1">
                    {Math.abs(selectedPrediction.predicted_change || 0).toFixed(2)}%
                  </span>
                </p>
              </div>

              {/* Confidence */}
              <div>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mb-1">
                  Confidence Score
                </p>
                <p className="text-xl sm:text-3xl font-bold text-slate-900 dark:text-white">
                  {((selectedPrediction.confidence || 0) * 100).toFixed(1)}%
                </p>
                <div className="w-full bg-slate-300 dark:bg-slate-700 rounded-full h-2 mt-1 sm:mt-2">
                  <div
                    className={`${getConfidenceColor(selectedPrediction.confidence || 0)} h-2 rounded-full transition-all`}
                    style={{
                      width: `${(selectedPrediction.confidence || 0) * 100}%`,
                    }}
                  />
                </div>
              </div>

              {/* Model Used */}
              <div>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mb-1">
                  Model Used
                </p>
                <p className="text-lg sm:text-2xl font-bold text-slate-900 dark:text-white truncate">
                  {selectedPrediction.model || 'Deep Learning'}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 sm:mt-2">
                  Best performing baseline
                </p>
              </div>
            </div>

            {/* Signal Message */}
            <div
              className={`p-3 sm:p-4 rounded-lg border text-sm ${
                selectedPrediction.recommendation === 'BUY'
                  ? 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700'
                  : selectedPrediction.recommendation === 'SELL'
                    ? 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700'
                    : 'bg-amber-100 dark:bg-amber-900/30 border-amber-300 dark:border-amber-700'
              }`}
            >
              <p className="text-xs sm:text-sm font-semibold mb-1">Signal Analysis</p>
              <p className="text-xs sm:text-sm leading-relaxed">
                {getRecommendationMessage(selectedPrediction.recommendation)}
              </p>
            </div>

            {/* Analysis Footer */}
            <div className="text-xs text-slate-500 dark:text-slate-400 text-center">
              Analysis based on 10 years of historical data and advanced technical indicators
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Technical Indicators */}
      {selectedPrediction && selectedPrediction.indicators && (
        <TechnicalIndicators
          indicators={selectedPrediction.indicators}
          symbol={selectedPrediction.symbol}
        />
      )}

      {/* Prediction History */}
      {selectedPrediction && (
        <PredictionHistory predictions={selectedPrediction} />
      )}

      {/* Empty State */}
      {!selectedPrediction && !loading && !error && (
        <EmptyState
          title="Start Predicting"
          description="Search for a stock symbol to get AI-powered price predictions and technical analysis."
          icon={<TrendingUp className="w-12 h-12 text-blue-600" />}
        />
      )}
    </div>
  );
}
