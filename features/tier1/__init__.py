"""
Tier-1 Features Module

High-priority, always-computed features for stock forecasting:
- Returns: Simple and log returns
- Normalized Prices: Normalized close and volume indicators

All Tier-1 features are foundational and should be computed for all symbols.
"""

from features.tier1.returns import ReturnsFeature
from features.tier1.normalized_prices import NormalizedPricesFeature

__all__ = [
    'ReturnsFeature',
    'NormalizedPricesFeature',
]
