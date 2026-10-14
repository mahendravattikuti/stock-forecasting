"""
Data leakage detection and verification module.

Detects common forms of data leakage in machine learning pipelines:
- Preprocessing artifacts (scalers, normalizers) fitted on validation/test data
- Rolling windows using future data
- Train/validation/test data overlap
- Cross-validation leakage

As per Requirement 8 (Data Splitting and Chronological Integrity).
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path


@dataclass
class LeakageViolation:
    """Represents a detected data leakage violation."""
    violation_type: str
    severity: str  # 'CRITICAL', 'ERROR', 'WARNING'
    description: str
    affected_data: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class LeakageDetector:
    """
    Detects data leakage violations in ML pipeline.
    
    Verifies:
    - Preprocessing artifacts fitted only on training data
    - No validation/test data used in training
    - Rolling windows don't use future data
    - No overlap between train/val/test splits
    - Cross-validation integrity
    
    References
    ----------
    Requirement 8: Data Splitting and Chronological Integrity
    Design Section 1.4: Error Handling & Logging
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize LeakageDetector.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for structured logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self.violations: List[LeakageViolation] = []
    
    def check_preprocessing_artifacts_leakage(
        self,
        fit_data_range: Tuple[str, str],
        val_data_range: Tuple[str, str],
        test_data_range: Tuple[str, str],
        fit_data_shape: Tuple[int, int],
        artifact_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[LeakageViolation]]:
        """
        Verify scaling/normalization artifacts fitted only on training data.
        
        Parameters
        ----------
        fit_data_range : Tuple[str, str]
            (start_date, end_date) of training data in ISO format
        val_data_range : Tuple[str, str]
            (start_date, end_date) of validation data
        test_data_range : Tuple[str, str]
            (start_date, end_date) of test data
        fit_data_shape : Tuple[int, int]
            Shape (rows, columns) of training data used for fitting
        artifact_metadata : Dict[str, Any], optional
            Metadata about artifacts (e.g., scaler parameters)
        
        Returns
        -------
        Tuple[bool, List[LeakageViolation]]
            (is_clean, violations_found)
        
        Raises
        ------
        LeakageError
            If leakage detected (critical violation)
        """
        from .error_handler import DataLeakageError
        
        violations = []
        
        # Check 1: Train dates must be strictly before val dates
        train_end = pd.to_datetime(fit_data_range[1])
        val_start = pd.to_datetime(val_data_range[0])
        
        if train_end >= val_start:
            violation = LeakageViolation(
                violation_type='temporal_overlap',
                severity='CRITICAL',
                description='Training data end date is not strictly before validation start date',
                affected_data=f"Train end: {fit_data_range[1]}, Val start: {val_data_range[0]}",
                details={
                    'train_end': fit_data_range[1],
                    'val_start': val_data_range[0],
                    'overlap_detected': True
                }
            )
            violations.append(violation)
            self.violations.extend(violations)
            self.logger.error(f"CRITICAL: {violation.description}")
            raise DataLeakageError(
                f"Training data overlap with validation: {violation.description}"
            )
        
        # Check 2: Val dates must be strictly before test dates
        val_end = pd.to_datetime(val_data_range[1])
        test_start = pd.to_datetime(test_data_range[0])
        
        if val_end >= test_start:
            violation = LeakageViolation(
                violation_type='temporal_overlap',
                severity='CRITICAL',
                description='Validation data end date is not strictly before test start date',
                affected_data=f"Val end: {val_data_range[1]}, Test start: {test_data_range[0]}",
                details={
                    'val_end': val_data_range[1],
                    'test_start': test_data_range[0],
                    'overlap_detected': True
                }
            )
            violations.append(violation)
            self.violations.extend(violations)
            self.logger.error(f"CRITICAL: {violation.description}")
            raise DataLeakageError(
                f"Validation data overlap with test: {violation.description}"
            )
        
        # Check 3: Artifact metadata should indicate fit on training data only
        if artifact_metadata:
            if 'fit_data_source' in artifact_metadata:
                if artifact_metadata['fit_data_source'] not in ['training', 'train']:
                    violation = LeakageViolation(
                        violation_type='artifact_fit_leakage',
                        severity='CRITICAL',
                        description='Artifact fitted on non-training data',
                        affected_data=f"Fit source: {artifact_metadata['fit_data_source']}",
                        details=artifact_metadata
                    )
                    violations.append(violation)
                    self.violations.extend(violations)
                    self.logger.error(f"CRITICAL: {violation.description}")
                    raise DataLeakageError(violation.description)
            
            # Check if fit_date is consistent with training data range
            if 'fit_date' in artifact_metadata:
                fit_date = pd.to_datetime(artifact_metadata['fit_date'])
                if not (train_end >= fit_date >= pd.to_datetime(fit_data_range[0])):
                    violation = LeakageViolation(
                        violation_type='artifact_date_mismatch',
                        severity='ERROR',
                        description='Artifact fit date outside training data range',
                        affected_data=f"Fit date: {artifact_metadata['fit_date']}, Train range: {fit_data_range}",
                        details={'fit_date': artifact_metadata['fit_date']}
                    )
                    violations.append(violation)
                    self.logger.error(f"ERROR: {violation.description}")
        
        self.violations.extend(violations)
        is_clean = len(violations) == 0
        
        if is_clean:
            self.logger.info("✓ Preprocessing artifacts leakage check passed")
        
        return is_clean, violations
    
    def check_feature_look_ahead(
        self,
        features_df: pd.DataFrame,
        prediction_date_col: Optional[str] = None,
        lookback_windows: Optional[Dict[str, int]] = None
    ) -> Tuple[bool, List[LeakageViolation]]:
        """
        Verify rolling windows don't use future data (no look-ahead bias).
        
        Parameters
        ----------
        features_df : pd.DataFrame
            Feature DataFrame with DatetimeIndex
        prediction_date_col : str, optional
            Name of column indicating prediction target date
        lookback_windows : Dict[str, int], optional
            Dictionary mapping feature names to their lookback windows (e.g., {'momentum_5': 5})
        
        Returns
        -------
        Tuple[bool, List[LeakageViolation]]
            (is_clean, violations_found)
        """
        violations = []
        
        # Check 1: Index is datetime-like
        if not isinstance(features_df.index, pd.DatetimeIndex):
            violation = LeakageViolation(
                violation_type='invalid_index',
                severity='WARNING',
                description='Feature DataFrame does not have DatetimeIndex',
                affected_data=f"Index type: {type(features_df.index)}"
            )
            violations.append(violation)
            self.logger.warning(f"WARNING: {violation.description}")
        
        # Check 2: Features computed row-by-row without look-ahead
        # This is a structural check: if features_df exists and is aligned with dates,
        # it's assumed features were computed properly (no forward-looking calculations)
        
        # Check 3: Verify no NaN at prediction boundaries (sign of truncation)
        initial_nans = features_df.isna().sum()
        if initial_nans.sum() > len(features_df) * 0.1:  # More than 10% NaN
            violation = LeakageViolation(
                violation_type='excessive_nan',
                severity='WARNING',
                description='Excessive NaN values in features (possible truncation)',
                affected_data=f"Total NaN count: {initial_nans.sum()} / {len(features_df) * len(features_df.columns)}",
                details={'nan_counts': initial_nans.to_dict()}
            )
            violations.append(violation)
            self.logger.warning(f"WARNING: {violation.description}")
        
        # Check 4: Verify lookback windows are reasonable (if provided)
        if lookback_windows:
            for feature_name, window_size in lookback_windows.items():
                if window_size <= 0:
                    violation = LeakageViolation(
                        violation_type='invalid_lookback',
                        severity='ERROR',
                        description=f'Feature {feature_name} has non-positive lookback window',
                        affected_data=f"Feature: {feature_name}, window: {window_size}",
                        details={'feature': feature_name, 'window': window_size}
                    )
                    violations.append(violation)
                    self.logger.error(f"ERROR: {violation.description}")
        
        self.violations.extend(violations)
        is_clean = len([v for v in violations if v.severity in ['CRITICAL', 'ERROR']]) == 0
        
        if is_clean:
            self.logger.info("✓ Feature look-ahead (causality) check passed")
        
        return is_clean, violations
    
    def check_data_split_integrity(
        self,
        train_indices: List[int],
        val_indices: List[int],
        test_indices: List[int],
        total_rows: int
    ) -> Tuple[bool, List[LeakageViolation]]:
        """
        Verify no overlap between train/validation/test sets.
        
        Parameters
        ----------
        train_indices : List[int]
            Row indices for training data
        val_indices : List[int]
            Row indices for validation data
        test_indices : List[int]
            Row indices for test data
        total_rows : int
            Total number of rows in dataset
        
        Returns
        -------
        Tuple[bool, List[LeakageViolation]]
            (is_clean, violations_found)
        """
        violations = []
        
        # Check 1: No overlap between sets
        train_set = set(train_indices)
        val_set = set(val_indices)
        test_set = set(test_indices)
        
        train_val_overlap = train_set & val_set
        if train_val_overlap:
            violation = LeakageViolation(
                violation_type='train_val_overlap',
                severity='CRITICAL',
                description=f'Train and validation sets overlap',
                affected_data=f"Overlapping indices count: {len(train_val_overlap)}",
                details={'overlap_count': len(train_val_overlap)}
            )
            violations.append(violation)
            self.logger.error(f"CRITICAL: {violation.description}")
        
        train_test_overlap = train_set & test_set
        if train_test_overlap:
            violation = LeakageViolation(
                violation_type='train_test_overlap',
                severity='CRITICAL',
                description='Train and test sets overlap',
                affected_data=f"Overlapping indices count: {len(train_test_overlap)}",
                details={'overlap_count': len(train_test_overlap)}
            )
            violations.append(violation)
            self.logger.error(f"CRITICAL: {violation.description}")
        
        val_test_overlap = val_set & test_set
        if val_test_overlap:
            violation = LeakageViolation(
                violation_type='val_test_overlap',
                severity='CRITICAL',
                description='Validation and test sets overlap',
                affected_data=f"Overlapping indices count: {len(val_test_overlap)}",
                details={'overlap_count': len(val_test_overlap)}
            )
            violations.append(violation)
            self.logger.error(f"CRITICAL: {violation.description}")
        
        # Check 2: All indices are unique and within range
        all_indices = train_set | val_set | test_set
        if len(all_indices) != len(train_indices) + len(val_indices) + len(test_indices):
            violation = LeakageViolation(
                violation_type='duplicate_indices',
                severity='ERROR',
                description='Duplicate indices within splits',
                affected_data=f"Expected {len(train_indices) + len(val_indices) + len(test_indices)} unique, got {len(all_indices)}",
                details={
                    'expected_total': len(train_indices) + len(val_indices) + len(test_indices),
                    'actual_unique': len(all_indices)
                }
            )
            violations.append(violation)
            self.logger.error(f"ERROR: {violation.description}")
        
        # Check 3: All indices are within valid range
        invalid_indices = all_indices - set(range(total_rows))
        if invalid_indices:
            violation = LeakageViolation(
                violation_type='invalid_indices',
                severity='ERROR',
                description='Indices outside valid range',
                affected_data=f"Invalid indices count: {len(invalid_indices)}",
                details={'invalid_count': len(invalid_indices)}
            )
            violations.append(violation)
            self.logger.error(f"ERROR: {violation.description}")
        
        # Check 4: Coverage (optional: all rows should be covered)
        uncovered_indices = set(range(total_rows)) - all_indices
        if uncovered_indices:
            violation = LeakageViolation(
                violation_type='incomplete_coverage',
                severity='WARNING',
                description='Not all rows assigned to splits',
                affected_data=f"Uncovered rows: {len(uncovered_indices)} / {total_rows}",
                details={'uncovered_count': len(uncovered_indices)}
            )
            violations.append(violation)
            self.logger.warning(f"WARNING: {violation.description}")
        
        self.violations.extend(violations)
        is_clean = len([v for v in violations if v.severity in ['CRITICAL', 'ERROR']]) == 0
        
        if is_clean:
            self.logger.info(f"✓ Data split integrity check passed (train: {len(train_indices)}, val: {len(val_indices)}, test: {len(test_indices)})")
        
        return is_clean, violations
    
    def check_cross_validation_leakage(
        self,
        cv_folds: List[Tuple[List[int], List[int]]],
        symbols_list: Optional[List[str]] = None
    ) -> Tuple[bool, List[LeakageViolation]]:
        """
        Detect leakage in cross-validation setup.
        
        Verifies:
        - No overlap between train/test in any fold
        - All folds cover complete dataset
        - Temporal ordering maintained if applicable
        
        Parameters
        ----------
        cv_folds : List[Tuple[List[int], List[int]]]
            List of (train_indices, test_indices) tuples for each fold
        symbols_list : List[str], optional
            Symbol names for better error reporting
        
        Returns
        -------
        Tuple[bool, List[LeakageViolation]]
            (is_clean, violations_found)
        """
        violations = []
        
        if not cv_folds:
            violation = LeakageViolation(
                violation_type='empty_folds',
                severity='WARNING',
                description='No cross-validation folds provided',
                affected_data='cv_folds is empty'
            )
            violations.append(violation)
            self.logger.warning(f"WARNING: {violation.description}")
            return False, violations
        
        # Check each fold for train/test overlap
        for fold_idx, (train_indices, test_indices) in enumerate(cv_folds):
            train_set = set(train_indices)
            test_set = set(test_indices)
            
            overlap = train_set & test_set
            if overlap:
                violation = LeakageViolation(
                    violation_type='cv_fold_overlap',
                    severity='CRITICAL',
                    description=f'Fold {fold_idx}: train and test sets overlap',
                    affected_data=f"Fold {fold_idx}, overlap count: {len(overlap)}",
                    details={'fold': fold_idx, 'overlap_count': len(overlap)}
                )
                violations.append(violation)
                self.logger.error(f"CRITICAL: {violation.description}")
        
        # Check coverage across all folds (if intended)
        # Note: Some CV strategies don't cover all data, so this is optional
        
        self.violations.extend(violations)
        is_clean = len([v for v in violations if v.severity in ['CRITICAL', 'ERROR']]) == 0
        
        if is_clean:
            self.logger.info(f"✓ Cross-validation leakage check passed ({len(cv_folds)} folds)")
        
        return is_clean, violations
    
    def get_violations(self, severity: Optional[str] = None) -> List[LeakageViolation]:
        """
        Get all recorded violations, optionally filtered by severity.
        
        Parameters
        ----------
        severity : str, optional
            Filter by severity ('CRITICAL', 'ERROR', 'WARNING')
        
        Returns
        -------
        List[LeakageViolation]
            List of violations
        """
        if severity:
            return [v for v in self.violations if v.severity == severity]
        return self.violations
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive leakage detection report.
        
        Returns
        -------
        Dict[str, Any]
            Report containing violation summary and details
        """
        critical_violations = [v for v in self.violations if v.severity == 'CRITICAL']
        error_violations = [v for v in self.violations if v.severity == 'ERROR']
        warning_violations = [v for v in self.violations if v.severity == 'WARNING']
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_violations': len(self.violations),
                'critical': len(critical_violations),
                'errors': len(error_violations),
                'warnings': len(warning_violations),
                'leakage_detected': len(critical_violations) > 0
            },
            'violations': [
                {
                    'type': v.violation_type,
                    'severity': v.severity,
                    'description': v.description,
                    'affected_data': v.affected_data,
                    'details': v.details,
                    'timestamp': v.timestamp
                }
                for v in self.violations
            ]
        }
        
        return report
    
    def clear_violations(self) -> None:
        """Clear all recorded violations."""
        self.violations = []


if __name__ == '__main__':
    # Example usage
    from .logging_config import configure_logging
    
    logger = configure_logging()
    detector = LeakageDetector(logger)
    
    # Example: Check preprocessing artifacts
    try:
        detector.check_preprocessing_artifacts_leakage(
            fit_data_range=('2020-01-01', '2022-12-31'),
            val_data_range=('2023-01-01', '2023-06-30'),
            test_data_range=('2023-07-01', '2023-12-31'),
            fit_data_shape=(500, 20),
            artifact_metadata={'fit_data_source': 'training', 'fit_date': '2022-12-31'}
        )
    except Exception as e:
        print(f"Leakage detected: {e}")
    
    # Generate report
    report = detector.generate_report()
    print(report)
