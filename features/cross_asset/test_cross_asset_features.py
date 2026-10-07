"""Tests for Phase 10 cross-asset data management and features."""

import json

import numpy as np
import pandas as pd

from features.cross_asset import CrossAssetFeatureComputer, MarketDataManager


def _prices(index, close):
    close = pd.Series(close, index=index, dtype=float)
    return pd.DataFrame({
        'Open': close,
        'High': close * 1.01,
        'Low': close * 0.99,
        'Close': close,
        'Volume': 1_000_000,
    }, index=index)


def test_market_data_manager_caches_downloads(tmp_path):
    calls = []

    def downloader(symbol, start, end):
        calls.append((symbol, start, end))
        dates = pd.date_range(start, end - pd.Timedelta(days=1), freq='D')
        return _prices(dates, np.arange(len(dates), dtype=float) + 100)

    manager = MarketDataManager(cache_dir=tmp_path, downloader=downloader)
    first = manager.get_market_data('SPY', '2024-01-01', '2024-01-10')
    second = manager.get_market_data('SPY', '2024-01-01', '2024-01-10')

    assert len(calls) == 1
    pd.testing.assert_frame_equal(first, second)
    assert manager.last_sources['SPY'] == 'cache:v1'
    assert list(tmp_path.glob('v1_SPY_*.csv'))


def test_market_data_alignment_does_not_backfill():
    target_index = pd.date_range('2024-01-01', periods=4, freq='D')
    market_index = target_index[1:3]
    market_data = {'SPY': _prices(market_index, [100, 101])}

    aligned = MarketDataManager.align_data(market_data, target_index)

    assert pd.isna(aligned.loc[target_index[0], 'SPY'])
    assert aligned['SPY'].tolist()[1:] == [100, 101, 101]


def test_cross_asset_computation_and_manifest_are_causal(tmp_path):
    rng = np.random.default_rng(8)
    index = pd.date_range('2024-01-01', periods=120, freq='D')
    market_returns = rng.normal(0.0004, 0.008, len(index))
    spy = 100 * np.exp(np.cumsum(market_returns))
    stock = 50 * np.exp(np.cumsum(market_returns + rng.normal(0, 0.004, len(index))))
    sector = 80 * np.exp(np.cumsum(market_returns + rng.normal(0, 0.003, len(index))))
    peer_a = 30 * np.exp(np.cumsum(market_returns + rng.normal(0, 0.002, len(index))))
    peer_b = 20 * np.exp(np.cumsum(-market_returns + rng.normal(0, 0.002, len(index))))
    stock_data = _prices(index, stock)
    market_data = {
        'SPY': _prices(index, spy),
        'XLK': _prices(index, sector),
        'MSFT': _prices(index, peer_a),
        'NVDA': _prices(index, peer_b),
    }
    manifest_path = tmp_path / 'cross_asset_manifest.json'
    computer = CrossAssetFeatureComputer(correlation_window=20, top_peers=2)

    features, manifest = computer.compute_all_cross_asset_features(
        'AAPL', stock_data, market_data=market_data,
        sector='Information Technology', manifest_path=manifest_path,
    )

    expected_columns = {
        'relative_strength', 'sector_correlation', 'market_regime',
        'market_volatility_annualized', 'sector_peer_corr_top_1',
        'sector_peer_corr_top_2', 'sector_peer_corr_top_mean',
    }
    assert expected_columns.issubset(features.columns)
    assert features.index.equals(index)
    assert features['relative_strength'].notna().any()
    assert features['sector_correlation'].notna().any()
    assert features['sector_peer_corr_top_mean'].notna().any()
    assert manifest['causality_status'] == 'VERIFIED'
    assert manifest['sector_etf'] == 'XLK'
    assert manifest['data_sources']['SPY'] == 'provided'
    assert manifest_path.exists()
    assert json.loads(manifest_path.read_text(encoding='utf-8')) == manifest


def test_cross_asset_computer_downloads_missing_market_data(tmp_path):
    dates = pd.date_range('2024-01-01', periods=40, freq='D')
    calls = []

    def downloader(symbol, start, end):
        calls.append(symbol)
        download_dates = pd.date_range(start, end - pd.Timedelta(days=1), freq='D')
        values = np.linspace(100, 110, len(download_dates))
        return _prices(download_dates, values)

    manager = MarketDataManager(cache_dir=tmp_path / 'cache', downloader=downloader)
    computer = CrossAssetFeatureComputer(
        market_data_manager=manager, correlation_window=10
    )
    features, manifest = computer.compute_all_cross_asset_features(
        'AAPL', _prices(dates, np.linspace(50, 55, len(dates))),
        sector='Information Technology', manifest_path=tmp_path / 'manifest.json',
    )

    assert set(calls) == {'SPY', 'XLK'}
    assert features['relative_strength'].notna().any()
    assert manifest['data_sources']['SPY'] == 'yfinance'