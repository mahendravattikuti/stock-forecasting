"""
Example usage of the DashboardGenerator for creating data quality dashboards.

This script demonstrates how to:
1. Load cleaning reports and feature manifests from the results directory
2. Generate an interactive HTML dashboard
3. Save the dashboard to the visualizations directory

The dashboard provides interactive visualizations showing:
- Data completeness by symbol
- Cleaning impact (before/after comparison)
- Feature distribution by tier
- Quality status overview
- Summary statistics

Usage:
    python reporting/example_dashboard_usage.py
    
    # Or with custom results directory:
    python reporting/example_dashboard_usage.py --results-dir /path/to/results
"""

import argparse
import logging
from pathlib import Path

from reporting.dashboard_generator import DashboardGenerator, load_context_from_results_directory


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def main():
    """Main entry point for dashboard generation."""
    parser = argparse.ArgumentParser(
        description="Generate data quality dashboard from pipeline results"
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='results',
        help='Path to results directory containing cleaning_reports and features_manifests (default: results)'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default='results/visualizations/data_quality_dashboard.html',
        help='Path where to save the dashboard HTML file (default: results/visualizations/data_quality_dashboard.html)'
    )
    
    args = parser.parse_args()
    logger = setup_logging()
    
    logger.info(f"Loading context from {args.results_dir}")
    
    # Load cleaning reports and feature manifests
    cleaning_reports, features_manifests = load_context_from_results_directory(args.results_dir)
    
    if not cleaning_reports:
        logger.warning("No cleaning reports found in results directory")
        logger.info("Using sample data for demonstration")
        
        # Create sample data for demonstration
        cleaning_reports = {
            'AAPL': {
                'symbol': 'AAPL',
                'raw_data_rows': 2525,
                'cleaned_data_rows': 2522,
                'completeness_percent': 99.88,
                'quality_status': 'PASS',
                'forward_fills_applied': 2,
                'spikes_corrected': 0,
                'ohlc_corrections_applied': 0,
                'adjustments_applied': 1,
                'rows_excluded': 3
            },
            'MSFT': {
                'symbol': 'MSFT',
                'raw_data_rows': 2530,
                'cleaned_data_rows': 2530,
                'completeness_percent': 100.0,
                'quality_status': 'PASS',
                'forward_fills_applied': 0,
                'spikes_corrected': 0,
                'ohlc_corrections_applied': 0,
                'adjustments_applied': 2,
                'rows_excluded': 0
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'raw_data_rows': 2150,
                'cleaned_data_rows': 2143,
                'completeness_percent': 99.67,
                'quality_status': 'PASS',
                'forward_fills_applied': 3,
                'spikes_corrected': 2,
                'ohlc_corrections_applied': 1,
                'adjustments_applied': 1,
                'rows_excluded': 7
            }
        }
        
        features_manifests = {
            'AAPL': {
                'symbol': 'AAPL',
                'features': [
                    {'name': 'simple_return', 'tier': 1},
                    {'name': 'log_return', 'tier': 1},
                    {'name': 'rsi_14', 'tier': 2},
                    {'name': 'macd_line', 'tier': 2},
                    {'name': 'regime', 'tier': 3}
                ],
                'tier_counts': {'tier1': 2, 'tier2': 2, 'tier3': 1}
            },
            'MSFT': {
                'symbol': 'MSFT',
                'features': [
                    {'name': 'simple_return', 'tier': 1},
                    {'name': 'log_return', 'tier': 1},
                    {'name': 'rsi_14', 'tier': 2}
                ],
                'tier_counts': {'tier1': 2, 'tier2': 1}
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'features': [
                    {'name': 'simple_return', 'tier': 1},
                    {'name': 'log_return', 'tier': 1},
                    {'name': 'rsi_14', 'tier': 2},
                    {'name': 'regime', 'tier': 3}
                ],
                'tier_counts': {'tier1': 2, 'tier2': 1, 'tier3': 1}
            }
        }
    
    logger.info(f"Loaded {len(cleaning_reports)} cleaning reports")
    logger.info(f"Loaded {len(features_manifests)} feature manifests")
    
    # Generate dashboard
    logger.info("Generating data quality dashboard")
    generator = DashboardGenerator(logger=logger)
    
    html = generator.generate_dashboard(
        cleaning_reports=cleaning_reports,
        features_manifests=features_manifests
    )
    
    logger.info(f"Generated HTML dashboard ({len(html)} bytes)")
    
    # Save dashboard
    logger.info(f"Saving dashboard to {args.output_path}")
    saved_path = generator.save_dashboard(html, args.output_path)
    
    logger.info(f"Dashboard successfully saved to {saved_path}")
    logger.info("Open the HTML file in your browser to view the interactive dashboard")
    
    print(f"\n✓ Dashboard generated successfully!")
    print(f"  Location: {saved_path}")
    print(f"  Symbols: {', '.join(sorted(cleaning_reports.keys()))}")
    print(f"  Total Features: {sum(len(m.get('features', [])) for m in features_manifests.values())}")


if __name__ == "__main__":
    main()
