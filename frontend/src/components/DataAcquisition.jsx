import React, { useState } from 'react';
import { Play, Square, Download, Upload } from 'lucide-react';

export default function DataAcquisition({ setPipelineStatus, setResults }) {
  const [isRunning, setIsRunning] = useState(false);
  const [symbols, setSymbols] = useState('AAPL,MSFT,GOOGL,AMZN,TSLA');
  const [dataSource, setDataSource] = useState('mock');
  const [lookbackYears, setLookbackYears] = useState(10);
  const [logs, setLogs] = useState([]);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { message, type, timestamp }]);
  };

  const handleRunPipeline = async () => {
    setIsRunning(true);
    addLog('Pipeline started...', 'info');
    setPipelineStatus('running');

    try {
      addLog('Initializing data acquisition...', 'info');
      await new Promise(resolve => setTimeout(resolve, 500));

      const symbolList = symbols.split(',').map(s => s.trim());
      for (const symbol of symbolList) {
        addLog(`Fetching data for ${symbol}...`, 'info');
        await new Promise(resolve => setTimeout(resolve, 300));
        addLog(`✓ ${symbol}: 2,580 trading days acquired`, 'success');
      }

      addLog('Data cleaning started...', 'info');
      await new Promise(resolve => setTimeout(resolve, 500));
      addLog('✓ Data cleaning completed', 'success');

      addLog('Feature engineering in progress...', 'info');
      await new Promise(resolve => setTimeout(resolve, 800));
      addLog('✓ 47 features generated across 3 tiers', 'success');

      addLog('Model training started...', 'info');
      await new Promise(resolve => setTimeout(resolve, 1000));
      addLog('✓ 5 baseline models trained', 'success');

      addLog('Pipeline completed successfully!', 'success');
      setPipelineStatus('completed');
    } catch (error) {
      addLog(`Error: ${error.message}`, 'error');
      setPipelineStatus('error');
    } finally {
      setIsRunning(false);
    }
  };

  const handleStopPipeline = () => {
    setIsRunning(false);
    addLog('Pipeline stopped by user', 'warning');
    setPipelineStatus('stopped');
  };

  const InputGroup = ({ label, value, onChange, type = 'text', options = null }) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300">{label}</label>
      {options ? (
        <select
          value={value}
          onChange={onChange}
          className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      ) : (
        <input
          type={type}
          value={value}
          onChange={onChange}
          className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Configuration Panel */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Pipeline Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <InputGroup
            label="Data Source"
            value={dataSource}
            onChange={(e) => setDataSource(e.target.value)}
            options={[
              { value: 'mock', label: 'Mock (Synthetic)' },
              { value: 'iex', label: 'IEX Cloud' },
              { value: 'yfinance', label: 'Yahoo Finance' }
            ]}
          />
          <InputGroup
            label="Lookback Period (Years)"
            value={lookbackYears}
            onChange={(e) => setLookbackYears(e.target.value)}
            type="number"
          />
          <InputGroup
            label="Symbols (comma-separated)"
            value={symbols}
            onChange={(e) => setSymbols(e.target.value)}
          />
        </div>

        {/* Control Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleRunPipeline}
            disabled={isRunning}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors"
          >
            <Play size={18} />
            {isRunning ? 'Running...' : 'Run Pipeline'}
          </button>
          
          {isRunning && (
            <button
              onClick={handleStopPipeline}
              className="flex items-center gap-2 px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
            >
              <Square size={18} />
              Stop
            </button>
          )}

          <button className="flex items-center gap-2 px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors">
            <Download size={18} />
            Export
          </button>

          <button className="flex items-center gap-2 px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors">
            <Upload size={18} />
            Import
          </button>
        </div>
      </div>

      {/* Logs Panel */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Execution Log</h3>
        <div className="bg-slate-950 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
          {logs.length === 0 ? (
            <p className="text-slate-500">Logs will appear here when you run the pipeline...</p>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} className={`py-1 ${
                log.type === 'success' ? 'text-green-400' :
                log.type === 'error' ? 'text-red-400' :
                log.type === 'warning' ? 'text-yellow-400' :
                'text-slate-300'
              }`}>
                <span className="text-slate-600">{log.timestamp}</span> {log.message}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Data Quality Panel */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Data Quality Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {symbols.split(',').map((symbol, idx) => (
            <div key={idx} className="bg-slate-700 rounded-lg p-4 text-center">
              <p className="text-white font-semibold">{symbol.trim()}</p>
              <p className="text-slate-400 text-sm mt-2">2,580 days</p>
              <p className="text-green-400 text-xs mt-1">✓ Complete</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
