"""
Unit tests for LeakageDetector module.

Tests data leakage detection across all scenarios:
- Preprocessing artifacts leakage
- Feature look-ahead bias
- Data split integrity
- Cross-validation leakage
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.leakage_detector import LeakageDetector, LeakageViolation
from utils.error_handler import DataLeakageError


class TestLeakageDetector:
    """Test suite for LeakageDetector."""
    
    @pytest.fixture
    def logger(self):
        """Create logger for tests."""
        return logging.getLogger('test_leakage_detector')
    
    @pytest.fixture
    def detector(self, logger):
        """Create LeakageDetector instance."""
        return LeakageDetector(logger)
    
    # ========================================================================
    # Test: Preprocessing Artifacts Leakage
    # ========================================================================
    
    def test_valid_preprocessing_artifacts_leakage(self, detector):
        """Test: Valid preprocessing artifacts (fitted on train only)."""
        is_clean, violations = detector.check_preprocessing_artifacts_leakage(
            fit_data_range=('2020-01-01', '2022-12-31'),
            val_data_range=('2023-01-01', '2023-06-30'),
            test_data_range=('2023-07-01', '2023-12-31'),
            fit_data_shape=(500, 20),
            artifact_metadata={'fit_data_source': 'training', 'fit_date': '2022-12-31'}
        )
        
        assert is_clean is True
        assert len(violations) == 0
    
    def test_train_val_overlap_leakage(self, detector):
        """Test: CRITICAL - Training data overlaps with validation."""
        with pytest.raises(DataLeakageError) as exc_info:
            detector.check_preprocessing_artifacts_leakage(
                fit_data_range=('2020-01-01', '2023-01-15'),  # Overlaps with val
                val_data_range=('2023-01-01', '2023-06-30'),
                test_data_range=('2023-07-01', '2023-12-31'),
                fit_data_shape=(500, 20)
            )
        
        assert 'overlap' in str(exc_info.value).lower()
    
    def test_val_test_overlap_leakage(self, detector):
        """Test: CRITICAL - Validation data overlaps with test."""
        with pytest.raises(DataLeakageError) as exc_info:
            detector.check_preprocessing_artifacts_leakage(
                fit_data_range=('2020-01-01', '2022-12-31'),
                val_data_range=('2023-01-01', '2023-07-15'),  # Overlaps with test
                test_data_range=('2023-07-01', '2023-12-31'),
                fit_data_shape=(500, 20)
            )
        
        assert 'overlap' in str(exc_info.value).lower()
    
    def test_artifact_fitted_on_non_training(self, detector):
        """Test: CRITICAL - Artifact fitted on validation/test data."""
        with pytest.raises(DataLeakageError) as exc_info:
            detector.check_preprocessing_artifacts_leakage(
                fit_data_range=('2020-01-01', '2022-12-31'),
                val_data_range=('2023-01-01', '2023-06-30'),
                test_data_range=('2023-07-01', '2023-12-31'),
                fit_data_shape=(500, 20),
                artifact_metadata={'fit_data_source': 'validation'}  # Wrong!
            )
        
        assert 'non-training' in str(exc_info.value).lower()
    
    def test_artifact_date_mismatch(self, detector):
        """Test: ERROR - Artifact fit date outside training range."""
        is_clean, violations = detector.check_preprocessing_artifacts_leakage(
            fit_data_range=('2020-01-01', '2022-12-31'),
            val_data_range=('2023-01-01', '2023-06-30'),
            test_data_range=('2023-07-01', '2023-12-31'),
            fit_data_shape=(500, 20),
            artifact_metadata={'fit_data_source': 'training', 'fit_date': '2023-06-01'}  # Outside range
        )
        
        assert is_clean is False
        assert any(v.severity == 'ERROR' for v in violations)
    
    # ========================================================================
    # Test: Feature Look-Ahead (Causality)
    # ========================================================================
    
    def test_valid_feature_causality(self, detector):
        """Test: Valid features with no look-ahead bias."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        }, index=dates)
        
        is_clean, violations = detector.check_feature_look_ahead(df)
        
        # May have warnings but should be clean (no CRITICAL/ERROR)
        assert all(v.severity not in ['CRITICAL', 'ERROR'] for v in violations)
    
    def test_excessive_nan_in_features(self, detector):
        """Test: WARNING - Excessive NaN in features."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'feature1': [np.nan] * 50 + [1.0] * 50,  # 50% NaN
            'feature2': [np.nan] * 50 + [2.0] * 50
        }, index=dates)
        
        is_clean, violations = detector.check_feature_look_ahead(df)
        
        assert any(v.severity == 'WARNING' for v in violations)
    
    def test_invalid_lookback_window(self, detector):
        """Test: ERROR - Invalid (negative/zero) lookback window."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'feature1': np.random.randn(100)
        }, index=dates)
        
        is_clean, violations = detector.check_feature_look_ahead(
            df,
            lookback_windows={'momentum': -5}  # Invalid!
        )
        
        assert is_clean is False
        assert any(v.severity == 'ERROR' for v in violations)
    
    def test_non_datetime_index(self, detector):
        """Test: WARNING - DataFrame doesn't have DatetimeIndex."""
        df = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        })
        
        is_clean, violations = detector.check_feature_look_ahead(df)
        
        assert any(v.severity == 'WARNING' for v in violations)
    
    # ========================================================================
    # Test: Data Split Integrity
    # ========================================================================
    
    def test_valid_data_split_integrity(self, detector):
        """Test: Valid split with no overlap."""
        train_idx = list(range(0, 70))
        val_idx = list(range(70, 85))
        test_idx = list(range(85, 100))
        
        is_clean, violations = detector.check_data_split_integrity(
            train_idx, val_idx, test_idx, total_rows=100
        )
        
        assert is_clean is True
        assert len([v for v in violations if v.severity in ['CRITICAL', 'ERROR']]) == 0
    
    def test_train_val_overlap_split(self, detector):
        """Test: CRITICAL - Train and validation sets overlap."""
        train_idx = list(range(0, 75))
        val_idx = list(range(70, 85))  # Overlaps with train
        test_idx = list(range(85, 100))
        
        is_clean, violations = detector.check_data_split_integrity(
            train_idx, val_idx, test_idx, total_rows=100
        )
        
        assert is_clean is False
        assert any(v.violation_type == 'train_val_overlap' for v in violations)
    
    def test_train_test_overlap_split(self, detector):
        """Test: CRITICAL - Train and test sets overlap."""
        train_idx = list(range(0, 80))
        val_idx = list(range(80, 90))
        test_idx = list(range(75, 100))  # Overlaps with train
        
        is_clean, violations = detector.check_data_split_integrity(
            train_idx, val_idx, test_idx, total_rows=100
        )
        
        assert is_clean is False
        assert any(v.violation_type == 'train_test_overlap' for v in violations)
    
    def test_val_test_overlap_split(self, detector):
        """Test: CRITICAL - Validation and test sets overlap."""
        train_idx = list(range(0, 70))
        val_idx = list(range(70, 90))
        test_idx = list(range(80, 100))  # Overlaps with val
        
        is_clean, violations = detector.check_data_split_integrity(
            train_idx, val_idx, test_idx, total_rows=100
        )
        
        assert is_clean is False
        assert any(v.violation_type == 'val_test_overlap' for v in violations)
    
    def test_indices_out_of_range(self, detector):
        """Test: ERROR - Indices outside valid range."""
        train_idx = list(range(0, 70))
        val_idx = list(range(70, 85))
        test_idx = list(range(85, 105))  # Indices 100-104 are out of range!
        
        is_clean, violations = detector.check_data_split_integrity(
            train_idx, val_idx, test_idx, total_rows=100
        )
        
        assert is_clean is False
        assert any(v.violation_type == 'invalid_indices' for v in violations)
    
    def test_incomplete_coverage_split(self, detector):
        """Test: WARNING - Not all rows assigned to splits."""
        train_idx = list(range(0, 60))
        val_idx = list(range(60, 80))
        test_idx = list(range(80, 90))  # Rows 90-99 not covered
        
        is_clean, violations = detector.check_data_split_integrity(
            train_idx, val_idx, test_idx, total_rows=100
        )
        
        # Should still be "clean" (no critical errors) but have warning
        assert any(v.violation_type == 'incomplete_coverage' for v in violations)
    
    # ========================================================================
    # Test: Cross-Validation Leakage
    # ========================================================================
    
    def test_valid_cv_folds(self, detector):
        """Test: Valid cross-validation folds."""
        cv_folds = [
            (list(range(0, 80)), list(range(80, 100))),
            (list(range(0, 20)) + list(range(80, 100)), list(range(20, 80))),
            (list(range(0, 40)) + list(range(60, 100)), list(range(40, 60)))
        ]
        
        is_clean, violations = detector.check_cross_validation_leakage(cv_folds)
        
        assert is_clean is True
        assert len([v for v in violations if v.severity in ['CRITICAL', 'ERROR']]) == 0
    
    def test_cv_fold_overlap(self, detector):
        """Test: CRITICAL - CV fold has train/test overlap."""
        cv_folds = [
            (list(range(0, 80)), list(range(70, 100)))  # Overlaps!
        ]
        
        is_clean, violations = detector.check_cross_validation_leakage(cv_folds)
        
        assert is_clean is False
        assert any(v.violation_type == 'cv_fold_overlap' for v in violations)
    
    def test_empty_cv_folds(self, detector):
        """Test: WARNING - Empty CV folds list."""
        cv_folds = []
        
        is_clean, violations = detector.check_cross_validation_leakage(cv_folds)
        
        assert any(v.violation_type == 'empty_folds' for v in violations)
    
    # ========================================================================
    # Test: Report Generation
    # ========================================================================
    
    def test_generate_report(self, detector):
        """Test: Generate comprehensive leakage report."""
        # Trigger some violations
        try:
            detector.check_preprocessing_artifacts_leakage(
                fit_data_range=('2020-01-01', '2023-01-15'),
                val_data_range=('2023-01-01', '2023-06-30'),
                test_data_range=('2023-07-01', '2023-12-31'),
                fit_data_shape=(500, 20)
            )
        except DataLeakageError:
            pass
        
        report = detector.generate_report()
        
        assert 'timestamp' in report
        assert 'summary' in report
        assert 'violations' in report
        assert report['summary']['total_violations'] > 0
        assert report['summary']['leakage_detected'] is True
    
    def test_get_violations_by_severity(self, detector):
        """Test: Get violations filtered by severity."""
        try:
            detector.check_preprocessing_artifacts_leakage(
                fit_data_range=('2020-01-01', '2023-01-15'),
                val_data_range=('2023-01-01', '2023-06-30'),
                test_data_range=('2023-07-01', '2023-12-31'),
                fit_data_shape=(500, 20)
            )
        except DataLeakageError:
            pass
        
        critical = detector.get_violations('CRITICAL')
        assert len(critical) > 0
        assert all(v.severity == 'CRITICAL' for v in critical)
    
    def test_clear_violations(self, detector):
        """Test: Clear violation records."""
        try:
            detector.check_preprocessing_artifacts_leakage(
                fit_data_range=('2020-01-01', '2023-01-15'),
                val_data_range=('2023-01-01', '2023-06-30'),
                test_data_range=('2023-07-01', '2023-12-31'),
                fit_data_shape=(500, 20)
            )
        except DataLeakageError:
            pass
        
        assert len(detector.violations) > 0
        
        detector.clear_violations()
        
        assert len(detector.violations) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
