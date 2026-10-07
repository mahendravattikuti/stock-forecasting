"""
yfinance data adapter for fetching stock market data.

Implements DataAdapter interface for Yahoo Finance API (fallback source).
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from .base_adapter import DataAdapter, DataAdapterError


class YFinanceAdapter(DataAdapter):
    """
    Data adapter for Yahoo Finance API via yfinance library.
    
    Features:
    - Reliable fallback source when primary source fails
    - Automatic handling of delisted/invalid symbols
    - Timeout and error handling
    
    Parameters
    ----------
    timeout : int
        Request timeout in seconds (default: 30)
    
    Examples
    --------
    >>> adapter = YFinanceAdapter()
    >>> df = adapter.fetch('AAPL', '2020-01-01', '2024-01-19')
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize YFinanceAdapter.
        
        Parameters
        ----------
        timeout : int
            Request timeout in seconds
        """
        super().__init__(name='yfinance', timeout=timeout)
    
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Yahoo Finance.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
        start_date : str
            Start date 'YYYY-MM-DD'
        end_date : str
            End date 'YYYY-MM-DD'
        
        Returns
        -------
        pd.DataFrame
            OHLCV data with columns [Date, Open, High, Low, Close, Volume]
        
        Raises
        ------
        DataAdapterError
            If fetch fails or data invalid
        """
        try:
            # Create yfinance ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            df = ticker.history(
                start=start_date,
                end=end_date,
                timeout=self.timeout
            )
            
            # Check if data was returned
            if df.empty:
                raise DataAdapterError(f"No data returned for {symbol} from {start_date} to {end_date}")
            
            # Rename columns to standard format
            column_mapping = {
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            }
            df = df.rename(columns=column_mapping)
            
            # Keep only required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df[[col for col in required_columns if col in df.columns]]
            
            # Ensure index is named 'Date'
            df.index.name = 'Date'
            
            # Sort chronologically
            df = df.sort_index()
            
            # Validate
            if not self.validate_response(df):
                raise DataAdapterError(f"Validation failed for {symbol}")
            
            return df
            
        except DataAdapterError:
            raise
        except Exception as e:
            raise DataAdapterError(
                f"Failed to fetch {symbol} from yfinance: {str(e)}"
            )
    
    def validate_response(self, df: pd.DataFrame) -> bool:
        """
        Validate yfinance response.
        
        Checks:
        - Required columns present
        - Non-empty data
        - Valid OHLC relationships
        - Chronological ordering
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate
        
        Returns
        -------
        bool
            True if valid
        
        Raises
        ------
        DataAdapterError
            If validation fails
        """
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check columns
        if not all(col in df.columns for col in required_columns):
            raise DataAdapterError(f"Missing required columns")
        
        # Check not empty
        if len(df) == 0:
            raise DataAdapterError("Empty DataFrame returned")
        
        # Check for null values in required columns
        null_rows = df[required_columns].isnull().any(axis=1).sum()
        if null_rows > 0:
            raise DataAdapterError(f"{null_rows} rows with null values")
        
        # Check OHLC relationships
        invalid_ohlc = ((df['High'] < df['Low']) | 
                        (df['High'] < df['Close']) | 
                        (df['Low'] > df['Close'])).sum()
        if invalid_ohlc > 0:
            raise DataAdapterError(f"{invalid_ohlc} rows with invalid OHLC relationships")
        
        # Check chronological ordering
        if not df.index.is_monotonic_increasing:
            raise DataAdapterError("Data not sorted chronologically")
        
        return True
