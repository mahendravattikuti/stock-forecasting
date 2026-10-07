"""Compute date-aligned, causal market and sector context features."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from features.cross_asset.market_data_manager import MarketDataManager
from features.tier3.cross_asset import RelativeStrengthFeature, SectorCorrelationFeature


class CrossAssetFeatureComputer:
    """Build rolling market, sector, and same-sector peer features.

    External prices may be supplied directly for reproducible runs, or loaded
    through ``MarketDataManager``. Rolling statistics use observations through
    each feature date; market series are aligned using forward-fill only.
    """

    def __init__(
        self,
        market_data_manager: Optional[MarketDataManager] = None,
        symbol_registry=None,
        correlation_window: int = 60,
        top_peers: int = 5,
        high_volatility_threshold: float = 0.25,
        logger: Optional[logging.Logger] = None,
    ):
        if correlation_window < 2:
            raise ValueError("correlation_window must be at least 2")
        if top_peers < 1:
            raise ValueError("top_peers must be positive")
        self.market_data_manager = market_data_manager or MarketDataManager()
        self.symbol_registry = symbol_registry
        self.correlation_window = correlation_window
        self.top_peers = top_peers
        self.high_volatility_threshold = high_volatility_threshold
        self.logger = logger or logging.getLogger(__name__)

    def _sector_for(self, symbol: str, sector: Optional[str]) -> Optional[str]:
        if sector:
            return sector
        if self.symbol_registry is not None:
            return self.symbol_registry.get_sector(symbol)
        return None

    def _peer_symbols(self, sector: Optional[str], symbol: str) -> list[str]:
        if not sector or self.symbol_registry is None:
            return []
        return [
            peer.upper() for peer in self.symbol_registry.get_symbols_by_sector(sector)
            if peer.upper() != symbol.upper()
        ]

    @staticmethod
    def _market_frame(
        data: Dict[str, pd.DataFrame | pd.Series], index: pd.DatetimeIndex
    ) -> pd.DataFrame:
        prices = {}
        for ticker, value in data.items():
            if isinstance(value, pd.DataFrame):
                if 'Close' in value.columns:
                    series = value['Close']
                elif ticker in value.columns:
                    series = value[ticker]
                else:
                    raise ValueError(f"No close-price series found for {ticker}")
            else:
                series = value
            series = pd.Series(series, index=series.index, dtype=float)
            if not isinstance(series.index, pd.DatetimeIndex):
                series.index = pd.to_datetime(series.index)
            if series.index.tz is not None:
                series.index = series.index.tz_localize(None)
            series = series.loc[~series.index.duplicated(keep='last')].sort_index()
            prices[ticker.upper()] = series.reindex(index).ffill()
        return pd.DataFrame(prices, index=index)

    def _compute_features(
        self,
        symbol: str,
        stock: pd.DataFrame,
        market_prices: pd.DataFrame,
        sector: Optional[str],
        sector_etf: Optional[str],
        peer_tickers: list[str],
    ) -> pd.DataFrame:
        window = self.correlation_window
        close = stock['Close'].astype(float)
        features = pd.DataFrame(index=stock.index)

        if 'SPY' in market_prices:
            relative = RelativeStrengthFeature()
            relative.correlation_period = window
            relative.spy_data = market_prices['SPY']
            features = features.join(relative.compute(stock))

            spy_close = market_prices['SPY']
            spy_returns = spy_close.pct_change(fill_method=None)
            trend = spy_close.pct_change(periods=window, fill_method=None)
            annualized_volatility = (
                spy_returns.rolling(window, min_periods=window).std() * np.sqrt(252)
            )
            regime = pd.Series(np.nan, index=stock.index, dtype=float)
            valid = trend.notna() & annualized_volatility.notna()
            high_vol = valid & (annualized_volatility > self.high_volatility_threshold)
            regime.loc[high_vol] = 3
            normal = valid & ~high_vol
            regime.loc[normal & (trend > 0.02)] = 2
            regime.loc[normal & (trend < -0.02)] = 0
            regime.loc[normal & (trend.abs() <= 0.02)] = 1
            features['market_regime'] = regime
            features['market_volatility_annualized'] = annualized_volatility

        if sector_etf and sector_etf in market_prices:
            sector_feature = SectorCorrelationFeature(
                config={'sector_etf': sector_etf, 'sector_data': market_prices[sector_etf]}
            )
            sector_feature.correlation_period = window
            features = features.join(sector_feature.compute(stock))

        peer_correlations = {}
        stock_returns = close.pct_change(fill_method=None)
        for peer in peer_tickers:
            if peer not in market_prices:
                continue
            peer_returns = market_prices[peer].pct_change(fill_method=None)
            peer_correlations[peer] = stock_returns.rolling(
                window, min_periods=window
            ).corr(peer_returns)

        for rank in range(self.top_peers):
            features[f'sector_peer_corr_top_{rank + 1}'] = np.nan
        if peer_correlations:
            correlations = pd.DataFrame(peer_correlations, index=stock.index)
            for rank in range(min(self.top_peers, correlations.shape[1])):
                features[f'sector_peer_corr_top_{rank + 1}'] = correlations.apply(
                    lambda row, rank=rank: (
                        row.nlargest(rank + 1).iloc[-1]
                        if row.notna().sum() > rank else np.nan
                    ),
                    axis=1,
                )
            features['sector_peer_corr_top_mean'] = correlations.apply(
                lambda row: row.nlargest(self.top_peers).mean(), axis=1
            )

        return features

    def _check_causality(
        self,
        symbol: str,
        stock: pd.DataFrame,
        market_prices: pd.DataFrame,
        sector: Optional[str],
        sector_etf: Optional[str],
        peer_tickers: list[str],
        baseline: pd.DataFrame,
    ) -> None:
        if len(stock) < 2:
            return
        cutoffs = np.unique(np.linspace(0, len(stock) - 2, num=min(3, len(stock) - 1), dtype=int))
        for cutoff in cutoffs:
            changed_stock = stock.copy(deep=True)
            changed_market = market_prices.copy(deep=True)
            changed_stock.iloc[cutoff + 1:, changed_stock.columns.get_loc('Close')] *= 1.137
            changed_market.iloc[cutoff + 1:, :] *= 1.137
            changed = self._compute_features(
                symbol, changed_stock, changed_market, sector, sector_etf, peer_tickers
            )
            try:
                assert_frame_equal(
                    baseline.iloc[:cutoff + 1], changed.iloc[:cutoff + 1],
                    check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-10,
                )
            except AssertionError as exc:
                raise ValueError(
                    f"Cross-asset features for {symbol} depend on data after row {cutoff}"
                ) from exc

    def compute_all_cross_asset_features(
        self,
        symbol: str,
        symbol_data: pd.DataFrame,
        market_data: Optional[Dict[str, pd.DataFrame | pd.Series]] = None,
        peer_data: Optional[Dict[str, pd.DataFrame | pd.Series]] = None,
        sector: Optional[str] = None,
        manifest_path: Optional[str | Path] = None,
    ) -> Tuple[pd.DataFrame, dict]:
        """Compute cross-asset features and return them with a manifest."""
        if symbol_data is None or symbol_data.empty:
            raise ValueError("symbol_data must be a non-empty DataFrame")
        if not isinstance(symbol_data.index, pd.DatetimeIndex):
            raise ValueError("symbol_data must have a DatetimeIndex")
        if 'Close' not in symbol_data.columns:
            raise ValueError("symbol_data must contain a Close column")
        if not symbol_data.index.is_monotonic_increasing or symbol_data.index.has_duplicates:
            raise ValueError("symbol_data index must be strictly increasing and unique")

        symbol = symbol.upper()
        sector = self._sector_for(symbol, sector)
        sector_etf = self.market_data_manager.SECTOR_ETFS.get(sector) if sector else None
        supplied_market = dict(market_data or {})
        supplied_peers = dict(peer_data or {})
        supplied_market.update(supplied_peers)
        benchmark_tickers = {'SPY', sector_etf}
        peer_tickers = list(dict.fromkeys(
            self._peer_symbols(sector, symbol)
            + [ticker.upper() for ticker in supplied_peers]
            + [
                ticker.upper() for ticker in supplied_market
                if ticker.upper() not in benchmark_tickers
                and ticker.upper() != symbol
            ]
        ))
        needed = ['SPY'] + ([sector_etf] if sector_etf else [])
        needed.extend(peer_tickers)
        missing = [ticker for ticker in needed if ticker and ticker not in supplied_market]
        downloaded_symbols = set(missing)
        if missing:
            downloaded = self.market_data_manager.download_market_data(
                symbol_data.index[0], symbol_data.index[-1], symbols=missing
            )
            supplied_market.update(downloaded)

        market_prices = self._market_frame(supplied_market, symbol_data.index)
        features = self._compute_features(
            symbol, symbol_data, market_prices, sector, sector_etf, peer_tickers
        )
        self._check_causality(
            symbol, symbol_data, market_prices, sector, sector_etf,
            peer_tickers, features,
        )

        last_top_peers = []
        if peer_tickers and len(market_prices):
            peer_values = {}
            stock_returns = symbol_data['Close'].astype(float).pct_change(fill_method=None)
            for peer in peer_tickers:
                if peer in market_prices:
                    peer_values[peer] = stock_returns.rolling(
                        self.correlation_window,
                        min_periods=self.correlation_window,
                    ).corr(market_prices[peer].pct_change(fill_method=None))
            if peer_values:
                final = pd.DataFrame(peer_values).iloc[-1].dropna().sort_values(ascending=False)
                last_top_peers = [
                    {'symbol': peer, 'correlation': float(value)}
                    for peer, value in final.head(self.top_peers).items()
                ]

        manifest = {
            'symbol': symbol,
            'sector': sector,
            'sector_etf': sector_etf,
            'calculation_date': pd.Timestamp.now(tz='UTC').isoformat(),
            'date_range': {
                'start': symbol_data.index[0].isoformat(),
                'end': symbol_data.index[-1].isoformat(),
            },
            'window_size': self.correlation_window,
            'top_peers_requested': self.top_peers,
            'top_peers_at_latest_date': last_top_peers,
            'peer_universe': peer_tickers,
            'features': list(features.columns),
            'methods': {
                'relative_strength': '60-day rolling Pearson correlation of daily returns',
                'sector_correlation': 'Rolling Pearson correlation of daily returns',
                'market_regime': 'SPY rolling trend and annualized volatility; 0=bear, 1=range, 2=bull, 3=high-vol',
                'sector_peers': 'Per-date rolling correlations ranked by value; top peer slots are dynamic',
            },
            'data_sources': {
                ticker: (
                    self.market_data_manager.last_sources.get(ticker, 'downloaded')
                    if ticker in downloaded_symbols else 'provided'
                )
                for ticker in market_prices.columns
            },
            'cache_version': self.market_data_manager.cache_version,
            'alignment': 'Reindex to symbol dates and forward-fill only; never backfill future observations',
            'causality_status': 'VERIFIED',
        }
        if manifest_path is None:
            manifest_path = (
                Path('results/features_manifests') / symbol / 'cross_asset_manifest.json'
            )
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open('w', encoding='utf-8') as file:
            json.dump(manifest, file, indent=2, default=str)
        return features, manifest