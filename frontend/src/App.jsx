import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import DataAcquisition from './components/DataAcquisition';
import ModelResults from './components/ModelResults';
import Configuration from './components/Configuration';
import StockPredictor from './components/StockPredictor';
import Navigation from './components/Navigation';
import { BarChart3, Database, TrendingUp, Settings, Zap } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('predictor');
  const [pipelineStatus, setPipelineStatus] = useState('idle');
  const [results, setResults] = useState(null);

  const tabs = [
    { id: 'predictor', label: 'Stock Predictor', icon: Zap },
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'data', label: 'Data Acquisition', icon: Database },
    { id: 'models', label: 'Model Results', icon: TrendingUp },
    { id: 'config', label: 'Configuration', icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Navigation tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'predictor' && <StockPredictor />}
        {activeTab === 'dashboard' && <Dashboard pipelineStatus={pipelineStatus} results={results} />}
        {activeTab === 'data' && <DataAcquisition setPipelineStatus={setPipelineStatus} setResults={setResults} />}
        {activeTab === 'models' && <ModelResults results={results} />}
        {activeTab === 'config' && <Configuration />}
      </main>
    </div>
  );
}
