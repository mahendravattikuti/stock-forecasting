"""
Tests for pipeline report generator.

Tests the PipelineReportGenerator class with sample data to verify:
- Report content generation
- File save operations
- Format and structure correctness
- Data aggregation from multiple sources
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
import tempfile

import pytest
import pandas as pd
import numpy as np

from reporting.report_generator import (
    PipelineReportGenerator,
    PipelineExecutionContext,
    FeaturesReportGenerator,
    load_context_from_results_directory
)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Create sample pipeline configuration."""
    return {
        'pipeline_metadata': {
            'execution_timestamp': '2024-01-19T10:00:00Z',
            'pipeline_version': '1.0',
            'stage': 'Stage_1_DataCleaning_FeatureEngineering'
        },
        'environment': {
            'python_version': '3.10.12',
            'numpy_version': '1.24.3',
            'pandas_version': '2.0.3',
            'scikit_learn_version': '1.2.2',
            'tensorflow_version': '2.13.0'
        },
        'random_seeds': {
            'numpy_seed': 42,
            'random_seed': 42,
            'tensorflow_seed': 42
        },
        'data_acquisition': {
            'primary_source': 'iex_cloud',
            'fallback_source': 'yfinance',
            'lookback_years': 10,
            'min_trading_days': 2500,
            'retry_attempts': 3,
            'retry_backoff_factor': 2,
            'timeout_seconds': 30
        },
        'symbols': {
            'list': ['AAPL', 'MSFT', 'GOOGL'],
            'max_portfolio_size': 100,
            'supported_exchanges': ['NYSE', 'NASDAQ', 'AMEX']
        },
        'data_cleaning': {
            'forward_fill_max_days': 2,
            'spike_detection_threshold': 0.20,
            'ohlc_correction_method': 'linear_interpolation',
            'volume_zero_handling': 'forward_fill',
            'quality_threshold_completeness': 0.99
        },
        'feature_engineering': {
            'tier1_enabled': True,
            'tier2_enabled': True,
            'tier3_enabled': True,
            'signal_processing_enabled': False,
            'tier2_features': ['rsi_14', 'macd_line', 'bollinger_bands', 'momentum']
        },
        'data_splitting': {
            'methodology': 'chronological_70_15_15',
            'train_ratio': 0.70,
            'val_ratio': 0.15,
            'test_ratio': 0.15,
            'temporal_integrity_verified': True
        },
        'baseline_models': {
            'random_walk': {'enabled': True},
            'arima_111': {'enabled': True},
            'linear_regression': {'enabled': True},
            'ridge_regression': {'enabled': True},
            'historical_mean': {'enabled': True}
        }
    }


@pytest.fixture
def sample_cleaning_reports() -> Dict[str, Dict[str, Any]]:
    """Create sample cleaning reports."""
    return {
        'AAPL': {
            'symbol': 'AAPL',
            'report_timestamp': '2024-01-19T10:30:00Z',
            'raw_data_rows': 2525,
            'raw_date_range': ['2002-01-02', '2024-01-19'],
            'missing_values_detected': 2,
            'date_gaps_detected': 1,
            'spikes_detected': 1,
            'ohlc_violations_detected': 0,
            'forward_fills_applied': 2,
            'spikes_corrected': 0,
            'ohlc_corrections_applied': 0,
            'adjustments_applied': 1,
            'rows_excluded': 3,
            'cleaned_data_rows': 2522,
            'cleaned_date_range': ['2002-01-02', '2024-01-19'],
            'validation_passed': True,
            'validation_errors': [],
            'completeness_percent': 99.88,
            'quality_status': 'PASS',
            'quality_notes': 'Excellent data quality after cleaning'
        },
        'MSFT': {
            'symbol': 'MSFT',
            'report_timestamp': '2024-01-19T10:30:30Z',
            'raw_data_rows': 2530,
            'raw_date_range': ['1997-08-01', '2024-01-19'],
            'missing_values_detected': 0,
            'date_gaps_detected': 0,
            'spikes_detected': 0,
            'ohlc_violations_detected': 0,
            'forward_fills_applied': 0,
            'spikes_corrected': 0,
            'ohlc_corrections_applied': 0,
            'adjustments_applied': 2,
            'rows_excluded': 0,
            'cleaned_data_rows': 2530,
            'cleaned_date_range': ['1997-08-01', '2024-01-19'],
            'validation_passed': True,
            'validation_errors': [],
            'completeness_percent': 100.0,
            'quality_status': 'PASS',
            'quality_notes': 'No cleaning required'
        }
    }


@pytest.fixture
def sample_features_manifests() -> Dict[str, Dict[str, Any]]:
    """Create sample feature manifests."""
    return {
        'AAPL': {
            'symbol': 'AAPL',
            'timestamp': '2024-01-19T10:35:00Z',
            'features': [
                {'name': 'simple_return', 'tier': 1, 'type': 'return'},
                {'name': 'log_return', 'tier': 1, 'type': 'return'},
                {'name': 'rsi_14', 'tier': 2, 'type': 'technical'},
                {'name': 'macd_line', 'tier': 2, 'type': 'technical'},
                {'name': 'bollinger_bands', 'tier': 2, 'type': 'technical'},
                {'name': 'momentum_5', 'tier': 2, 'type': 'technical'},
                {'name': 'momentum_20', 'tier': 2, 'type': 'technical'},
                {'name': 'regime', 'tier': 3, 'type': 'regime'}
            ],
            'tier_counts': {'tier1': 2, 'tier2': 5, 'tier3': 1},
            'causality_verified': True
        },
        'MSFT': {
            'symbol': 'MSFT',
            'timestamp': '2024-01-19T10:35:30Z',
            'features': [
                {'name': 'simple_return', 'tier': 1, 'type': 'return'},
                {'name': 'log_return', 'tier': 1, 'type': 'return'},
                {'name': 'rsi_14', 'tier': 2, 'type': 'technical'},
                {'name': 'macd_line', 'tier': 2, 'type': 'technical'},
                {'name': 'bollinger_bands', 'tier': 2, 'type': 'technical'},
                {'name': 'momentum_5', 'tier': 2, 'type': 'technical'},
            ],
            'tier_counts': {'tier1': 2, 'tier2': 4},
            'causality_verified': True
        }
    }


@pytest.fixture
def sample_splits_metadata() -> Dict[str, Any]:
    """Create sample splits metadata."""
    return {
        'method': 'chronological_shared_calendar_cutoffs',
        'ratios': {'train': 0.70, 'val': 0.15, 'test': 0.15},
        'cutoff_dates': {
            'train_end': '2021-09-15',
            'val_start': '2021-09-16',
            'val_end': '2023-02-28',
            'test_start': '2023-03-01',
            'test_end': '2024-01-19'
        },
        'splits': {
            'train': {
                'row_count': 4900,
                'start_date': '2002-01-02',
                'end_date': '2021-09-15'
            },
            'val': {
                'row_count': 350,
                'start_date': '2021-09-16',
                'end_date': '2023-02-28'
            },
            'test': {
                'row_count': 350,
                'start_date': '2023-03-01',
                'end_date': '2024-01-19'
            }
        },
        'temporal_integrity_verified': True
    }


@pytest.fixture
def sample_baseline_results() -> Dict[str, Dict[str, Any]]:
    """Create sample baseline results."""
    return {
        'random_walk': {
            'validation': {
                'mae': 0.0234,
                'rmse': 0.0312,
                'directional_accuracy': 0.48
            },
            'test': {
                'mae': 0.0241,
                'rmse': 0.0318,
                'directional_accuracy': 0.49
            }
        },
        'arima_111': {
            'validation': {
                'mae': 0.0218,
                'rmse': 0.0289,
                'directional_accuracy': 0.51
            },
            'test': {
                'mae': 0.0225,
                'rmse': 0.0295,
                'directional_accuracy': 0.52
            }
        },
        'linear_regression': {
            'validation': {
                'mae': 0.0205,
                'rmse': 0.0271,
                'directional_accuracy': 0.54
            },
            'test': {
                'mae': 0.0212,
                'rmse': 0.0277,
                'directional_accuracy': 0.55
            }
        }
    }


@pytest.fixture
def sample_context(
    sample_config,
    sample_cleaning_reports,
    sample_features_manifests,
    sample_splits_metadata,
    sample_baseline_results
) -> PipelineExecutionContext:
    """Create sample pipeline execution context."""
    return PipelineExecutionContext(
        config=sample_config,
        cleaning_reports=sample_cleaning_reports,
        features_manifests=sample_features_manifests,
        splits_metadata=sample_splits_metadata,
        baseline_results=sample_baseline_results,
        errors=[],
        warnings=[
            {
                'type': 'SYMBOL_EXCLUDED',
                'symbol': 'GOOGL',
                'message': 'Insufficient data: only 2400 trading days (required: 2500)'
            }
        ]
    )


class TestPipelineReportGenerator:
    """Test suite for PipelineReportGenerator."""
    
    def test_generate_pipeline_report(self, sample_context):
        """Test report generation produces valid markdown."""
        generator = PipelineReportGenerator()
        report = generator.generate_pipeline_report(sample_context)
        
        # Check report is non-empty
        assert len(report) > 0
        
        # Check for key sections
        assert '# Stock Market Forecasting System' in report
        assert 'Executive Summary' in report
        assert 'Data Sources' in report
        assert 'Symbols Processed' in report
        assert 'Data Cleaning Summary' in report
        assert 'Feature Engineering Summary' in report
        assert 'Data Splitting' in report
        assert 'Baseline Models' in report
        assert 'Errors and Warnings' in report
        assert 'Reproducibility Information' in report
    
    def test_report_contains_symbols(self, sample_context):
        """Test report includes symbol information."""
        generator = PipelineReportGenerator()
        report = generator.generate_pipeline_report(sample_context)
        
        for symbol in ['AAPL', 'MSFT']:
            assert symbol in report
    
    def test_report_contains_metrics(self, sample_context):
        """Test report includes key metrics."""
        generator = PipelineReportGenerator()
        report = generator.generate_pipeline_report(sample_context)
        
        # Check for data retention rate
        assert 'Data Retention Rate' in report
        
        # Check for feature counts
        assert 'Total Features Generated' in report
        
        # Check for baseline metrics
        assert 'MAE' in report
        assert 'RMSE' in report
        assert 'Dir. Accuracy' in report or 'Directional' in report
    
    def test_save_report(self, sample_context, tmp_path):
        """Test report saving to file."""
        generator = PipelineReportGenerator()
        report = generator.generate_pipeline_report(sample_context)
        
        output_file = tmp_path / "pipeline_report.md"
        saved_path = generator.save_report(report, str(output_file))
        
        # Check file was created
        assert Path(saved_path).exists()
        
        # Check content
        with open(saved_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert '# Stock Market Forecasting System' in content
    
    def test_report_with_no_warnings(self, sample_config, sample_cleaning_reports, sample_features_manifests):
        """Test report generation with no warnings or errors."""
        context = PipelineExecutionContext(
            config=sample_config,
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests,
            splits_metadata={},
            baseline_results={},
            errors=[],
            warnings=[]
        )
        
        generator = PipelineReportGenerator()
        report = generator.generate_pipeline_report(context)
        
        assert 'No errors encountered' in report
        assert 'No warnings encountered' in report
    
    def test_report_with_errors(self, sample_config):
        """Test report generation with errors."""
        context = PipelineExecutionContext(
            config=sample_config,
            cleaning_reports={},
            features_manifests={},
            splits_metadata={},
            baseline_results={},
            errors=[
                {
                    'type': 'DATA_ACQUISITION_FAILURE',
                    'symbol': 'UNKNOWN',
                    'message': 'Failed to acquire data: all sources exhausted'
                }
            ],
            warnings=[]
        )
        
        generator = PipelineReportGenerator()
        report = generator.generate_pipeline_report(context)
        
        assert 'DATA_ACQUISITION_FAILURE' in report
        assert 'all sources exhausted' in report
    
    def test_report_markdown_structure(self, sample_context):
        """Test report has valid markdown structure."""
        generator = PipelineReportGenerator()
        report = generator.generate_pipeline_report(sample_context)
        
        # Check for markdown headers
        assert report.count('##') > 0  # At least one level-2 header
        assert report.count('###') > 0  # At least one level-3 header
        
        # Check for markdown tables
        assert '|' in report  # Tables use pipes
        assert '-' in report  # Tables use dashes
    
    def test_load_context_from_empty_directory(self, tmp_path):
        """Test loading context from empty results directory."""
        context = load_context_from_results_directory(
            config={'symbols': {'list': ['AAPL']}},
            results_dir=str(tmp_path)
        )
        
        assert context.config is not None
        assert len(context.cleaning_reports) == 0
        assert len(context.features_manifests) == 0
        assert len(context.baseline_results) == 0
    
    def test_load_context_from_directory_with_files(self, tmp_path, sample_cleaning_reports):
        """Test loading context from directory with JSON files."""
        # Create cleaning reports directory and files
        cleaning_dir = tmp_path / "cleaning_reports"
        cleaning_dir.mkdir(parents=True)
        
        for symbol, report in sample_cleaning_reports.items():
            report_file = cleaning_dir / f"{symbol}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f)
        
        context = load_context_from_results_directory(
            config={'symbols': {'list': ['AAPL', 'MSFT']}},
            results_dir=str(tmp_path)
        )
        
        assert len(context.cleaning_reports) == 2
        assert 'AAPL' in context.cleaning_reports
        assert 'MSFT' in context.cleaning_reports


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



class TestFeaturesReportGenerator:
    """Test suite for FeaturesReportGenerator."""
    
    @pytest.fixture
    def sample_features_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Create sample features data with train/val/test splits."""
        np.random.seed(42)
        
        n_train = 1000
        n_val = 200
        n_test = 200
        
        # Create features data
        features_data = {
            'AAPL': {
                'train': pd.DataFrame({
                    'return_simple': np.random.normal(0.001, 0.02, n_train),
                    'return_log': np.random.normal(0.001, 0.02, n_train),
                    'rsi_14': np.random.uniform(20, 80, n_train),
                    'momentum_5': np.random.normal(0, 0.05, n_train),
                    'momentum_20': np.random.normal(0, 0.03, n_train),
                    'volatility': np.random.uniform(0.01, 0.05, n_train),
                }),
                'val': pd.DataFrame({
                    'return_simple': np.random.normal(0.0015, 0.021, n_val),
                    'return_log': np.random.normal(0.0015, 0.021, n_val),
                    'rsi_14': np.random.uniform(25, 75, n_val),
                    'momentum_5': np.random.normal(0.001, 0.052, n_val),
                    'momentum_20': np.random.normal(0.001, 0.031, n_val),
                    'volatility': np.random.uniform(0.01, 0.055, n_val),
                }),
                'test': pd.DataFrame({
                    'return_simple': np.random.normal(0.002, 0.022, n_test),
                    'return_log': np.random.normal(0.002, 0.022, n_test),
                    'rsi_14': np.random.uniform(30, 70, n_test),
                    'momentum_5': np.random.normal(0.002, 0.053, n_test),
                    'momentum_20': np.random.normal(0.002, 0.032, n_test),
                    'volatility': np.random.uniform(0.015, 0.06, n_test),
                })
            },
            'MSFT': {
                'train': pd.DataFrame({
                    'return_simple': np.random.normal(0.0012, 0.019, n_train),
                    'return_log': np.random.normal(0.0012, 0.019, n_train),
                    'rsi_14': np.random.uniform(25, 75, n_train),
                    'momentum_5': np.random.normal(0, 0.048, n_train),
                    'momentum_20': np.random.normal(0, 0.028, n_train),
                    'volatility': np.random.uniform(0.01, 0.048, n_train),
                }),
                'val': pd.DataFrame({
                    'return_simple': np.random.normal(0.0015, 0.02, n_val),
                    'return_log': np.random.normal(0.0015, 0.02, n_val),
                    'rsi_14': np.random.uniform(25, 75, n_val),
                    'momentum_5': np.random.normal(0.001, 0.049, n_val),
                    'momentum_20': np.random.normal(0.001, 0.029, n_val),
                    'volatility': np.random.uniform(0.012, 0.052, n_val),
                }),
                'test': pd.DataFrame({
                    'return_simple': np.random.normal(0.0018, 0.021, n_test),
                    'return_log': np.random.normal(0.0018, 0.021, n_test),
                    'rsi_14': np.random.uniform(28, 72, n_test),
                    'momentum_5': np.random.normal(0.002, 0.05, n_test),
                    'momentum_20': np.random.normal(0.002, 0.03, n_test),
                    'volatility': np.random.uniform(0.012, 0.055, n_test),
                })
            }
        }
        
        return features_data
    
    @pytest.fixture
    def sample_splits_metadata(self) -> Dict[str, Any]:
        """Create sample splits metadata."""
        return {
            'method': 'chronological_shared_calendar_cutoffs',
            'ratios': {'train': 0.70, 'val': 0.15, 'test': 0.15},
            'cutoff_dates': {
                'train_end': '2021-09-15',
                'val_start': '2021-09-16',
                'val_end': '2023-02-28',
                'test_start': '2023-03-01',
                'test_end': '2024-01-19'
            },
            'splits': {
                'train': {
                    'row_count': 4900,
                    'start_date': '2002-01-02',
                    'end_date': '2021-09-15'
                },
                'val': {
                    'row_count': 350,
                    'start_date': '2021-09-16',
                    'end_date': '2023-02-28'
                },
                'test': {
                    'row_count': 350,
                    'start_date': '2023-03-01',
                    'end_date': '2024-01-19'
                }
            }
        }
    
    def test_generate_features_report(self, sample_features_data, sample_splits_metadata):
        """Test report generation produces valid HTML."""
        generator = FeaturesReportGenerator()
        report_html = generator.generate_features_report(
            features_data=sample_features_data,
            splits_metadata=sample_splits_metadata
        )
        
        # Check report is non-empty
        assert len(report_html) > 0
        
        # Check for key HTML elements
        assert '<html>' in report_html or '<!DOCTYPE' in report_html or 'plotly' in report_html
        assert 'histogram' in report_html.lower() or 'trace' in report_html.lower()
    
    def test_report_contains_statistics_table(self, sample_features_data, sample_splits_metadata):
        """Test report includes statistics table."""
        generator = FeaturesReportGenerator()
        report_html = generator.generate_features_report(
            features_data=sample_features_data,
            splits_metadata=sample_splits_metadata
        )
        
        # Check for statistics table markers
        assert 'Feature Statistics' in report_html or 'statistics' in report_html.lower()
        assert 'Mean' in report_html or 'mean' in report_html.lower()
    
    def test_report_contains_shift_detection(self, sample_features_data, sample_splits_metadata):
        """Test report includes distribution shift analysis."""
        generator = FeaturesReportGenerator()
        report_html = generator.generate_features_report(
            features_data=sample_features_data,
            splits_metadata=sample_splits_metadata
        )
        
        # Check for shift detection section
        assert 'shift' in report_html.lower() or 'distribution' in report_html.lower()
    
    def test_report_contains_leakage_check(self, sample_features_data, sample_splits_metadata):
        """Test report includes data leakage verification section."""
        generator = FeaturesReportGenerator()
        report_html = generator.generate_features_report(
            features_data=sample_features_data,
            splits_metadata=sample_splits_metadata
        )
        
        # Check for leakage check section
        assert 'Leakage' in report_html or 'leakage' in report_html.lower() or 'Verification' in report_html
    
    def test_save_report(self, sample_features_data, sample_splits_metadata, tmp_path):
        """Test report saving to file."""
        generator = FeaturesReportGenerator()
        report_html = generator.generate_features_report(
            features_data=sample_features_data,
            splits_metadata=sample_splits_metadata
        )
        
        output_file = tmp_path / "features_distribution_report.html"
        saved_path = generator.save_report(report_html, str(output_file))
        
        # Check file was created
        assert Path(saved_path).exists()
        
        # Check content
        with open(saved_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert 'histogram' in content.lower() or 'plotly' in content.lower()
    
    def test_aggregate_features_by_split(self, sample_features_data):
        """Test aggregation of features across symbols per split."""
        generator = FeaturesReportGenerator()
        aggregated = generator._aggregate_features_by_split(sample_features_data)
        
        # Check aggregation
        assert 'train' in aggregated
        assert 'val' in aggregated
        assert 'test' in aggregated
        
        # Check shapes (should combine AAPL and MSFT)
        assert aggregated['train'].shape[0] == 2000  # 1000 + 1000
        assert aggregated['val'].shape[0] == 400  # 200 + 200
        assert aggregated['test'].shape[0] == 400  # 200 + 200
    
    def test_compute_feature_statistics(self, sample_features_data):
        """Test computation of feature statistics."""
        generator = FeaturesReportGenerator()
        aggregated = generator._aggregate_features_by_split(sample_features_data)
        stats = generator._compute_feature_statistics(aggregated)
        
        # Check stats structure
        assert 'train' in stats
        assert 'val' in stats
        assert 'test' in stats
        
        # Check feature names
        for split in stats:
            for feature in stats[split]:
                assert 'mean' in stats[split][feature]
                assert 'std' in stats[split][feature]
                assert 'min' in stats[split][feature]
                assert 'max' in stats[split][feature]
                assert 'median' in stats[split][feature]
    
    def test_detect_distribution_shifts(self, sample_features_data):
        """Test distribution shift detection."""
        generator = FeaturesReportGenerator()
        aggregated = generator._aggregate_features_by_split(sample_features_data)
        stats = generator._compute_feature_statistics(aggregated)
        shifts = generator._detect_distribution_shifts(aggregated, stats)
        
        # Check shifts structure
        assert 'train_vs_val' in shifts or 'val_vs_test' in shifts or 'train_vs_test' in shifts
        
        # Check shift metrics
        for pair_key in shifts:
            for feature in shifts[pair_key]:
                shift_data = shifts[pair_key][feature]
                assert 'mean_shift_pct' in shift_data
                assert 'std_shift_pct' in shift_data
                assert isinstance(shift_data['mean_shift_pct'], float)
                assert isinstance(shift_data['std_shift_pct'], float)
    
    def test_statistics_validity(self, sample_features_data):
        """Test that computed statistics are valid."""
        generator = FeaturesReportGenerator()
        aggregated = generator._aggregate_features_by_split(sample_features_data)
        stats = generator._compute_feature_statistics(aggregated)
        
        # Verify statistics validity
        for split in stats:
            for feature in stats[split]:
                s = stats[split][feature]
                
                # Min <= quantiles <= max
                assert s['min'] <= s['25%'] <= s['median'] <= s['75%'] <= s['max']
                
                # Mean and std are non-negative std
                assert s['std'] >= 0
                
                # Count should be positive
                assert s['count'] > 0
    
    def test_no_nan_in_report_generation(self, sample_features_data, sample_splits_metadata):
        """Test that report generation handles NaN values gracefully."""
        # Add some NaN values to features
        for symbol in sample_features_data:
            for split in sample_features_data[symbol]:
                sample_features_data[symbol][split].iloc[0, 0] = np.nan
        
        generator = FeaturesReportGenerator()
        
        # Should not raise error
        report_html = generator.generate_features_report(
            features_data=sample_features_data,
            splits_metadata=sample_splits_metadata
        )
        
        assert len(report_html) > 0
    
    def test_single_symbol_features(self, sample_splits_metadata):
        """Test report generation with single symbol."""
        np.random.seed(42)
        
        features_data = {
            'AAPL': {
                'train': pd.DataFrame({
                    'return_simple': np.random.normal(0.001, 0.02, 500),
                    'rsi_14': np.random.uniform(20, 80, 500),
                }),
                'val': pd.DataFrame({
                    'return_simple': np.random.normal(0.001, 0.02, 100),
                    'rsi_14': np.random.uniform(20, 80, 100),
                }),
                'test': pd.DataFrame({
                    'return_simple': np.random.normal(0.001, 0.02, 100),
                    'rsi_14': np.random.uniform(20, 80, 100),
                })
            }
        }
        
        generator = FeaturesReportGenerator()
        report_html = generator.generate_features_report(
            features_data=features_data,
            splits_metadata=sample_splits_metadata
        )
        
        assert len(report_html) > 0
        assert 'return_simple' in report_html or 'rsi' in report_html.lower()
    
    def test_many_features_handling(self, sample_splits_metadata):
        """Test report generation with many features."""
        np.random.seed(42)
        n_features = 50
        
        feature_data = {f'feature_{i}': np.random.normal(0, 1, 1000) for i in range(n_features)}
        
        features_data = {
            'AAPL': {
                'train': pd.DataFrame({**feature_data}),
                'val': pd.DataFrame({f: np.random.normal(0, 1, 200) for f in feature_data}),
                'test': pd.DataFrame({f: np.random.normal(0, 1, 200) for f in feature_data}),
            }
        }
        
        generator = FeaturesReportGenerator()
        
        # Should complete without error (may limit visualization to first 6 features)
        report_html = generator.generate_features_report(
            features_data=features_data,
            splits_metadata=sample_splits_metadata
        )
        
        assert len(report_html) > 0
