"""
Feature engineering orchestrator for coordinating feature computation across all tiers.

Manages initialization of all feature modules, sequential execution with dependency
management, dynamic feature selection, feature registry, manifest generation,
and feature grouping for ablation studies.
"""

import pandas as pd
import numpy as np
import logging
import json
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime

from features.base_features import FeatureModule


class FeatureGrouping(Enum):
    """
    Feature grouping for organizing features by tier and component type.
    
    Attributes
    ----------
    TIER1 : str
        Tier-1 features: basic returns and normalized prices
    TIER2 : str
        Tier-2 features: technical indicators and momentum
    TIER3 : str
        Tier-3 features: market regime and cross-asset context
    SIGNAL_PROCESSING : str
        Signal processing features: wavelet, SSA, Kalman
    """
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"
    SIGNAL_PROCESSING = "signal_processing"


@dataclass
class FeatureMetadata:
    """Metadata for a single feature in the registry."""
    name: str
    module_name: str
    grouping: FeatureGrouping
    description: str = ""
    lookback_window: Optional[int] = None
    causality_checked: bool = False
    computation_method: str = ""
    external_data_required: bool = False
    external_data_source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'module_name': self.module_name,
            'grouping': self.grouping.value,
            'description': self.description,
            'lookback_window': self.lookback_window,
            'causality_checked': self.causality_checked,
            'computation_method': self.computation_method,
            'external_data_required': self.external_data_required,
            'external_data_source': self.external_data_source,
        }


@dataclass
class FeatureManifest:
    """Manifest documenting all computed features for a symbol."""
    symbol: str
    manifest_timestamp: str
    features: List[FeatureMetadata] = field(default_factory=list)
    data_quality_checks: Dict[str, Any] = field(default_factory=dict)
    total_features: int = 0
    total_nan_values: int = 0
    causality_status: str = "PENDING"  # PENDING, VERIFIED, ISSUES
    
    def add_features(
        self,
        features_list: List[Dict[str, Any]],
        grouping: FeatureGrouping
    ) -> None:
        """
        Add features to manifest.
        
        Parameters
        ----------
        features_list : List[Dict]
            List of feature metadata dicts with keys:
            name, module_name, description, lookback_window, etc.
        grouping : FeatureGrouping
            Feature grouping (TIER1, TIER2, etc.)
        """
        for feature_dict in features_list:
            meta = FeatureMetadata(
                name=feature_dict.get('name'),
                module_name=feature_dict.get('module_name'),
                grouping=grouping,
                description=feature_dict.get('description', ''),
                lookback_window=feature_dict.get('lookback_window'),
                causality_checked=feature_dict.get('causality_checked', False),
                computation_method=feature_dict.get('computation_method', ''),
                external_data_required=feature_dict.get('external_data_required', False),
                external_data_source=feature_dict.get('external_data_source', '')
            )
            self.features.append(meta)
        
        self.total_features = len(self.features)
    
    def add_data_quality_info(self, quality_info: Dict[str, Any]) -> None:
        """
        Add data quality check results to manifest.
        
        Parameters
        ----------
        quality_info : Dict
            Data quality information (NaN counts, inf counts, validation results, etc.)
        """
        self.data_quality_checks.update(quality_info)
    
    def set_causality_status(self, status: str, issues: List[str] = None) -> None:
        """
        Update causality verification status.
        
        Parameters
        ----------
        status : str
            Status: VERIFIED, ISSUES, FAILED
        issues : List[str], optional
            List of causality issues if status is ISSUES or FAILED
        """
        self.causality_status = status
        if issues:
            self.data_quality_checks['causality_issues'] = issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'manifest_timestamp': self.manifest_timestamp,
            'total_features': self.total_features,
            'causality_status': self.causality_status,
            'data_quality_checks': self.data_quality_checks,
            'features': [f.to_dict() for f in self.features],
        }
    
    def save_to_json(self, output_path: str = None) -> str:
        """
        Save manifest to JSON file.
        
        Parameters
        ----------
        output_path : str, optional
            Path to write manifest; defaults to results/features_manifests/{symbol}_manifest.json
        
        Returns
        -------
        str
            Path where manifest was saved
        """
        if output_path is None:
            output_path = f"results/features_manifests/{self.symbol}_manifest.json"
        
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        
        return output_path


class FeatureRegistry:
    """
    Registry mapping feature names to modules and metadata.
    
    Tracks all available features and their properties, enabling dynamic
    feature selection and enabling/disabling for ablation studies.
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize FeatureRegistry.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.registry: Dict[str, Dict[str, Any]] = {}
    
    def register_feature(
        self,
        feature_name: str,
        module_name: str,
        grouping: FeatureGrouping,
        enabled: bool = True,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Register a feature in the registry.
        
        Parameters
        ----------
        feature_name : str
            Unique feature identifier
        module_name : str
            Name of feature module
        grouping : FeatureGrouping
            Feature grouping (TIER1, TIER2, etc.)
        enabled : bool
            Whether feature is enabled by default
        metadata : Dict, optional
            Additional metadata (description, lookback_window, etc.)
        """
        self.registry[feature_name] = {
            'module_name': module_name,
            'grouping': grouping,
            'enabled': enabled,
            'metadata': metadata or {}
        }
        self.logger.debug(f"Registered feature: {feature_name} ({grouping.value})")
    
    def enable_feature(self, feature_name: str) -> None:
        """Enable a feature."""
        if feature_name in self.registry:
            self.registry[feature_name]['enabled'] = True
            self.logger.info(f"Enabled feature: {feature_name}")
    
    def disable_feature(self, feature_name: str) -> None:
        """Disable a feature."""
        if feature_name in self.registry:
            self.registry[feature_name]['enabled'] = False
            self.logger.info(f"Disabled feature: {feature_name}")
    
    def enable_group(self, grouping: FeatureGrouping) -> None:
        """Enable all features in a group."""
        count = 0
        for feature_name, feature_info in self.registry.items():
            if feature_info['grouping'] == grouping:
                feature_info['enabled'] = True
                count += 1
        self.logger.info(f"Enabled {count} features in group {grouping.value}")
    
    def disable_group(self, grouping: FeatureGrouping) -> None:
        """Disable all features in a group."""
        count = 0
        for feature_name, feature_info in self.registry.items():
            if feature_info['grouping'] == grouping:
                feature_info['enabled'] = False
                count += 1
        self.logger.info(f"Disabled {count} features in group {grouping.value}")
    
    def get_enabled_features(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled features."""
        return {
            name: info for name, info in self.registry.items()
            if info['enabled']
        }
    
    def get_features_by_group(self, grouping: FeatureGrouping) -> Dict[str, Dict[str, Any]]:
        """Get all features in a specific group (regardless of enabled status)."""
        return {
            name: info for name, info in self.registry.items()
            if info['grouping'] == grouping
        }
    
    def get_enabled_features_by_group(
        self,
        grouping: FeatureGrouping
    ) -> Dict[str, Dict[str, Any]]:
        """Get enabled features in a specific group."""
        return {
            name: info for name, info in self.registry.items()
            if info['grouping'] == grouping and info['enabled']
        }


class FeatureOrchestrator:
    """
    Main orchestrator for feature engineering pipeline.
    
    Coordinates initialization of all feature modules, sequential execution
    with dependency management, feature grouping, dynamic selection,
    and manifest generation.
    
    Examples
    --------
    >>> orchestrator = FeatureOrchestrator(config=config)
    >>> features_df, manifest = orchestrator.compute_all_features(
    ...     symbol='AAPL',
    ...     ohlcv_df=cleaned_data,
    ...     fit_data=training_data
    ... )
    >>> print(f"Computed {manifest.total_features} features")
    
    >>> # Disable Tier-3 features for ablation study
    >>> orchestrator.registry.disable_group(FeatureGrouping.TIER3)
    >>> features_ablated_df, manifest = orchestrator.compute_all_features(...)
    """
    
    def __init__(
        self,
        config: Dict[str, Any] = None,
        logger: logging.Logger = None
    ):
        """
        Initialize FeatureOrchestrator.
        
        Parameters
        ----------
        config : Dict, optional
            Configuration dictionary with feature settings:
            - include_tier1: bool (default True)
            - include_tier2: bool (default True)
            - include_tier3: bool (default False)
            - include_signal_processing: bool (default False)
        logger : logging.Logger, optional
            Logger instance
        """
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        
        self.tier1_modules: List[FeatureModule] = []
        self.tier2_modules: List[FeatureModule] = []
        self.tier3_modules: List[FeatureModule] = []
        self.signal_modules: List[FeatureModule] = []
        
        self.registry = FeatureRegistry(logger=self.logger)
        
        self._initialize_modules()
    
    def _initialize_modules(self) -> None:
        """
        Initialize all feature modules based on configuration.
        
        Note: This is a placeholder. In production, this would instantiate
        actual feature module classes (ReturnsFeature, RSIFeature, etc.).
        For Phase 5, we're just setting up the infrastructure.
        """
        # TODO: Instantiate actual feature modules here
        # For now, this is a framework ready to accept modules
        self.logger.debug("Feature orchestrator initialized (modules pending)")
    
    def register_module(
        self,
        module: FeatureModule,
        grouping: FeatureGrouping
    ) -> None:
        """
        Register a feature module with the orchestrator.
        
        Parameters
        ----------
        module : FeatureModule
            Feature module instance inheriting from FeatureModule
        grouping : FeatureGrouping
            Feature grouping (TIER1, TIER2, etc.)
        """
        if grouping == FeatureGrouping.TIER1:
            self.tier1_modules.append(module)
        elif grouping == FeatureGrouping.TIER2:
            self.tier2_modules.append(module)
        elif grouping == FeatureGrouping.TIER3:
            self.tier3_modules.append(module)
        elif grouping == FeatureGrouping.SIGNAL_PROCESSING:
            self.signal_modules.append(module)
        
        # Register in feature registry
        self.registry.register_feature(
            feature_name=module.name,
            module_name=module.__class__.__name__,
            grouping=grouping,
            enabled=True,
            metadata={
                'description': module.__class__.__doc__ or '',
                'tier': module.tier,
            }
        )
        
        self.logger.debug(f"Registered module: {module.name} ({grouping.value})")
    
    def compute_all_features(
        self,
        symbol: str,
        ohlcv_df: pd.DataFrame,
        fit_data: Optional[pd.DataFrame] = None,
        market_context_df: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.DataFrame, FeatureManifest]:
        """
        Compute all configured features for a symbol.
        
        Executes feature modules in sequence (Tier-1 → Tier-2 → Tier-3 → Signal),
        aggregates results into single DataFrame aligned by date, and generates
        comprehensive manifest.
        
        Parameters
        ----------
        symbol : str
            Stock symbol being processed
        ohlcv_df : pd.DataFrame
            OHLCV DataFrame with DatetimeIndex
        fit_data : pd.DataFrame, optional
            Data to fit parameters on (typically training data).
            Used for modules like RSI smoothing to prevent data leakage.
        market_context_df : pd.DataFrame, optional
            Market context data (e.g., S&P 500) for cross-asset features
        
        Returns
        -------
        Tuple[pd.DataFrame, FeatureManifest]
            (features_df, manifest) where:
            - features_df: DataFrame with all computed features, indexed by date
            - manifest: Comprehensive feature documentation
        
        Examples
        --------
        >>> orchestrator = FeatureOrchestrator(config={'include_tier2': True})
        >>> features, manifest = orchestrator.compute_all_features(
        ...     symbol='AAPL',
        ...     ohlcv_df=cleaned_ohlcv,
        ...     fit_data=train_ohlcv
        ... )
        >>> print(f"Total features: {manifest.total_features}")
        """
        self.logger.info(f"Computing features for {symbol} ({len(ohlcv_df)} rows)")
        
        # Initialize output
        all_features = pd.DataFrame(index=ohlcv_df.index)
        manifest = FeatureManifest(
            symbol=symbol,
            manifest_timestamp=datetime.utcnow().isoformat() + 'Z'
        )
        
        # Compute features by tier/group
        modules_executed = []
        
        # Tier-1 features
        self.logger.debug("Computing Tier-1 features...")
        tier1_features_list = []
        for module in self.tier1_modules:
            if not self.registry.registry.get(module.name, {}).get('enabled', True):
                self.logger.debug(f"Skipping disabled Tier-1 module: {module.name}")
                continue
            
            try:
                features = module.compute(ohlcv_df, fit_data=fit_data)
                all_features = all_features.join(features)
                
                tier1_features_list.append({
                    'name': module.name,
                    'module_name': module.__class__.__name__,
                    'description': f"Tier-1 feature: {module.name}",
                    'computation_method': 'Rolling window calculation',
                })
                modules_executed.append((module.name, 1))
                self.logger.debug(f"  ✓ {module.name}")
            except Exception as e:
                self.logger.error(f"Error computing {module.name}: {e}")
                raise
        
        if tier1_features_list:
            manifest.add_features(tier1_features_list, FeatureGrouping.TIER1)
        
        # Tier-2 features
        if self.config.get('include_tier2', True):
            self.logger.debug("Computing Tier-2 features...")
            tier2_features_list = []
            for module in self.tier2_modules:
                if not self.registry.registry.get(module.name, {}).get('enabled', True):
                    self.logger.debug(f"Skipping disabled Tier-2 module: {module.name}")
                    continue
                
                try:
                    features = module.compute(ohlcv_df, fit_data=fit_data)
                    all_features = all_features.join(features)
                    
                    tier2_features_list.append({
                        'name': module.name,
                        'module_name': module.__class__.__name__,
                        'description': f"Tier-2 technical indicator: {module.name}",
                        'computation_method': 'Technical analysis',
                    })
                    modules_executed.append((module.name, 2))
                    self.logger.debug(f"  ✓ {module.name}")
                except Exception as e:
                    self.logger.error(f"Error computing {module.name}: {e}")
                    raise
            
            if tier2_features_list:
                manifest.add_features(tier2_features_list, FeatureGrouping.TIER2)
        
        # Tier-3 features
        if self.config.get('include_tier3', False):
            self.logger.debug("Computing Tier-3 features...")
            tier3_features_list = []
            for module in self.tier3_modules:
                if not self.registry.registry.get(module.name, {}).get('enabled', True):
                    self.logger.debug(f"Skipping disabled Tier-3 module: {module.name}")
                    continue
                
                try:
                    features = module.compute(ohlcv_df, fit_data=fit_data, market_context_df=market_context_df)
                    all_features = all_features.join(features)
                    
                    tier3_features_list.append({
                        'name': module.name,
                        'module_name': module.__class__.__name__,
                        'description': f"Tier-3 market context: {module.name}",
                        'computation_method': 'Cross-asset analysis',
                        'external_data_required': True,
                    })
                    modules_executed.append((module.name, 3))
                    self.logger.debug(f"  ✓ {module.name}")
                except Exception as e:
                    self.logger.error(f"Error computing {module.name}: {e}")
                    raise
            
            if tier3_features_list:
                manifest.add_features(tier3_features_list, FeatureGrouping.TIER3)
        
        # Signal processing features
        if self.config.get('include_signal_processing', False):
            self.logger.debug("Computing signal processing features...")
            signal_features_list = []
            for module in self.signal_modules:
                if not self.registry.registry.get(module.name, {}).get('enabled', True):
                    self.logger.debug(f"Skipping disabled signal module: {module.name}")
                    continue
                
                try:
                    features = module.compute(ohlcv_df, fit_data=fit_data)
                    all_features = all_features.join(features)
                    
                    signal_features_list.append({
                        'name': module.name,
                        'module_name': module.__class__.__name__,
                        'description': f"Signal processing: {module.name}",
                        'computation_method': 'Multi-scale decomposition',
                    })
                    modules_executed.append((module.name, 4))
                    self.logger.debug(f"  ✓ {module.name}")
                except Exception as e:
                    self.logger.error(f"Error computing {module.name}: {e}")
                    raise
            
            if signal_features_list:
                manifest.add_features(signal_features_list, FeatureGrouping.SIGNAL_PROCESSING)
        
        # Quality checks
        nan_total = all_features.isna().sum().sum()
        manifest.add_data_quality_info({
            'total_rows': len(all_features),
            'total_columns': len(all_features.columns),
            'total_nan_values': int(nan_total),
            'modules_executed': modules_executed,
        })
        
        self.logger.info(
            f"Feature computation complete for {symbol}: "
            f"{len(all_features.columns)} features, {nan_total} NaN values"
        )
        
        return all_features, manifest
    
    def get_enabled_features_info(self) -> Dict[str, Any]:
        """
        Get information about currently enabled features.
        
        Returns
        -------
        Dict[str, Any]
            Information grouped by FeatureGrouping
        """
        info = {}
        for grouping in FeatureGrouping:
            enabled = self.registry.get_enabled_features_by_group(grouping)
            info[grouping.value] = {
                'count': len(enabled),
                'features': list(enabled.keys())
            }
        return info
