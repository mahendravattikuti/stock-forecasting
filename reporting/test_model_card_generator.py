"""
Test suite for Model Card Generator.

Tests cover:
- Model card generation with sample data
- Markdown output format validity
- All required sections present
- Edge cases (missing data, single baseline, etc.)
- Data loading from results directory
- Output file saving
"""

import pytest
import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from reporting.model_card_generator import (
    ModelCardGenerator,
    ModelCardContext,
    load_context_from_results_directory
)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Create sample pipeline configuration."""
    return {
        'data_acquisition': {
            'primary_source': 'iex_cloud',
            'fallback_source': 'yfinance',
            'lookback_years': 10,
        },
        'symbols': {
            'list': ['AAPL', 'MSFT', 'GOOGL'],
            'max_portfolio_size': 100,
        },
        'feature_engineering': {
            'include_tier1': True,
            'include_tier2': True,
            'include_tier3': False,
        },
        'random_seeds': {
            'seed': 42,
            'numpy': 42,
            'random': 42,
            'tensorflow': 42,
        }
    }


@pytest.fixture
def sample_cleaning_reports() -> Dict[str, Dict[str, Any]]:
    """Create sample cleaning reports for multiple symbols."""
    return {
        'AAPL': {
            'symbol': 'AAPL',
            'raw_data_stats': {
                'total_rows': 2525,
                'date_range': ['2002-01-02', '2024-01-19'],
                'missing_values': 5,
            },
            'cleaned_data_stats': {
                'total_rows_retained': 2520,
                'date_range': ['2002-01-02', '2024-01-19'],
                'missing_values': 0,
                'rows_excluded': 5,
            },
            'cleaning_actions': {
                'forward_fills': {'count': 2},
                'spike_removals': {'count': 1},
                'ohlc_corrections': {'count': 1},
                'split_adjustments': {'count': 1},
            }
        },
        'MSFT': {
            'symbol': 'MSFT',
            'raw_data_stats': {
                'total_rows': 2530,
                'date_range': ['2002-01-02', '2024-01-19'],
                'missing_values': 0,
            },
            'cleaned_data_stats': {
                'total_rows_retained': 2530,
                'date_range': ['2002-01-02', '2024-01-19'],
                'missing_values': 0,
                'rows_excluded': 0,
            },
            'cleaning_actions': {
                'forward_fills': {'count': 0},
                'spike_removals': {'count': 0},
                'ohlc_corrections': {'count': 0},
                'split_adjustments': {'count': 2},
            }
        },
        'GOOGL': {
            'symbol': 'GOOGL',
            'raw_data_stats': {
                'total_rows': 2000,
                'date_range': ['2008-08-19', '2024-01-19'],
                'missing_values': 2,
            },
            'cleaned_data_stats': {
                'total_rows_retained': 1998,
                'date_range': ['2008-08-19', '2024-01-19'],
                'missing_values': 0,
                'rows_excluded': 2,
            },
            'cleaning_actions': {
                'forward_fills': {'count': 1},
                'spike_removals': {'count': 0},
                'ohlc_corrections': {'count': 0},
                'split_adjustments': {'count': 0},
            }
        }
    }


@pytest.fixture
def sample_features_manifests() -> Dict[str, Dict[str, Any]]:
    """Create sample features manifests."""
    return {
        'AAPL': {
            'symbol': 'AAPL',
            'features': [
                {
                    'tier': 1,
                    'module_name': 'returns',
                    'feature_names': ['simple_return', 'log_return'],
                    'description': 'Basic return calculations'
                },
                {
                    'tier': 1,
                    'module_name': 'normalized_prices',
                    'feature_names': ['normalized_close', 'normalized_volume'],
                    'description': 'Normalized price and volume'
                },
                {
                    'tier': 2,
                    'module_name': 'technical_indicators',
                    'feature_names': ['rsi_14', 'macd_line', 'bb_upper', 'bb_lower', 'atr_14'],
                    'description': 'Technical indicators'
                },
            ]
        },
        'MSFT': {
            'symbol': 'MSFT',
            'features': [
                {
                    'tier': 1,
                    'module_name': 'returns',
                    'feature_names': ['simple_return', 'log_return'],
                    'description': 'Basic return calculations'
                },
                {
                    'tier': 1,
                    'module_name': 'normalized_prices',
                    'feature_names': ['normalized_close', 'normalized_volume'],
                    'description': 'Normalized price and volume'
                },
                {
                    'tier': 2,
                    'module_name': 'technical_indicators',
                    'feature_names': ['rsi_14', 'macd_line', 'bb_upper', 'bb_lower', 'atr_14'],
                    'description': 'Technical indicators'
                },
            ]
        },
        'GOOGL': {
            'symbol': 'GOOGL',
            'features': [
                {
                    'tier': 1,
                    'module_name': 'returns',
                    'feature_names': ['simple_return', 'log_return'],
                    'description': 'Basic return calculations'
                },
                {
                    'tier': 1,
                    'module_name': 'normalized_prices',
                    'feature_names': ['normalized_close', 'normalized_volume'],
                    'description': 'Normalized price and volume'
                },
                {
                    'tier': 2,
                    'module_name': 'technical_indicators',
                    'feature_names': ['rsi_14', 'macd_line', 'bb_upper', 'bb_lower', 'atr_14'],
                    'description': 'Technical indicators'
                },
            ]
        }
    }


@pytest.fixture
def sample_splits_metadata() -> Dict[str, Any]:
    """Create sample splits metadata."""
    return {
        'train_start_date': '2002-01-02',
        'train_end_date': '2017-02-20',
        'val_start_date': '2017-02-21',
        'val_end_date': '2020-01-01',
        'test_start_date': '2020-01-02',
        'test_end_date': '2024-01-19',
        'train_rows': 3800,
        'val_rows': 600,
        'test_rows': 600,
        'temporal_integrity_verified': True,
    }


@pytest.fixture
def sample_baseline_results() -> Dict[str, Dict[str, Any]]:
    """Create sample baseline model results."""
    return {
        'random_walk': {
            'test': {
                'mae': 0.0267,
                'rmse': 0.0389,
                'directional_accuracy': 0.49,
                'sharpe_ratio': 0.32,
                'information_coefficient': 0.05,
            }
        },
        'arima': {
            'test': {
                'mae': 0.0243,
                'rmse': 0.0361,
                'directional_accuracy': 0.51,
                'sharpe_ratio': 0.41,
                'information_coefficient': 0.08,
            }
        },
        'linear_regression': {
            'test': {
                'mae': 0.0228,
                'rmse': 0.0334,
                'directional_accuracy': 0.52,
                'sharpe_ratio': 0.48,
                'information_coefficient': 0.10,
            }
        },
        'ridge_regression': {
            'test': {
                'mae': 0.0211,
                'rmse': 0.0312,
                'directional_accuracy': 0.54,
                'sharpe_ratio': 0.55,
                'information_coefficient': 0.12,
            }
        },
        'historical_mean': {
            'test': {
                'mae': 0.0301,
                'rmse': 0.0418,
                'directional_accuracy': 0.47,
                'sharpe_ratio': 0.25,
                'information_coefficient': 0.02,
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
) -> ModelCardContext:
    """Create sample model card context."""
    return ModelCardContext(
        config=sample_config,
        cleaning_reports=sample_cleaning_reports,
        features_manifests=sample_features_manifests,
        splits_metadata=sample_splits_metadata,
        baseline_results=sample_baseline_results,
        errors=[],
        warnings=[]
    )


class TestModelCardGenerator:
    """Tests for ModelCardGenerator class."""
    
    def test_generate_model_card(self, sample_context):
        """Test basic model card generation."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert isinstance(model_card, str)
        assert len(model_card) > 1000
        assert "# Model Card" in model_card
    
    def test_model_card_contains_title(self, sample_context):
        """Test that model card contains title section."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "Model Card: Stock Market Forecasting System" in model_card
        assert "Executive Summary" in model_card
    
    def test_model_card_contains_intended_use(self, sample_context):
        """Test that model card contains intended use section."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "Intended Use" in model_card
        assert "Primary Use Cases" in model_card
        assert "Out-of-Scope and Prohibited Use Cases" in model_card
    
    def test_model_card_contains_training_data(self, sample_context):
        """Test that model card contains training data section."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "Training Data" in model_card
        assert "Data Sources and Collection" in model_card
        assert "Symbols and Coverage" in model_card
        assert "Feature Engineering" in model_card
    
    def test_model_card_contains_evaluation_methodology(self, sample_context):
        """Test that model card contains evaluation methodology section."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "Evaluation Methodology" in model_card
        assert "Evaluation Metrics" in model_card
        assert "Test Protocol" in model_card
    
    def test_model_card_contains_limitations(self, sample_context):
        """Test that model card contains limitations section."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "Limitations" in model_card
        assert "Data Limitations" in model_card
        assert "Model Limitations" in model_card
    
    def test_model_card_contains_recommendations(self, sample_context):
        """Test that model card contains recommendations section."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "Recommendations" in model_card
        assert "When to Use This Model" in model_card
        assert "When NOT to Use This Model" in model_card
    
    def test_model_card_contains_risk_assessment(self, sample_context):
        """Test that model card contains risk assessment section."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "Risk Assessment" in model_card
        assert "Model Failure Modes" in model_card
    
    def test_model_card_contains_symbols_count(self, sample_context):
        """Test that model card mentions symbol count."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        # Should mention 3 symbols (AAPL, MSFT, GOOGL)
        assert "3" in model_card and "symbol" in model_card.lower()
    
    def test_model_card_contains_date_ranges(self, sample_context):
        """Test that model card includes date ranges."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert sample_context.splits_metadata['train_start_date'] in model_card
        assert sample_context.splits_metadata['test_end_date'] in model_card
    
    def test_model_card_contains_baseline_performance(self, sample_context):
        """Test that model card includes baseline performance."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "ridge_regression" in model_card or "Ridge" in model_card
        assert "Test Set Performance" in model_card or "Baseline" in model_card
    
    def test_model_card_with_empty_baseline_results(self, sample_context):
        """Test model card generation with empty baseline results."""
        sample_context.baseline_results = {}
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert isinstance(model_card, str)
        assert len(model_card) > 1000
    
    def test_model_card_with_single_symbol(self, sample_config):
        """Test model card generation with single symbol."""
        context = ModelCardContext(
            config=sample_config,
            cleaning_reports={
                'AAPL': {
                    'symbol': 'AAPL',
                    'raw_data_stats': {
                        'total_rows': 2525,
                        'date_range': ['2002-01-02', '2024-01-19']
                    },
                    'cleaned_data_stats': {
                        'total_rows_retained': 2520,
                        'rows_excluded': 5
                    }
                }
            },
            features_manifests={
                'AAPL': {
                    'symbol': 'AAPL',
                    'features': [
                        {
                            'tier': 1,
                            'module_name': 'returns',
                            'feature_names': ['simple_return', 'log_return']
                        }
                    ]
                }
            },
            splits_metadata={
                'train_start_date': '2002-01-02',
                'train_end_date': '2020-01-01',
                'val_start_date': '2020-01-02',
                'val_end_date': '2022-01-01',
                'test_start_date': '2022-01-02',
                'test_end_date': '2024-01-19'
            },
            baseline_results={}
        )
        
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(context)
        
        assert isinstance(model_card, str)
        assert len(model_card) > 1000
        # Should mention single symbol in the coverage
        assert "1" in model_card and "symbol" in model_card.lower()

    
    def test_model_card_markdown_structure(self, sample_context):
        """Test that model card has valid markdown structure."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        # Check for markdown headers
        assert "# Model Card" in model_card
        assert "##" in model_card or "###" in model_card
        
        # Check for common markdown elements
        assert "**" in model_card  # bold
        assert "-" in model_card  # list items
    
    def test_save_model_card(self, sample_context, tmp_path):
        """Test saving model card to file."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        output_path = tmp_path / "model_card.md"
        saved_path = generator.save_model_card(model_card, str(output_path))
        
        assert Path(saved_path).exists()
        
        # Verify file content
        with open(saved_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == model_card
        assert "Model Card: Stock Market Forecasting System" in content
    
    def test_save_model_card_creates_parent_directories(self, sample_context, tmp_path):
        """Test that save_model_card creates parent directories."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        output_path = tmp_path / "reports" / "subdir" / "model_card.md"
        saved_path = generator.save_model_card(model_card, str(output_path))
        
        assert Path(saved_path).exists()
        assert Path(saved_path).parent.exists()
    
    def test_count_features(self, sample_features_manifests):
        """Test feature counting utility."""
        generator = ModelCardGenerator()
        feature_count = generator._count_features(sample_features_manifests)
        
        # AAPL has: 2 returns + 2 normalized + 5 technical = 9 features
        # All symbols have same features, so total = 9 (counted from first)
        assert feature_count == 9
    
    def test_count_features_empty(self):
        """Test feature counting with empty manifests."""
        generator = ModelCardGenerator()
        feature_count = generator._count_features({})
        
        assert feature_count == 0
    
    def test_compute_feature_statistics(self, sample_features_manifests):
        """Test feature statistics computation."""
        generator = ModelCardGenerator()
        stats = generator._compute_feature_statistics(sample_features_manifests)
        
        assert 'tier1' in stats
        assert 'tier2' in stats
        assert 'tier3' in stats
        assert stats['tier1'] == 4  # 2 returns + 2 normalized
        assert stats['tier2'] == 5  # technical indicators
        assert stats['tier3'] == 0
    
    def test_extract_baseline_performance(self, sample_baseline_results):
        """Test baseline performance extraction."""
        generator = ModelCardGenerator()
        performance_str = generator._extract_baseline_performance(sample_baseline_results)
        
        assert "ridge_regression" in performance_str or "Ridge" in performance_str
        assert "0.0211" in performance_str or "0.021" in performance_str
    
    def test_extract_baseline_performance_empty(self):
        """Test baseline performance extraction with empty results."""
        generator = ModelCardGenerator()
        performance_str = generator._extract_baseline_performance({})
        
        assert isinstance(performance_str, str)
    
    def test_model_card_with_warnings(self, sample_context):
        """Test model card generation with warnings."""
        sample_context.warnings = [
            {'type': 'REPORT_LOAD_ERROR', 'message': 'Failed to load cleaning report'},
            {'type': 'DATA_QUALITY_WARNING', 'message': 'Low data quality detected'},
        ]
        
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert isinstance(model_card, str)
        assert len(model_card) > 1000
    
    def test_model_card_with_errors(self, sample_context):
        """Test model card generation with errors."""
        sample_context.errors = [
            {'type': 'DATA_LEAKAGE', 'message': 'Data leakage detected in features'},
        ]
        
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert isinstance(model_card, str)
        assert len(model_card) > 1000
    
    def test_model_card_contains_ethical_considerations(self, sample_context):
        """Test that model card contains ethical considerations section."""
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(sample_context)
        
        assert "Ethical" in model_card or "ethical" in model_card
        assert "bias" in model_card.lower()


class TestLoadContextFromResultsDirectory:
    """Tests for loading context from results directory."""
    
    def test_load_context_from_empty_directory(self, tmp_path):
        """Test loading context from empty directory."""
        context = load_context_from_results_directory(str(tmp_path))
        
        assert isinstance(context, ModelCardContext)
        assert len(context.cleaning_reports) == 0
        assert len(context.features_manifests) == 0
    
    def test_load_context_with_cleaning_reports(self, tmp_path, sample_cleaning_reports):
        """Test loading context with cleaning reports."""
        # Create cleaning reports
        cleaning_dir = tmp_path / "cleaning_reports"
        cleaning_dir.mkdir(parents=True)
        
        for symbol, report in sample_cleaning_reports.items():
            report_file = cleaning_dir / f"{symbol}_cleaning_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f)
        
        context = load_context_from_results_directory(str(tmp_path))
        
        assert len(context.cleaning_reports) == 3
        assert 'AAPL' in context.cleaning_reports
        assert context.cleaning_reports['AAPL']['symbol'] == 'AAPL'
    
    def test_load_context_with_features_manifests(self, tmp_path, sample_features_manifests):
        """Test loading context with features manifests."""
        # Create features manifests
        manifests_dir = tmp_path / "features_manifests"
        manifests_dir.mkdir(parents=True)
        
        for symbol, manifest in sample_features_manifests.items():
            manifest_file = manifests_dir / f"{symbol}_features_manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
        
        context = load_context_from_results_directory(str(tmp_path))
        
        assert len(context.features_manifests) == 3
        assert 'MSFT' in context.features_manifests
    
    def test_load_context_with_splits_metadata(self, tmp_path, sample_splits_metadata):
        """Test loading context with splits metadata."""
        # Create splits metadata
        splits_dir = tmp_path / "splits_metadata"
        splits_dir.mkdir(parents=True)
        splits_file = splits_dir / "splits_metadata.json"
        
        with open(splits_file, 'w') as f:
            json.dump(sample_splits_metadata, f)
        
        context = load_context_from_results_directory(str(tmp_path))
        
        assert context.splits_metadata['train_start_date'] == '2002-01-02'
        assert context.splits_metadata['test_end_date'] == '2024-01-19'
    
    def test_load_context_with_baseline_results(self, tmp_path, sample_baseline_results):
        """Test loading context with baseline results."""
        # Create baseline results
        baseline_file = tmp_path / "baseline_results.json"
        
        with open(baseline_file, 'w') as f:
            json.dump(sample_baseline_results, f)
        
        context = load_context_from_results_directory(str(tmp_path))
        
        assert len(context.baseline_results) > 0
        assert 'ridge_regression' in context.baseline_results
    
    def test_load_context_with_config(self, tmp_path, sample_config):
        """Test loading context with config."""
        # Create config file
        config_file = tmp_path / "master_config.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        context = load_context_from_results_directory(str(tmp_path))
        
        assert context.config['data_acquisition']['primary_source'] == 'iex_cloud'
    
    def test_load_context_handles_corrupted_files(self, tmp_path):
        """Test that loading handles corrupted JSON files gracefully."""
        # Create corrupted cleaning report
        cleaning_dir = tmp_path / "cleaning_reports"
        cleaning_dir.mkdir(parents=True)
        corrupted_file = cleaning_dir / "corrupted.json"
        
        with open(corrupted_file, 'w') as f:
            f.write("{ invalid json }")
        
        context = load_context_from_results_directory(str(tmp_path))
        
        # Should still return context, with warnings
        assert isinstance(context, ModelCardContext)
        assert len(context.warnings) > 0
    
    def test_load_context_with_custom_results_dir(self, tmp_path, sample_baseline_results):
        """Test loading from custom results directory path."""
        results_subdir = tmp_path / "custom_results"
        results_subdir.mkdir(parents=True)
        
        baseline_file = results_subdir / "baseline_results.json"
        with open(baseline_file, 'w') as f:
            json.dump(sample_baseline_results, f)
        
        context = load_context_from_results_directory(str(results_subdir))
        
        assert len(context.baseline_results) > 0


class TestModelCardIntegration:
    """Integration tests for full model card generation workflow."""
    
    def test_full_model_card_workflow(self, sample_context, tmp_path):
        """Test complete model card generation and saving workflow."""
        generator = ModelCardGenerator()
        
        # Generate model card
        model_card = generator.generate_model_card(sample_context)
        assert isinstance(model_card, str)
        assert len(model_card) > 5000
        
        # Save model card
        output_path = tmp_path / "reports" / "model_card.md"
        saved_path = generator.save_model_card(model_card, str(output_path))
        
        # Verify saved file
        assert Path(saved_path).exists()
        with open(saved_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == model_card
    
    def test_model_card_with_loaded_context(self, tmp_path, sample_context):
        """Test model card generation with context loaded from directory."""
        # First, save all data to tmp directory
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        # Save config
        config_file = results_dir / "master_config.json"
        with open(config_file, 'w') as f:
            json.dump(sample_context.config, f)
        
        # Save cleaning reports
        cleaning_dir = results_dir / "cleaning_reports"
        cleaning_dir.mkdir()
        for symbol, report in sample_context.cleaning_reports.items():
            with open(cleaning_dir / f"{symbol}.json", 'w') as f:
                json.dump(report, f)
        
        # Save features manifests
        manifests_dir = results_dir / "features_manifests"
        manifests_dir.mkdir()
        for symbol, manifest in sample_context.features_manifests.items():
            with open(manifests_dir / f"{symbol}.json", 'w') as f:
                json.dump(manifest, f)
        
        # Save splits
        splits_dir = results_dir / "splits_metadata"
        splits_dir.mkdir()
        with open(splits_dir / "splits_metadata.json", 'w') as f:
            json.dump(sample_context.splits_metadata, f)
        
        # Save baseline results
        with open(results_dir / "baseline_results.json", 'w') as f:
            json.dump(sample_context.baseline_results, f)
        
        # Now load and generate model card
        loaded_context = load_context_from_results_directory(str(results_dir))
        generator = ModelCardGenerator()
        model_card = generator.generate_model_card(loaded_context)
        
        assert isinstance(model_card, str)
        assert len(model_card) > 5000
        assert "Model Card" in model_card
