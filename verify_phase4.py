#!/usr/bin/env python
"""Verification script for Phase 4 implementations."""

import sys
import pandas as pd
import numpy as np
from preprocessing.data_cleaning.validators import (
    DataQualityValidator,
    ValidationReportGenerator,
    SymbolExclusionManager
)

def test_data_quality_validator():
    """Test DataQualityValidator."""
    print("Testing DataQualityValidator...")
    
    # Create valid test data
    dates = pd.date_range('2010-01-01', periods=2500, freq='D')
    data = {
        'Open': np.random.uniform(100, 105, 2500),
        'High': np.random.uniform(105, 110, 2500),
        'Low': np.random.uniform(95, 100, 2500),
        'Close': np.random.uniform(100, 105, 2500),
        'Volume': np.random.uniform(1000000, 5000000, 2500)
    }
    df = pd.DataFrame(data, index=dates)
    df['Low'] = df[['Open', 'High', 'Low', 'Close']].min(axis=1)
    df['High'] = df[['Open', 'High', 'Low', 'Close']].max(axis=1)
    
    validator = DataQualityValidator(min_trading_days=2500)
    result = validator.validate_quality(df)
    
    assert result['checks']['min_trading_days']['pass'], "Min trading days check failed"
    assert result['checks']['ohlc_relationships']['pass'], "OHLC relationships check failed"
    assert result['checks']['statistics']['pass'], "Statistics check failed"
    print("  ✓ DataQualityValidator works correctly")
    
    # Test with insufficient data
    small_dates = pd.date_range('2010-01-01', periods=2499, freq='D')
    small_df = pd.DataFrame(data[:2499], index=small_dates)
    result_small = validator.validate_quality(small_df)
    assert not result_small['checks']['min_trading_days']['pass'], "Should fail with < 2500 days"
    print("  ✓ Correctly rejects insufficient data (2499 days)")
    
    # Test stasis detection
    stasis_dates = pd.date_range('2010-01-01', periods=2500, freq='D')
    stasis_data = {
        'Open': np.full(2500, 100.0),
        'High': np.full(2500, 105.0),
        'Low': np.full(2500, 95.0),
        'Close': np.full(2500, 100.0),
        'Volume': np.full(2500, 1000000.0)
    }
    stasis_df = pd.DataFrame(stasis_data, index=stasis_dates)
    result_stasis = validator.validate_quality(stasis_df)
    assert result_stasis['checks']['price_stasis']['detected'], "Should detect stasis"
    print("  ✓ Correctly detects multi-day price stasis")

def test_validation_report_generator():
    """Test ValidationReportGenerator."""
    print("Testing ValidationReportGenerator...")
    
    generator = ValidationReportGenerator()
    
    validation_results = {
        'AAPL': {
            'overall_pass': True,
            'total_rows': 2500,
            'checks': {
                'min_trading_days': {'pass': True, 'actual': 2500},
                'ohlc_relationships': {'pass': True, 'actual': '99.50%', 'valid': 2488, 'total': 2500},
                'statistics': {'pass': True, 'errors': []},
                'price_stasis': {'detected': False, 'ranges': []}
            }
        },
        'MSFT': {
            'overall_pass': False,
            'total_rows': 2400,
            'checks': {
                'min_trading_days': {'pass': False, 'actual': 2400},
                'ohlc_relationships': {'pass': True, 'actual': '98.50%'},
                'statistics': {'pass': True, 'errors': []},
                'price_stasis': {'detected': False, 'ranges': []}
            }
        }
    }
    
    excluded_symbols = {'DELISTED': 'symbol_delisted', 'BADDATA': 'insufficient_data'}
    
    report = generator.generate_validation_report(validation_results, excluded_symbols, '/tmp/test_report.json')
    
    assert report['summary']['total_symbols'] == 4
    assert report['summary']['symbols_passed'] == 1
    assert report['summary']['symbols_excluded'] == 2
    assert 'AAPL' in report['symbols']
    assert report['symbols']['AAPL']['completeness_percent'] == 99.50
    print("  ✓ ValidationReportGenerator works correctly")
    print("  ✓ Extracts completeness percentage from OHLC check")

def test_symbol_exclusion_manager():
    """Test SymbolExclusionManager."""
    print("Testing SymbolExclusionManager...")
    
    manager = SymbolExclusionManager()
    
    manager.exclude_symbol('AAPL', 'insufficient_data')
    manager.exclude_symbol('MSFT', 'invalid_ohlc')
    manager.exclude_symbol('GOOGL', 'insufficient_data')
    
    excluded = manager.get_excluded_symbols()
    assert len(excluded) == 3
    assert excluded['AAPL'] == 'insufficient_data'
    assert manager.is_excluded('AAPL')
    assert not manager.is_excluded('TSLA')
    print("  ✓ Exclude and retrieve symbols")
    
    summary = manager.generate_exclusion_summary('/tmp/test_exclusion.json')
    assert summary['total_excluded'] == 3
    assert 'insufficient_data' in summary['excluded_by_reason']
    assert len(summary['excluded_by_reason']['insufficient_data']) == 2
    print("  ✓ Generate exclusion summary")

def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("Phase 4: Data Quality Validation - Implementation Verification")
    print("=" * 60 + "\n")
    
    try:
        test_data_quality_validator()
        test_validation_report_generator()
        test_symbol_exclusion_manager()
        
        print("\n" + "=" * 60)
        print("✅ All Phase 4 implementations verified successfully!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
