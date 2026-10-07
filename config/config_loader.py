"""
Configuration loader for Stock Forecasting System.

Handles loading, validation, and environment variable substitution for pipeline configuration.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class ConfigLoader:
    """
    Load and validate configuration from JSON files.
    
    Supports environment variable substitution and schema validation.
    
    Parameters
    ----------
    config_path : str
        Path to master_config.json file
    
    Examples
    --------
    >>> loader = ConfigLoader('master_config.json')
    >>> config = loader.load_config()
    >>> primary_source = config['data_acquisition']['primary_source']
    """
    
    # Required top-level sections in config
    REQUIRED_SECTIONS = [
        'pipeline_metadata',
        'environment',
        'random_seeds',
        'data_acquisition',
        'data_cleaning',
        'feature_engineering',
        'data_splitting',
        'preprocessing_artifacts',
        'baseline_models',
        'ablation_studies',
        'evaluation',
        'reporting'
    ]
    
    def __init__(self, config_path: str = 'master_config.json'):
        """
        Initialize ConfigLoader with path to config file.
        
        Parameters
        ----------
        config_path : str
            Path to master_config.json
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Performs environment variable substitution and schema validation.
        
        Returns
        -------
        Dict[str, Any]
            Configuration dictionary
            
        Raises
        ------
        ConfigError
            If file not found, JSON invalid, or validation fails
        """
        # Load JSON file
        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                raw_config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {self.config_path}: {e}")
        
        # Perform environment variable substitution
        self.config = self._substitute_env_vars(raw_config)
        
        # Validate schema
        self._validate_schema()
        
        return self.config
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in config.
        
        Supports ${VAR_NAME} syntax.
        
        Parameters
        ----------
        obj : Any
            Object to process (dict, list, str, or primitive)
        
        Returns
        -------
        Any
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Replace ${VAR_NAME} with environment variable value
            def replace_var(match):
                var_name = match.group(1)
                env_value = os.environ.get(var_name)
                if env_value is None:
                    raise ConfigError(f"Environment variable {var_name} not set")
                return env_value
            
            return re.sub(r'\$\{(\w+)\}', replace_var, obj)
        else:
            return obj
    
    def _validate_schema(self) -> None:
        """
        Validate that config has all required sections.
        
        Raises
        ------
        ConfigError
            If required sections are missing
        """
        for section in self.REQUIRED_SECTIONS:
            if section not in self.config:
                raise ConfigError(f"Missing required section: {section}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value using dot notation.
        
        Parameters
        ----------
        key_path : str
            Path to value (e.g., 'data_acquisition.primary_source')
        default : Any, optional
            Default value if key not found
        
        Returns
        -------
        Any
            Config value or default
            
        Examples
        --------
        >>> value = loader.get('data_acquisition.primary_source')
        >>> value = loader.get('unknown.key', default='default_value')
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def create_template(output_path: str = 'master_config.json') -> None:
        """
        Create a template master_config.json file.
        
        Parameters
        ----------
        output_path : str
            Path where to save template config
        """
        template = {
            "pipeline_metadata": {
                "execution_timestamp": "2024-01-19T10:00:00Z",
                "pipeline_version": "1.0",
                "stage": "Stage_1_DataCleaning_FeatureEngineering"
            },
            "environment": {
                "python_version": "3.10.12",
                "numpy_version": "1.24.3",
                "pandas_version": "2.0.3",
                "scikit_learn_version": "1.2.2",
                "tensorflow_version": "2.13.0",
                "pywt_version": "1.4.1"
            },
            "random_seeds": {
                "numpy_seed": 42,
                "random_seed": 42,
                "tensorflow_seed": 42,
                "os_random_seed": 42,
                "documentation": "All seeds initialized for reproducibility"
            },
            "data_acquisition": {
                "primary_source": "iex_cloud",
                "fallback_source": "yfinance",
                "iex_api_token": "${IEX_CLOUD_TOKEN}",
                "lookback_years": 10,
                "min_trading_days": 2500,
                "retry_attempts": 3,
                "retry_backoff_factor": 2,
                "timeout_seconds": 30
            },
            "symbols": {
                "list": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
                "max_portfolio_size": 100,
                "supported_exchanges": ["NYSE", "NASDAQ", "AMEX"],
                "metadata_file": "symbols_registry.csv"
            },
            "data_cleaning": {
                "forward_fill_max_days": 2,
                "spike_detection_threshold": 0.20,
                "ohlc_correction_method": "linear_interpolation",
                "volume_zero_handling": "forward_fill",
                "quality_threshold_completeness": 0.99
            },
            "feature_engineering": {
                "tier1_enabled": True,
                "tier2_enabled": True,
                "tier3_enabled": True,
                "signal_processing_enabled": False,
                "tier2_features": [
                    "rsi_14", "macd_line", "macd_signal", "bollinger_bands",
                    "stochastic", "atr_14", "adx_14", "obv", "momentum", "volatility"
                ],
                "total_features_generated": 0,
                "total_symbols_with_features": 0
            },
            "data_splitting": {
                "methodology": "chronological_70_15_15",
                "train_ratio": 0.70,
                "val_ratio": 0.15,
                "test_ratio": 0.15,
                "temporal_integrity_verified": False
            },
            "preprocessing_artifacts": {
                "version": "v1",
                "artifacts_directory": "reproducibility_artifacts/",
                "scalers_saved": False,
                "kalman_params_saved": False,
                "feature_config_saved": False,
                "preprocessing_log_saved": False,
                "leakage_verification_status": "PENDING"
            },
            "baseline_models": {
                "random_walk": {"enabled": True},
                "arima_111": {"enabled": True},
                "linear_regression": {"enabled": True},
                "ridge_regression": {"enabled": True, "alpha_range": [0.001, 1000]},
                "historical_mean": {"enabled": True}
            },
            "ablation_studies": {
                "enabled": False,
                "ablation_plan": "ablation_plan.json",
                "planned_ablations": 0
            },
            "evaluation": {
                "metrics": ["mae", "rmse", "mape", "directional_accuracy", "sharpe_ratio", "ic"],
                "confidence_interval_method": "bootstrapping",
                "bootstrap_samples": 1000,
                "confidence_level": 0.95
            },
            "reporting": {
                "output_directory": "results/",
                "generate_visualizations": True,
                "visualization_dpi": 300,
                "generate_dashboard": False,
                "generate_model_card": True
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
