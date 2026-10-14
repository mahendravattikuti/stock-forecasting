import React, { useState } from 'react';
import { Search, TrendingUp, TrendingDown, Minus, Loader } from 'lucide-react';

export default function StockPredictor() {
  const [symbol, setSymbol] = useState('');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const handlePredict = async () => {
    if (!symbol.trim()) {
      setError('Please enter a stock symbol');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:5000/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: symbol.toUpperCase() })
      });

      if (!response.ok) throw new Error('Failed to fetch prediction');
      
      const data = await response.json();
      setPrediction(data);
      
      // Add to history
      setHistory(prev => [{
        symbol: data.symbol,
        recommendation: data.recommendation,
        confidence: data.confidence,
        price: data.current_price,
        timestamp: new Date().toLocaleTimeString()
      }, ...prev].slice(0, 10));
      
      setSymbol('');
    } catch (err) {
      setError(err.message || 'Error fetching prediction');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (rec) => {
    switch (rec) {
      case 'BUY': return 'text-green-400 bg-green-950';
      case 'SELL': return 'text-red-400 bg-red-950';
      case 'HOLD': return 'text-yellow-400 bg-yellow-950';
      default: return 'text-slate-400 bg-slate-800';
    }
  };

  const getRecommendationIcon = (rec) => {
    switch (rec) {
      case 'BUY': return <TrendingUp size={24} />;
      case 'SELL': return <TrendingDown size={24} />;
      case 'HOLD': return <Minus size={24} />;
      default: return null;
    }
  };

  const getConfidenceBarColor = (confidence) => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.6) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Real-Time Stock Prediction</h3>
        
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              onKeyPress={(e) => e.key === 'Enter' && handlePredict()}
              placeholder="Enter stock symbol (e.g., AAPL, MSFT, GOOGL)"
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Search className="absolute right-3 top-3 text-slate-400" size={20} />
          </div>
          
          <button
            onClick={handlePredict}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader size={18} className="animate-spin" />
                Predicting...
              </>
            ) : (
              <>
                <Search size={18} />
                Predict
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-3 p-3 bg-red-950 border border-red-700 rounded-lg text-red-200 text-sm">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Current Prediction */}
      {prediction && (
        <div className={`border rounded-lg p-8 ${getRecommendationColor(prediction.recommendation)}`}>
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-3xl font-bold text-white">{prediction.symbol}</h2>
              <p className="text-slate-300 mt-1">Current Price: ${prediction.current_price.toFixed(2)}</p>
            </div>
            <div className="text-6xl opacity-20">
              {getRecommendationIcon(prediction.recommendation)}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <p className="text-sm opacity-75 mb-1">Predicted Next Day</p>
              <p className="text-2xl font-bold">${prediction.predicted_price.toFixed(2)}</p>
              <p className="text-sm mt-1">
                {prediction.predicted_change >= 0 ? '📈' : '📉'} 
                {' '}{Math.abs(prediction.predicted_change).toFixed(2)}%
              </p>
            </div>
            
            <div>
              <p className="text-sm opacity-75 mb-1">Confidence Score</p>
              <p className="text-2xl font-bold">{(prediction.confidence * 100).toFixed(1)}%</p>
              <div className="w-full bg-slate-700 rounded-full h-2 mt-2">
                <div
                  className={`${getConfidenceBarColor(prediction.confidence)} h-2 rounded-full`}
                  style={{ width: `${prediction.confidence * 100}%` }}
                />
              </div>
            </div>

            <div>
              <p className="text-sm opacity-75 mb-1">Model Used</p>
              <p className="text-2xl font-bold">{prediction.model}</p>
              <p className="text-sm mt-1 opacity-75">Best performing baseline</p>
            </div>
          </div>

          <div className="border-t border-current opacity-25 pt-4">
            <p className="text-center text-sm opacity-75">
              Analysis based on 10 years of historical data and technical indicators
            </p>
          </div>

          {prediction.recommendation === 'BUY' && (
            <div className="mt-6 p-4 bg-green-900 bg-opacity-50 rounded-lg border border-green-700">
              <p className="text-sm">
                <strong>Signal:</strong> Technical indicators suggest bullish momentum. 
                Stock showing positive trends with predicted upward movement.
              </p>
            </div>
          )}

          {prediction.recommendation === 'SELL' && (
            <div className="mt-6 p-4 bg-red-900 bg-opacity-50 rounded-lg border border-red-700">
              <p className="text-sm">
                <strong>Signal:</strong> Technical indicators suggest bearish momentum.
                Stock showing negative trends with predicted downward movement.
              </p>
            </div>
          )}

          {prediction.recommendation === 'HOLD' && (
            <div className="mt-6 p-4 bg-yellow-900 bg-opacity-50 rounded-lg border border-yellow-700">
              <p className="text-sm">
                <strong>Signal:</strong> Technical indicators suggest neutral momentum.
                Stock showing mixed signals - maintain current position.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Popular Stocks */}
      {!prediction && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Access - Popular Stocks</h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'].map(sym => (
              <button
                key={sym}
                onClick={() => {
                  setSymbol(sym);
                  setTimeout(() => {
                    document.querySelector('button[class*="bg-blue-600"]').click();
                  }, 0);
                }}
                className="p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-white font-semibold transition-colors"
              >
                {sym}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Prediction History */}
      {history.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Predictions</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {history.map((entry, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors">
                <div className="flex items-center gap-3 flex-1">
                  <span className="font-semibold text-white w-16">{entry.symbol}</span>
                  <span className="text-slate-400 text-sm">${entry.price.toFixed(2)}</span>
                  <span className="text-xs text-slate-500">{entry.timestamp}</span>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className={`font-semibold text-sm ${
                      entry.recommendation === 'BUY' ? 'text-green-400' :
                      entry.recommendation === 'SELL' ? 'text-red-400' :
                      'text-yellow-400'
                    }`}>
                      {entry.recommendation}
                    </p>
                    <p className="text-xs text-slate-400">
                      {(entry.confidence * 100).toFixed(0)}% confidence
                    </p>
                  </div>
                  
                  <div className="text-2xl">
                    {entry.recommendation === 'BUY' ? '🟢' :
                     entry.recommendation === 'SELL' ? '🔴' :
                     '🟡'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
