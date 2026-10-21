import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import DataAcquisition from './components/DataAcquisition';
import ModelResults from './components/ModelResults';
import Configuration from './components/Configuration';
import StockPredictor from './components/StockPredictor';
import Navigation from './components/Navigation';
import AppLayout from './components/layout/AppLayout';
import { ThemeProvider } from './context/ThemeContext';
import { BarChart3, Database, TrendingUp, Settings, Zap } from 'lucide-react';

function AppContent() {
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

  // Update document title when active tab changes
  useEffect(() => {
    const activeTabLabel = tabs.find(tab => tab.id === activeTab)?.label || 'Stock Optimizer';
    document.title = `${activeTabLabel} - Stock Optimizer`;
  }, [activeTab, tabs]);

  return (
    <>
      <Navigation tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab} />
      <AppLayout title="Stock Market Forecasting System">
        <main className="container mx-auto px-4 py-8" role="main">
          {activeTab === 'predictor' && <StockPredictor />}
          {activeTab === 'dashboard' && <Dashboard pipelineStatus={pipelineStatus} results={results} />}
          {activeTab === 'data' && <DataAcquisition setPipelineStatus={setPipelineStatus} setResults={setResults} />}
          {activeTab === 'models' && <ModelResults results={results} />}
          {activeTab === 'config' && <Configuration />}
        </main>
      </AppLayout>
    </>
  );
}

export default function App() {
  return (
    <ThemeProvider defaultTheme="light">
      <AppContent />
    </ThemeProvider>
  );
}
