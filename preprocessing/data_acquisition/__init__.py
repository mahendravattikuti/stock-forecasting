"""
Data acquisition module for Stock Forecasting System.

Provides adapters for fetching market data from multiple sources.
"""

from .base_adapter import DataAdapter, DataAdapterError
from .iex_adapter import IEXAdapter
from .yfinance_adapter import YFinanceAdapter
from .acquisition_coordinator import AcquisitionCoordinator
from .symbol_registry import SymbolRegistry

__all__ = [
    'DataAdapter',
    'DataAdapterError',
    'IEXAdapter',
    'YFinanceAdapter',
    'AcquisitionCoordinator',
    'SymbolRegistry'
]
