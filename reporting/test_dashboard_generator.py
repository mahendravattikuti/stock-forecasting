"""
Tests for data quality dashboard generator.

Tests the DashboardGenerator class with various data scenarios to verify:
- HTML dashboard generation
- Plotly components presence
- All charts render correctly
- Summary statistics calculation
- File save operations
- Edge cases (empty data, missing manifests)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
import tempfile

import pytest

from reporting.dashboard_generator import (
    DashboardGenerator, 
    load_context_from_results_directory,
    AblationDashboardGenerator,
    load_ablation_results
)


@pytest.fixture
def sample_cleaning_reports() -> Dict[str, Dict[str, Any]]:
    """Create sample cleaning reports for testing."""
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
        },
        'GOOGL': {
            'symbol': 'GOOGL',
            'report_timestamp': '2024-01-19T10:31:00Z',
            'raw_data_rows': 2150,
            'raw_date_range': ['2004-08-19', '2024-01-19'],
            'missing_values_detected': 5,
            'date_gaps_detected': 2,
            'spikes_detected': 2,
            'ohlc_violations_detected': 1,
            'forward_fills_applied': 3,
            'spikes_corrected': 2,
            'ohlc_corrections_applied': 1,
            'adjustments_applied': 1,
            'rows_excluded': 7,
            'cleaned_data_rows': 2143,
            'cleaned_date_range': ['2004-08-19', '2024-01-19'],
            'validation_passed': True,
            'validation_errors': [],
            'completeness_percent': 99.67,
            'quality_status': 'PASS',
            'quality_notes': 'Minor cleaning performed'
        }
    }


@pytest.fixture
def sample_features_manifests() -> Dict[str, Dict[str, Any]]:
    """Create sample feature manifests for testing."""
    return {
        'AAPL': {
            'symbol': 'AAPL',
            'timestamp': '2024-01-19T10:35:00Z',
            'features': [
                {'name': 'simple_return', 'tier': 1, 'type': 'return'},
                {'name': 'log_return', 'tier': 1, 'type': 'return'},
                {'name': 'normalized_close', 'tier': 1, 'type': 'normalized'},
                {'name': 'rsi_14', 'tier': 2, 'type': 'technical'},
                {'name': 'macd_line', 'tier': 2, 'type': 'technical'},
                {'name': 'bollinger_bands', 'tier': 2, 'type': 'technical'},
                {'name': 'momentum_5', 'tier': 2, 'type': 'technical'},
                {'name': 'momentum_20', 'tier': 2, 'type': 'technical'},
                {'name': 'regime', 'tier': 3, 'type': 'regime'}
            ],
            'tier_counts': {'tier1': 3, 'tier2': 5, 'tier3': 1},
            'causality_verified': True
        },
        'MSFT': {
            'symbol': 'MSFT',
            'timestamp': '2024-01-19T10:35:30Z',
            'features': [
                {'name': 'simple_return', 'tier': 1, 'type': 'return'},
                {'name': 'log_return', 'tier': 1, 'type': 'return'},
                {'name': 'normalized_close', 'tier': 1, 'type': 'normalized'},
                {'name': 'rsi_14', 'tier': 2, 'type': 'technical'},
                {'name': 'macd_line', 'tier': 2, 'type': 'technical'},
                {'name': 'bollinger_bands', 'tier': 2, 'type': 'technical'},
            ],
            'tier_counts': {'tier1': 3, 'tier2': 3},
            'causality_verified': True
        },
        'GOOGL': {
            'symbol': 'GOOGL',
            'timestamp': '2024-01-19T10:36:00Z',
            'features': [
                {'name': 'simple_return', 'tier': 1, 'type': 'return'},
                {'name': 'log_return', 'tier': 1, 'type': 'return'},
                {'name': 'normalized_close', 'tier': 1, 'type': 'normalized'},
                {'name': 'rsi_14', 'tier': 2, 'type': 'technical'},
                {'name': 'macd_line', 'tier': 2, 'type': 'technical'},
                {'name': 'regime', 'tier': 3, 'type': 'regime'}
            ],
            'tier_counts': {'tier1': 3, 'tier2': 2, 'tier3': 1},
            'causality_verified': True
        }
    }


class TestDashboardGenerator:
    """Test suite for DashboardGenerator."""
    
    def test_initialization(self):
        """Test DashboardGenerator initialization."""
        generator = DashboardGenerator()
        assert generator is not None
        assert generator.logger is not None
    
    def test_generate_dashboard_basic(self, sample_cleaning_reports, sample_features_manifests):
        """Test basic dashboard generation with sample data."""
        generator = DashboardGenerator()
        
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests
        )
        
        # Verify HTML is generated
        assert isinstance(html, str)
        assert len(html) > 0
        assert html.startswith('<!DOCTYPE html>') or '<html' in html or 'plotly' in html.lower()
    
    def test_plotly_components_present(self, sample_cleaning_reports, sample_features_manifests):
        """Test that Plotly components are present in generated HTML."""
        generator = DashboardGenerator()
        
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests
        )
        
        # Check for Plotly library inclusion
        assert 'plotly' in html.lower()
        assert 'go.' in html or 'scatter' in html.lower() or 'bar' in html.lower()
    
    def test_summary_section_present(self, sample_cleaning_reports, sample_features_manifests):
        """Test that summary statistics section is included."""
        generator = DashboardGenerator()
        
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests
        )
        
        # Check for summary section
        assert 'Summary Statistics' in html or 'summary' in html.lower()
        assert 'Symbols Processed' in html or 'symbols' in html.lower()
    
    def test_all_symbols_represented(self, sample_cleaning_reports, sample_features_manifests):
        """Test that all symbols are represented in dashboard."""
        generator = DashboardGenerator()
        
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests
        )
        
        # Check that all symbols are present
        for symbol in sample_cleaning_reports.keys():
            assert symbol in html
    
    def test_completeness_metrics_extraction(self, sample_cleaning_reports):
        """Test extraction of completeness metrics."""
        generator = DashboardGenerator()
        
        metrics = generator._extract_completeness_metrics(sample_cleaning_reports)
        
        assert len(metrics) == 3
        assert 'AAPL' in metrics
        assert 'MSFT' in metrics
        assert 'GOOGL' in metrics
        
        # Verify structure
        assert metrics['AAPL']['completeness_percent'] == 99.88
        assert metrics['AAPL']['raw_rows'] == 2525
        assert metrics['AAPL']['cleaned_rows'] == 2522
        assert metrics['MSFT']['completeness_percent'] == 100.0
    
    def test_cleaning_impact_extraction(self, sample_cleaning_reports):
        """Test extraction of cleaning impact statistics."""
        generator = DashboardGenerator()
        
        impact = generator._extract_cleaning_impact(sample_cleaning_reports)
        
        # Verify aggregation
        assert impact['actions']['forward_fills'] == 5  # 2 + 0 + 3
        assert impact['actions']['spikes_corrected'] == 2  # 0 + 0 + 2
        assert impact['actions']['ohlc_corrections'] == 1  # 0 + 0 + 1
        assert impact['actions']['adjustments'] == 4  # 1 + 2 + 1
        assert impact['total_rows_removed'] == 10  # 3 + 0 + 7
    
    def test_missing_data_trends_extraction(self, sample_cleaning_reports):
        """Test extraction of missing data trends."""
        generator = DashboardGenerator()
        
        trends = generator._extract_missing_data_trends(sample_cleaning_reports)
        
        assert len(trends) == 3
        assert trends['AAPL']['missing_values_detected'] == 2
        assert trends['MSFT']['date_gaps_detected'] == 0
        assert trends['GOOGL']['rows_excluded'] == 7
    
    def test_feature_stats_extraction(self, sample_features_manifests):
        """Test extraction of feature statistics."""
        generator = DashboardGenerator()
        
        stats = generator._extract_feature_stats(sample_features_manifests)
        
        assert 'tier_counts' in stats
        assert stats['tier_counts']['tier1'] >= 3
        assert stats['tier_counts']['tier2'] >= 5
        assert stats['tier_counts']['tier3'] >= 1
    
    def test_save_dashboard(self, sample_cleaning_reports, sample_features_manifests):
        """Test saving dashboard to file."""
        generator = DashboardGenerator()
        
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_dashboard.html"
            
            saved_path = generator.save_dashboard(html, str(output_path))
            
            # Verify file was saved
            assert Path(saved_path).exists()
            
            # Verify content
            with open(saved_path, 'r') as f:
                content = f.read()
                assert content == html
    
    def test_save_dashboard_creates_directories(self, sample_cleaning_reports, sample_features_manifests):
        """Test that save_dashboard creates parent directories."""
        generator = DashboardGenerator()
        
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "another" / "test_dashboard.html"
            
            saved_path = generator.save_dashboard(html, str(output_path))
            
            # Verify file was saved in nested directory
            assert Path(saved_path).exists()
            assert Path(saved_path).parent.exists()
    
    def test_generate_dashboard_empty_manifests(self, sample_cleaning_reports):
        """Test dashboard generation with empty feature manifests."""
        generator = DashboardGenerator()
        
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests={}
        )
        
        # Should still generate dashboard
        assert isinstance(html, str)
        assert len(html) > 0
    
    def test_generate_dashboard_single_symbol(self):
        """Test dashboard generation with single symbol."""
        cleaning_reports = {
            'AAPL': {
                'symbol': 'AAPL',
                'raw_data_rows': 2500,
                'cleaned_data_rows': 2495,
                'completeness_percent': 99.8,
                'quality_status': 'PASS',
                'forward_fills_applied': 1,
                'spikes_corrected': 0,
                'ohlc_corrections_applied': 0,
                'adjustments_applied': 0,
                'rows_excluded': 5
            }
        }
        
        generator = DashboardGenerator()
        html = generator.generate_dashboard(
            cleaning_reports=cleaning_reports,
            features_manifests={}
        )
        
        assert isinstance(html, str)
        assert 'AAPL' in html
    
    def test_generate_dashboard_many_symbols(self):
        """Test dashboard generation with many symbols."""
        # Create reports for 20 symbols
        cleaning_reports = {}
        for i in range(20):
            symbol = f"SYM{i:02d}"
            cleaning_reports[symbol] = {
                'symbol': symbol,
                'raw_data_rows': 2500 + i * 10,
                'cleaned_data_rows': 2495 + i * 10,
                'completeness_percent': 99.8 - i * 0.01,
                'quality_status': 'PASS',
                'forward_fills_applied': i % 3,
                'spikes_corrected': i % 5,
                'ohlc_corrections_applied': i % 2,
                'adjustments_applied': i % 4,
                'rows_excluded': 5 + i
            }
        
        generator = DashboardGenerator()
        html = generator.generate_dashboard(
            cleaning_reports=cleaning_reports,
            features_manifests={}
        )
        
        assert isinstance(html, str)
        assert len(html) > 1000  # Substantial HTML
        
        # Verify some symbols are present
        assert 'SYM00' in html
        assert 'SYM19' in html
    
    def test_load_context_from_results_directory(self):
        """Test loading context from results directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create results directory structure
            results_dir = Path(tmpdir)
            cleaning_dir = results_dir / "cleaning_reports"
            manifest_dir = results_dir / "features_manifests"
            
            cleaning_dir.mkdir(parents=True)
            manifest_dir.mkdir(parents=True)
            
            # Write sample files
            cleaning_report = {
                'symbol': 'AAPL',
                'raw_data_rows': 2500,
                'cleaned_data_rows': 2495,
                'completeness_percent': 99.8
            }
            
            feature_manifest = {
                'symbol': 'AAPL',
                'features': [{'name': 'return', 'tier': 1}]
            }
            
            with open(cleaning_dir / "AAPL.json", 'w') as f:
                json.dump(cleaning_report, f)
            
            with open(manifest_dir / "AAPL.json", 'w') as f:
                json.dump(feature_manifest, f)
            
            # Load context
            cleaning_reports, features_manifests = load_context_from_results_directory(str(results_dir))
            
            assert 'AAPL' in cleaning_reports
            assert 'AAPL' in features_manifests
            assert cleaning_reports['AAPL']['completeness_percent'] == 99.8
            assert len(features_manifests['AAPL']['features']) == 1
    
    def test_load_context_missing_directories(self):
        """Test loading from directory with missing subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create subdirectories
            cleaning_reports, features_manifests = load_context_from_results_directory(tmpdir)
            
            # Should return empty dicts
            assert cleaning_reports == {}
            assert features_manifests == {}
    
    def test_html_contains_key_statistics(self, sample_cleaning_reports, sample_features_manifests):
        """Test that HTML contains key statistics values."""
        generator = DashboardGenerator()
        
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests
        )
        
        # Check for key values in HTML
        assert '3' in html  # 3 symbols
        assert '99' in html  # Completeness percentage
        assert 'PASS' in html  # Quality status


class TestDashboardGeneratorIntegration:
    """Integration tests for dashboard generator."""
    
    def test_full_workflow(self, sample_cleaning_reports, sample_features_manifests):
        """Test complete dashboard generation workflow."""
        generator = DashboardGenerator()
        
        # Generate dashboard
        html = generator.generate_dashboard(
            cleaning_reports=sample_cleaning_reports,
            features_manifests=sample_features_manifests
        )
        
        # Save dashboard
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results" / "visualizations" / "dashboard.html"
            
            saved_path = generator.save_dashboard(html, str(output_path))
            
            # Verify file exists and contains expected content
            assert Path(saved_path).exists()
            
            with open(saved_path, 'r') as f:
                saved_content = f.read()
            
            # Verify content
            assert 'AAPL' in saved_content
            assert 'plotly' in saved_content.lower()
    
    def test_dashboard_with_varied_quality_statuses(self):
        """Test dashboard with varied quality statuses."""
        cleaning_reports = {
            'PASS_SYMBOL': {
                'symbol': 'PASS_SYMBOL',
                'raw_data_rows': 2500,
                'cleaned_data_rows': 2495,
                'completeness_percent': 99.8,
                'quality_status': 'PASS',
                'forward_fills_applied': 1,
                'spikes_corrected': 0,
                'ohlc_corrections_applied': 0,
                'adjustments_applied': 0,
                'rows_excluded': 5
            },
            'WARNING_SYMBOL': {
                'symbol': 'WARNING_SYMBOL',
                'raw_data_rows': 2400,
                'cleaned_data_rows': 2350,
                'completeness_percent': 97.9,
                'quality_status': 'WARNING',
                'forward_fills_applied': 5,
                'spikes_corrected': 3,
                'ohlc_corrections_applied': 2,
                'adjustments_applied': 1,
                'rows_excluded': 50
            }
        }
        
        generator = DashboardGenerator()
        html = generator.generate_dashboard(
            cleaning_reports=cleaning_reports,
            features_manifests={}
        )
        
        # Verify both statuses are in HTML
        assert 'PASS' in html
        assert 'WARNING' in html


@pytest.fixture
def sample_ablation_results() -> Dict[str, Any]:
    """Create sample ablation results for testing."""
    return {
        'baseline': {
            'mae': 0.0185,
            'rmse': 0.0245,
            'directional_accuracy': 0.562
        },
        'ablations': [
            {
                'name': 'remove_rsi',
                'description': 'Remove RSI-based momentum features',
                'removed_columns': ['rsi_14', 'rsi_9', 'rsi_21'],
                'validation_metrics': {'mae': 0.0195, 'rmse': 0.0255, 'directional_accuracy': 0.550},
                'test_metrics': {'mae': 0.0210, 'rmse': 0.0275, 'directional_accuracy': 0.545},
                'delta_validation': {'mae': 0.0010, 'rmse': 0.0010, 'directional_accuracy': -0.012},
                'delta_test': {'mae': 0.0025, 'rmse': 0.0030, 'directional_accuracy': -0.017}
            },
            {
                'name': 'remove_macd',
                'description': 'Remove MACD family features',
                'removed_columns': ['macd_line', 'macd_signal', 'macd_histogram'],
                'validation_metrics': {'mae': 0.0192, 'rmse': 0.0250, 'directional_accuracy': 0.555},
                'test_metrics': {'mae': 0.0198, 'rmse': 0.0262, 'directional_accuracy': 0.552},
                'delta_validation': {'mae': 0.0007, 'rmse': 0.0005, 'directional_accuracy': -0.007},
                'delta_test': {'mae': 0.0013, 'rmse': 0.0017, 'directional_accuracy': -0.010}
            },
            {
                'name': 'remove_tier2',
                'description': 'Remove all Tier-2 technical indicators',
                'removed_columns': ['rsi_14', 'macd_line', 'macd_signal', 'bollinger_upper', 'bollinger_lower', 
                                   'stochastic_k', 'atr_14', 'adx_14', 'obv', 'momentum', 'volatility'],
                'validation_metrics': {'mae': 0.0225, 'rmse': 0.0290, 'directional_accuracy': 0.530},
                'test_metrics': {'mae': 0.0245, 'rmse': 0.0310, 'directional_accuracy': 0.520},
                'delta_validation': {'mae': 0.0040, 'rmse': 0.0045, 'directional_accuracy': -0.032},
                'delta_test': {'mae': 0.0060, 'rmse': 0.0065, 'directional_accuracy': -0.042}
            },
            {
                'name': 'remove_tier3',
                'description': 'Remove Tier-3 market context features',
                'removed_columns': ['market_regime', 'sector_momentum', 'market_beta', 'cross_asset_correlation'],
                'validation_metrics': {'mae': 0.0188, 'rmse': 0.0248, 'directional_accuracy': 0.560},
                'test_metrics': {'mae': 0.0192, 'rmse': 0.0255, 'directional_accuracy': 0.558},
                'delta_validation': {'mae': 0.0003, 'rmse': 0.0003, 'directional_accuracy': -0.002},
                'delta_test': {'mae': 0.0007, 'rmse': 0.0010, 'directional_accuracy': -0.004}
            },
            {
                'name': 'remove_signal_processing',
                'description': 'Remove all signal-processing features',
                'removed_columns': ['wavelet_approximation', 'wavelet_detail', 'wavelet_energy', 
                                   'ssa_component_1', 'ssa_component_2', 'ssa_reconstruction',
                                   'kalman_state', 'kalman_smoothed', 'kalman_gain'],
                'validation_metrics': {'mae': 0.0198, 'rmse': 0.0258, 'directional_accuracy': 0.545},
                'test_metrics': {'mae': 0.0218, 'rmse': 0.0282, 'directional_accuracy': 0.535},
                'delta_validation': {'mae': 0.0013, 'rmse': 0.0013, 'directional_accuracy': -0.017},
                'delta_test': {'mae': 0.0033, 'rmse': 0.0037, 'directional_accuracy': -0.027}
            }
        ]
    }


@pytest.fixture
def sample_ablation_plan() -> Dict[str, Any]:
    """Create sample ablation plan for testing."""
    return {
        'name': 'phase_15_default',
        'feature_groups': {
            'full_feature_set': {
                'columns': [],
                'description': 'Full feature set baseline'
            },
            'remove_rsi': {
                'columns': ['rsi_14', 'rsi_9', 'rsi_21'],
                'description': 'Remove RSI-based momentum features'
            },
            'remove_tier2': {
                'columns': ['rsi_14', 'macd_line', 'macd_signal', 'bollinger_upper', 'bollinger_lower'],
                'description': 'Remove all Tier-2 technical indicators'
            }
        }
    }


class TestAblationDashboardGenerator:
    """Test suite for AblationDashboardGenerator."""
    
    def test_initialization(self):
        """Test AblationDashboardGenerator initialization."""
        generator = AblationDashboardGenerator()
        assert generator is not None
        assert generator.logger is not None
    
    def test_generate_ablation_dashboard_basic(self, sample_ablation_results):
        """Test basic ablation dashboard generation."""
        generator = AblationDashboardGenerator()
        
        html = generator.generate_ablation_dashboard(sample_ablation_results)
        
        # Verify HTML is generated
        assert isinstance(html, str)
        assert len(html) > 0
        assert 'plotly' in html.lower()
    
    def test_ablation_dashboard_contains_all_ablations(self, sample_ablation_results):
        """Test that all ablations are represented in dashboard."""
        generator = AblationDashboardGenerator()
        
        html = generator.generate_ablation_dashboard(sample_ablation_results)
        
        # Check that all ablation names are present
        for ablation in sample_ablation_results['ablations']:
            assert ablation['name'] in html
    
    def test_ablation_dashboard_contains_metrics(self, sample_ablation_results):
        """Test that key metrics are present in dashboard."""
        generator = AblationDashboardGenerator()
        
        html = generator.generate_ablation_dashboard(sample_ablation_results)
        
        # Check for key metric labels
        assert 'MAE' in html
        assert 'RMSE' in html
        assert 'directional' in html.lower() or 'accuracy' in html.lower()
    
    def test_sort_ablations_by_impact(self, sample_ablation_results):
        """Test sorting of ablations by impact."""
        generator = AblationDashboardGenerator()
        
        ablations = sample_ablation_results['ablations']
        sorted_ablations = generator._sort_ablations_by_impact(ablations)
        
        # First should be remove_tier2 (highest MAE delta of 0.0060)
        assert sorted_ablations[0]['name'] == 'remove_tier2'
        
        # Verify descending order by MAE delta
        for i in range(len(sorted_ablations) - 1):
            mae_delta_i = abs(sorted_ablations[i].get('delta_test', {}).get('mae', 0))
            mae_delta_next = abs(sorted_ablations[i+1].get('delta_test', {}).get('mae', 0))
            assert mae_delta_i >= mae_delta_next
    
    def test_prepare_heatmap_data(self, sample_ablation_results):
        """Test preparation of heatmap data."""
        generator = AblationDashboardGenerator()
        
        ablations = sample_ablation_results['ablations']
        sorted_ablations = generator._sort_ablations_by_impact(ablations)
        
        z_data, y_labels, x_labels = generator._prepare_heatmap_data(sorted_ablations)
        
        # Verify structure
        assert len(z_data) == len(sorted_ablations)
        assert len(y_labels) == len(sorted_ablations)
        assert len(x_labels) == 3  # mae, rmse, directional_accuracy
        
        # Each row should have 3 values
        for row in z_data:
            assert len(row) == 3
    
    def test_extract_tier_contributions(self, sample_ablation_results):
        """Test extraction of feature tier contributions."""
        generator = AblationDashboardGenerator()
        
        ablations = sample_ablation_results['ablations']
        tier_contributions = generator._extract_tier_contributions(ablations)
        
        # Should have some tier contributions
        assert isinstance(tier_contributions, dict)
        assert len(tier_contributions) > 0
    
    def test_save_ablation_dashboard(self, sample_ablation_results):
        """Test saving ablation dashboard to file."""
        generator = AblationDashboardGenerator()
        
        html = generator.generate_ablation_dashboard(sample_ablation_results)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ablation_dashboard.html"
            
            saved_path = generator.save_dashboard(html, str(output_path))
            
            # Verify file was saved
            assert Path(saved_path).exists()
            
            # Verify content
            with open(saved_path, 'r') as f:
                content = f.read()
                assert content == html
    
    def test_generate_ablation_dashboard_with_plan(self, sample_ablation_results, sample_ablation_plan):
        """Test ablation dashboard generation with ablation plan."""
        generator = AblationDashboardGenerator()
        
        html = generator.generate_ablation_dashboard(
            ablation_results=sample_ablation_results,
            ablation_plan=sample_ablation_plan
        )
        
        # Should still generate successfully
        assert isinstance(html, str)
        assert len(html) > 0
    
    def test_generate_empty_dashboard(self):
        """Test generation of empty dashboard when no results provided."""
        generator = AblationDashboardGenerator()
        
        html = generator._generate_empty_dashboard()
        
        # Should generate minimal dashboard
        assert isinstance(html, str)
        assert len(html) > 0
    
    def test_ablation_dashboard_with_single_ablation(self):
        """Test ablation dashboard with single ablation."""
        ablation_results = {
            'baseline': {
                'mae': 0.0185,
                'rmse': 0.0245,
                'directional_accuracy': 0.562
            },
            'ablations': [
                {
                    'name': 'remove_rsi',
                    'description': 'Remove RSI',
                    'removed_columns': ['rsi_14'],
                    'validation_metrics': {'mae': 0.0195, 'rmse': 0.0255, 'directional_accuracy': 0.550},
                    'test_metrics': {'mae': 0.0210, 'rmse': 0.0275, 'directional_accuracy': 0.545},
                    'delta_validation': {'mae': 0.0010, 'rmse': 0.0010, 'directional_accuracy': -0.012},
                    'delta_test': {'mae': 0.0025, 'rmse': 0.0030, 'directional_accuracy': -0.017}
                }
            ]
        }
        
        generator = AblationDashboardGenerator()
        html = generator.generate_ablation_dashboard(ablation_results)
        
        assert isinstance(html, str)
        assert 'remove_rsi' in html
    
    def test_ablation_dashboard_summary_section(self, sample_ablation_results):
        """Test that summary section is added to ablation dashboard."""
        generator = AblationDashboardGenerator()
        
        html = generator.generate_ablation_dashboard(sample_ablation_results)
        
        # Check for summary section elements
        assert 'Ablation Study Summary' in html or 'summary' in html.lower()
        assert 'Baseline' in html
        assert 'Impact' in html or 'impact' in html.lower()
    
    def test_load_ablation_results_from_files(self):
        """Test loading ablation results from files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)
            
            # Create ablation results file
            ablation_results = {
                'baseline': {'mae': 0.0185, 'rmse': 0.0245, 'directional_accuracy': 0.562},
                'ablations': []
            }
            
            with open(results_dir / "ablation_results.json", 'w') as f:
                json.dump(ablation_results, f)
            
            # Load results
            loaded_results, loaded_plan = load_ablation_results(str(results_dir))
            
            assert 'baseline' in loaded_results
            assert loaded_results['baseline']['mae'] == 0.0185
    
    def test_load_ablation_plan_from_files(self):
        """Test loading ablation plan from files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)
            
            # Create ablation plan file
            ablation_plan = {
                'name': 'test_plan',
                'feature_groups': {
                    'group1': {'columns': ['col1'], 'description': 'Group 1'}
                }
            }
            
            with open(results_dir / "ablation_plan.json", 'w') as f:
                json.dump(ablation_plan, f)
            
            # Load plan
            loaded_results, loaded_plan = load_ablation_results(str(results_dir))
            
            assert 'name' in loaded_plan
            assert loaded_plan['name'] == 'test_plan'


class TestAblationDashboardIntegration:
    """Integration tests for ablation dashboard."""
    
    def test_full_ablation_workflow(self, sample_ablation_results, sample_ablation_plan):
        """Test complete ablation dashboard workflow."""
        generator = AblationDashboardGenerator()
        
        # Generate dashboard
        html = generator.generate_ablation_dashboard(
            ablation_results=sample_ablation_results,
            ablation_plan=sample_ablation_plan
        )
        
        # Save dashboard
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results" / "visualizations" / "ablation_dashboard.html"
            
            saved_path = generator.save_dashboard(html, str(output_path))
            
            # Verify file exists and contains expected content
            assert Path(saved_path).exists()
            
            with open(saved_path, 'r') as f:
                saved_content = f.read()
            
            # Verify content
            assert 'remove_tier2' in saved_content  # Most impactful
            assert 'plotly' in saved_content.lower()
            assert 'Ablation Study Summary' in saved_content or 'summary' in saved_content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
