"""
Acquisition coordinator orchestrating data fetching with fallback strategy.

Manages primary and fallback data sources with logging and validation.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .base_adapter import DataAdapter, DataAdapterError
from .iex_adapter import IEXAdapter
from .yfinance_adapter import YFinanceAdapter


class AcquisitionCoordinator:
    """
    Orchestrates data acquisition with fallback strategy.
    
    Attempts to fetch data from primary source (IEX Cloud) and falls back
    to yfinance if primary source fails. Logs all attempts and outcomes.
    
    Parameters
    ----------
    primary_adapter : DataAdapter
        Primary data source adapter
    fallback_adapter : DataAdapter
        Fallback data source adapter
    logger : logging.Logger, optional
        Logger for tracking acquisition attempts
    
    Examples
    --------
    >>> iex = IEXAdapter(api_token='YOUR_TOKEN')
    >>> yf = YFinanceAdapter()
    >>> coordinator = AcquisitionCoordinator(iex, yf)
    >>> df = coordinator.fetch_with_fallback('AAPL', '2020-01-01', '2024-01-19')
    """
    
    def __init__(
        self,
        primary_adapter: DataAdapter,
        fallback_adapter: DataAdapter,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize AcquisitionCoordinator.
        
        Parameters
        ----------
        primary_adapter : DataAdapter
            Primary source
        fallback_adapter : DataAdapter
            Fallback source
        logger : logging.Logger, optional
            Logger instance
        """
        self.primary_adapter = primary_adapter
        self.fallback_adapter = fallback_adapter
        self.logger = logger or logging.getLogger(__name__)
        self.acquisition_log: List[Dict] = []
    
    def fetch_with_fallback(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        min_trading_days: int = 2500
    ) -> Tuple[pd.DataFrame, str]:
        """
        Fetch data with automatic fallback on failure.
        
        Attempts primary source first. If it fails, automatically tries fallback.
        Logs all attempts and outcomes.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
        start_date : str
            Start date 'YYYY-MM-DD'
        end_date : str
            End date 'YYYY-MM-DD'
        min_trading_days : int
            Minimum required trading days (default: 2500)
        
        Returns
        -------
        Tuple[pd.DataFrame, str]
            Tuple of (data_frame, source) indicating which source succeeded
            
        Raises
        ------
        DataAdapterError
            If both primary and fallback sources fail
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'attempts': []
        }
        
        # Try primary source
        self.logger.info(f"Acquiring data for {symbol} from {self.primary_adapter.get_name()}")
        try:
            df = self.primary_adapter.fetch(symbol, start_date, end_date)
            
            # Validate minimum trading days
            if len(df) < min_trading_days:
                raise DataAdapterError(
                    f"Insufficient data: {len(df)} trading days, need {min_trading_days}"
                )
            
            log_entry['attempts'].append({
                'source': self.primary_adapter.get_name(),
                'status': 'success',
                'rows': len(df)
            })
            log_entry['status'] = 'success'
            log_entry['source'] = self.primary_adapter.get_name()
            
            self.logger.info(
                f"✓ {symbol}: {len(df)} trading days from {self.primary_adapter.get_name()}"
            )
            self.acquisition_log.append(log_entry)
            
            return df, self.primary_adapter.get_name()
            
        except DataAdapterError as e:
            primary_error = str(e)
            self.logger.warning(
                f"✗ {symbol}: Primary source failed: {primary_error}"
            )
            log_entry['attempts'].append({
                'source': self.primary_adapter.get_name(),
                'status': 'failed',
                'error': primary_error
            })
            
            # Try fallback source
            self.logger.info(f"Attempting fallback source: {self.fallback_adapter.get_name()}")
            try:
                df = self.fallback_adapter.fetch(symbol, start_date, end_date)
                
                # Validate minimum trading days
                if len(df) < min_trading_days:
                    raise DataAdapterError(
                        f"Insufficient data: {len(df)} trading days, need {min_trading_days}"
                    )
                
                log_entry['attempts'].append({
                    'source': self.fallback_adapter.get_name(),
                    'status': 'success',
                    'rows': len(df)
                })
                log_entry['status'] = 'success'
                log_entry['source'] = self.fallback_adapter.get_name()
                
                self.logger.info(
                    f"✓ {symbol}: {len(df)} trading days from {self.fallback_adapter.get_name()} (fallback)"
                )
                self.acquisition_log.append(log_entry)
                
                return df, self.fallback_adapter.get_name()
                
            except DataAdapterError as e:
                fallback_error = str(e)
                self.logger.error(
                    f"✗ {symbol}: Fallback source failed: {fallback_error}"
                )
                log_entry['attempts'].append({
                    'source': self.fallback_adapter.get_name(),
                    'status': 'failed',
                    'error': fallback_error
                })
                log_entry['status'] = 'failed'
                self.acquisition_log.append(log_entry)
                
                raise DataAdapterError(
                    f"All sources exhausted for {symbol}. "
                    f"Primary: {primary_error}. Fallback: {fallback_error}"
                )
    
    def fetch_multiple(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        min_trading_days: int = 2500
    ) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
        """
        Fetch data for multiple symbols.
        
        Parameters
        ----------
        symbols : List[str]
            List of symbols to fetch
        start_date : str
            Start date
        end_date : str
            End date
        min_trading_days : int
            Minimum trading days per symbol
        
        Returns
        -------
        Tuple[Dict[str, DataFrame], Dict[str, str]]
            Tuple of (data_dict, source_dict) where:
            - data_dict: {symbol: DataFrame}
            - source_dict: {symbol: source_name}
        """
        data_dict = {}
        source_dict = {}
        
        for i, symbol in enumerate(symbols, 1):
            self.logger.info(f"[{i}/{len(symbols)}] Processing {symbol}")
            try:
                df, source = self.fetch_with_fallback(
                    symbol, start_date, end_date, min_trading_days
                )
                data_dict[symbol] = df
                source_dict[symbol] = source
            except DataAdapterError as e:
                self.logger.error(f"Failed to acquire {symbol}: {e}")
                source_dict[symbol] = 'failed'
        
        return data_dict, source_dict
    
    def get_acquisition_log(self) -> List[Dict]:
        """
        Get acquisition attempt log.
        
        Returns
        -------
        List[Dict]
            List of acquisition attempts with outcomes
        """
        return self.acquisition_log
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of acquisition attempts.
        
        Returns
        -------
        Dict
            Summary with success count, failure count, sources used
        """
        if not self.acquisition_log:
            return {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        
        successful = sum(1 for entry in self.acquisition_log if entry.get('status') == 'success')
        failed = len(self.acquisition_log) - successful
        
        sources_used = {}
        for entry in self.acquisition_log:
            if entry.get('status') == 'success':
                source = entry.get('source', 'unknown')
                sources_used[source] = sources_used.get(source, 0) + 1
        
        return {
            'total_attempts': len(self.acquisition_log),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(self.acquisition_log) if self.acquisition_log else 0.0,
            'sources_used': sources_used
        }
