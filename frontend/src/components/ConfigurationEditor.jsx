import React, { useState, useEffect } from 'react';
import { Save, X, RefreshCw } from 'lucide-react';
import { useConfig } from '../hooks/useConfig';
import { api } from '../services/api';
import { Card, LoadingSpinner, ErrorAlert } from './ui';

/**
 * ConfigurationEditor Component
 * 
 * Allows editing and saving pipeline configuration.
 * Integrates with /api/config endpoints.
 * 
 * @component
 * @param {function} props.onClose - Callback when closing editor
 * @returns {React.ReactNode} Configuration editor interface
 */
export function ConfigurationEditor({ onClose }) {
  const [localConfig, setLocalConfig] = useState({});
  const [hasChanges, setHasChanges] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Load configuration
  const { config, loading, error, loadConfig, updateConfig } = useConfig({
    autoLoad: true,
  });

  // Initialize local config from loaded config
  useEffect(() => {
    if (config) {
      setLocalConfig(config);
      setHasChanges(false);
    }
  }, [config]);

  // Handle field change
  const handleChange = (field, value) => {
    setLocalConfig((prev) => ({
      ...prev,
      [field]: value,
    }));
    setHasChanges(true);
    setSaveError(null);
  };

  // Handle save configuration
  const handleSave = async () => {
    try {
      setSaveLoading(true);
      setSaveError(null);
      await updateConfig(localConfig);
      setHasChanges(false);
    } catch (err) {
      setSaveError(err);
    } finally {
      setSaveLoading(false);
    }
  };

  // Handle discard changes
  const handleDiscard = () => {
    setLocalConfig(config || {});
    setHasChanges(false);
  };

  if (loading) {
    return (
      <Card>
        <Card.Header title="Pipeline Configuration" />
        <Card.Body>
          <LoadingSpinner message="Loading configuration..." size="sm" />
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card>
      <Card.Header
        title="Pipeline Configuration"
        subtitle="Edit settings and save to the backend"
        action={
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors text-slate-600 dark:text-slate-400"
            aria-label="Close configuration editor"
          >
            <X size={20} />
          </button>
        }
      />
      <Card.Body>
        {/* Error Alert */}
        {error && (
          <div className="mb-4">
            <ErrorAlert
              title="Failed to Load Configuration"
              message={error.message}
              onRetry={loadConfig}
            />
          </div>
        )}

        {saveError && (
          <div className="mb-4">
            <ErrorAlert
              title="Failed to Save Configuration"
              message={saveError.message}
              onRetry={handleSave}
            />
          </div>
        )}

        {/* Configuration Form */}
        <div className="space-y-4 max-h-96 overflow-y-auto">
          <ConfigurationField
            label="Data Source"
            description="Primary data source for acquisition"
            value={localConfig.data_source || 'iex'}
            onChange={(value) => handleChange('data_source', value)}
            options={['iex', 'yfinance', 'mock']}
            type="select"
          />

          <ConfigurationField
            label="Lookback Period (Years)"
            description="Historical data lookback window"
            value={localConfig.lookback_years || 10}
            onChange={(value) => handleChange('lookback_years', parseInt(value))}
            type="number"
            min="1"
            max="20"
          />

          <ConfigurationField
            label="Symbols"
            description="Comma-separated stock symbols"
            value={localConfig.symbols || 'AAPL,MSFT,GOOGL'}
            onChange={(value) => handleChange('symbols', value)}
            type="textarea"
          />

          <ConfigurationField
            label="Train/Val/Test Split"
            description="Data split ratio (e.g., 0.7,0.15,0.15)"
            value={localConfig.train_val_test_split || '0.7,0.15,0.15'}
            onChange={(value) => handleChange('train_val_test_split', value)}
            type="text"
          />

          <ConfigurationField
            label="Feature Tier"
            description="Feature engineering tier (1=basic, 3=advanced)"
            value={localConfig.feature_tier || 2}
            onChange={(value) => handleChange('feature_tier', parseInt(value))}
            options={[1, 2, 3]}
            type="select"
          />

          <ConfigurationField
            label="Random Seed"
            description="Seed for reproducibility"
            value={localConfig.random_seed || 42}
            onChange={(value) => handleChange('random_seed', parseInt(value))}
            type="number"
            min="1"
            max="999999"
          />

          <ConfigurationField
            label="Batch Size"
            description="Batch size for model training"
            value={localConfig.batch_size || 32}
            onChange={(value) => handleChange('batch_size', parseInt(value))}
            type="number"
            min="1"
            max="512"
          />

          <ConfigurationField
            label="Epochs"
            description="Number of training epochs"
            value={localConfig.epochs || 50}
            onChange={(value) => handleChange('epochs', parseInt(value))}
            type="number"
            min="1"
            max="1000"
          />

          <ConfigurationField
            label="Learning Rate"
            description="Model learning rate (0.0001-0.1)"
            value={localConfig.learning_rate || 0.001}
            onChange={(value) => handleChange('learning_rate', parseFloat(value))}
            type="number"
            min="0.0001"
            max="0.1"
            step="0.0001"
          />

          <ConfigurationField
            label="Enable Validation"
            description="Run validation during training"
            value={localConfig.enable_validation !== false}
            onChange={(value) => handleChange('enable_validation', value)}
            type="checkbox"
          />

          <ConfigurationField
            label="Enable Ablation Studies"
            description="Run ablation studies after training"
            value={localConfig.enable_ablation !== false}
            onChange={(value) => handleChange('enable_ablation', value)}
            type="checkbox"
          />
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex gap-3 border-t border-slate-200 dark:border-slate-700 pt-4">
          <button
            onClick={handleSave}
            disabled={!hasChanges || saveLoading}
            className="flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save size={18} />
            {saveLoading ? 'Saving...' : 'Save Configuration'}
          </button>

          <button
            onClick={handleDiscard}
            disabled={!hasChanges}
            className="flex items-center gap-2 px-6 py-2.5 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw size={18} />
            Discard Changes
          </button>

          <button
            onClick={onClose}
            className="flex items-center gap-2 px-6 py-2.5 bg-slate-300 dark:bg-slate-700 hover:bg-slate-400 dark:hover:bg-slate-600 text-slate-900 dark:text-white rounded-lg font-medium transition-colors ml-auto"
          >
            <X size={18} />
            Close
          </button>
        </div>

        {/* Change Indicator */}
        {hasChanges && (
          <div className="mt-4 p-3 bg-amber-100 dark:bg-amber-900 border border-amber-300 dark:border-amber-700 rounded-lg text-amber-800 dark:text-amber-200 text-sm">
            ⚠️ You have unsaved changes
          </div>
        )}
      </Card.Body>
    </Card>
  );
}

/**
 * ConfigurationField Sub-component
 */
function ConfigurationField({
  label,
  description,
  value,
  onChange,
  type = 'text',
  options = [],
  min,
  max,
  step,
}) {
  return (
    <div>
      <label className="block text-sm font-semibold text-slate-900 dark:text-white mb-1">
        {label}
      </label>
      <p className="text-xs text-slate-600 dark:text-slate-400 mb-2">
        {description}
      </p>

      {type === 'select' ? (
        <select
          value={value}
          onChange={(e) => onChange(
            options.some((opt) => typeof opt === 'number')
              ? parseInt(e.target.value)
              : e.target.value
          )}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 transition-all"
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      ) : type === 'textarea' ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows="3"
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 transition-all font-mono text-sm"
        />
      ) : type === 'checkbox' ? (
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={value}
            onChange={(e) => onChange(e.target.checked)}
            className="w-5 h-5 accent-blue-600"
          />
          <span className="text-sm text-slate-700 dark:text-slate-300">
            Enabled
          </span>
        </label>
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) =>
            onChange(
              type === 'number' ? parseFloat(e.target.value) : e.target.value
            )
          }
          min={min}
          max={max}
          step={step}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 transition-all"
        />
      )}
    </div>
  );
}

export default ConfigurationEditor;
