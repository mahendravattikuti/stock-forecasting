"""
Tier-3 Market Context Features

Implements features that provide market context for individual stocks:
- MarketRegimeFeature: Classification of market conditions (bearish/sideways/bullish/high-vol)
- RelativeStrengthFeature: Correlation with S&P 500
- SectorCorrelationFeature: Correlation with sector ETF (optional)

These features help capture market-level information that influences stock behavior.
"""

from features.tier3.regime import MarketRegimeFeature
from features.tier3.cross_asset import (
    RelativeStrengthFeature,
    SectorCorrelationFeature,
)

__all__ = [
    'MarketRegimeFeature',
    'RelativeStrengthFeature',
    'SectorCorrelationFeature',
]
