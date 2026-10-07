"""
Adjustment algorithms for normalizing historical prices based on corporate actions.

Handles stock splits and dividend adjustments to ensure price continuity.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

try:
    import yfinance as yf
except ImportError:
    yf = None


@dataclass
class StockAdjustment:
    """Represents a stock split or dividend adjustment."""
    date: pd.Timestamp
    adjustment_type: str  # 'split' or 'dividend'
    factor: float  # Split ratio (e.g., 7.0 for 7:1 split) or dividend as %
    description: str  # Human-readable description (e.g., "7:1 split")
    prices_adjusted: bool  # Whether prices were adjusted


@dataclass
class AdjustmentRecord:
    """Record of an applied price adjustment."""
    date: pd.Timestamp
    adjustment_type: str
    factor: float
    before_close: float
    after_close: float
    description: str


class SplitDividendAdjuster:
    """
    Adjusts historical prices for stock splits and dividend payouts.
    
    Behavior:
    - Queries adjustment data from yfinance or other sources
    - Applies adjustment factor: adjusted_price = price / factor
    - Logs all adjustments with date, type (split/dividend), and factor
    - Documents when adjustment data is unavailable
    
    Examples
    --------
    >>> adjuster = SplitDividendAdjuster()
    >>> adjusted_df, adjustments = adjuster.adjust_prices(symbol, df)
    >>> print(adjusted_df['AdjClose'])
    """
    
    def __init__(
        self,
        use_yfinance: bool = True,
        logger: logging.Logger = None
    ):
        """
        Initialize SplitDividendAdjuster.
        
        Parameters
        ----------
        use_yfinance : bool
            Whether to use yfinance as primary source for adjustment data (default: True)
        logger : logging.Logger, optional
            Logger instance
        """
        self.use_yfinance = use_yfinance
        self.logger = logger or logging.getLogger(__name__)
        self.adjustments: List[StockAdjustment] = []
        self.adjustment_records: List[AdjustmentRecord] = []
    
    def adjust_prices(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, List[AdjustmentRecord]]:
        """
        Adjust historical prices for splits and dividends.
        
        Parameters
        ----------
        symbol : str
            Stock symbol (e.g., 'AAPL')
        df : pd.DataFrame
            OHLCV DataFrame with Date index
        
        Returns
        -------
        Tuple[pd.DataFrame, List[AdjustmentRecord]]
            (adjusted_df, list_of_adjustments)
        """
        self.adjustments = []
        self.adjustment_records = []
        adjusted_df = df.copy()
        
        # Validate required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in adjusted_df.columns for col in required_cols):
            self.logger.warning(f"Missing required columns for {symbol}")
            return adjusted_df, self.adjustment_records
        
        # Add AdjClose column if not present (copy of Close initially)
        if 'AdjClose' not in adjusted_df.columns:
            adjusted_df['AdjClose'] = adjusted_df['Close']
        
        # Get adjustment data
        adjustment_data = self._get_adjustment_data(symbol, adjusted_df)
        
        if not adjustment_data:
            self.logger.warning(
                f"No adjustment data available for {symbol}; "
                "using unadjusted prices"
            )
            return adjusted_df, self.adjustment_records
        
        # Sort adjustments by date (process in reverse chronological order)
        adjustment_data_sorted = sorted(
            adjustment_data, 
            key=lambda x: x['date'],
            reverse=True
        )
        
        # Apply adjustments in reverse chronological order
        cumulative_factor = 1.0
        
        for adj in adjustment_data_sorted:
            adj_date = adj['date']
            adj_type = adj['type']
            adj_factor = adj['factor']
            
            # Validate adjustment data
            if adj_date not in adjusted_df.index:
                self.logger.warning(
                    f"Adjustment date {adj_date} not in data range; skipping"
                )
                continue
            
            # Find all rows before this adjustment date
            mask = adjusted_df.index <= adj_date
            
            if not mask.any():
                self.logger.warning(
                    f"No rows before adjustment date {adj_date} for {symbol}"
                )
                continue
            
            # Apply adjustment factor to historical prices (before adjustment date)
            before_close = adjusted_df.loc[mask, 'Close'].copy()
            
            # Update cumulative factor
            cumulative_factor *= adj_factor
            
            # Apply to all relevant price columns
            price_columns = ['Open', 'High', 'Low', 'Close', 'AdjClose']
            for col in price_columns:
                if col in adjusted_df.columns:
                    adjusted_df.loc[mask, col] = (
                        adjusted_df.loc[mask, col] / adj_factor
                    )
            
            # Record adjustment
            description = self._format_adjustment_description(adj_type, adj_factor)
            
            self.adjustments.append(
                StockAdjustment(
                    date=adj_date,
                    adjustment_type=adj_type,
                    factor=adj_factor,
                    description=description,
                    prices_adjusted=True
                )
            )
            
            # Record details for audit trail
            after_close = adjusted_df.loc[adj_date, 'Close']
            self.adjustment_records.append(
                AdjustmentRecord(
                    date=adj_date,
                    adjustment_type=adj_type,
                    factor=adj_factor,
                    before_close=before_close[adj_date] if adj_date in before_close.index else None,
                    after_close=after_close,
                    description=description
                )
            )
            
            self.logger.info(
                f"Applied {adj_type} adjustment on {adj_date}: "
                f"{description} (factor: {adj_factor:.4f})"
            )
        
        self.logger.info(
            f"Adjustment complete for {symbol}: "
            f"{len(self.adjustments)} adjustments applied"
        )
        
        return adjusted_df, self.adjustment_records
    
    def _get_adjustment_data(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve stock split and dividend adjustment data.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
        df : pd.DataFrame
            OHLCV DataFrame (to determine date range)
        
        Returns
        -------
        Optional[List[Dict[str, Any]]]
            List of adjustments with {'date', 'type', 'factor'}
            or None if data unavailable
        """
        if not self.use_yfinance or yf is None:
            self.logger.warning(
                f"yfinance not available; cannot retrieve adjustment data for {symbol}"
            )
            return None
        
        try:
            # Download yfinance data with splits and dividends
            start_date = df.index.min()
            end_date = df.index.max()
            
            # Download with actions=True to get splits and dividends
            ticker = yf.Ticker(symbol)
            
            adjustments = []
            
            # Get splits
            splits = ticker.splits
            if splits is not None and len(splits) > 0:
                for split_date, split_ratio in splits.items():
                    # Convert to pandas Timestamp if needed
                    if not isinstance(split_date, pd.Timestamp):
                        split_date = pd.Timestamp(split_date)
                    
                    # Only include splits within our date range
                    if start_date <= split_date <= end_date:
                        adjustments.append({
                            'date': split_date,
                            'type': 'split',
                            'factor': split_ratio,  # e.g., 7.0 for 7:1 split
                            'description': f"{split_ratio:.0f}:1 split"
                        })
                        self.logger.debug(
                            f"Found {split_ratio:.0f}:1 split on {split_date}"
                        )
            
            # Get dividends
            dividends = ticker.dividends
            if dividends is not None and len(dividends) > 0:
                for div_date, div_amount in dividends.items():
                    # Convert to pandas Timestamp if needed
                    if not isinstance(div_date, pd.Timestamp):
                        div_date = pd.Timestamp(div_date)
                    
                    # Only include dividends within our date range
                    if start_date <= div_date <= end_date:
                        # Get close price on that date (or nearby) for adjustment factor
                        try:
                            # Find closest date in our data
                            closest_date = None
                            min_diff = timedelta.max
                            
                            for data_date in df.index:
                                diff = abs((data_date - div_date).days)
                                if diff < min_diff:
                                    min_diff = diff
                                    closest_date = data_date
                            
                            if closest_date is not None and min_diff <= 2:
                                close_price = df.loc[closest_date, 'Close']
                                # Dividend adjustment factor
                                div_factor = 1 + (div_amount / close_price)
                                
                                adjustments.append({
                                    'date': div_date,
                                    'type': 'dividend',
                                    'factor': div_factor,
                                    'description': f"${div_amount:.2f} dividend"
                                })
                                self.logger.debug(
                                    f"Found ${div_amount:.2f} dividend on {div_date}"
                                )
                        except Exception as e:
                            self.logger.warning(
                                f"Error processing dividend on {div_date}: {e}"
                            )
            
            return adjustments if adjustments else None
        
        except Exception as e:
            self.logger.error(
                f"Failed to retrieve adjustment data for {symbol}: {e}"
            )
            return None
    
    def _format_adjustment_description(
        self,
        adjustment_type: str,
        factor: float
    ) -> str:
        """
        Format adjustment description for logging.
        
        Parameters
        ----------
        adjustment_type : str
            Type of adjustment ('split' or 'dividend')
        factor : float
            Adjustment factor
        
        Returns
        -------
        str
            Human-readable description
        """
        if adjustment_type == 'split':
            # For splits, factor is the split ratio
            if factor > 1:
                return f"{factor:.0f}:1 split"
            else:
                # Reverse split
                reverse_factor = 1 / factor
                return f"1:{reverse_factor:.0f} reverse split"
        elif adjustment_type == 'dividend':
            # For dividends, factor is (1 + dividend/price)
            div_pct = (factor - 1) * 100
            return f"{div_pct:.2f}% dividend adjustment"
        else:
            return f"Adjustment factor: {factor:.4f}"
    
    def get_adjustment_summary(self) -> Dict[str, Any]:
        """
        Get summary of all adjustments applied.
        
        Returns
        -------
        Dict[str, Any]
            Summary including counts by type and total adjustments
        """
        split_count = sum(1 for a in self.adjustments if a.adjustment_type == 'split')
        dividend_count = sum(1 for a in self.adjustments if a.adjustment_type == 'dividend')
        
        return {
            'total_adjustments': len(self.adjustments),
            'splits': split_count,
            'dividends': dividend_count,
            'adjustments_list': [
                {
                    'date': str(a.date.date()),
                    'type': a.adjustment_type,
                    'factor': a.factor,
                    'description': a.description
                }
                for a in sorted(self.adjustments, key=lambda x: x.date)
            ]
        }

