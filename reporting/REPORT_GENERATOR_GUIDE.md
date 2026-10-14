# Pipeline Execution Report Generator Guide

## Overview

The `PipelineReportGenerator` class creates comprehensive markdown reports documenting the entire Stock Market Forecasting System pipeline execution. These reports provide stakeholders with:

- **Data Source Documentation**: Source providers, acquisition configuration, fallback strategies
- **Symbol Processing Summary**: Per-symbol acquisition status, data quality, retention rates
- **Data Cleaning Details**: Actions taken (forward fills, spike corrections, OHLC fixes, adjustments)
- **Feature Engineering Summary**: Tier breakdown, feature counts, causality verification
- **Data Split Documentation**: Train/val/test date ranges, row counts, temporal integrity verification
- **Baseline Model Performance**: Metrics for all trained baseline models
- **Error/Warning Summary**: Issues encountered and recovery actions
- **Reproducibility Information**: Environment versions, random seeds, configuration references

## Usage

### Basic Usage

```python
from reporting.report_generator import (
    PipelineReportGenerator,
    PipelineExecutionContext,
    load_context_from_results_directory
)
import json

# Load configuration
with open('master_config.json', 'r') as f:
    config = json.load(f)

# Load execution results from directory
context = load_context_from_results_directory(
    config=config,
    results_dir='results'
)

# Generate report
generator = PipelineReportGenerator()
report = generator.generate_pipeline_report(context)

# Save to file
generator.save_report(report, 'results/reports/pipeline_execution_report.md')
```

### Manual Context Building

```python
from reporting.report_generator import PipelineReportGenerator, PipelineExecutionContext

# Build context manually
context = PipelineExecutionContext(
    config=config_dict,
    cleaning_reports={
        'AAPL': {...},  # Per-symbol cleaning report
        'MSFT': {...}
    },
    features_manifests={
        'AAPL': {...},  # Per-symbol feature manifest
        'MSFT': {...}
    },
    splits_metadata={...},  # Data split information
    baseline_results={
        'random_walk': {...},
        'arima_111': {...}
    },
    errors=[],  # List of errors encountered
    warnings=[]  # List of warnings
)

# Generate and save report
generator = PipelineReportGenerator()
report = generator.generate_pipeline_report(context)
generator.save_report(report, 'output_path.md')
```

## Report Sections

### 1. Execution Metadata
- Report generation timestamp
- Pipeline execution timestamp
- Pipeline stage (Stage 1, 2, etc.)
- Pipeline version

### 2. Executive Summary
Summary table with key metrics:
- Symbols targeted and successfully processed
- Data retention rate
- Row counts (before/after cleaning)
- Feature generation statistics

### 3. Data Sources
- Primary data source (IEX Cloud, yfinance, etc.)
- Fallback source configuration
- Data acquisition parameters (lookback period, minimum trading days, retry strategy)
- Data format specification (OHLCV fields, adjustment method)

### 4. Symbols Processed
- Complete list of target symbols
- Per-symbol processing results:
  - Raw and cleaned row counts
  - Date ranges
  - Quality assessment

### 5. Data Cleaning Summary
- Aggregate statistics on cleaning actions:
  - Forward fills applied
  - Price spikes corrected
  - OHLC relationship fixes
  - Stock split/dividend adjustments
  - Rows excluded
- Cleaning configuration parameters
- Per-symbol cleaning details

### 6. Feature Engineering Summary
- Feature tier configuration (Tier-1, Tier-2, Tier-3, Signal Processing)
- Enabled technical indicators
- Feature statistics (total count, per-symbol breakdown)
- Quality checks (no look-ahead bias, causality verification)

### 7. Data Splitting
- Splitting methodology and ratios (70/15/15)
- Date ranges and row counts per split
- Chronological cutoff dates
- Data leakage prevention verification

### 8. Baseline Models
- List of configured baseline models
- Performance metrics (MAE, RMSE, directional accuracy)
- Per-dataset results (validation, test)

### 9. Errors and Warnings
- All errors encountered during execution
- All warnings raised (e.g., symbol exclusions)
- Per-error/warning: type, symbol, message

### 10. Reproducibility Information
- Environment versions (Python, NumPy, Pandas, TensorFlow, etc.)
- Random seeds used
- Key configuration file references

## Data Sources

The report generator reads from the following directories and files:

```
results/
├── cleaning_reports/
│   ├── AAPL.json          # CleaningReport for each symbol
│   ├── MSFT.json
│   └── ...
├── features_manifests/
│   ├── AAPL.json          # FeatureManifest for each symbol
│   ├── MSFT.json
│   └── ...
├── splits_metadata/
│   └── splits_metadata.json  # Shared splits information
├── baseline_models/
│   ├── random_walk.json
│   ├── arima_111.json
│   └── ...
└── reports/
    └── pipeline_execution_report.md  # Generated report
```

## PipelineExecutionContext Data Structure

```python
@dataclass
class PipelineExecutionContext:
    config: Dict[str, Any]  # master_config.json
    cleaning_reports: Dict[str, Dict[str, Any]]  # symbol -> CleaningReport dict
    features_manifests: Dict[str, Dict[str, Any]]  # symbol -> FeatureManifest dict
    splits_metadata: Dict[str, Any]  # Shared splits information
    baseline_results: Dict[str, Dict[str, Any]]  # baseline_name -> results dict
    errors: List[Dict[str, Any]]  # List of errors encountered
    warnings: List[Dict[str, Any]]  # List of warnings encountered
```

## Expected Data Formats

### CleaningReport (per symbol)
```json
{
    "symbol": "AAPL",
    "raw_data_rows": 2525,
    "raw_date_range": ["2002-01-02", "2024-01-19"],
    "cleaned_data_rows": 2522,
    "cleaned_date_range": ["2002-01-02", "2024-01-19"],
    "forward_fills_applied": 2,
    "spikes_corrected": 0,
    "ohlc_corrections_applied": 0,
    "adjustments_applied": 1,
    "rows_excluded": 3,
    "quality_status": "PASS",
    "quality_notes": "Excellent data quality after cleaning",
    "completeness_percent": 99.88
}
```

### FeatureManifest (per symbol)
```json
{
    "symbol": "AAPL",
    "timestamp": "2024-01-19T10:35:00Z",
    "features": [
        {"name": "simple_return", "tier": 1, "type": "return"},
        {"name": "rsi_14", "tier": 2, "type": "technical"}
    ],
    "tier_counts": {"tier1": 2, "tier2": 5},
    "causality_verified": true
}
```

### SplitsMetadata (shared)
```json
{
    "method": "chronological_shared_calendar_cutoffs",
    "ratios": {"train": 0.70, "val": 0.15, "test": 0.15},
    "cutoff_dates": {
        "train_end": "2021-09-15",
        "val_start": "2021-09-16",
        "val_end": "2023-02-28",
        "test_start": "2023-03-01",
        "test_end": "2024-01-19"
    },
    "splits": {
        "train": {"row_count": 4900, "start_date": "2002-01-02", "end_date": "2021-09-15"},
        "val": {"row_count": 350, "start_date": "2021-09-16", "end_date": "2023-02-28"},
        "test": {"row_count": 350, "start_date": "2023-03-01", "end_date": "2024-01-19"}
    }
}
```

### BaselineResults (per model)
```json
{
    "random_walk": {
        "validation": {
            "mae": 0.0234,
            "rmse": 0.0312,
            "directional_accuracy": 0.48
        },
        "test": {
            "mae": 0.0241,
            "rmse": 0.0318,
            "directional_accuracy": 0.49
        }
    }
}
```

## Markdown Report Output Example

The generated report is a well-structured markdown file with:

- **Headers**: Multi-level hierarchy (##, ###, ####)
- **Tables**: For metrics, configuration, per-symbol details
- **Lists**: For feature names, baseline descriptions
- **Code Blocks**: For symbol lists
- **Prose**: Explanatory text and notes

### Sample Output Structure
```markdown
# Stock Market Forecasting System - Pipeline Execution Report

## Execution Metadata
...

## Executive Summary
| Metric | Value |
|--------|-------|
| Symbols Targeted | 500 |
| Data Retention Rate | 99.87% |
...

## Data Sources
### Acquisition Configuration
| Parameter | Value |
...

## Symbols Processed
### Per-Symbol Processing Results
| Symbol | Raw Rows | Cleaned Rows | Quality |
...

## Data Cleaning Summary
...

[Additional sections follow same pattern]
```

## Error Handling

The report generator handles missing or malformed data gracefully:

- **Missing cleaning reports**: Symbols listed as "Not processed"
- **Missing features manifests**: Shown as "No features computed"
- **Missing baseline results**: Displayed as "N/A"
- **Malformed JSON**: Logged as warnings; context still generated with available data

All errors and warnings encountered during context loading are included in the report's
Errors and Warnings section.

## Integration with Pipeline

The report generator is typically called at the end of pipeline execution:

```python
# In main pipeline orchestrator
pipeline = StockForecastingPipeline()
pipeline.run()  # Execute all pipeline stages

# Generate report
context = load_context_from_results_directory(config, 'results')
generator = PipelineReportGenerator(logger=logger)
report = generator.generate_pipeline_report(context)
generator.save_report(report, 'results/reports/pipeline_execution_report.md')

logger.info(f"✓ Pipeline execution report generated")
```

## Requirements Reference

- **Requirement 13.1**: Output and Reporting Format
  - Pipeline execution report documenting data sources, symbols, cleaning, features, splits, baselines
- **Design Section 12.2**: Reporting Architecture
  - Comprehensive markdown formatting with sections, tables, metrics

## Testing

Run the test suite:

```bash
pytest reporting/test_report_generator.py -v
```

Tests cover:
- Report generation with valid data
- Report file saving
- Content verification
- Markdown structure validation
- Context loading from directory
- Error handling with missing files

## Performance Notes

- Report generation: O(symbols * features) typically < 1 second
- File I/O: Typically < 100ms for large reports
- Memory: All data loaded into memory; scalable up to thousands of symbols
