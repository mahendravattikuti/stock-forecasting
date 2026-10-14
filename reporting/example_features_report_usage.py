"""
Example usage of FeaturesReportGenerator for generating interactive
features distribution reports with shift detection and leakage verification.

This example demonstrates:
1. Creating sample features data with train/val/test splits
2. Generating an interactive HTML report
3. Saving the report to disk
4. Accessing distribution shift analysis
"""

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

from reporting.report_generator import FeaturesReportGenerator, load_context_from_results_directory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_features_data():
    """Create sample features data with realistic train/val/test distributions."""
    np.random.seed(42)
    
    n_train = 1000
    n_val = 200
    n_test = 200
    
    # Create features with slightly different distributions across splits
    # to demonstrate shift detection
    features_data = {
        'AAPL': {
            'train': pd.DataFrame({
                'return_simple': np.random.normal(0.001, 0.020, n_train),
                'return_log': np.random.normal(0.001, 0.020, n_train),
                'rsi_14': np.random.uniform(20, 80, n_train),
                'momentum_5': np.random.normal(0, 0.05, n_train),
                'momentum_20': np.random.normal(0, 0.03, n_train),
                'volatility': np.random.uniform(0.01, 0.05, n_train),
                'volume_normalized': np.random.lognormal(10, 1, n_train),
            }),
            'val': pd.DataFrame({
                # Slightly higher mean returns in validation
                'return_simple': np.random.normal(0.0015, 0.021, n_val),
                'return_log': np.random.normal(0.0015, 0.021, n_val),
                'rsi_14': np.random.uniform(25, 75, n_val),
                'momentum_5': np.random.normal(0.001, 0.052, n_val),
                'momentum_20': np.random.normal(0.001, 0.031, n_val),
                'volatility': np.random.uniform(0.01, 0.055, n_val),
                'volume_normalized': np.random.lognormal(10.1, 1, n_val),
            }),
            'test': pd.DataFrame({
                # Even higher mean returns in test (potential shift)
                'return_simple': np.random.normal(0.002, 0.022, n_test),
                'return_log': np.random.normal(0.002, 0.022, n_test),
                'rsi_14': np.random.uniform(30, 70, n_test),
                'momentum_5': np.random.normal(0.002, 0.053, n_test),
                'momentum_20': np.random.normal(0.002, 0.032, n_test),
                'volatility': np.random.uniform(0.015, 0.06, n_test),
                'volume_normalized': np.random.lognormal(10.2, 1.1, n_test),
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
                'volume_normalized': np.random.lognormal(9.9, 1, n_train),
            }),
            'val': pd.DataFrame({
                'return_simple': np.random.normal(0.0015, 0.020, n_val),
                'return_log': np.random.normal(0.0015, 0.020, n_val),
                'rsi_14': np.random.uniform(25, 75, n_val),
                'momentum_5': np.random.normal(0.001, 0.049, n_val),
                'momentum_20': np.random.normal(0.001, 0.029, n_val),
                'volatility': np.random.uniform(0.012, 0.052, n_val),
                'volume_normalized': np.random.lognormal(10, 1, n_val),
            }),
            'test': pd.DataFrame({
                'return_simple': np.random.normal(0.0018, 0.021, n_test),
                'return_log': np.random.normal(0.0018, 0.021, n_test),
                'rsi_14': np.random.uniform(28, 72, n_test),
                'momentum_5': np.random.normal(0.002, 0.050, n_test),
                'momentum_20': np.random.normal(0.002, 0.030, n_test),
                'volatility': np.random.uniform(0.012, 0.055, n_test),
                'volume_normalized': np.random.lognormal(10.05, 1, n_test),
            })
        }
    }
    
    return features_data


def create_sample_splits_metadata():
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


def main():
    """Main example: generate features distribution report."""
    
    logger.info("=" * 80)
    logger.info("Features Distribution Report Generator - Example Usage")
    logger.info("=" * 80)
    
    # Create sample data
    logger.info("\n[1/4] Creating sample features data...")
    features_data = create_sample_features_data()
    splits_metadata = create_sample_splits_metadata()
    logger.info(f"  ✓ Created features for {len(features_data)} symbols")
    for symbol in features_data:
        logger.info(f"    - {symbol}: {len(features_data[symbol]['train'])} train, "
                   f"{len(features_data[symbol]['val'])} val, "
                   f"{len(features_data[symbol]['test'])} test samples")
    
    # Generate report
    logger.info("\n[2/4] Generating features distribution report...")
    generator = FeaturesReportGenerator(logger=logger)
    
    report_html = generator.generate_features_report(
        features_data=features_data,
        splits_metadata=splits_metadata
    )
    logger.info(f"  ✓ Report generated ({len(report_html)} characters)")
    
    # Analyze distributions
    logger.info("\n[3/4] Analyzing feature distributions...")
    aggregated = generator._aggregate_features_by_split(features_data)
    stats = generator._compute_feature_statistics(aggregated)
    shifts = generator._detect_distribution_shifts(aggregated, stats)
    
    # Print statistics summary
    logger.info("  Feature Statistics (Train Split):")
    for feature in list(stats['train'].keys())[:3]:
        s = stats['train'][feature]
        logger.info(f"    - {feature}:")
        logger.info(f"        Mean: {s['mean']:.6f}, Std: {s['std']:.6f}")
        logger.info(f"        Min: {s['min']:.6f}, Max: {s['max']:.6f}")
    
    # Print shift analysis
    logger.info("  Distribution Shifts (Train vs Test):")
    if 'train_vs_test' in shifts:
        for feature in list(shifts['train_vs_test'].keys())[:3]:
            shift_data = shifts['train_vs_test'][feature]
            logger.info(f"    - {feature}:")
            logger.info(f"        Mean shift: {shift_data['mean_shift_pct']:+.2f}%")
            logger.info(f"        Std shift: {shift_data['std_shift_pct']:+.2f}%")
    
    # Save report
    logger.info("\n[4/4] Saving report to disk...")
    output_path = "results/visualizations/features_distribution_report.html"
    saved_path = generator.save_report(report_html, output_path)
    logger.info(f"  ✓ Report saved to: {saved_path}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Example completed successfully!")
    logger.info("Open the HTML file in a browser to view interactive visualizations.")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
