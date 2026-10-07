"""Tests for chronological splits and temporal integrity verification."""

import json

import numpy as np
import pandas as pd
import pytest

from preprocessing.data_splitter import ChronologicalDataSplitter


def _frame(dates, offset=0):
    return pd.DataFrame(
        {'Close': np.arange(len(dates), dtype=float) + 100 + offset},
        index=pd.DatetimeIndex(dates),
    )


def test_single_frame_split_is_chronological_and_persists_metadata(tmp_path):
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    output_path = tmp_path / 'splits' / 'split_metadata.json'

    splits, metadata = ChronologicalDataSplitter().split(
        _frame(dates), output_path=output_path
    )

    assert [len(splits[name]) for name in ('train', 'validation', 'test')] == [70, 15, 15]
    assert splits['train'].index.max() < splits['validation'].index.min()
    assert splits['validation'].index.max() < splits['test'].index.min()
    assert metadata['temporal_integrity_verified'] is True
    assert metadata['cutoff_dates']['train_end_date'] == dates[69].isoformat()
    assert metadata['cutoff_dates']['val_start_date'] == dates[70].isoformat()
    assert metadata['cutoff_dates']['test_start_date'] == dates[85].isoformat()
    assert set(metadata['cutoff_dates']) == {
        'train_start_date', 'train_end_date', 'val_start_date',
        'val_end_date', 'test_start_date', 'test_end_date',
    }
    assert metadata['splits']['validation']['row_count'] == 15
    assert json.loads(output_path.read_text(encoding='utf-8'))['temporal_integrity_verified']


def test_multiple_symbols_share_cutoffs_despite_date_gaps(tmp_path):
    calendar = pd.date_range('2024-01-01', periods=100, freq='D')
    symbol_data = {
        'AAA': _frame(calendar.delete([5, 6, 30, 70])),
        'BBB': _frame(calendar.delete([10, 11, 12, 71, 72]), offset=20),
    }

    splits, metadata = ChronologicalDataSplitter().split(
        symbol_data, output_path=tmp_path / 'metadata.json'
    )

    assert metadata['cutoff_dates']['train_end_date'] == calendar[69].isoformat()
    assert metadata['cutoff_dates']['val_start_date'] == calendar[70].isoformat()
    for symbol in symbol_data:
        assert splits['train'][symbol].index.max() <= calendar[69]
        assert (splits['validation'][symbol].index > calendar[69]).all()
        assert (splits['validation'][symbol].index <= calendar[84]).all()
        assert (splits['test'][symbol].index > calendar[84]).all()
    assert metadata['splits']['train']['symbols']['AAA']['row_count'] == len(splits['train']['AAA'])


def test_three_timestamp_minimum_still_creates_three_splits(tmp_path):
    dates = pd.date_range('2024-01-01', periods=3, freq='D')
    splits, _ = ChronologicalDataSplitter().split(
        _frame(dates), output_path=tmp_path / 'test_minimum.json'
    )

    assert [len(splits[name]) for name in ('train', 'validation', 'test')] == [1, 1, 1]


@pytest.mark.parametrize('ratios', [
    (0.6, 0.2, 0.1),
    (0, 0.5, 0.5),
])
def test_invalid_ratios_are_rejected(ratios):
    with pytest.raises(ValueError):
        ChronologicalDataSplitter(*ratios)


def test_integrity_verifier_rejects_date_overlap():
    dates = pd.date_range('2024-01-01', periods=4, freq='D')
    invalid = {
        'train': _frame(dates[:2]),
        'validation': _frame(dates[1:3]),
        'test': _frame(dates[3:]),
    }

    with pytest.raises(ValueError, match='overlap'):
        ChronologicalDataSplitter.verify_no_leakage(invalid)


def test_integrity_verifier_rejects_out_of_order_ranges():
    dates = pd.date_range('2024-01-01', periods=6, freq='D')
    invalid = {
        'train': _frame(dates[2:4]),
        'validation': _frame(dates[:2]),
        'test': _frame(dates[4:]),
    }

    with pytest.raises(ValueError, match='Chronological ordering'):
        ChronologicalDataSplitter.verify_no_leakage(invalid)


def test_split_rejects_duplicate_or_unsorted_dates():
    dates = pd.date_range('2024-01-01', periods=6, freq='D')
    splitter = ChronologicalDataSplitter()

    with pytest.raises(ValueError, match='chronologically sorted'):
        splitter.split(_frame(dates[::-1]), output_path='bad.json')
    with pytest.raises(ValueError, match='duplicate timestamps'):
        splitter.split(
            _frame(dates.insert(3, dates[2])),
            output_path='duplicate.json',
        )