"""
Test suite for Phase 5 Feature Engineering Infrastructure.

Verifies that:
- Base FeatureModule class works correctly
- Feature validator detects issues
- Feature orchestrator initializes and manages features
- Feature grouping and manifest generation work
"""

import pytest
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

from features.base_features import FeatureModule
from features.feature_validator import (
    FeatureValidator,
    FeatureValidationResult,
)
from features.feature_orchestrator import (
    FeatureOrchestrator,
    FeatureGrouping,
    FeatureManifest,
    FeatureMetadata,
    FeatureRegistry,
)


# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestFeatureModule:
    """Test the base FeatureModule class."""
    
    def test_feature_module_initialization(self):
        """Test FeatureModule initialization."""
        
        class SimpleFeature(FeatureModule):
            def compute(self, df, fit_data=None):
                return pd.DataFrame(index=df.index)
            
            def validate(self, features):
                return True, []
        
        feature = SimpleFeature(
            name="test_feature",
            tier=1,
            config={"param": "value"}
        )
        
        assert feature.name == "test_feature"
        assert feature.tier == 1
        assert feature.config == {"param": "value"}
        assert feature.logger is not None
    
    def test_feature_module_validate_input_dataframe(self):
        """Test input DataFrame validation."""
        
        class SimpleFeature(FeatureModule):
            def compute(self, df, fit_data=None):
                return pd.DataFrame(index=df.index)
            
            def validate(self, features):
                return True, []
        
        feature = SimpleFeature(name="test", tier=1)
        
        # Valid DataFrame
        dates = pd.date_range('2020-01-01', periods=100)
        valid_df = pd.DataFrame({
            'Open': np.random.rand(100),
            'High': np.random.rand(100),
            'Low': np.random.rand(100),
            'Close': np.random.rand(100),
            'Volume': np.random.randint(1000000, 10000000, 100),
        }, index=dates)
        
        is_valid, errors = feature._validate_input_dataframe(valid_df)
        assert is_valid
        assert len(errors) == 0
        
        # Invalid DataFrame (missing column)
        invalid_df = pd.DataFrame({
            'Close': np.random.rand(100),
            'Volume': np.random.randint(1000000, 10000000, 100),
        }, index=dates)
        
        is_valid, errors = feature._validate_input_dataframe(invalid_df)
        assert not is_valid
        assert len(errors) > 0
        assert "Missing required columns" in errors[0]
    
    def test_feature_module_nan_and_inf_check(self):
        """Test NaN and infinite value checking."""
        
        class SimpleFeature(FeatureModule):
            def compute(self, df, fit_data=None):
                return pd.DataFrame(index=df.index)
            
            def validate(self, features):
                return True, []
        
        feature = SimpleFeature(name="test", tier=1)
        
        # DataFrame with expected NaN (first 20 rows)
        dates = pd.date_range('2020-01-01', periods=100)
        clean_df = pd.DataFrame({
            'feature1': [np.nan] * 20 + list(range(80)),
            'feature2': list(range(100)),
        }, index=dates)
        
        is_valid, errors = feature._check_for_nan_and_inf(clean_df, expected_nan_rows=20)
        assert is_valid
        assert len(errors) == 0
        
        # DataFrame with unexpected NaN
        bad_df = pd.DataFrame({
            'feature1': [np.nan] * 30 + list(range(70)),  # 30 NaN, but only 20 expected
            'feature2': list(range(100)),
        }, index=dates)
        
        is_valid, errors = feature._check_for_nan_and_inf(bad_df, expected_nan_rows=20)
        assert not is_valid
        assert len(errors) > 0
        
        # DataFrame with infinite values
        inf_df = pd.DataFrame({
            'feature1': [np.nan] * 20 + [np.inf] + list(range(79)),
            'feature2': list(range(100)),
        }, index=dates)
        
        is_valid, errors = feature._check_for_nan_and_inf(inf_df, expected_nan_rows=20)
        assert not is_valid
        assert any("infinite" in err.lower() for err in errors)


class TestFeatureValidator:
    """Test the FeatureValidator class."""
    
    def test_feature_validator_initialization(self):
        """Test FeatureValidator initialization."""
        validator = FeatureValidator(logger=logger)
        assert validator.logger is not None
    
    def test_validate_features_with_rsi(self):
        """Test feature validation with RSI-like data."""
        validator = FeatureValidator(logger=logger)
        
        dates = pd.date_range('2020-01-01', periods=100)
        features_df = pd.DataFrame({
            'rsi_14': [np.nan] * 14 + [50.0] * 86,  # Valid RSI in [0, 100]
            'momentum': [np.nan] * 20 + list(np.linspace(-0.1, 0.1, 80)),
        }, index=dates)
        
        result = validator.validate_features(features_df, symbol='TEST', expected_nan_rows=20)
        
        assert isinstance(result, FeatureValidationResult)
        assert result.symbol == 'TEST'
        assert result.is_valid
        assert len(result.error_messages) == 0
    
    def test_validate_features_with_out_of_range_values(self):
        """Test detection of out-of-range values."""
        validator = FeatureValidator(logger=logger)
        
        dates = pd.date_range('2020-01-01', periods=100)
        features_df = pd.DataFrame({
            'rsi_14': [np.nan] * 14 + [50.0] * 50 + [105.0] * 36,  # 105 > 100!
        }, index=dates)
        
        result = validator.validate_features(features_df, symbol='TEST', expected_nan_rows=14)
        
        assert not result.is_valid
        assert any('RSI' in msg for msg in result.error_messages)
    
    def test_validate_features_with_unexpected_nan(self):
        """Test detection of unexpected NaN values."""
        validator = FeatureValidator(logger=logger)
        
        dates = pd.date_range('2020-01-01', periods=100)
        features_df = pd.DataFrame({
            'feature1': [np.nan] * 50 + list(range(50)),  # 50 NaN, but only 20 expected
        }, index=dates)
        
        result = validator.validate_features(features_df, symbol='TEST', expected_nan_rows=20)
        
        assert not result.is_valid
        assert any('unexpected NaN' in msg.lower() for msg in result.error_messages)


class TestFeatureRegistry:
    """Test the FeatureRegistry class."""
    
    def test_register_feature(self):
        """Test feature registration."""
        registry = FeatureRegistry(logger=logger)
        
        registry.register_feature(
            feature_name='test_feature',
            module_name='TestModule',
            grouping=FeatureGrouping.TIER1,
            enabled=True,
            metadata={'description': 'Test feature'}
        )
        
        assert 'test_feature' in registry.registry
        assert registry.registry['test_feature']['grouping'] == FeatureGrouping.TIER1
        assert registry.registry['test_feature']['enabled']
    
    def test_enable_disable_feature(self):
        """Test enabling and disabling features."""
        registry = FeatureRegistry(logger=logger)
        
        registry.register_feature('feat1', 'Mod1', FeatureGrouping.TIER1, enabled=True)
        registry.register_feature('feat2', 'Mod2', FeatureGrouping.TIER1, enabled=True)
        
        # Disable one feature
        registry.disable_feature('feat1')
        assert not registry.registry['feat1']['enabled']
        assert registry.registry['feat2']['enabled']
        
        # Get enabled features
        enabled = registry.get_enabled_features()
        assert 'feat1' not in enabled
        assert 'feat2' in enabled
    
    def test_enable_disable_group(self):
        """Test enabling and disabling feature groups."""
        registry = FeatureRegistry(logger=logger)
        
        registry.register_feature('t1_feat1', 'Mod1', FeatureGrouping.TIER1, enabled=True)
        registry.register_feature('t1_feat2', 'Mod2', FeatureGrouping.TIER1, enabled=True)
        registry.register_feature('t2_feat1', 'Mod3', FeatureGrouping.TIER2, enabled=True)
        
        # Disable Tier-1
        registry.disable_group(FeatureGrouping.TIER1)
        
        # Check status
        tier1 = registry.get_enabled_features_by_group(FeatureGrouping.TIER1)
        tier2 = registry.get_enabled_features_by_group(FeatureGrouping.TIER2)
        
        assert len(tier1) == 0
        assert len(tier2) == 1


class TestFeatureManifest:
    """Test the FeatureManifest class."""
    
    def test_manifest_creation(self):
        """Test FeatureManifest creation and serialization."""
        manifest = FeatureManifest(
            symbol='AAPL',
            manifest_timestamp=datetime.utcnow().isoformat() + 'Z'
        )
        
        assert manifest.symbol == 'AAPL'
        assert manifest.total_features == 0
        assert manifest.causality_status == 'PENDING'
    
    def test_manifest_add_features(self):
        """Test adding features to manifest."""
        manifest = FeatureManifest(
            symbol='AAPL',
            manifest_timestamp=datetime.utcnow().isoformat() + 'Z'
        )
        
        features_list = [
            {
                'name': 'simple_return',
                'module_name': 'ReturnsFeature',
                'description': 'Simple returns',
                'lookback_window': None,
            }
        ]
        
        manifest.add_features(features_list, FeatureGrouping.TIER1)
        
        assert manifest.total_features == 1
        assert len(manifest.features) == 1
        assert manifest.features[0].name == 'simple_return'
    
    def test_manifest_to_dict(self):
        """Test manifest serialization to dict."""
        manifest = FeatureManifest(
            symbol='AAPL',
            manifest_timestamp=datetime.utcnow().isoformat() + 'Z'
        )
        
        features_list = [
            {
                'name': 'rsi_14',
                'module_name': 'RSIFeature',
                'description': 'RSI indicator',
                'lookback_window': 14,
            }
        ]
        
        manifest.add_features(features_list, FeatureGrouping.TIER2)
        manifest.add_data_quality_info({'total_rows': 2500, 'total_nan': 0})
        
        manifest_dict = manifest.to_dict()
        
        assert manifest_dict['symbol'] == 'AAPL'
        assert manifest_dict['total_features'] == 1
        assert 'data_quality_checks' in manifest_dict
        assert manifest_dict['data_quality_checks']['total_rows'] == 2500


class TestFeatureOrchestrator:
    """Test the FeatureOrchestrator class."""
    
    def test_orchestrator_initialization(self):
        """Test FeatureOrchestrator initialization."""
        config = {
            'include_tier1': True,
            'include_tier2': False,
            'include_tier3': False,
            'include_signal_processing': False,
        }
        
        orchestrator = FeatureOrchestrator(config=config, logger=logger)
        
        assert orchestrator.registry is not None
        assert len(orchestrator.tier1_modules) == 0  # No modules registered yet
    
    def test_register_module(self):
        """Test registering a module with orchestrator."""
        
        class DummyFeature(FeatureModule):
            def compute(self, df, fit_data=None):
                return pd.DataFrame(index=df.index)
            
            def validate(self, features):
                return True, []
        
        orchestrator = FeatureOrchestrator(logger=logger)
        module = DummyFeature(name='dummy_feature', tier=1)
        
        orchestrator.register_module(module, FeatureGrouping.TIER1)
        
        assert len(orchestrator.tier1_modules) == 1
        assert 'dummy_feature' in orchestrator.registry.registry
    
    def test_get_enabled_features_info(self):
        """Test getting info about enabled features."""
        
        class DummyFeature1(FeatureModule):
            def compute(self, df, fit_data=None):
                return pd.DataFrame(index=df.index)
            
            def validate(self, features):
                return True, []
        
        class DummyFeature2(FeatureModule):
            def compute(self, df, fit_data=None):
                return pd.DataFrame(index=df.index)
            
            def validate(self, features):
                return True, []
        
        orchestrator = FeatureOrchestrator(logger=logger)
        
        module1 = DummyFeature1(name='feature1', tier=1)
        module2 = DummyFeature2(name='feature2', tier=2)
        
        orchestrator.register_module(module1, FeatureGrouping.TIER1)
        orchestrator.register_module(module2, FeatureGrouping.TIER2)
        
        info = orchestrator.get_enabled_features_info()
        
        assert info['tier1']['count'] == 1
        assert info['tier2']['count'] == 1
        assert 'feature1' in info['tier1']['features']
        assert 'feature2' in info['tier2']['features']


# ==================== Test Execution ====================

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
