"""Property-based tests for data splitting integrity.

**Validates: Requirements 8.1, 8.2**

These tests use hypothesis to generate randomized data scenarios and verify that
chronological data splitting maintains temporal integrity, prevents data leakage,
and preserves symbol consistency across splits.

Optimization: Reduced max_examples for speed (20-30 examples vs 50+)
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from hypothesis import given, settings, strategies as st

from preprocessing.data_splitter import ChronologicalDataSplitter


class TestPBTSplitting:
    """Property-based tests for data splitting integrity."""

    @settings(max_examples=30, deadline=None)
    @given(
        n_rows=st.integers(min_value=300, max_value=500),
        n_symbols=st.integers(min_value=1, max_value=5)
    )
    def test_temporal_ordering(self, n_rows, n_symbols):
        """**Validates: Requirements 8.1, 8.2**
        
        Property: train_end_date < val_start_date < test_start_date
        
        Why: Chronological order is critical to prevent look-ahead bias.
        The temporal integrity constraint ensures that training data strictly precedes
        validation data, which strictly precedes test data, maintaining causality.
        """
        # Generate realistic date range with small dataset for speed
        dates = pd.date_range('2020-01-01', periods=n_rows, freq='D')
        
        # Generate multi-symbol data with same date index
        symbol_data = {}
        base_price = 100.0
        
        for i in range(n_symbols):
            symbol = f"S{i}"
            # Generate realistic price movements
            close_prices = base_price + np.cumsum(
                np.random.normal(0, base_price * 0.01, len(dates))
            )
            close_prices = np.maximum(close_prices, 1)
            
            df = pd.DataFrame({
                'Open': close_prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
                'High': close_prices * (1 + np.random.uniform(0, 0.02, len(dates))),
                'Low': close_prices * (1 + np.random.uniform(-0.02, 0, len(dates))),
                'Close': close_prices,
                'Volume': np.random.randint(1_000_000, 100_000_000, len(dates)),
            }, index=dates)
            symbol_data[symbol] = df
        
        # Perform chronological split
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'splits_metadata.json'
            splits, metadata = ChronologicalDataSplitter().split(
                symbol_data, output_path=output_path
            )
            
            # Get cutoff dates from metadata
            cutoff_dates = metadata['cutoff_dates']
            train_end = pd.Timestamp(cutoff_dates['train_end_date'])
            val_start = pd.Timestamp(cutoff_dates['val_start_date'])
            val_end = pd.Timestamp(cutoff_dates['val_end_date'])
            test_start = pd.Timestamp(cutoff_dates['test_start_date'])
            
            # Verify temporal ordering: train < val < test
            assert train_end < val_start, \
                f"train_end ({train_end}) >= val_start ({val_start})"
            assert val_end < test_start, \
                f"val_end ({val_end}) >= test_start ({test_start})"

    @settings(max_examples=25, deadline=None)
    @given(
        n_rows=st.integers(min_value=300, max_value=500),
        n_symbols=st.integers(min_value=2, max_value=5)
    )
    def test_no_symbol_overlap(self, n_rows, n_symbols):
        """**Validates: Requirements 8.1, 8.2**
        
        Property: No date appears in multiple splits for the same symbol
        
        Why: Ensures no data contamination between splits. Each date must belong to
        exactly one split (train, validation, or test) to maintain data integrity
        and prevent leakage.
        """
        # Generate realistic date range with small dataset for speed
        dates = pd.date_range('2020-01-01', periods=n_rows, freq='D')
        
        # Generate multi-symbol data
        symbol_data = {}
        base_price = 100.0
        
        for i in range(n_symbols):
            symbol = f"S{i}"
            close_prices = base_price + np.cumsum(
                np.random.normal(0, base_price * 0.01, len(dates))
            )
            close_prices = np.maximum(close_prices, 1)
            
            df = pd.DataFrame({
                'Open': close_prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
                'High': close_prices * (1 + np.random.uniform(0, 0.02, len(dates))),
                'Low': close_prices * (1 + np.random.uniform(-0.02, 0, len(dates))),
                'Close': close_prices,
                'Volume': np.random.randint(1_000_000, 100_000_000, len(dates)),
            }, index=dates)
            symbol_data[symbol] = df
        
        # Perform chronological split
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'splits_metadata.json'
            splits, metadata = ChronologicalDataSplitter().split(
                symbol_data, output_path=output_path
            )
            
            # Verify no date overlap within each symbol
            for symbol in symbol_data:
                train_dates = set(splits['train'][symbol].index)
                val_dates = set(splits['validation'][symbol].index)
                test_dates = set(splits['test'][symbol].index)
                
                # Check pairwise intersections - must be empty (disjoint sets)
                assert len(train_dates & val_dates) == 0, \
                    f"{symbol}: {len(train_dates & val_dates)} dates overlap between train and validation"
                assert len(train_dates & test_dates) == 0, \
                    f"{symbol}: {len(train_dates & test_dates)} dates overlap between train and test"
                assert len(val_dates & test_dates) == 0, \
                    f"{symbol}: {len(val_dates & test_dates)} dates overlap between validation and test"

    @settings(max_examples=20, deadline=None)
    @given(
        n_rows=st.integers(min_value=300, max_value=500)
    )
    def test_split_ratios(self, n_rows):
        """**Validates: Requirements 8.1, 8.2**
        
        Property: Row counts match expected ratios (70/15/15) within ±2% tolerance
        
        Why: Ensures that the split reasonably approximates the specified ratios.
        Some deviation is expected due to discrete rounding, but it should remain
        close to target ratios to maintain data distribution balance.
        """
        # Generate realistic date range with small dataset for speed
        dates = pd.date_range('2020-01-01', periods=n_rows, freq='D')
        
        # Generate single-symbol data for simple ratio check
        base_price = 100.0
        close_prices = base_price + np.cumsum(
            np.random.normal(0, base_price * 0.01, len(dates))
        )
        close_prices = np.maximum(close_prices, 1)
        
        df = pd.DataFrame({
            'Open': close_prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
            'High': close_prices * (1 + np.random.uniform(0, 0.02, len(dates))),
            'Low': close_prices * (1 + np.random.uniform(-0.02, 0, len(dates))),
            'Close': close_prices,
            'Volume': np.random.randint(1_000_000, 100_000_000, len(dates)),
        }, index=dates)
        
        # Perform chronological split with standard 70/15/15 ratios
        splitter = ChronologicalDataSplitter(
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15
        )
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'splits_metadata.json'
            splits, metadata = splitter.split(df, output_path=output_path)
            
            train_df = splits['train']
            val_df = splits['validation']
            test_df = splits['test']
            
            total_rows = len(train_df) + len(val_df) + len(test_df)
            
            # Compute actual ratios
            train_pct = len(train_df) / total_rows if total_rows > 0 else 0
            val_pct = len(val_df) / total_rows if total_rows > 0 else 0
            test_pct = len(test_df) / total_rows if total_rows > 0 else 0
            
            # Allow ±2% tolerance for rounding effects
            tolerance = 0.02
            assert abs(train_pct - 0.70) <= tolerance, \
                f"Train ratio {train_pct:.4f} deviates > ±{tolerance} from target 0.70"
            assert abs(val_pct - 0.15) <= tolerance, \
                f"Validation ratio {val_pct:.4f} deviates > ±{tolerance} from target 0.15"
            assert abs(test_pct - 0.15) <= tolerance, \
                f"Test ratio {test_pct:.4f} deviates > ±{tolerance} from target 0.15"
