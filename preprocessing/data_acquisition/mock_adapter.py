"""
Mock Data Adapter for Offline Testing and Demonstrations
Generates synthetic but realistic stock OHLCV data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .base_adapter import DataAdapter


class MockAdapter(DataAdapter):
    """
    Generates synthetic stock market data with realistic characteristics:
    - Brownian motion for price movement
    - Realistic volume patterns
    - Market holidays respected
    - Proper OHLC relationships
    """
    
    def __init__(self, lookback_years: int = 10, seed: int = 42):
        """
        Initialize mock adapter with synthetic data generation parameters.
        
        Args:
            lookback_years: Years of historical data to generate
            seed: Random seed for reproducibility
        """
        super().__init__(name="MockAdapter", timeout=1)
        self.lookback_years = lookback_years
        self.seed = seed
        np.random.seed(seed)
        
    def fetch(self, symbol: str, **kwargs) -> pd.DataFrame:
        """
        Generate synthetic OHLCV data for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            **kwargs: Additional parameters (ignored)
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            # Symbol-specific parameters for realistic diversity
            params = self._get_symbol_params(symbol)
            
            # Generate date range (trading days only)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_years * 365)
            dates = self._generate_trading_dates(start_date, end_date)
            
            # Generate price series using geometric Brownian motion
            prices = self._generate_prices(
                initial_price=params['initial_price'],
                drift=params['drift'],
                volatility=params['volatility'],
                dates=dates
            )
            
            # Generate OHLC from price series
            ohlc_data = self._generate_ohlc(prices, symbol)
            
            # Generate volume
            volumes = self._generate_volume(len(dates), params['avg_volume'])
            
            # Construct DataFrame
            df = pd.DataFrame({
                'date': dates,
                'open': ohlc_data['open'],
                'high': ohlc_data['high'],
                'low': ohlc_data['low'],
                'close': ohlc_data['close'],
                'volume': volumes
            })
            
            # Set date as index
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.index.name = 'date'
            
            return df
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate mock data for {symbol}: {str(e)}")
    
    def validate_response(self, df: pd.DataFrame) -> bool:
        """Validate synthetic data has required columns and structure."""
        required_cols = {'open', 'high', 'low', 'close', 'volume'}
        return required_cols.issubset(df.columns) and len(df) > 0
    
    @staticmethod
    def _get_symbol_params(symbol: str) -> Dict[str, float]:
        """Get realistic market parameters for each symbol."""
        params_map = {
            'AAPL': {'initial_price': 25.0, 'drift': 0.15, 'volatility': 0.35, 'avg_volume': 50e6},
            'MSFT': {'initial_price': 20.0, 'drift': 0.14, 'volatility': 0.30, 'avg_volume': 25e6},
            'GOOGL': {'initial_price': 150.0, 'drift': 0.16, 'volatility': 0.28, 'avg_volume': 15e6},
            'AMZN': {'initial_price': 10.0, 'drift': 0.17, 'volatility': 0.42, 'avg_volume': 40e6},
            'TSLA': {'initial_price': 1.0, 'drift': 0.25, 'volatility': 0.60, 'avg_volume': 100e6},
        }
        
        # Default parameters for unknown symbols
        return params_map.get(symbol, {
            'initial_price': 50.0,
            'drift': 0.12,
            'volatility': 0.25,
            'avg_volume': 20e6
        })
    
    @staticmethod
    def _generate_trading_dates(start_date: datetime, end_date: datetime) -> list:
        """Generate trading dates (excluding weekends and major holidays)."""
        dates = []
        current = start_date
        
        # US market holidays (simplified)
        holidays = {
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (11, 25), # Thanksgiving (approx)
            (12, 25), # Christmas
        }
        
        while current <= end_date:
            # Skip weekends
            if current.weekday() < 5:
                # Skip holidays
                if (current.month, current.day) not in holidays:
                    dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    @staticmethod
    def _generate_prices(
        initial_price: float,
        drift: float,
        volatility: float,
        dates: list
    ) -> np.ndarray:
        """Generate price series using geometric Brownian motion."""
        n = len(dates)
        dt = 1/252  # Trading days per year
        
        # Generate random returns
        random_returns = np.random.normal(
            loc=drift * dt,
            scale=volatility * np.sqrt(dt),
            size=n
        )
        
        # Calculate price series
        prices = np.exp(np.cumsum(random_returns)) * initial_price
        return prices
    
    @staticmethod
    def _generate_ohlc(prices: np.ndarray, symbol: str) -> Dict[str, np.ndarray]:
        """Generate realistic OHLC from price series."""
        np.random.seed(hash(symbol) % 2**32)  # Reproducible per symbol
        
        n = len(prices)
        
        # Intraday volatility
        intraday_vol = 0.02
        
        opens = prices * (1 + np.random.normal(0, intraday_vol/2, n))
        
        # High: random walk up from open
        highs = opens + np.abs(np.random.normal(0, intraday_vol, n) * opens)
        highs = np.maximum(highs, prices)
        
        # Low: random walk down from open
        lows = opens - np.abs(np.random.normal(0, intraday_vol, n) * opens)
        lows = np.minimum(lows, prices)
        
        closes = prices
        
        # Ensure OHLC relationships
        highs = np.maximum.reduce([opens, closes, highs])
        lows = np.minimum.reduce([opens, closes, lows])
        
        return {
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes
        }
    
    @staticmethod
    def _generate_volume(n_days: int, avg_volume: float) -> np.ndarray:
        """Generate realistic trading volumes with autocorrelation."""
        # Base volume with mean reversion
        volumes = np.zeros(n_days)
        volumes[0] = avg_volume
        
        for i in range(1, n_days):
            # Mean-reverting process
            mean_reversion = 0.3
            noise = np.random.normal(0, avg_volume * 0.3)
            volumes[i] = (
                mean_reversion * volumes[i-1] + 
                (1 - mean_reversion) * avg_volume + 
                noise
            )
        
        # Ensure positive volumes
        volumes = np.maximum(volumes, avg_volume * 0.1)
        
        return volumes.astype(int)


if __name__ == "__main__":
    # Test the mock adapter
    adapter = MockAdapter(lookback_years=10)
    
    print("Generating mock data for test symbols...")
    for symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']:
        df = adapter.fetch(symbol)
        print(f"\n{symbol}: {len(df)} days of data")
        print(df.head())
        print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
