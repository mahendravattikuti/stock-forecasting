"""
Main pipeline orchestrator for Stock Market Forecasting System.

Sequences all operations: acquisition → cleaning → validation → feature engineering →
splitting → preprocessing → baselines → evaluation, with comprehensive error handling,
logging, and reproducibility management.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

import numpy as np
import pandas as pd

from config.config_loader import ConfigLoader
from preprocessing.data_acquisition.acquisition_coordinator import AcquisitionCoordinator
from preprocessing.data_acquisition.iex_adapter import IEXAdapter
from preprocessing.data_acquisition.yfinance_adapter import YFinanceAdapter
from preprocessing.data_cleaning.cleaner import DataCleaner
from preprocessing.data_cleaning.validators import DataQualityValidator
from preprocessing.data_splitter import ChronologicalDataSplitter
from preprocessing.artifact_manager import TrainOnlyStandardScaler
from features.feature_orchestrator import FeatureOrchestrator
from baselines import BaselineManager
from evaluation.metrics import EvaluationMetrics
from utils.logging_config import StructuredLogger
from utils.error_handler import ErrorHandler, DataLeakageError, DataValidationError
from utils.leakage_detector import LeakageDetector
from utils.reproducibility import ReproducibilityManager
from reporting.report_generator import PipelineReportGenerator, PipelineExecutionContext


class StockForecastingPipeline:
    """
    Main orchestrator for the Stock Market Forecasting System pipeline.

    Coordinates all stages of the pipeline:
    1. Data Acquisition (IEX Cloud + yfinance fallback)
    2. Data Cleaning & Quality Validation
    3. Feature Engineering (Tier-1, Tier-2, Tier-3, Signal Processing)
    4. Chronological Data Splitting
    5. Preprocessing & Standardization (Train-only fitting)
    6. Baseline Model Training & Evaluation
    7. Report Generation & Artifact Management

    Attributes
    ----------
    config : Dict[str, Any]
        Configuration dictionary loaded from master_config.json
    logger : logging.Logger
        Structured logger instance
    error_handler : ErrorHandler
        Error tracking and recovery manager
    leakage_detector : LeakageDetector
        Data leakage detection and verification
    reproducibility_manager : ReproducibilityManager
        Reproducibility seed and artifact tracking

    Examples
    --------
    >>> pipeline = StockForecastingPipeline(config_path='master_config.json')
    >>> results = pipeline.run(symbols=['AAPL', 'MSFT', 'GOOGL'])
    >>> print(f"Pipeline execution completed")
    """

    def __init__(self, config_path: str = 'master_config.json'):
        """
        Initialize StockForecastingPipeline.

        Parameters
        ----------
        config_path : str
            Path to master_config.json file

        Raises
        ------
        ConfigurationError
            If configuration cannot be loaded or validated
        """
        # Load configuration
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load_config()
        self.config_loader.validate_schema()
        self.config_loader.override_from_env()

        # Initialize logging
        base_logger = logging.getLogger('StockForecastingPipeline')
        if not base_logger.handlers:
            # Configure only if not already configured
            from utils.logging_config import configure_logging
            configure_logging(log_dir='logs/')
            base_logger = logging.getLogger('StockForecastingPipeline')
        
        structured_logger = StructuredLogger(base_logger)
        self.logger = structured_logger.logger

        # Initialize core managers
        self.error_handler = ErrorHandler(logger=self.logger)
        self.leakage_detector = LeakageDetector(logger=self.logger)
        self.reproducibility_manager = ReproducibilityManager(
            seed=self.config.get('random_seeds', {}).get('numpy_seed', 42)
        )

        # Initialize component managers (will be created in run())
        self.acquisition_coordinator: Optional[AcquisitionCoordinator] = None
        self.data_cleaner: Optional[DataCleaner] = None
        self.quality_validator: Optional[DataQualityValidator] = None
        self.feature_orchestrator: Optional[FeatureOrchestrator] = None
        self.data_splitter: Optional[ChronologicalDataSplitter] = None
        self.baseline_manager: Optional[BaselineManager] = None
        self.report_generator: Optional[PipelineReportGenerator] = None

        # Execution state
        self.execution_start_time: Optional[datetime] = None
        self.execution_end_time: Optional[datetime] = None
        self.symbols_processed: Set[str] = set()
        self.symbols_failed: Set[str] = set()

        # Result aggregators
        self.cleaned_data: Dict[str, pd.DataFrame] = {}
        self.features_data: Dict[str, pd.DataFrame] = {}
        self.features_manifests: Dict[str, Dict[str, Any]] = {}
        self.baseline_results: Optional[Dict[str, Any]] = None
        self.splits_metadata: Optional[Dict[str, Any]] = None

        self.logger.info(
            "StockForecastingPipeline initialized",
            extra={'config_path': config_path}
        )

    def run(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute the complete pipeline for specified symbols.

        Orchestrates:
        1. Initialize reproducibility (seeds, logging)
        2. Data acquisition for all symbols
        3. Data cleaning with error recovery
        4. Data quality validation
        5. Feature engineering (all tiers)
        6. Chronological data splitting
        7. Preprocessing/standardization
        8. Baseline model training and evaluation
        9. Report generation
        10. Artifact management

        Parameters
        ----------
        symbols : List[str], optional
            List of stock symbols to process. If None, uses config['symbols']['list']

        Returns
        -------
        Dict[str, Any]
            Pipeline execution results with summary statistics and paths to outputs

        Raises
        ------
        StockForecastingError
            On critical unrecoverable errors (logs error_summary.json if applicable)
        """
        self.execution_start_time = datetime.now(timezone.utc)
        self.logger.info(
            "Pipeline execution started",
            extra={'timestamp': self.execution_start_time.isoformat()}
        )

        try:
            # === PHASE 1: Initialize Reproducibility ===
            self._initialize_reproducibility()

            # === PHASE 2: Configure Components ===
            self._configure_components()

            # === PHASE 3: Determine Symbols ===
            symbols = symbols or self.config.get('symbols', {}).get('list', [])
            if not symbols:
                raise ValueError("No symbols specified in config or arguments")
            self.logger.info(f"Processing {len(symbols)} symbols", extra={'symbols': symbols})

            # === PHASE 4: Data Acquisition ===
            raw_data = self._acquire_data(symbols)
            successfully_acquired = set(raw_data.keys())
            self.logger.info(
                f"Data acquisition complete: {len(successfully_acquired)}/{len(symbols)}",
                extra={'acquired': list(successfully_acquired)}
            )

            # === PHASE 5: Data Cleaning ===
            self.cleaned_data = self._clean_data(raw_data)
            successfully_cleaned = set(self.cleaned_data.keys())
            self.logger.info(
                f"Data cleaning complete: {len(successfully_cleaned)}/{len(successfully_acquired)}",
                extra={'cleaned': list(successfully_cleaned)}
            )

            # === PHASE 6: Data Quality Validation ===
            self._validate_data_quality(self.cleaned_data)

            # === PHASE 7: Feature Engineering ===
            self.features_data, self.features_manifests = self._compute_features(self.cleaned_data)
            self.logger.info(
                f"Feature engineering complete: {len(self.features_data)} symbols",
                extra={'symbols_with_features': list(self.features_data.keys())}
            )

            # === PHASE 8: Data Splitting ===
            splits = self._split_data(self.features_data)
            self.splits_metadata = splits['metadata']

            # === PHASE 9: Preprocessing & Standardization ===
            processed_splits = self._preprocess_splits(splits['data'])

            # === PHASE 10: Baseline Training & Evaluation ===
            self.baseline_results = self._train_baselines(processed_splits)

            # === PHASE 11: Data Leakage Detection ===
            self._verify_no_data_leakage(splits['data'], processed_splits)

            # === PHASE 12: Generate Reports ===
            reports = self._generate_reports()

            # === PHASE 13: Save Artifacts ===
            self._save_artifacts()

            # === Execution Complete ===
            self.execution_end_time = datetime.now(timezone.utc)
            duration = (self.execution_end_time - self.execution_start_time).total_seconds()

            results = {
                'status': 'SUCCESS',
                'execution_timestamp': self.execution_start_time.isoformat(),
                'duration_seconds': duration,
                'symbols_requested': len(symbols),
                'symbols_processed': len(self.symbols_processed),
                'symbols_failed': len(self.symbols_failed),
                'data_acquisition': {
                    'symbols_acquired': len(successfully_acquired),
                    'symbols_failed': len(symbols) - len(successfully_acquired)
                },
                'data_cleaning': {
                    'symbols_cleaned': len(successfully_cleaned),
                    'symbols_failed': len(successfully_acquired) - len(successfully_cleaned)
                },
                'features': {
                    'symbols_with_features': len(self.features_data),
                    'total_features_per_symbol': len(self.features_data[list(self.features_data.keys())[0]].columns) if self.features_data else 0
                },
                'splits': {
                    'train_rows': self.splits_metadata.get('splits', {}).get('train', {}).get('row_count', 0),
                    'validation_rows': self.splits_metadata.get('splits', {}).get('validation', {}).get('row_count', 0),
                    'test_rows': self.splits_metadata.get('splits', {}).get('test', {}).get('row_count', 0)
                },
                'baselines': {
                    'models_trained': len(self.baseline_results.get('models', {})) if self.baseline_results else 0,
                    'best_model': self._get_best_baseline_model()
                },
                'reports_generated': reports,
                'errors': {
                    'total_errors': len(self.error_handler.errors),
                    'critical_errors': len([e for e in self.error_handler.errors if e.severity == 'CRITICAL']),
                    'has_critical_errors': self.error_handler.has_critical_errors()
                }
            }

            self.logger.info(
                "Pipeline execution completed successfully",
                extra={
                    'duration_seconds': duration,
                    'symbols_processed': len(self.symbols_processed),
                    'errors': len(self.error_handler.errors)
                }
            )

            return results

        except Exception as e:
            self.execution_end_time = datetime.now(timezone.utc)
            self.error_handler.log_error(
                error=e,
                component='pipeline.orchestration',
                context={'phase': 'unknown'},
                symbol=None
            )
            self.logger.error(
                f"Pipeline execution failed: {str(e)}",
                extra={'error': str(e), 'error_type': type(e).__name__}
            )
            
            # Generate error summary
            self._generate_error_summary()
            
            raise

    def _initialize_reproducibility(self) -> None:
        """Initialize reproducibility: seeds, environment variables, logging."""
        self.logger.info("Initializing reproducibility...")
        
        try:
            seeds_log = self.reproducibility_manager.initialize_seeds()
            self.logger.debug(f"Seeds initialized: {seeds_log}")
            
            # Create artifacts directory
            artifacts_dir = Path(self.config.get('preprocessing_artifacts', {}).get('artifacts_directory', 'reproducibility_artifacts/'))
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Save seeds log
            self.reproducibility_manager.save_seeds_log(
                str(artifacts_dir / 'v1_seeds.json')
            )
            
            self.logger.info("Reproducibility initialization complete")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                component='reproducibility',
                context={'action': 'initialize_seeds'},
                symbol=None
            )
            raise

    def _configure_components(self) -> None:
        """Configure all pipeline components."""
        self.logger.info("Configuring pipeline components...")
        
        try:
            # Data acquisition
            iex_token = self.config.get('data_acquisition', {}).get('iex_api_token', '')
            primary_adapter = IEXAdapter(api_token=iex_token) if iex_token else None
            fallback_adapter = YFinanceAdapter()
            
            if primary_adapter is None:
                self.logger.warning("IEX Cloud API token not configured; using yfinance only")
                primary_adapter = fallback_adapter
            
            self.acquisition_coordinator = AcquisitionCoordinator(
                primary_adapter=primary_adapter,
                fallback_adapter=fallback_adapter,
                logger=self.logger
            )
            
            # Data cleaning
            cleaning_config = self.config.get('data_cleaning', {})
            self.data_cleaner = DataCleaner(
                max_forward_fill_days=cleaning_config.get('max_forward_fill_days', 2),
                spike_threshold=cleaning_config.get('spike_threshold', 0.20),
                min_completeness=cleaning_config.get('min_completeness', 0.99),
                apply_adjustments=cleaning_config.get('apply_adjustments', True),
                logger=self.logger
            )
            self.quality_validator = DataQualityValidator(
                min_trading_days=cleaning_config.get('min_trading_days', 2500),
                min_completeness=cleaning_config.get('min_completeness', 0.99),
                logger=self.logger
            )
            
            # Feature engineering
            feature_config = self.config.get('feature_engineering', {})
            self.feature_orchestrator = FeatureOrchestrator(config=feature_config, logger=self.logger)
            
            # Data splitting
            split_config = self.config.get('data_splitting', {})
            self.data_splitter = ChronologicalDataSplitter(
                train_ratio=split_config.get('train_ratio', 0.70),
                val_ratio=split_config.get('val_ratio', 0.15),
                test_ratio=split_config.get('test_ratio', 0.15),
                logger=self.logger
            )
            
            # Baseline manager
            self.baseline_manager = BaselineManager(
                model_dir='results/baseline_models',
                config=self.config.get('baseline_models', {}),
                logger=self.logger
            )
            
            # Report generator
            self.report_generator = PipelineReportGenerator(logger=self.logger)
            
            self.logger.info("Component configuration complete")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                component='configuration',
                context={'action': 'configure_components'},
                symbol=None
            )
            raise

    def _acquire_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Acquire raw OHLCV data for all symbols."""
        self.logger.info(f"Starting data acquisition for {len(symbols)} symbols...")
        
        raw_data = {}
        
        # Get date range from config
        data_config = self.config.get('data_acquisition', {})
        start_date = data_config.get('start_date', '2014-01-01')
        end_date = data_config.get('end_date', '2024-10-12')
        min_trading_days = data_config.get('min_trading_days', 2500)
        
        for symbol in symbols:
            try:
                self.logger.debug(f"Acquiring data for {symbol}...")
                df, source = self.acquisition_coordinator.fetch_with_fallback(
                    symbol, 
                    start_date=start_date,
                    end_date=end_date,
                    min_trading_days=min_trading_days
                )
                
                if df is not None and len(df) > 0:
                    raw_data[symbol] = df
                    self.symbols_processed.add(symbol)
                    self.logger.debug(f"  ✓ {symbol}: {len(df)} rows from {source}")
                else:
                    self.logger.warning(f"  ✗ {symbol}: No data returned")
                    self.symbols_failed.add(symbol)
                    
            except Exception as e:
                self.error_handler.log_error(
                    error=e,
                    component='data_acquisition',
                    context={'symbol': symbol},
                    symbol=symbol
                )
                self.logger.error(f"  ✗ {symbol}: {str(e)}")
                self.symbols_failed.add(symbol)
        
        self.logger.info(f"Data acquisition complete: {len(raw_data)}/{len(symbols)} symbols")
        return raw_data

    def _clean_data(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Clean OHLCV data for all symbols."""
        self.logger.info(f"Starting data cleaning for {len(raw_data)} symbols...")
        
        cleaned_data = {}
        
        for symbol, df in raw_data.items():
            try:
                self.logger.debug(f"Cleaning {symbol}...")
                cleaned_df, cleaning_report = self.data_cleaner.clean_symbol(symbol, df)
                
                if cleaned_df is not None and len(cleaned_df) > 0:
                    cleaned_data[symbol] = cleaned_df
                    self.logger.debug(f"  ✓ {symbol}: {len(cleaned_df)} rows (from {len(df)})")
                    
                    # Save cleaning report
                    reports_dir = Path('results/cleaning_reports')
                    reports_dir.mkdir(parents=True, exist_ok=True)
                    report_path = reports_dir / f'{symbol}_cleaning_report.json'
                    with open(report_path, 'w') as f:
                        json.dump(cleaning_report.to_dict(), f, indent=2, default=str)
                else:
                    self.logger.warning(f"  ✗ {symbol}: No data after cleaning")
                    
            except Exception as e:
                self.error_handler.log_error(
                    error=e,
                    component='data_cleaning',
                    context={'symbol': symbol},
                    symbol=symbol
                )
                self.logger.error(f"  ✗ {symbol}: {str(e)}")
        
        self.logger.info(f"Data cleaning complete: {len(cleaned_data)}/{len(raw_data)} symbols")
        return cleaned_data

    def _validate_data_quality(self, cleaned_data: Dict[str, pd.DataFrame]) -> None:
        """Validate data quality for all cleaned symbols."""
        self.logger.info(f"Starting data quality validation for {len(cleaned_data)} symbols...")
        
        for symbol, df in cleaned_data.items():
            try:
                self.logger.debug(f"Validating {symbol}...")
                quality_result = self.quality_validator.validate_quality(df)
                
                if quality_result.get('overall_pass', False):
                    self.logger.debug(f"  ✓ {symbol}: Quality validation passed")
                else:
                    self.logger.warning(f"  ⚠ {symbol}: Validation warnings: {quality_result}")
                    
            except Exception as e:
                self.error_handler.log_error(
                    error=e,
                    component='data_validation',
                    context={'symbol': symbol},
                    symbol=symbol
                )
                self.logger.error(f"  ✗ {symbol}: {str(e)}")
        
        self.logger.info("Data quality validation complete")

    def _compute_features(self, cleaned_data: Dict[str, pd.DataFrame]) -> tuple[Dict[str, pd.DataFrame], Dict[str, Dict]]:
        """Compute all features for all symbols."""
        self.logger.info(f"Starting feature engineering for {len(cleaned_data)} symbols...")
        
        features_data = {}
        features_manifests = {}
        
        for symbol, df in cleaned_data.items():
            try:
                self.logger.debug(f"Computing features for {symbol}...")
                features_df, manifest = self.feature_orchestrator.compute_all_features(
                    symbol=symbol,
                    ohlcv_df=df,
                    fit_data=df  # Use same data for fitting (no leakage in initial features)
                )
                
                features_data[symbol] = features_df
                features_manifests[symbol] = manifest.to_dict() if hasattr(manifest, 'to_dict') else manifest
                self.logger.debug(f"  ✓ {symbol}: {len(features_df.columns)} features")
                
                # Save manifest
                manifests_dir = Path('results/features_manifests')
                manifests_dir.mkdir(parents=True, exist_ok=True)
                manifest_path = manifests_dir / f'{symbol}_features_manifest.json'
                with open(manifest_path, 'w') as f:
                    json.dump(features_manifests[symbol], f, indent=2, default=str)
                    
            except Exception as e:
                self.error_handler.log_error(
                    error=e,
                    component='feature_engineering',
                    context={'symbol': symbol},
                    symbol=symbol
                )
                self.logger.error(f"  ✗ {symbol}: {str(e)}")
        
        self.logger.info(f"Feature engineering complete: {len(features_data)}/{len(cleaned_data)} symbols")
        return features_data, features_manifests

    def _split_data(self, features_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Perform chronological train/val/test split."""
        self.logger.info("Performing chronological data split...")
        
        try:
            # Combine all features data
            combined_data = {
                symbol: df for symbol, df in features_data.items()
            }
            
            # Perform split
            splits, metadata = self.data_splitter.split(combined_data)
            
            # Verify no leakage
            self.data_splitter.verify_no_leakage(splits)
            
            # Save metadata
            metadata_dir = Path('results/splits_metadata')
            metadata_dir.mkdir(parents=True, exist_ok=True)
            metadata_path = metadata_dir / 'split_metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            self.logger.info(
                "Data split complete",
                extra={
                    'train_rows': metadata['splits']['train']['row_count'],
                    'validation_rows': metadata['splits']['validation']['row_count'],
                    'test_rows': metadata['splits']['test']['row_count']
                }
            )
            
            return {'data': splits, 'metadata': metadata}
            
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                component='data_splitting',
                context={'action': 'split_data'},
                symbol=None
            )
            raise

    def _preprocess_splits(self, splits: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Preprocess splits: standardize using train-only fitting."""
        self.logger.info("Preprocessing splits with train-only standardization...")
        
        try:
            processed_splits = {}
            scaler = TrainOnlyStandardScaler(logger=self.logger)
            
            # Fit on training data only
            self.logger.debug("Fitting scaler on training data...")
            # Get first training symbol to fit
            first_train_symbol = list(splits['train'].keys())[0] if splits['train'] else None
            if first_train_symbol:
                first_train_df = splits['train'][first_train_symbol]
                scaler.fit(first_train_df, split_name='train')
            
            # Apply to all splits
            for split_name in ['train', 'validation', 'test']:
                processed_splits[split_name] = {}
                self.logger.debug(f"Scaling {split_name} data...")
                
                for symbol, df in splits.get(split_name, {}).items():
                    # Apply fitted scaler without refitting
                    if split_name == 'train':
                        scaled_df = scaler.fit_transform(df, split_name=split_name)
                    else:
                        scaled_df = scaler.transform(df, split_name=split_name)
                    processed_splits[split_name][symbol] = scaled_df
            
            # Save scaler
            artifacts_dir = Path(self.config.get('preprocessing_artifacts', {}).get('artifacts_directory', 'reproducibility_artifacts/'))
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            scaler_path = artifacts_dir / 'v1_scalers.joblib'
            import joblib
            joblib.dump(scaler, scaler_path)
            
            self.logger.info("Preprocessing complete")
            return processed_splits
            
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                component='preprocessing',
                context={'action': 'preprocess_splits'},
                symbol=None
            )
            raise

    def _train_baselines(self, processed_splits: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, Any]:
        """Train and evaluate baseline models."""
        self.logger.info("Training baseline models...")
        
        try:
            # Prepare data for baseline training
            # For simplicity, aggregate across symbols (in practice, might train per-symbol)
            
            train_data_list = []
            val_data_list = []
            test_data_list = []
            
            for symbol in processed_splits['train'].keys():
                if symbol in processed_splits['validation'] and symbol in processed_splits['test']:
                    train_data_list.append(processed_splits['train'][symbol])
                    val_data_list.append(processed_splits['validation'][symbol])
                    test_data_list.append(processed_splits['test'][symbol])
            
            if not train_data_list:
                self.logger.warning("No complete train/val/test data found for baselines")
                return {}
            
            # Concatenate across symbols
            X_train = pd.concat(train_data_list, ignore_index=False)
            X_val = pd.concat(val_data_list, ignore_index=False)
            X_test = pd.concat(test_data_list, ignore_index=False)
            
            # Use first feature as target (simple_return)
            y_train = X_train.iloc[:, 0] if len(X_train.columns) > 0 else None
            y_val = X_val.iloc[:, 0] if len(X_val.columns) > 0 else None
            y_test = X_test.iloc[:, 0] if len(X_test.columns) > 0 else None
            
            if y_train is None or len(y_train) == 0:
                self.logger.warning("No target data for baseline training")
                return {}
            
            # Train all baselines
            results = self.baseline_manager.train_and_evaluate_all(
                y_train=y_train,
                y_validation=y_val,
                y_test=y_test,
                X_train=X_train,
                X_validation=X_val,
                X_test=X_test,
                X_tier1_train=X_train,
                X_tier1_validation=X_val,
                X_tier1_test=X_test,
                close_train=X_train.iloc[:, -1] if len(X_train.columns) > 0 else None,
                close_validation=X_val.iloc[:, -1] if len(X_val.columns) > 0 else None,
                close_test=X_test.iloc[:, -1] if len(X_test.columns) > 0 else None,
                results_path='results/reports/baseline_results.json'
            )
            
            self.logger.info(
                "Baseline training complete",
                extra={'models_trained': len(results.get('models', {}))}
            )
            
            return results
            
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                component='baselines',
                context={'action': 'train_and_evaluate_all'},
                symbol=None
            )
            self.logger.error(f"Baseline training failed: {str(e)}")
            return {}

    def _verify_no_data_leakage(self, splits: Dict[str, Dict[str, pd.DataFrame]], 
                                processed_splits: Dict[str, Dict[str, pd.DataFrame]]) -> None:
        """Verify no data leakage using LeakageDetector."""
        self.logger.info("Verifying data leakage...")
        
        try:
            # Check split integrity
            train_dates = set()
            val_dates = set()
            test_dates = set()
            
            for symbol, df in splits['train'].items():
                train_dates.update(df.index)
            for symbol, df in splits['validation'].items():
                val_dates.update(df.index)
            for symbol, df in splits['test'].items():
                test_dates.update(df.index)
            
            # Verify no overlap
            if train_dates & val_dates:
                raise DataLeakageError("Train/Validation date overlap detected")
            if val_dates & test_dates:
                raise DataLeakageError("Validation/Test date overlap detected")
            if train_dates & test_dates:
                raise DataLeakageError("Train/Test date overlap detected")
            
            self.logger.info("Data leakage verification passed")
            
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                component='leakage_detection',
                context={'action': 'verify_no_data_leakage'},
                symbol=None
            )
            raise

    def _generate_reports(self) -> Dict[str, str]:
        """Generate pipeline reports."""
        self.logger.info("Generating reports...")
        
        try:
            reports = {}
            
            # Create execution context
            context = PipelineExecutionContext(
                execution_timestamp=self.execution_start_time.isoformat(),
                total_symbols_requested=len(self.symbols_processed) + len(self.symbols_failed),
                total_symbols_processed=len(self.symbols_processed),
                total_symbols_failed=len(self.symbols_failed),
                data_acquisition_stats={
                    'symbols_acquired': len(self.cleaned_data) + len(self.symbols_failed),
                    'symbols_failed': len(self.symbols_failed)
                },
                data_cleaning_stats={
                    'symbols_cleaned': len(self.cleaned_data),
                    'symbols_failed': len(self.symbols_processed) - len(self.cleaned_data)
                },
                features_stats={
                    'total_features': len(self.features_data[list(self.features_data.keys())[0]].columns) if self.features_data else 0,
                    'symbols_with_features': len(self.features_data)
                },
                splits_metadata=self.splits_metadata,
                baseline_results=self.baseline_results,
                error_count=len(self.error_handler.errors),
                error_summary=self.error_handler.generate_error_summary() if self.error_handler.errors else None
            )
            
            # Generate pipeline report
            report_content = self.report_generator.generate_pipeline_report(context)
            report_path = self.report_generator.save_report(
                report_content,
                'results/reports/pipeline_execution_report.md'
            )
            reports['pipeline_report'] = report_path
            
            self.logger.info(f"Pipeline report saved: {report_path}")
            
            return reports
            
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                component='reporting',
                context={'action': 'generate_reports'},
                symbol=None
            )
            self.logger.error(f"Report generation failed: {str(e)}")
            return {}

    def _save_artifacts(self) -> None:
        """Save all pipeline artifacts and metadata."""
        self.logger.info("Saving pipeline artifacts...")
        
        try:
            artifacts_dir = Path(self.config.get('preprocessing_artifacts', {}).get('artifacts_directory', 'reproducibility_artifacts/'))
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            config_path = artifacts_dir / 'v1_config.json'
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2, default=str)
            
            # Save execution metadata
            execution_metadata = {
                'execution_start': self.execution_start_time.isoformat(),
                'execution_end': self.execution_end_time.isoformat(),
                'duration_seconds': (self.execution_end_time - self.execution_start_time).total_seconds(),
                'symbols_processed': list(self.symbols_processed),
                'symbols_failed': list(self.symbols_failed),
                'pipeline_version': '1.0'
            }
            metadata_path = artifacts_dir / 'v1_execution_metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(execution_metadata, f, indent=2, default=str)
            
            self.logger.info("Artifacts saved successfully")
            
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                component='artifact_management',
                context={'action': 'save_artifacts'},
                symbol=None
            )
            self.logger.error(f"Artifact saving failed: {str(e)}")

    def _generate_error_summary(self) -> None:
        """Generate error summary if critical errors occurred."""
        try:
            if self.error_handler.has_critical_errors():
                error_summary = self.error_handler.generate_error_summary(
                    output_file='results/reports/error_summary.json'
                )
                self.logger.warning(
                    f"Error summary generated with {len(self.error_handler.errors)} errors"
                )
        except Exception as e:
            self.logger.error(f"Failed to generate error summary: {str(e)}")

    def _get_best_baseline_model(self) -> Optional[str]:
        """Get best performing baseline model."""
        if not self.baseline_results or 'models' not in self.baseline_results:
            return None
        
        best_model = None
        best_mae = float('inf')
        
        for model_name, model_results in self.baseline_results['models'].items():
            test_mae = model_results.get('test', {}).get('mae', float('inf'))
            if test_mae < best_mae:
                best_mae = test_mae
                best_model = model_name
        
        return best_model


if __name__ == '__main__':
    # Example usage
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'master_config.json'
    
    pipeline = StockForecastingPipeline(config_path=config_path)
    results = pipeline.run()
    
    print("\n" + "="*80)
    print("PIPELINE EXECUTION RESULTS")
    print("="*80)
    print(json.dumps(results, indent=2, default=str))
