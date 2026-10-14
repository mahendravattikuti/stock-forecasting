import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

export default function Dashboard({ pipelineStatus, results }) {
  const [stats, setStats] = useState({
    symbolsProcessed: 5,
    dataPoints: 12900,
    featuresGenerated: 47,
    modelsTraining: 5
  });

  const sampleData = [
    { date: '2024-01-01', price: 150, prediction: 152 },
    { date: '2024-01-02', price: 155, prediction: 154 },
    { date: '2024-01-03', price: 152, prediction: 151 },
    { date: '2024-01-04', price: 158, prediction: 159 },
    { date: '2024-01-05', price: 162, prediction: 161 },
    { date: '2024-01-06', price: 160, prediction: 162 },
  ];

  const baselineMetrics = [
    { model: 'Random Walk', mae: 2.34, rmse: 3.21 },
    { model: 'ARIMA', mae: 1.87, rmse: 2.45 },
    { model: 'Linear Reg', mae: 1.65, rmse: 2.12 },
    { model: 'Ridge Reg', mae: 1.43, rmse: 1.89 },
    { model: 'Hist Mean', mae: 2.12, rmse: 2.78 },
  ];

  const StatusCard = ({ icon: Icon, label, value, color }) => (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-all">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm font-medium">{label}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon size={24} className="text-white" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatusCard icon={Activity} label="Symbols Processed" value={stats.symbolsProcessed} color="bg-blue-600" />
        <StatusCard icon={CheckCircle2} label="Data Points" value={stats.dataPoints.toLocaleString()} color="bg-green-600" />
        <StatusCard icon={Activity} label="Features" value={stats.featuresGenerated} color="bg-purple-600" />
        <StatusCard icon={Clock} label="Models" value={stats.modelsTraining} color="bg-orange-600" />
      </div>

      {/* Pipeline Status */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Pipeline Status</h3>
        <div className="space-y-3">
          {[
            { phase: 'Data Acquisition', status: 'completed' },
            { phase: 'Data Cleaning', status: 'completed' },
            { phase: 'Feature Engineering', status: 'completed' },
            { phase: 'Model Training', status: 'in_progress' },
            { phase: 'Evaluation', status: 'pending' },
          ].map((item, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${
                item.status === 'completed' ? 'bg-green-500' :
                item.status === 'in_progress' ? 'bg-blue-500 animate-pulse' :
                'bg-slate-600'
              }`} />
              <span className="text-slate-300">{item.phase}</span>
              <span className={`ml-auto text-sm font-medium ${
                item.status === 'completed' ? 'text-green-400' :
                item.status === 'in_progress' ? 'text-blue-400' :
                'text-slate-500'
              }`}>
                {item.status === 'completed' ? '✓' :
                 item.status === 'in_progress' ? '⟳' : '○'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Price Prediction */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Price Prediction (Sample)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sampleData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
              <Legend />
              <Line type="monotone" dataKey="price" stroke="#06b6d4" name="Actual" strokeWidth={2} />
              <Line type="monotone" dataKey="prediction" stroke="#f59e0b" name="Prediction" strokeWidth={2} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Baseline Model Comparison */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Baseline Model Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={baselineMetrics}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="model" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
              <Legend />
              <Bar dataKey="mae" fill="#06b6d4" name="MAE" />
              <Bar dataKey="rmse" fill="#f59e0b" name="RMSE" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
