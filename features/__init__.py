"""
Feature engineering module for stock forecasting system.

Provides base classes, validators, and orchestrators for computing
multi-tier features from OHLCV data.
"""

from features.base_features import FeatureModule
from features.feature_validator import (
    FeatureValidator,
    FeatureValidationResult,
    FeatureValidationReporter,
)
from features.feature_orchestrator import (
    FeatureOrchestrator,
    FeatureGrouping,
    FeatureManifest,
    FeatureMetadata,
    FeatureRegistry,
)

__all__ = [
    'FeatureModule',
    'FeatureValidator',
    'FeatureValidationResult',
    'FeatureValidationReporter',
    'FeatureOrchestrator',
    'FeatureGrouping',
    'FeatureManifest',
    'FeatureMetadata',
    'FeatureRegistry',
]
