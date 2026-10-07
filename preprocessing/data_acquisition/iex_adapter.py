"""
IEX Cloud data adapter for fetching stock market data.

Implements DataAdapter interface for IEX Cloud API with retry logic.
"""

import requests
import pandas as pd
import time
from typing import Optional, Dict, Any
from datetime import datetime
from .base_adapter import DataAdapter, DataAdapterError


class IEXAdapter(DataAdapter):
    """
    Data adapter for IEX Cloud API.
    
    Features:
    - Exponential backoff retry logic (3 attempts)
    - Rate limit handling
    - Comprehensive error handling and logging
    
    Parameters
    ----------
    api_token : str
        IEX Cloud API token
    timeout : int
        Request timeout in seconds (default: 30)
    retry_attempts : int
        Number of retry attempts (default: 3)
    retry_backoff_factor : float
        Backoff factor for retries (default: 2)
    
    Examples
    --------
    >>> adapter = IEXAdapter(api_token='YOUR_TOKEN')
    >>> df = adapter.fetch('AAPL', '2020-01-01', '2024-01-19')
    """
    
    BASE_URL = "https://api.iexcloud.io/stable"
    
    def __init__(
        self,
        api_token: str,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_backoff_factor: float = 2
    ):
        """
        Initialize IEXAdapter.
        
        Parameters
        ----------
        api_token : str
            IEX Cloud API token
        timeout : int
            Request timeout in seconds
        retry_attempts : int
            Number of retry attempts
        retry_backoff_factor : float
            Backoff factor for exponential backoff
        """
        super().__init__(name='iex_cloud', timeout=timeout)
        self.api_token = api_token
        self.retry_attempts = retry_attempts
        self.retry_backoff_factor = retry_backoff_factor
        self.last_status_code = None
        self.rate_limit_remaining = None
    
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from IEX Cloud.
        
        Fetches maximum available historical data (range=max) and filters
        to requested date range. Implements exponential backoff retry logic.
        
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
            If all retries exhausted or data invalid
        """
        url = f"{self.BASE_URL}/stock/{symbol}/chart/max"
        params = {'token': self.api_token}
        
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                # Store status and rate limit info
                self.last_status_code = response.status_code
                self.rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.retry_backoff_factor ** attempt))
                    raise DataAdapterError(f"Rate limited. Retry after {retry_after}s")
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # Convert to DataFrame
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df.index.name = 'Date'
                
                # Rename columns to standard format
                column_mapping = {
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }
                df = df.rename(columns=column_mapping)
                
                # Filter to requested date range
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df.index >= start_dt) & (df.index <= end_dt)]
                
                # Sort chronologically
                df = df.sort_index()
                
                # Validate
                if not self.validate_response(df):
                    raise DataAdapterError(f"Validation failed for {symbol}")
                
                return df
                
            except (requests.RequestException, KeyError, ValueError) as e:
                last_exception = e
                
                if attempt < self.retry_attempts - 1:
                    # Calculate backoff time
                    backoff_time = self.retry_backoff_factor ** attempt
                    time.sleep(backoff_time)
                else:
                    # All retries exhausted
                    raise DataAdapterError(
                        f"Failed to fetch {symbol} after {self.retry_attempts} attempts: {str(last_exception)}"
                    )
        
        # Should not reach here
        raise DataAdapterError(f"Unexpected error fetching {symbol}")
    
    def validate_response(self, df: pd.DataFrame) -> bool:
        """
        Validate IEX Cloud response.
        
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
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise DataAdapterError(f"Missing columns: {missing_cols}")
        
        # Check not empty
        if len(df) == 0:
            raise DataAdapterError("Empty DataFrame returned")
        
        # Check for null values in required columns
        null_rows = df[required_columns].isnull().any(axis=1).sum()
        if null_rows > 0:
            raise DataAdapterError(f"{null_rows} rows with null values in required columns")
        
        # Check OHLC relationships (High >= Low, etc.)
        invalid_ohlc = ((df['High'] < df['Low']) | 
                        (df['High'] < df['Close']) | 
                        (df['Low'] > df['Close'])).sum()
        if invalid_ohlc > 0:
            raise DataAdapterError(f"{invalid_ohlc} rows with invalid OHLC relationships")
        
        # Check chronological ordering
        if not df.index.is_monotonic_increasing:
            raise DataAdapterError("Data not sorted chronologically")
        
        return True
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get rate limit status from last request.
        
        Returns
        -------
        Dict[str, Any]
            Rate limit information
        """
        return {
            'last_status_code': self.last_status_code,
            'rate_limit_remaining': self.rate_limit_remaining
        }
