"""Download, cache, and align shared market and sector price data."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

import pandas as pd


class MarketDataManager:
    """Retrieve close-price history with versioned local CSV caching.

    Parameters
    ----------
    cache_dir : str or Path
        Directory used for versioned CSV files.
    cache_version : str
        Cache namespace, changed when the normalization policy changes.
    downloader : callable, optional
        Test or application downloader taking ``(symbol, start, end)`` and
        returning a DataFrame. ``end`` is exclusive.
    logger : logging.Logger, optional
        Logger used for cache and download events.
    """

    SECTOR_ETFS = {
        'Communication Services': 'XLC',
        'Consumer Discretionary': 'XLY',
        'Consumer Staples': 'XLP',
        'Energy': 'XLE',
        'Financials': 'XLF',
        'Health Care': 'XLV',
        'Industrials': 'XLI',
        'Information Technology': 'XLK',
        'Materials': 'XLB',
        'Real Estate': 'XLRE',
        'Utilities': 'XLU',
    }
    DEFAULT_SYMBOLS = ('SPY',) + tuple(dict.fromkeys(SECTOR_ETFS.values()))

    def __init__(
        self,
        cache_dir: str | Path = 'data/market_cache',
        cache_version: str = 'v1',
        downloader: Optional[Callable] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if not cache_version or not re.fullmatch(r'[A-Za-z0-9_.-]+', cache_version):
            raise ValueError("cache_version must contain only letters, digits, '.', '_' or '-'")
        self.cache_dir = Path(cache_dir)
        self.cache_version = cache_version
        self.downloader = downloader
        self.logger = logger or logging.getLogger(__name__)
        self.last_sources: Dict[str, str] = {}

    def _cache_path(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> Path:
        safe_symbol = re.sub(r'[^A-Za-z0-9_.-]', '_', symbol.upper())
        return self.cache_dir / (
            f"{self.cache_version}_{safe_symbol}_{start:%Y%m%d}_{end:%Y%m%d}.csv"
        )

    @staticmethod
    def _normalize_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
        if frame is None or frame.empty:
            raise ValueError(f"No market data returned for {symbol}")
        result = frame.copy()
        if isinstance(result.columns, pd.MultiIndex):
            result.columns = result.columns.get_level_values(0)
        if 'Close' not in result.columns:
            raise ValueError(f"Market data for {symbol} has no Close column")
        result.index = pd.DatetimeIndex(pd.to_datetime(result.index), freq=None)
        if result.index.tz is not None:
            result.index = result.index.tz_localize(None)
        result.index.name = None
        result = result.loc[~result.index.duplicated(keep='last')].sort_index()
        result['Close'] = pd.to_numeric(result['Close'], errors='coerce')
        result = result.loc[result['Close'].notna() & (result['Close'] > 0)]
        if result.empty:
            raise ValueError(f"Market data for {symbol} has no valid closing prices")
        return result

    def _download(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        if self.downloader is not None:
            return self.downloader(symbol, start, end)
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError(
                "Market downloads require yfinance; install project requirements"
            ) from exc

        return yf.Ticker(symbol).history(
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
            auto_adjust=True,
            actions=False,
        )

    def get_market_data(
        self,
        symbol: str,
        start_date,
        end_date,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Load one symbol from cache or download and cache it.

        ``end_date`` is inclusive at this public boundary; the downloader
        receives an exclusive end date to match yfinance semantics.
        """
        start = pd.Timestamp(start_date).tz_localize(None).normalize()
        end_inclusive = pd.Timestamp(end_date).tz_localize(None).normalize()
        if start > end_inclusive:
            raise ValueError("start_date must be on or before end_date")
        end = end_inclusive + pd.Timedelta(days=1)
        cache_path = self._cache_path(symbol, start, end)

        if cache_path.exists() and not force_refresh:
            cached = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            normalized = self._normalize_frame(cached, symbol)
            self.last_sources[symbol.upper()] = f'cache:{self.cache_version}'
            return normalized.loc[(normalized.index >= start) & (normalized.index < end)]

        downloaded = self._normalize_frame(self._download(symbol, start, end), symbol)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        downloaded.to_csv(cache_path, index_label='Date')
        self.last_sources[symbol.upper()] = 'yfinance'
        self.logger.info(
            "Cached market data",
            extra={'symbol': symbol.upper(), 'rows': len(downloaded), 'cache': str(cache_path)},
        )
        return downloaded.loc[(downloaded.index >= start) & (downloaded.index < end)]

    def download_market_data(
        self,
        start_date,
        end_date,
        symbols: Optional[Iterable[str]] = None,
        force_refresh: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """Download or load SPY and sector ETF data for a requested range."""
        requested = tuple(dict.fromkeys(
            symbol.upper() for symbol in (symbols or self.DEFAULT_SYMBOLS)
        ))
        data = {
            symbol: self.get_market_data(
                symbol, start_date, end_date, force_refresh=force_refresh
            )
            for symbol in requested
        }
        return data

    @staticmethod
    def align_data(
        market_data: Dict[str, pd.DataFrame],
        target_index: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        """Align close prices to target dates using forward-fill only.

        No backfill is used: dates before the first available observation stay
        missing rather than receiving a future market close.
        """
        if not isinstance(target_index, pd.DatetimeIndex):
            raise ValueError("target_index must be a DatetimeIndex")
        aligned = {}
        for symbol, frame in market_data.items():
            normalized = MarketDataManager._normalize_frame(frame, symbol)
            aligned[symbol.upper()] = normalized['Close'].reindex(
                target_index
            ).ffill()
        return pd.DataFrame(aligned, index=target_index)