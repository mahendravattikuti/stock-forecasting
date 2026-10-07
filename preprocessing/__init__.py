"""
Preprocessing module for Stock Forecasting System.

Handles data acquisition, cleaning, validation, and feature engineering.
"""

from .data_acquisition import (
    DataAdapter,
    DataAdapterError,
    IEXAdapter,
    YFinanceAdapter
)

__all__ = [
    'DataAdapter',
    'DataAdapterError',
    'IEXAdapter',
    'YFinanceAdapter'
]
