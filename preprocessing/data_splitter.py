"""Chronological train/validation/test splitting with temporal integrity checks."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional, Union

import pandas as pd


SplitInput = Union[pd.DataFrame, Mapping[str, pd.DataFrame]]
SplitOutput = Dict[str, Union[pd.DataFrame, Dict[str, pd.DataFrame]]]


@dataclass
class SplitMetadataGenerator:
    """Create and persist JSON-compatible split metadata."""

    @staticmethod
    def generate_splits_metadata(
        splits: SplitOutput,
        cutoffs: Dict[str, pd.Timestamp],
        input_was_mapping: bool,
        ratios: Dict[str, float],
    ) -> dict:
        """Describe date ranges, row counts, and integrity for each split."""
        details = {}
        for split_name, split_data in splits.items():
            frames = split_data if isinstance(split_data, dict) else {'__single__': split_data}
            symbol_info = {}
            all_dates = []
            total_rows = 0
            for symbol, frame in frames.items():
                total_rows += len(frame)
                dates = ChronologicalDataSplitter._normalized_index(frame.index)
                if len(dates):
                    all_dates.extend([dates.min(), dates.max()])
                    symbol_info[symbol] = {
                        'row_count': len(frame),
                        'start_date': dates.min().isoformat(),
                        'end_date': dates.max().isoformat(),
                    }
                else:
                    symbol_info[symbol] = {
                        'row_count': 0,
                        'start_date': None,
                        'end_date': None,
                    }
            details[split_name] = {
                'row_count': total_rows,
                'start_date': min(all_dates).isoformat() if all_dates else None,
                'end_date': max(all_dates).isoformat() if all_dates else None,
                'symbols': symbol_info if input_was_mapping else None,
            }

        return {
            'method': 'chronological_shared_calendar_cutoffs',
            'ratios': ratios,
            'cutoff_dates': {
                name: timestamp.isoformat() for name, timestamp in cutoffs.items()
            },
            'splits': details,
            'temporal_integrity_verified': True,
        }

    @staticmethod
    def save(metadata: dict, output_path: str | Path) -> str:
        """Write split metadata to JSON and return the output path."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as file:
            json.dump(metadata, file, indent=2)
        return str(path)


class ChronologicalDataSplitter:
    """Split one or more time-indexed datasets without shuffling.

    For multiple symbols, boundaries are derived once from the sorted union of
    their timestamps and reused for every symbol. This preserves a common
    calendar cutoff even when individual symbols have missing dates.
    """

    SPLIT_NAMES = ('train', 'validation', 'test')

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        logger: Optional[logging.Logger] = None,
    ):
        ratios = (train_ratio, val_ratio, test_ratio)
        if any(ratio <= 0 or ratio >= 1 for ratio in ratios):
            raise ValueError("Each split ratio must be greater than 0 and less than 1")
        if abs(sum(ratios) - 1.0) > 1e-9:
            raise ValueError("train_ratio, val_ratio, and test_ratio must sum to 1")
        self.train_ratio = float(train_ratio)
        self.val_ratio = float(val_ratio)
        self.test_ratio = float(test_ratio)
        self.logger = logger or logging.getLogger(__name__)
        self.metadata_generator = SplitMetadataGenerator()

    @staticmethod
    def _normalized_index(index: pd.Index) -> pd.DatetimeIndex:
        if not isinstance(index, pd.DatetimeIndex):
            raise ValueError("Every input DataFrame must have a DatetimeIndex")
        if index.hasnans:
            raise ValueError("DatetimeIndex cannot contain NaT values")
        if index.tz is not None:
            return index.tz_convert('UTC').tz_localize(None)
        return index

    @classmethod
    def _validate_frame(cls, frame: pd.DataFrame, symbol: str) -> pd.DatetimeIndex:
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"Data for {symbol} must be a pandas DataFrame")
        if frame.empty:
            raise ValueError(f"Data for {symbol} is empty")
        normalized = cls._normalized_index(frame.index)
        if not normalized.is_monotonic_increasing:
            raise ValueError(f"Data for {symbol} must be chronologically sorted")
        if normalized.has_duplicates:
            raise ValueError(f"Data for {symbol} contains duplicate timestamps")
        return normalized

    @staticmethod
    def _frames(data: SplitInput) -> tuple[Dict[str, pd.DataFrame], bool]:
        if isinstance(data, pd.DataFrame):
            return {'__single__': data}, False
        if not isinstance(data, Mapping) or not data:
            raise ValueError("data must be a non-empty DataFrame or symbol-to-DataFrame mapping")
        return dict(data), True

    @staticmethod
    def _slice_frame(
        frame: pd.DataFrame,
        normalized_dates: pd.DatetimeIndex,
        train_end: pd.Timestamp,
        validation_end: pd.Timestamp,
    ) -> Dict[str, pd.DataFrame]:
        train_mask = normalized_dates <= train_end
        validation_mask = (normalized_dates > train_end) & (normalized_dates <= validation_end)
        test_mask = normalized_dates > validation_end
        return {
            'train': frame.loc[train_mask].copy(),
            'validation': frame.loc[validation_mask].copy(),
            'test': frame.loc[test_mask].copy(),
        }

    def split(
        self,
        data: SplitInput,
        output_path: Optional[str | Path] = None,
    ) -> tuple[SplitOutput, dict]:
        """Split data chronologically and optionally persist split metadata.

        Parameters
        ----------
        data : DataFrame or mapping[str, DataFrame]
            One time-indexed dataset, or multiple symbol datasets.
        output_path : str or Path, optional
            Metadata output location. Defaults to
            ``results/splits_metadata/split_metadata.json``.

        Returns
        -------
        tuple[dict, dict]
            ``(splits, metadata)``. Split keys are ``train``, ``validation``,
            and ``test``. Mapping input yields symbol mappings per split.
        """
        frames, input_was_mapping = self._frames(data)
        normalized_by_symbol = {
            symbol: self._validate_frame(frame, symbol)
            for symbol, frame in frames.items()
        }
        all_dates = pd.DatetimeIndex(
            sorted(set().union(*(set(dates) for dates in normalized_by_symbol.values())))
        )
        if len(all_dates) < 3:
            raise ValueError("At least three unique timestamps are required to create splits")

        train_count = max(1, int(len(all_dates) * self.train_ratio))
        validation_count = max(1, int(len(all_dates) * self.val_ratio))
        if train_count + validation_count >= len(all_dates):
            train_count = max(1, min(train_count, len(all_dates) - 2))
            validation_count = max(
                1, min(validation_count, len(all_dates) - train_count - 1)
            )

        train_end = all_dates[train_count - 1]
        validation_end = all_dates[train_count + validation_count - 1]
        cutoffs = {
            'train_start_date': all_dates[0],
            'train_end_date': train_end,
            'val_start_date': all_dates[train_count],
            'val_end_date': validation_end,
            'test_start_date': all_dates[train_count + validation_count],
            'test_end_date': all_dates[-1],
        }

        per_symbol: Dict[str, Dict[str, pd.DataFrame]] = {
            symbol: self._slice_frame(
                frame, normalized_by_symbol[symbol], train_end, validation_end
            )
            for symbol, frame in frames.items()
        }
        if input_was_mapping:
            splits: SplitOutput = {
                split_name: {
                    symbol: per_symbol[symbol][split_name] for symbol in frames
                }
                for split_name in self.SPLIT_NAMES
            }
        else:
            only = per_symbol['__single__']
            splits = {split_name: only[split_name] for split_name in self.SPLIT_NAMES}

        self.verify_no_leakage(splits)
        metadata = self.metadata_generator.generate_splits_metadata(
            splits,
            cutoffs,
            input_was_mapping,
            {
                'train': self.train_ratio,
                'validation': self.val_ratio,
                'test': self.test_ratio,
            },
        )
        path = output_path or Path('results/splits_metadata/split_metadata.json')
        metadata['metadata_path'] = self.metadata_generator.save(metadata, path)
        self.logger.info(
            "Chronological split complete",
            extra={
                'train_rows': metadata['splits']['train']['row_count'],
                'validation_rows': metadata['splits']['validation']['row_count'],
                'test_rows': metadata['splits']['test']['row_count'],
            },
        )
        return splits, metadata

    @classmethod
    def verify_no_leakage(cls, splits: Mapping[str, object]) -> bool:
        """Raise ValueError when split dates overlap or chronology is violated."""
        missing = set(cls.SPLIT_NAMES) - set(splits)
        if missing:
            raise ValueError(f"Missing required splits: {sorted(missing)}")

        split_dates: Dict[str, Dict[str, set[pd.Timestamp]]] = {}
        for split_name in cls.SPLIT_NAMES:
            split_data = splits[split_name]
            frames = split_data if isinstance(split_data, Mapping) else {'__single__': split_data}
            symbol_dates = {}
            for symbol, frame in frames.items():
                if not isinstance(frame, pd.DataFrame):
                    raise TypeError(f"Split data for {symbol} must be a DataFrame")
                dates = cls._normalized_index(frame.index)
                if not dates.is_monotonic_increasing or dates.has_duplicates:
                    raise ValueError(f"{split_name} dates for {symbol} are not unique and sorted")
                symbol_dates[symbol] = set(dates)
            split_dates[split_name] = symbol_dates

        symbols = set().union(*(item.keys() for item in split_dates.values()))
        for symbol in symbols:
            dates_by_split = [
                split_dates[split_name].get(symbol, set()) for split_name in cls.SPLIT_NAMES
            ]
            if any(dates_by_split[left] & dates_by_split[right]
                   for left in range(3) for right in range(left + 1, 3)):
                raise ValueError(f"Date overlap detected across splits for {symbol}")
            nonempty_ranges = [
                (min(dates), max(dates)) for dates in dates_by_split if dates
            ]
            if any(
                nonempty_ranges[position][1] >= nonempty_ranges[position + 1][0]
                for position in range(len(nonempty_ranges) - 1)
            ):
                raise ValueError(f"Chronological ordering violated across splits for {symbol}")
        return True