#!/usr/bin/env python
"""
Offline Demo Runner - Stock Forecasting System
Runs the complete pipeline using synthetic mock data (no network required)
Perfect for testing, demonstration, and development.
"""

import sys
import json
import logging
from pathlib import Path

# Add preprocessing to path
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing.data_acquisition.mock_adapter import MockAdapter
from preprocessing.data_cleaning.cleaner import DataCleaner
from config.config_loader import ConfigLoader


def setup_logging():
    """Configure logging for the offline demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def main():
    """Run the offline demonstration pipeline."""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("STOCK OPTIMIZER - OFFLINE DEMO")
    logger.info("Using Synthetic Mock Data (No Network Required)")
    logger.info("=" * 80)
    
    # Initialize mock data adapter
    logger.info("\n[1/5] Initializing Mock Data Adapter...")
    adapter = MockAdapter(lookback_years=10, seed=42)
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    # Generate synthetic data
    logger.info("\n[2/5] Generating Synthetic OHLCV Data...")
    data_dict = {}
    for symbol in symbols:
        logger.info(f"  Generating {symbol}...")
        df = adapter.fetch(symbol)
        data_dict[symbol] = df
        logger.info(f"    ✓ {symbol}: {len(df)} trading days")
        logger.info(f"      Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        logger.info(f"      Latest close: ${df['close'].iloc[-1]:.2f}")
    
    # Display sample data
    logger.info("\n[3/5] Sample Data (AAPL first 5 rows):")
    logger.info("\n" + str(data_dict['AAPL'].head()))
    
    # Display data quality metrics
    logger.info("\n[4/5] Data Quality Summary:")
    for symbol in symbols:
        df = data_dict[symbol]
        missing = df.isnull().sum().sum()
        logger.info(f"  {symbol}:")
        logger.info(f"    Total rows: {len(df)}")
        logger.info(f"    Missing values: {missing}")
        logger.info(f"    Date range: {df.index[0].date()} to {df.index[-1].date()}")
    
    # Save sample output
    logger.info("\n[5/5] Saving Results...")
    results_dir = Path('results/demo_run')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save sample data
    for symbol in symbols:
        output_file = results_dir / f'{symbol}_mock_data.csv'
        data_dict[symbol].to_csv(output_file)
        logger.info(f"  ✓ Saved {symbol} data to {output_file}")
    
    # Save summary report
    summary = {
        'status': 'success',
        'mode': 'offline_demo',
        'symbols_processed': symbols,
        'total_symbols': len(symbols),
        'data_quality': {
            symbol: {
                'rows': len(data_dict[symbol]),
                'missing_values': int(data_dict[symbol].isnull().sum().sum()),
                'price_range': {
                    'min': float(data_dict[symbol]['close'].min()),
                    'max': float(data_dict[symbol]['close'].max()),
                    'latest': float(data_dict[symbol]['close'].iloc[-1])
                }
            }
            for symbol in symbols
        }
    }
    
    summary_file = results_dir / 'demo_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"  ✓ Saved summary to {summary_file}")
    
    # Success message
    logger.info("\n" + "=" * 80)
    logger.info("✓ OFFLINE DEMO COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info("\nNext Steps:")
    logger.info("1. Review generated CSV files in: results/demo_run/")
    logger.info("2. For full pipeline with feature engineering:")
    logger.info("   python pipeline.py --config master_config_local.json")
    logger.info("3. For real data acquisition (requires IEX token):")
    logger.info("   set IEX_CLOUD_TOKEN=your_token")
    logger.info("   python pipeline.py")
    logger.info("\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
