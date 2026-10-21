import React, { useState } from 'react';
import { Save, RotateCcw, Download, Upload } from 'lucide-react';

export default function Configuration() {
  const [config, setConfig] = useState({
    dataSource: 'mock',
    lookbackYears: 10,
    trainRatio: 0.70,
    valRatio: 0.15,
    testRatio: 0.15,
    tier1Enabled: true,
    tier2Enabled: true,
    tier3Enabled: false,
    signalProcessing: false,
    randomSeed: 42,
    bootstrapSamples: 1000,
  });

  const handleChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const ConfigSection = ({ title, children }) => (
    <fieldset className="bg-slate-800 border border-slate-700 rounded-lg p-6 mb-6">
      <legend className="text-lg font-semibold text-white mb-4">{title}</legend>
      <div className="space-y-4">{children}</div>
    </fieldset>
  );

  const ConfigField = ({ label, type = 'text', value, onChange, options = null, children = null }) => {
    // Create unique ID for label-input association
    const fieldId = `config-${label.replace(/[^a-z0-9]/gi, '-').toLowerCase()}`;
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
        <label htmlFor={fieldId} className="text-slate-300 font-medium">
          {label}
        </label>
        <div className="md:col-span-2">
          {type === 'checkbox' ? (
            <div className="flex items-center gap-3">
              <input
                id={fieldId}
                type="checkbox"
                checked={value}
                onChange={(e) => onChange(e.target.checked)}
                className="w-4 h-4 rounded border-slate-600 text-blue-600 focus:ring-2 focus:ring-blue-500 cursor-pointer"
                aria-label={`Enable ${label}`}
              />
              <label htmlFor={fieldId} className="text-slate-400 text-sm cursor-pointer">
                {label}
              </label>
            </div>
          ) : options ? (
            <select
              id={fieldId}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              aria-label={`Select ${label}`}
            >
              {options.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          ) : (
            <input
              id={fieldId}
              type={type}
              value={value}
              onChange={(e) => onChange(type === 'number' ? parseFloat(e.target.value) : e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              aria-label={label}
            />
          )}
        </div>
      </div>
    );
  };

  return (
    <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
      <ConfigSection title="Data Acquisition">
        <ConfigField
          label="Data Source"
          options={[
            { value: 'mock', label: 'Mock (Synthetic)' },
            { value: 'iex', label: 'IEX Cloud' },
            { value: 'yfinance', label: 'Yahoo Finance' }
          ]}
          value={config.dataSource}
          onChange={(v) => handleChange('dataSource', v)}
        />
        <ConfigField
          label="Lookback Period (Years)"
          type="number"
          value={config.lookbackYears}
          onChange={(v) => handleChange('lookbackYears', v)}
        />
      </ConfigSection>

      <ConfigSection title="Data Splitting">
        <ConfigField
          label="Training Set Ratio"
          type="number"
          value={config.trainRatio}
          onChange={(v) => handleChange('trainRatio', v)}
        />
        <ConfigField
          label="Validation Set Ratio"
          type="number"
          value={config.valRatio}
          onChange={(v) => handleChange('valRatio', v)}
        />
        <ConfigField
          label="Test Set Ratio"
          type="number"
          value={config.testRatio}
          onChange={(v) => handleChange('testRatio', v)}
        />
      </ConfigSection>

      <ConfigSection title="Feature Engineering">
        <ConfigField
          label="Tier-1 Features (Returns, Prices)"
          type="checkbox"
          value={config.tier1Enabled}
          onChange={(v) => handleChange('tier1Enabled', v)}
        />
        <ConfigField
          label="Tier-2 Features (Technical Indicators)"
          type="checkbox"
          value={config.tier2Enabled}
          onChange={(v) => handleChange('tier2Enabled', v)}
        />
        <ConfigField
          label="Tier-3 Features (Market Regimes)"
          type="checkbox"
          value={config.tier3Enabled}
          onChange={(v) => handleChange('tier3Enabled', v)}
        />
        <ConfigField
          label="Signal Processing (Wavelet, SSA, Kalman)"
          type="checkbox"
          value={config.signalProcessing}
          onChange={(v) => handleChange('signalProcessing', v)}
        />
      </ConfigSection>

      <ConfigSection title="Reproducibility">
        <ConfigField
          label="Random Seed"
          type="number"
          value={config.randomSeed}
          onChange={(v) => handleChange('randomSeed', v)}
        />
        <ConfigField
          label="Bootstrap Samples"
          type="number"
          value={config.bootstrapSamples}
          onChange={(v) => handleChange('bootstrapSamples', v)}
        />
      </ConfigSection>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <button 
          type="button"
          aria-label="Save current configuration"
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
        >
          <Save size={18} aria-hidden="true" />
          Save Configuration
        </button>
        <button 
          type="reset"
          aria-label="Reset configuration to default values"
          className="flex items-center gap-2 px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
        >
          <RotateCcw size={18} aria-hidden="true" />
          Reset to Defaults
        </button>
        <button 
          type="button"
          aria-label="Export configuration to file"
          className="flex items-center gap-2 px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
        >
          <Download size={18} aria-hidden="true" />
          Export Config
        </button>
        <button 
          type="button"
          aria-label="Import configuration from file"
          className="flex items-center gap-2 px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
        >
          <Upload size={18} aria-hidden="true" />
          Import Config
        </button>
      </div>

      {/* Configuration Preview */}
      <section className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Configuration Preview (JSON)</h3>
        <pre 
          className="bg-slate-950 rounded-lg p-4 text-slate-300 text-sm overflow-x-auto"
          role="region"
          aria-label="JSON configuration preview"
        >
          {JSON.stringify(config, null, 2)}
        </pre>
      </section>
    </form>
  );
}
