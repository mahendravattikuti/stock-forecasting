"""
Abstract base class for data acquisition adapters.

Defines interface for all data providers (IEX Cloud, yfinance, etc.).
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, Any


class DataAdapter(ABC):
    """
    Abstract base class for financial data providers.
    
    All data adapters must implement this interface to provide consistent
    data acquisition behavior across different sources.
    
    Parameters
    ----------
    name : str
        Name of the data provider (e.g., 'iex_cloud', 'yfinance')
    timeout : int
        Request timeout in seconds (default: 30)
    
    Examples
    --------
    >>> adapter = IEXAdapter(api_token='YOUR_TOKEN')
    >>> df = adapter.fetch('AAPL', '2020-01-01', '2024-01-19')
    """
    
    def __init__(self, name: str, timeout: int = 30):
        """
        Initialize DataAdapter.
        
        Parameters
        ----------
        name : str
            Name of the data provider
        timeout : int
            Request timeout in seconds
        """
        self.name = name
        self.timeout = timeout
    
    @abstractmethod
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a symbol within date range.
        
        Parameters
        ----------
        symbol : str
            Stock symbol (e.g., 'AAPL')
        start_date : str
            Start date in format 'YYYY-MM-DD'
        end_date : str
            End date in format 'YYYY-MM-DD'
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns [Date, Open, High, Low, Close, Volume]
            Indexed by Date, sorted chronologically
        
        Raises
        ------
        DataAdapterError
            If fetch fails or data is invalid
        """
        pass
    
    @abstractmethod
    def validate_response(self, df: pd.DataFrame) -> bool:
        """
        Validate that fetched data meets minimum requirements.
        
        Checks:
        - Required columns present [Open, High, Low, Close, Volume]
        - No entirely empty columns
        - Date index is valid
        - Data is sorted chronologically
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate
        
        Returns
        -------
        bool
            True if valid, False otherwise
        
        Raises
        ------
        DataAdapterError
            If validation fails with detailed reason
        """
        pass
    
    def get_name(self) -> str:
        """
        Get adapter name.
        
        Returns
        -------
        str
            Name of data provider
        """
        return self.name


class DataAdapterError(Exception):
    """Exception raised for data adapter errors."""
    pass
