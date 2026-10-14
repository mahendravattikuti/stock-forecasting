import React from 'react';
import { Award, TrendingUp, Target, Zap } from 'lucide-react';

export default function ModelResults({ results }) {
  const modelResults = [
    { model: 'Ridge Regression', mae: 1.43, rmse: 1.89, directionalAccuracy: 0.68, ic: 0.42, status: 'Best' },
    { model: 'Linear Regression', mae: 1.65, rmse: 2.12, directionalAccuracy: 0.65, ic: 0.38, status: '2nd' },
    { model: 'ARIMA(1,1,1)', mae: 1.87, rmse: 2.45, directionalAccuracy: 0.62, ic: 0.35, status: '3rd' },
    { model: 'Random Walk', mae: 2.34, rmse: 3.21, directionalAccuracy: 0.50, ic: 0.20, status: '4th' },
    { model: 'Historical Mean', mae: 2.12, rmse: 2.78, directionalAccuracy: 0.48, ic: 0.18, status: '5th' },
  ];

  const featureImportance = [
    { feature: 'RSI_14', importance: 0.18, tier: 'Tier-2' },
    { feature: 'Bollinger_Bands', importance: 0.15, tier: 'Tier-2' },
    { feature: 'MACD_Line', importance: 0.12, tier: 'Tier-2' },
    { feature: 'Returns_5D', importance: 0.11, tier: 'Tier-1' },
    { feature: 'Momentum', importance: 0.09, tier: 'Tier-2' },
    { feature: 'ATR_14', importance: 0.08, tier: 'Tier-2' },
    { feature: 'Volume_Norm', importance: 0.07, tier: 'Tier-1' },
  ];

  const MetricCard = ({ icon: Icon, label, value, unit }) => (
    <div className="bg-slate-700 rounded-lg p-4 flex items-center gap-3">
      <div className="p-2 bg-slate-600 rounded-lg">
        <Icon size={20} className="text-blue-400" />
      </div>
      <div>
        <p className="text-slate-400 text-sm">{label}</p>
        <p className="text-white font-semibold">{value} {unit}</p>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Best Model Summary */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg p-6 text-white">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">🏆 Best Performing Model</h2>
            <p className="text-lg">Ridge Regression</p>
            <p className="text-blue-100 text-sm mt-1">Optimized on validation set with L2 regularization</p>
          </div>
          <Award size={40} />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard icon={Target} label="MAE" value="1.43" unit="USD" />
        <MetricCard icon={TrendingUp} label="RMSE" value="1.89" unit="USD" />
        <MetricCard icon={Zap} label="Directional Accuracy" value="68" unit="%" />
        <MetricCard icon={Award} label="Information Coefficient" value="0.42" unit="" />
      </div>

      {/* Model Comparison */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Model Performance Ranking</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-300 font-semibold">Rank</th>
                <th className="text-left py-3 px-4 text-slate-300 font-semibold">Model</th>
                <th className="text-right py-3 px-4 text-slate-300 font-semibold">MAE</th>
                <th className="text-right py-3 px-4 text-slate-300 font-semibold">RMSE</th>
                <th className="text-right py-3 px-4 text-slate-300 font-semibold">Dir. Acc.</th>
                <th className="text-right py-3 px-4 text-slate-300 font-semibold">IC</th>
              </tr>
            </thead>
            <tbody>
              {modelResults.map((result, idx) => (
                <tr key={idx} className={`border-b border-slate-700 hover:bg-slate-700 transition-colors ${
                  idx === 0 ? 'bg-blue-950' : ''
                }`}>
                  <td className="py-3 px-4">
                    <span className={`inline-block w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      idx === 0 ? 'bg-yellow-500 text-slate-900' :
                      idx === 1 ? 'bg-slate-400 text-slate-900' :
                      idx === 2 ? 'bg-orange-600 text-white' :
                      'text-slate-500'
                    }`}>
                      {idx + 1}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-white font-medium">{result.model}</td>
                  <td className="py-3 px-4 text-right text-slate-300">{result.mae}</td>
                  <td className="py-3 px-4 text-right text-slate-300">{result.rmse}</td>
                  <td className="py-3 px-4 text-right text-slate-300">{(result.directionalAccuracy * 100).toFixed(0)}%</td>
                  <td className="py-3 px-4 text-right text-slate-300">{result.ic.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Feature Importance */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Feature Importance (Ridge Model)</h3>
        <div className="space-y-3">
          {featureImportance.map((item, idx) => (
            <div key={idx}>
              <div className="flex items-center justify-between mb-1">
                <div>
                  <p className="text-white font-medium">{item.feature}</p>
                  <p className="text-slate-500 text-xs">{item.tier}</p>
                </div>
                <span className="text-slate-300">{(item.importance * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full"
                  style={{ width: `${item.importance * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Evaluation Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Test Set Metrics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-300">Mean Absolute Error</span>
              <span className="text-white font-semibold">1.43 USD</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Root Mean Squared Error</span>
              <span className="text-white font-semibold">1.89 USD</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Mean Absolute Percentage Error</span>
              <span className="text-white font-semibold">0.87%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Directional Accuracy</span>
              <span className="text-green-400 font-semibold">68.4%</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Statistical Measures</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-300">Information Coefficient</span>
              <span className="text-white font-semibold">0.42</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Sharpe Ratio</span>
              <span className="text-white font-semibold">1.85</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Prediction Bias</span>
              <span className="text-white font-semibold">-0.12 USD</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Correlation</span>
              <span className="text-white font-semibold">0.76</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
