import React from 'react';
import { Card, StatusBadge, Tooltip } from './ui';

/**
 * TechnicalIndicators Component
 * 
 * Displays technical indicators for a predicted stock.
 * Shows RSI, MACD, Bollinger Bands, and other technical analysis metrics.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Object} props.indicators - Technical indicator data
 * @param {string} [props.symbol] - Stock symbol for display
 * @returns {React.ReactNode} Technical indicators display
 */
export function TechnicalIndicators({ indicators = {}, symbol = '' }) {
  if (!indicators || Object.keys(indicators).length === 0) {
    return null;
  }

  const getIndicatorStatus = (name, value) => {
    switch (name) {
      case 'rsi':
        if (value < 30) return { status: 'warning', label: 'Oversold' };
        if (value > 70) return { status: 'warning', label: 'Overbought' };
        return { status: 'success', label: 'Normal' };
      case 'macd':
        if (value > 0) return { status: 'success', label: 'Bullish' };
        if (value < 0) return { status: 'error', label: 'Bearish' };
        return { status: 'info', label: 'Neutral' };
      default:
        return { status: 'info', label: 'Info' };
    }
  };

  const IndicatorCard = ({ title, value, unit = '', description, status }) => (
    <div className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
      <div className="flex items-start justify-between mb-2">
        <Tooltip content={description} position="top">
          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 cursor-help">
            {title}
          </h4>
        </Tooltip>
        {status && (
          <StatusBadge
            status={status.status}
            label={status.label}
            size="sm"
          />
        )}
      </div>
      <p className="text-2xl font-bold text-slate-900 dark:text-white">
        {typeof value === 'number' ? value.toFixed(2) : value}
        <span className="text-sm ml-1 text-slate-600 dark:text-slate-400">
          {unit}
        </span>
      </p>
    </div>
  );

  return (
    <Card>
      <Card.Header
        title="Technical Indicators"
        subtitle={symbol ? `for ${symbol}` : ''}
      />
      <Card.Body>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* RSI (Relative Strength Index) */}
          {indicators.rsi !== undefined && (
            <IndicatorCard
              title="RSI(14)"
              value={indicators.rsi}
              unit=""
              description="Relative Strength Index measures momentum. Below 30 = Oversold, Above 70 = Overbought"
              status={getIndicatorStatus('rsi', indicators.rsi)}
            />
          )}

          {/* MACD */}
          {indicators.macd !== undefined && (
            <IndicatorCard
              title="MACD"
              value={indicators.macd}
              unit=""
              description="Moving Average Convergence Divergence. Positive = Bullish, Negative = Bearish"
              status={getIndicatorStatus('macd', indicators.macd)}
            />
          )}

          {/* Bollinger Bands Width */}
          {indicators.bb_width !== undefined && (
            <IndicatorCard
              title="BB Width"
              value={indicators.bb_width}
              unit="%"
              description="Bollinger Bands Width indicates volatility. Higher = More volatile"
            />
          )}

          {/* Stochastic %K */}
          {indicators.stochastic_k !== undefined && (
            <IndicatorCard
              title="Stochastic %K"
              value={indicators.stochastic_k}
              unit=""
              description="Stochastic Oscillator %K. Below 20 = Oversold, Above 80 = Overbought"
              status={getIndicatorStatus('rsi', indicators.stochastic_k)}
            />
          )}

          {/* ATR (Average True Range) */}
          {indicators.atr !== undefined && (
            <IndicatorCard
              title="ATR(14)"
              value={indicators.atr}
              unit=""
              description="Average True Range measures volatility magnitude"
            />
          )}

          {/* ADX (Average Directional Index) */}
          {indicators.adx !== undefined && (
            <IndicatorCard
              title="ADX"
              value={indicators.adx}
              unit=""
              description="Average Directional Index. Above 25 = Strong trend"
            />
          )}

          {/* OBV (On-Balance Volume) */}
          {indicators.obv !== undefined && (
            <IndicatorCard
              title="OBV"
              value={indicators.obv}
              unit=""
              description="On-Balance Volume indicates volume trend direction"
            />
          )}

          {/* Momentum */}
          {indicators.momentum !== undefined && (
            <IndicatorCard
              title="Momentum"
              value={indicators.momentum}
              unit="%"
              description="Price momentum measure. Positive = Upward momentum"
              status={{
                status: indicators.momentum > 0 ? 'success' : 'error',
                label: indicators.momentum > 0 ? 'Bullish' : 'Bearish',
              }}
            />
          )}
        </div>

        {/* Summary Table */}
        <div className="mt-6 border-t border-slate-200 dark:border-slate-700 pt-6">
          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
            All Indicators
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(indicators).map(([key, value]) => (
              <div
                key={key}
                className="bg-slate-100 dark:bg-slate-700 px-3 py-2 rounded text-xs"
              >
                <p className="text-slate-600 dark:text-slate-400 font-medium uppercase">
                  {key}
                </p>
                <p className="text-slate-900 dark:text-white font-bold mt-1">
                  {typeof value === 'number' ? value.toFixed(2) : value}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-900 dark:text-blue-200">
          <p className="font-semibold mb-2">📊 Technical Analysis Summary</p>
          <ul className="space-y-1 text-xs">
            <li>
              <strong>RSI:</strong> Momentum indicator (0-100). &lt;30 oversold, &gt;70 overbought
            </li>
            <li>
              <strong>MACD:</strong> Trend following momentum. Positive = uptrend, Negative = downtrend
            </li>
            <li>
              <strong>Bollinger Bands:</strong> Volatility indicator. Width shows market volatility
            </li>
            <li>
              <strong>Stochastic:</strong> Momentum oscillator. &lt;20 oversold, &gt;80 overbought
            </li>
            <li>
              <strong>ATR:</strong> Volatility measurement. Higher = More volatile
            </li>
            <li>
              <strong>ADX:</strong> Trend strength. &gt;25 strong trend, &lt;20 weak trend
            </li>
            <li>
              <strong>OBV:</strong> Volume indicator. Rising = Bullish, Falling = Bearish
            </li>
          </ul>
        </div>
      </Card.Body>
    </Card>
  );
}

export default TechnicalIndicators;
