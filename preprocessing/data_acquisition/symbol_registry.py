"""
Symbol registry management for Stock Forecasting System.

Manages stock symbol metadata, validation, and sector/exchange information.
"""

import pandas as pd
import csv
from pathlib import Path
from typing import List, Dict, Optional, Set
import logging


class SymbolRegistry:
    """
    Manages stock symbol metadata and validation.
    
    Loads and maintains registry of symbols with exchange, sector, and date information.
    Validates symbol membership and provides lookups.
    
    Parameters
    ----------
    registry_file : str, optional
        Path to CSV registry file (default: 'symbols_registry.csv')
    logger : logging.Logger, optional
        Logger instance
    
    Examples
    --------
    >>> registry = SymbolRegistry()
    >>> registry.load_default_sp500()
    >>> is_valid = registry.validate_symbol('AAPL')
    >>> sector = registry.get_sector('AAPL')
    """
    
    # Default supported exchanges
    SUPPORTED_EXCHANGES = {'NYSE', 'NASDAQ', 'AMEX'}
    
    # Common sectors
    SECTORS = {
        'Communication Services',
        'Consumer Discretionary',
        'Consumer Staples',
        'Energy',
        'Financials',
        'Health Care',
        'Industrials',
        'Information Technology',
        'Materials',
        'Real Estate',
        'Utilities'
    }
    
    def __init__(
        self,
        registry_file: str = 'symbols_registry.csv',
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize SymbolRegistry.
        
        Parameters
        ----------
        registry_file : str
            Path to registry CSV file
        logger : logging.Logger, optional
            Logger instance
        """
        self.registry_file = Path(registry_file)
        self.logger = logger or logging.getLogger(__name__)
        self.registry: pd.DataFrame = pd.DataFrame()
        self._symbol_set: Set[str] = set()
    
    def load_registry(self) -> bool:
        """
        Load symbol registry from CSV file.
        
        Expected CSV columns:
        [Symbol, CompanyName, Sector, Exchange, FirstTradeDate, LastTradeDate, Status]
        
        Returns
        -------
        bool
            True if loaded successfully
            
        Raises
        ------
        FileNotFoundError
            If registry file not found
        ValueError
            If CSV structure invalid
        """
        if not self.registry_file.exists():
            self.logger.warning(f"Registry file not found: {self.registry_file}")
            return False
        
        try:
            self.registry = pd.read_csv(self.registry_file)
            
            # Validate required columns
            required_columns = [
                'Symbol', 'CompanyName', 'Sector', 'Exchange',
                'FirstTradeDate', 'LastTradeDate', 'Status'
            ]
            missing_columns = [col for col in required_columns if col not in self.registry.columns]
            if missing_columns:
                raise ValueError(f"Missing columns: {missing_columns}")
            
            # Build symbol set for fast lookups
            self._symbol_set = set(self.registry['Symbol'].str.upper().unique())
            
            self.logger.info(f"Loaded {len(self.registry)} symbols from {self.registry_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load registry: {e}")
            raise
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Check if symbol is in registry and active.
        
        Parameters
        ----------
        symbol : str
            Symbol to validate
        
        Returns
        -------
        bool
            True if symbol is active in registry
        """
        if self.registry.empty:
            return False
        
        symbol_upper = symbol.upper()
        if symbol_upper not in self._symbol_set:
            return False
        
        # Check if status is ACTIVE
        status = self.registry[self.registry['Symbol'].str.upper() == symbol_upper]['Status'].values
        return len(status) > 0 and status[0].upper() == 'ACTIVE'
    
    def get_sector(self, symbol: str) -> Optional[str]:
        """
        Get sector for a symbol.
        
        Parameters
        ----------
        symbol : str
            Symbol to lookup
        
        Returns
        -------
        str or None
            Sector name or None if not found
        """
        if self.registry.empty:
            return None
        
        result = self.registry[
            self.registry['Symbol'].str.upper() == symbol.upper()
        ]['Sector']
        
        return result.values[0] if len(result) > 0 else None
    
    def get_exchange(self, symbol: str) -> Optional[str]:
        """
        Get exchange for a symbol.
        
        Parameters
        ----------
        symbol : str
            Symbol to lookup
        
        Returns
        -------
        str or None
            Exchange name or None if not found
        """
        if self.registry.empty:
            return None
        
        result = self.registry[
            self.registry['Symbol'].str.upper() == symbol.upper()
        ]['Exchange']
        
        return result.values[0] if len(result) > 0 else None
    
    def get_symbols_by_sector(self, sector: str) -> List[str]:
        """
        Get all symbols in a sector.
        
        Parameters
        ----------
        sector : str
            Sector name
        
        Returns
        -------
        List[str]
            List of symbols in sector
        """
        if self.registry.empty:
            return []
        
        return self.registry[
            self.registry['Sector'].str.lower() == sector.lower()
        ]['Symbol'].tolist()
    
    def get_all_symbols(self) -> List[str]:
        """
        Get all active symbols.
        
        Returns
        -------
        List[str]
            List of all active symbols
        """
        if self.registry.empty:
            return []
        
        return self.registry[
            self.registry['Status'].str.upper() == 'ACTIVE'
        ]['Symbol'].tolist()
    
    def add_symbol(
        self,
        symbol: str,
        company_name: str,
        sector: str,
        exchange: str,
        first_trade_date: str,
        last_trade_date: str,
        status: str = 'ACTIVE'
    ) -> bool:
        """
        Add a symbol to registry.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
        company_name : str
            Company name
        sector : str
            Sector
        exchange : str
            Exchange
        first_trade_date : str
            First trade date
        last_trade_date : str
            Last trade date
        status : str
            Status (default: 'ACTIVE')
        
        Returns
        -------
        bool
            True if added successfully
        """
        if exchange.upper() not in self.SUPPORTED_EXCHANGES:
            self.logger.warning(f"Exchange {exchange} not supported")
            return False
        
        new_row = {
            'Symbol': symbol.upper(),
            'CompanyName': company_name,
            'Sector': sector,
            'Exchange': exchange.upper(),
            'FirstTradeDate': first_trade_date,
            'LastTradeDate': last_trade_date,
            'Status': status.upper()
        }
        
        self.registry = pd.concat(
            [self.registry, pd.DataFrame([new_row])],
            ignore_index=True
        )
        self._symbol_set.add(symbol.upper())
        
        return True
    
    def save_registry(self, output_path: Optional[str] = None) -> bool:
        """
        Save registry to CSV file.
        
        Parameters
        ----------
        output_path : str, optional
            Path to save registry (uses default if not specified)
        
        Returns
        -------
        bool
            True if saved successfully
        """
        try:
            save_path = output_path or str(self.registry_file)
            self.registry.to_csv(save_path, index=False)
            self.logger.info(f"Saved registry to {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save registry: {e}")
            return False
    
    def load_default_sp500(self) -> bool:
        """
        Load default S&P 500 constituents.
        
        Creates a minimal registry with common S&P 500 symbols.
        
        Returns
        -------
        bool
            True if loaded
        """
        sp500_data = [
            ('AAPL', 'Apple Inc.', 'Information Technology', 'NASDAQ', '1997-11-28', '2024-01-19', 'ACTIVE'),
            ('MSFT', 'Microsoft Corporation', 'Information Technology', 'NASDAQ', '1986-03-13', '2024-01-19', 'ACTIVE'),
            ('GOOGL', 'Alphabet Inc.', 'Communication Services', 'NASDAQ', '2006-08-19', '2024-01-19', 'ACTIVE'),
            ('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', 'NASDAQ', '1997-05-16', '2024-01-19', 'ACTIVE'),
            ('TSLA', 'Tesla Inc.', 'Consumer Discretionary', 'NASDAQ', '2010-06-29', '2024-01-19', 'ACTIVE'),
        ]
        
        self.registry = pd.DataFrame(
            sp500_data,
            columns=['Symbol', 'CompanyName', 'Sector', 'Exchange', 'FirstTradeDate', 'LastTradeDate', 'Status']
        )
        self._symbol_set = set(self.registry['Symbol'].unique())
        
        self.logger.info("Loaded default S&P 500 symbols (subset)")
        return True
    
    def get_registry_info(self) -> Dict:
        """
        Get registry information.
        
        Returns
        -------
        Dict
            Information about registry (count, sectors, exchanges)
        """
        if self.registry.empty:
            return {'total_symbols': 0}
        
        return {
            'total_symbols': len(self.registry),
            'active_symbols': (self.registry['Status'].str.upper() == 'ACTIVE').sum(),
            'sectors': self.registry['Sector'].unique().tolist(),
            'exchanges': self.registry['Exchange'].unique().tolist()
        }
