"""
Utility functions for end-to-end pipeline validation tests.

Provides helper functions for validating JSON schemas, data constraints,
date ordering, and numeric metrics from pipeline outputs.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json


def validate_json_schema(file_path: Path, required_keys: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate JSON file has all required keys.
    
    Parameters
    ----------
    file_path : Path
        Path to JSON file to validate
    required_keys : List[str]
        List of required top-level keys
    
    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_missing_keys)
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return False, [f"File error: {str(e)}"]
    
    if not isinstance(data, dict):
        return False, ["JSON root must be a dictionary"]
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        return False, [f"Missing required key: {key}" for key in missing_keys]
    
    return True, []


def validate_nested_keys(obj: Dict[str, Any], key_path: str, required: bool = True) -> Tuple[bool, str]:
    """
    Validate nested dictionary keys using dot notation.
    
    Parameters
    ----------
    obj : Dict
        Dictionary to validate
    key_path : str
        Dot-separated path (e.g., "splits.train.row_count")
    required : bool
        Whether the key is required
    
    Returns
    -------
    Tuple[bool, str]
        (exists, error_message)
    """
    keys = key_path.split('.')
    current = obj
    
    for i, key in enumerate(keys):
        if not isinstance(current, dict):
            path_so_far = '.'.join(keys[:i])
            return False, f"Path '{path_so_far}' is not a dictionary"
        
        if key not in current:
            if required:
                return False, f"Missing key: {key_path}"
            return True, ""
        
        current = current[key]
    
    return True, ""


def validate_date_ordering(dates_dict: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate cutoff dates are properly ordered.
    
    Expected keys (in order): train_start, train_end, val_start, val_end, test_start, test_end
    
    Parameters
    ----------
    dates_dict : Dict[str, str]
        Dictionary with date strings (ISO format: YYYY-MM-DD)
    
    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Parse dates
    dates_parsed = {}
    for key, date_str in dates_dict.items():
        try:
            dates_parsed[key] = datetime.fromisoformat(date_str)
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid date format for '{key}': {date_str} ({str(e)})")
    
    if errors:
        return False, errors
    
    # Expected ordering
    expected_order = [
        'train_start_date',
        'train_end_date',
        'val_start_date',
        'val_end_date',
        'test_start_date',
        'test_end_date'
    ]
    
    # Check which keys are present
    present_keys = [k for k in expected_order if k in dates_parsed]
    
    # Validate ordering
    for i in range(len(present_keys) - 1):
        curr_key = present_keys[i]
        next_key = present_keys[i + 1]
        
        if dates_parsed[curr_key] >= dates_parsed[next_key]:
            errors.append(
                f"Date ordering violation: {curr_key} ({dates_parsed[curr_key].date()}) "
                f"should be before {next_key} ({dates_parsed[next_key].date()})"
            )
    
    return len(errors) == 0, errors


def validate_numeric_metrics(metrics_dict: Dict[str, Any], 
                            expected_metrics: Optional[List[str]] = None,
                            min_value: float = 0,
                            max_value: Optional[float] = None) -> Tuple[bool, List[str]]:
    """
    Validate metrics are numeric and within expected ranges.
    
    Parameters
    ----------
    metrics_dict : Dict[str, Any]
        Dictionary of metrics to validate
    expected_metrics : List[str], optional
        List of expected metric keys. If None, validates all values.
    min_value : float
        Minimum allowed value (default 0)
    max_value : Optional[float]
        Maximum allowed value (default None = no upper bound)
    
    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_errors)
    """
    errors = []
    
    metrics_to_check = expected_metrics if expected_metrics else list(metrics_dict.keys())
    
    for metric_name in metrics_to_check:
        if metric_name not in metrics_dict:
            errors.append(f"Missing metric: {metric_name}")
            continue
        
        value = metrics_dict[metric_name]
        
        # Check if numeric
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"Metric '{metric_name}' is not numeric: {type(value).__name__}")
            continue
        
        # Check range
        if value < min_value:
            errors.append(f"Metric '{metric_name}' value {value} is below minimum {min_value}")
        
        if max_value is not None and value > max_value:
            errors.append(f"Metric '{metric_name}' value {value} is above maximum {max_value}")
    
    return len(errors) == 0, errors


def validate_feature_list(features_data: Any) -> Tuple[bool, List[str]]:
    """
    Validate features list has expected structure.
    
    Each feature should have: name, tier, description, lookback_window, causality_verified
    
    Parameters
    ----------
    features_data : Any
        Features data (should be list of dicts)
    
    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(features_data, list):
        return False, [f"Features must be a list, got {type(features_data).__name__}"]
    
    required_feature_keys = ['name', 'tier', 'description']
    
    for i, feature in enumerate(features_data):
        if not isinstance(feature, dict):
            errors.append(f"Feature {i} is not a dictionary")
            continue
        
        # Check required keys
        for key in required_feature_keys:
            if key not in feature:
                errors.append(f"Feature {i} ('{feature.get('name', 'UNKNOWN')}') missing key: {key}")
        
        # Verify tier is valid
        if 'tier' in feature:
            if feature['tier'] not in [1, 2, 3, 'signal_processing', 'cross_asset']:
                errors.append(f"Feature {i} has invalid tier: {feature['tier']}")
        
        # If causality_verified exists, it should be bool
        if 'causality_verified' in feature:
            if not isinstance(feature['causality_verified'], bool):
                errors.append(f"Feature {i} causality_verified must be bool, got {type(feature['causality_verified'])}")
    
    return len(errors) == 0, errors


def validate_csv_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate CSV file structure and contents.
    
    Parameters
    ----------
    file_path : Path
        Path to CSV file
    
    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (UnicodeDecodeError, FileNotFoundError) as e:
        return False, [f"File error: {str(e)}"]
    
    if len(lines) < 2:
        return False, ["CSV file has no header or data rows"]
    
    # Check header exists
    header_parts = lines[0].strip().split(',')
    if not header_parts:
        errors.append("CSV header is empty")
        return False, errors
    
    expected_col_count = len(header_parts)
    
    # Check all rows have same column count
    for i, line in enumerate(lines[1:], start=2):
        cols = line.strip().split(',')
        if len(cols) != expected_col_count and line.strip():  # Skip empty lines
            errors.append(f"Row {i} has {len(cols)} columns, expected {expected_col_count}")
    
    return len(errors) == 0, errors


def validate_markdown_file(file_path: Path, required_sections: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Validate Markdown file structure and content.
    
    Parameters
    ----------
    file_path : Path
        Path to Markdown file
    required_sections : List[str], optional
        List of required section headings (case-insensitive)
    
    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, FileNotFoundError) as e:
        return False, [f"File error: {str(e)}"]
    
    if not content or len(content) < 100:
        return False, ["Markdown file is empty or too small"]
    
    # Extract headings
    lines = content.split('\n')
    headings = []
    for line in lines:
        if line.startswith('#'):
            # Remove markdown formatting
            heading_text = line.lstrip('#').strip()
            headings.append(heading_text.lower())
    
    # Check required sections
    if required_sections:
        for section in required_sections:
            section_lower = section.lower()
            if not any(section_lower in h for h in headings):
                errors.append(f"Missing section: '{section}' (found headings: {headings})")
    
    # Basic markdown validation
    if '```' in content:
        code_fence_count = content.count('```')
        if code_fence_count % 2 != 0:
            errors.append("Unmatched code fence markers (```)")
    
    return len(errors) == 0, errors


def validate_split_consistency(splits_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that train/validation/test splits are consistent and non-overlapping.
    
    Parameters
    ----------
    splits_data : Dict
        Splits dictionary with 'train', 'validation', 'test' keys
    
    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_errors)
    """
    errors = []
    
    required_splits = ['train', 'validation', 'test']
    
    for split_name in required_splits:
        if split_name not in splits_data:
            errors.append(f"Missing split: {split_name}")
            continue
        
        split_info = splits_data[split_name]
        
        # Check required fields
        if 'row_count' not in split_info:
            errors.append(f"Split '{split_name}' missing 'row_count'")
        elif not isinstance(split_info['row_count'], int) or split_info['row_count'] <= 0:
            errors.append(f"Split '{split_name}' row_count must be positive integer")
        
        if 'date_range' not in split_info:
            errors.append(f"Split '{split_name}' missing 'date_range'")
        elif not isinstance(split_info['date_range'], list) or len(split_info['date_range']) != 2:
            errors.append(f"Split '{split_name}' date_range must be [start, end]")
    
    # Validate no overlaps in dates
    if all(s in splits_data for s in required_splits):
        try:
            train_end = datetime.fromisoformat(splits_data['train']['date_range'][1])
            val_start = datetime.fromisoformat(splits_data['validation']['date_range'][0])
            val_end = datetime.fromisoformat(splits_data['validation']['date_range'][1])
            test_start = datetime.fromisoformat(splits_data['test']['date_range'][0])
            
            if train_end >= val_start:
                errors.append(f"Train end ({train_end.date()}) overlaps with validation start ({val_start.date()})")
            
            if val_end >= test_start:
                errors.append(f"Validation end ({val_end.date()}) overlaps with test start ({test_start.date()})")
        except (ValueError, KeyError, IndexError, TypeError) as e:
            errors.append(f"Error validating date ordering: {str(e)}")
    
    return len(errors) == 0, errors


def validate_row_reduction(raw_count: int, cleaned_count: int, 
                          max_removal_percent: float = 5.0) -> Tuple[bool, str]:
    """
    Validate that row reduction during cleaning is reasonable.
    
    Parameters
    ----------
    raw_count : int
        Raw data row count before cleaning
    cleaned_count : int
        Cleaned data row count after cleaning
    max_removal_percent : float
        Maximum allowed removal percentage (default 5%)
    
    Returns
    -------
    Tuple[bool, str]
        (is_valid, error_message if invalid)
    """
    if raw_count <= 0:
        return False, "Raw count must be positive"
    
    if cleaned_count < 0:
        return False, "Cleaned count cannot be negative"
    
    if cleaned_count > raw_count:
        return False, f"Cleaned count ({cleaned_count}) exceeds raw count ({raw_count})"
    
    removal_percent = (raw_count - cleaned_count) / raw_count * 100
    
    if removal_percent > max_removal_percent:
        return False, (
            f"Row removal {removal_percent:.1f}% exceeds maximum {max_removal_percent}%"
        )
    
    return True, ""


def get_json_safely(file_path: Path, default: Any = None) -> Any:
    """
    Safely load JSON file with error handling.
    
    Parameters
    ----------
    file_path : Path
        Path to JSON file
    default : Any
        Default value if file cannot be loaded
    
    Returns
    -------
    Any
        Loaded JSON data or default value
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return default
