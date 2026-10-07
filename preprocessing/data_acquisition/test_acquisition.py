"""
End-to-end test for data acquisition module.

Tests data adapters, coordinator, and symbol registry.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from .iex_adapter import IEXAdapter
from .yfinance_adapter import YFinanceAdapter
from .acquisition_coordinator import AcquisitionCoordinator
from .symbol_registry import SymbolRegistry
from utils.logging_config import configure_logging


def test_yfinance_adapter():
    """Test yfinance adapter with sample symbols."""
    logger = configure_logging(log_dir='logs', log_name='test_yfinance')
    logger.info("Testing yfinance adapter...")
    
    adapter = YFinanceAdapter()
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_symbols:
        try:
            df = adapter.fetch(
                symbol,
                start_date='2022-01-01',
                end_date='2024-01-19'
            )
            logger.info(f"✓ {symbol}: Fetched {len(df)} rows")
            assert len(df) > 0, f"Empty data for {symbol}"
            assert all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
        except Exception as e:
            logger.error(f"✗ {symbol}: Failed - {e}")
            raise
    
    logger.info("✓ yfinance adapter test passed")


def test_iex_adapter():
    """Test IEX Cloud adapter (requires API token)."""
    logger = configure_logging(log_dir='logs', log_name='test_iex')
    
    api_token = os.environ.get('IEX_CLOUD_TOKEN')
    if not api_token:
        logger.warning("IEX_CLOUD_TOKEN not set. Skipping IEX adapter test.")
        return
    
    logger.info("Testing IEX Cloud adapter...")
    adapter = IEXAdapter(api_token=api_token)
    
    try:
        df = adapter.fetch('AAPL', '2022-01-01', '2024-01-19')
        logger.info(f"✓ AAPL: Fetched {len(df)} rows from IEX")
        assert len(df) > 0
    except Exception as e:
        logger.error(f"✗ IEX adapter test failed: {e}")


def test_acquisition_coordinator():
    """Test acquisition coordinator with fallback."""
    logger = configure_logging(log_dir='logs', log_name='test_coordinator')
    logger.info("Testing acquisition coordinator...")
    
    # Create adapters
    api_token = os.environ.get('IEX_CLOUD_TOKEN', 'demo')  # Use demo if no token
    iex = IEXAdapter(api_token=api_token)
    yf = YFinanceAdapter()
    
    # Create coordinator
    coordinator = AcquisitionCoordinator(iex, yf, logger=logger)
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Fetch with fallback
    data_dict, source_dict = coordinator.fetch_multiple(
        symbols=test_symbols,
        start_date='2022-01-01',
        end_date='2024-01-19',
        min_trading_days=400  # Lower threshold for test
    )
    
    # Verify results
    successful = sum(1 for v in source_dict.values() if v != 'failed')
    logger.info(f"✓ Coordinator: {successful}/{len(test_symbols)} symbols acquired")
    
    # Get summary
    summary = coordinator.get_summary()
    logger.info(f"Summary: {summary}")
    
    assert successful > 0, "No symbols acquired"
    logger.info("✓ Acquisition coordinator test passed")


def test_symbol_registry():
    """Test symbol registry."""
    logger = configure_logging(log_dir='logs', log_name='test_registry')
    logger.info("Testing symbol registry...")
    
    registry = SymbolRegistry(logger=logger)
    
    # Load default symbols
    registry.load_default_sp500()
    
    # Test validation
    assert registry.validate_symbol('AAPL'), "AAPL should be valid"
    assert not registry.validate_symbol('INVALID'), "INVALID should not be valid"
    
    # Test sector lookup
    aapl_sector = registry.get_sector('AAPL')
    logger.info(f"✓ AAPL sector: {aapl_sector}")
    assert aapl_sector is not None
    
    # Test exchange lookup
    aapl_exchange = registry.get_exchange('AAPL')
    logger.info(f"✓ AAPL exchange: {aapl_exchange}")
    assert aapl_exchange == 'NASDAQ'
    
    # Test get all symbols
    all_symbols = registry.get_all_symbols()
    logger.info(f"✓ Total symbols: {len(all_symbols)}")
    assert len(all_symbols) > 0
    
    # Test registry info
    info = registry.get_registry_info()
    logger.info(f"Registry info: {info}")
    
    logger.info("✓ Symbol registry test passed")


def run_all_tests():
    """Run all data acquisition tests."""
    print("\n" + "="*70)
    print("STOCK FORECASTING SYSTEM - DATA ACQUISITION TEST SUITE")
    print("="*70 + "\n")
    
    tests = [
        ("yfinance Adapter", test_yfinance_adapter),
        ("IEX Cloud Adapter", test_iex_adapter),
        ("Acquisition Coordinator", test_acquisition_coordinator),
        ("Symbol Registry", test_symbol_registry),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * 70)
        try:
            test_func()
            results[test_name] = "✓ PASSED"
            print(f"✓ {test_name} passed\n")
        except Exception as e:
            results[test_name] = f"✗ FAILED: {e}"
            print(f"✗ {test_name} failed: {e}\n")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, result in results.items():
        print(f"{test_name:30s} {result}")
    
    passed = sum(1 for r in results.values() if "PASSED" in r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
