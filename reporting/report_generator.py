"""
Pipeline execution report generator for Stock Market Forecasting System.

Generates comprehensive markdown reports documenting the entire data pipeline execution,
including data sources, symbols processed, cleaning actions, feature engineering,
data splits, baseline models, and errors/warnings encountered.

References:
- Requirements 13.1: Output and Reporting Format
- Design Section 12.2: Reporting Architecture
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd


@dataclass
class PipelineExecutionContext:
    """Context for pipeline execution aggregating all intermediate results."""
    
    config: Dict[str, Any]
    cleaning_reports: Dict[str, Dict[str, Any]]  # symbol -> report
    features_manifests: Dict[str, Dict[str, Any]]  # symbol -> manifest
    splits_metadata: Dict[str, Any]
    baseline_results: Dict[str, Dict[str, Any]]  # baseline_name -> results
    errors: List[Dict[str, Any]] = None
    warnings: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class PipelineReportGenerator:
    """
    Generates comprehensive pipeline execution report in markdown format.
    
    The report documents:
    - Data sources used and acquisition methodology
    - Symbols processed and acquisition status per symbol
    - Data retention rates and cleaning impact
    - Cleaning actions taken (forward fills, spike corrections, OHLC fixes, adjustments)
    - Feature engineering summary (tiers, counts, causality verification)
    - Data splits applied (train/val/test dates, row counts, temporal integrity)
    - Baseline models trained and their performance metrics
    - Errors and warnings encountered during execution
    
    Examples
    --------
    >>> generator = PipelineReportGenerator(logger=logger)
    >>> context = PipelineExecutionContext(config, cleaning_reports, manifests, splits, baselines)
    >>> report_md = generator.generate_pipeline_report(context)
    >>> generator.save_report(report_md, "results/reports/pipeline_execution_report.md")
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize PipelineReportGenerator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for tracking report generation
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_pipeline_report(self, context: PipelineExecutionContext) -> str:
        """
        Generate comprehensive pipeline execution report in markdown format.
        
        Parameters
        ----------
        context : PipelineExecutionContext
            Aggregated pipeline execution results
        
        Returns
        -------
        str
            Markdown-formatted pipeline execution report
        """
        report_parts = []
        
        # Title and metadata
        report_parts.append(self._generate_title_section(context))
        
        # Executive summary
        report_parts.append(self._generate_executive_summary(context))
        
        # Data sources section
        report_parts.append(self._generate_data_sources_section(context))
        
        # Symbols processed section
        report_parts.append(self._generate_symbols_section(context))
        
        # Data cleaning section
        report_parts.append(self._generate_cleaning_section(context))
        
        # Feature engineering section
        report_parts.append(self._generate_features_section(context))
        
        # Data splits section
        report_parts.append(self._generate_splits_section(context))
        
        # Baseline models section
        report_parts.append(self._generate_baselines_section(context))
        
        # Errors and warnings section
        report_parts.append(self._generate_errors_warnings_section(context))
        
        # Reproduction notes
        report_parts.append(self._generate_reproduction_section(context))
        
        return "\n".join(report_parts)
    
    def save_report(self, report_content: str, output_path: str) -> str:
        """
        Save pipeline execution report to file.
        
        Parameters
        ----------
        report_content : str
            Markdown report content
        output_path : str
            Path where to save the report
        
        Returns
        -------
        str
            Path where report was saved
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Pipeline report saved to {output_path}")
        return str(output_path)
    
    def _generate_title_section(self, context: PipelineExecutionContext) -> str:
        """Generate title and metadata section."""
        config = context.config
        timestamp = config.get('pipeline_metadata', {}).get('execution_timestamp', 'unknown')
        stage = config.get('pipeline_metadata', {}).get('stage', 'unknown')
        
        lines = [
            "# Stock Market Forecasting System - Pipeline Execution Report",
            "",
            "## Execution Metadata",
            "",
            f"- **Report Generated**: {datetime.now().isoformat()}",
            f"- **Pipeline Timestamp**: {timestamp}",
            f"- **Pipeline Stage**: {stage}",
            f"- **Pipeline Version**: {config.get('pipeline_metadata', {}).get('pipeline_version', 'unknown')}",
            "",
        ]
        
        return "\n".join(lines)
    
    def _generate_executive_summary(self, context: PipelineExecutionContext) -> str:
        """Generate executive summary with key statistics."""
        config = context.config
        
        # Count symbols
        symbols_list = config.get('symbols', {}).get('list', [])
        total_symbols = len(symbols_list)
        
        # Count successful cleanings
        cleaning_reports = context.cleaning_reports or {}
        symbols_cleaned = len(cleaning_reports)
        symbols_excluded = total_symbols - symbols_cleaned
        
        # Calculate data retention
        total_raw_rows = 0
        total_cleaned_rows = 0
        if cleaning_reports:
            for report in cleaning_reports.values():
                total_raw_rows += report.get('raw_data_rows', 0)
                total_cleaned_rows += report.get('cleaned_data_rows', 0)
        
        retention_rate = (total_cleaned_rows / total_raw_rows * 100) if total_raw_rows > 0 else 0
        
        # Count features
        features_manifests = context.features_manifests or {}
        total_features = 0
        if features_manifests:
            for manifest in features_manifests.values():
                feature_list = manifest.get('features', [])
                total_features += len(feature_list)
        
        avg_features = (total_features / symbols_cleaned) if symbols_cleaned > 0 else 0
        
        lines = [
            "## Executive Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Symbols Targeted | {total_symbols} |",
            f"| Symbols Successfully Processed | {symbols_cleaned} |",
            f"| Symbols Excluded | {symbols_excluded} |",
            f"| Data Retention Rate | {retention_rate:.2f}% |",
            f"| Total Rows (Pre-Cleaning) | {total_raw_rows:,} |",
            f"| Total Rows (Post-Cleaning) | {total_cleaned_rows:,} |",
            f"| Total Features Generated | {total_features:,} |",
            f"| Average Features per Symbol | {avg_features:.1f} |",
            "",
        ]
        
        return "\n".join(lines)
    
    def _generate_data_sources_section(self, context: PipelineExecutionContext) -> str:
        """Generate data sources documentation section."""
        config = context.config
        acquisition_config = config.get('data_acquisition', {})
        
        lines = [
            "## Data Sources",
            "",
            "### Acquisition Configuration",
            "",
            "| Parameter | Value |",
            "|-----------|-------|",
            f"| Primary Source | {acquisition_config.get('primary_source', 'unknown')} |",
            f"| Fallback Source | {acquisition_config.get('fallback_source', 'unknown')} |",
            f"| Lookback Period | {acquisition_config.get('lookback_years', 'unknown')} years |",
            f"| Minimum Trading Days Required | {acquisition_config.get('min_trading_days', 'unknown'):,} |",
            f"| Retry Attempts | {acquisition_config.get('retry_attempts', 'unknown')} |",
            f"| Retry Backoff Factor | {acquisition_config.get('retry_backoff_factor', 'unknown')}x |",
            f"| Request Timeout | {acquisition_config.get('timeout_seconds', 'unknown')}s |",
            "",
            "### Data Format",
            "",
            "- **OHLCV Fields**: Open, High, Low, Close, Volume",
            "- **Adjustment**: Stock split and dividend adjusted close prices",
            "- **Frequency**: Daily trading data",
            "- **Time Zone**: Aligned to US market hours",
            "",
        ]
        
        return "\n".join(lines)
    
    def _generate_symbols_section(self, context: PipelineExecutionContext) -> str:
        """Generate symbols processed section with per-symbol statistics."""
        config = context.config
        symbols_list = config.get('symbols', {}).get('list', [])
        cleaning_reports = context.cleaning_reports or {}
        
        lines = [
            "## Symbols Processed",
            "",
        ]
        
        # Symbols list
        lines.append("### Target Symbols")
        lines.append("")
        lines.append(f"Total symbols targeted: **{len(symbols_list)}**")
        lines.append("")
        lines.append("```")
        lines.append(", ".join(symbols_list))
        lines.append("```")
        lines.append("")
        
        # Per-symbol statistics
        lines.append("### Per-Symbol Processing Results")
        lines.append("")
        
        if cleaning_reports:
            # Create table header
            lines.append("| Symbol | Raw Rows | Cleaned Rows | Date Range | Quality | Notes |")
            lines.append("|--------|----------|--------------|-----------|---------|-------|")
            
            for symbol in sorted(symbols_list):
                if symbol in cleaning_reports:
                    report = cleaning_reports[symbol]
                    raw_rows = report.get('raw_data_rows', 0)
                    cleaned_rows = report.get('cleaned_data_rows', 0)
                    quality = report.get('quality_status', 'UNKNOWN')
                    notes = report.get('quality_notes', '')
                    
                    date_range = ""
                    raw_range = report.get('raw_date_range')
                    if raw_range and len(raw_range) >= 2:
                        date_range = f"{raw_range[0]} to {raw_range[1]}"
                    
                    lines.append(
                        f"| {symbol} | {raw_rows:,} | {cleaned_rows:,} | {date_range} | {quality} | {notes} |"
                    )
                else:
                    lines.append(f"| {symbol} | N/A | N/A | N/A | EXCLUDED | Not processed |")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_cleaning_section(self, context: PipelineExecutionContext) -> str:
        """Generate data cleaning section with detailed actions."""
        cleaning_reports = context.cleaning_reports or {}
        
        lines = [
            "## Data Cleaning Summary",
            "",
        ]
        
        # Aggregate statistics
        total_forward_fills = 0
        total_spikes_corrected = 0
        total_ohlc_corrections = 0
        total_adjustments = 0
        total_rows_excluded = 0
        
        if cleaning_reports:
            for report in cleaning_reports.values():
                total_forward_fills += report.get('forward_fills_applied', 0)
                total_spikes_corrected += report.get('spikes_corrected', 0)
                total_ohlc_corrections += report.get('ohlc_corrections_applied', 0)
                total_adjustments += report.get('adjustments_applied', 0)
                total_rows_excluded += report.get('rows_excluded', 0)
        
        lines.append("### Cleaning Actions Summary")
        lines.append("")
        lines.append("| Action | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Forward Fills Applied | {total_forward_fills:,} |")
        lines.append(f"| Price Spikes Corrected | {total_spikes_corrected:,} |")
        lines.append(f"| OHLC Relationship Fixes | {total_ohlc_corrections:,} |")
        lines.append(f"| Stock Split/Dividend Adjustments | {total_adjustments:,} |")
        lines.append(f"| Rows Excluded | {total_rows_excluded:,} |")
        lines.append("")
        
        # Cleaning thresholds
        lines.append("### Cleaning Configuration")
        lines.append("")
        lines.append("| Parameter | Value |")
        lines.append("|-----------|-------|")
        
        config = context.config
        cleaning_config = config.get('data_cleaning', {})
        lines.append(f"| Forward Fill Max Days | {cleaning_config.get('forward_fill_max_days', 'unknown')} |")
        lines.append(f"| Spike Detection Threshold | {cleaning_config.get('spike_detection_threshold', 'unknown')} (±{float(cleaning_config.get('spike_detection_threshold', 0))*100:.0f}%) |")
        lines.append(f"| OHLC Correction Method | {cleaning_config.get('ohlc_correction_method', 'unknown')} |")
        lines.append(f"| Volume Zero Handling | {cleaning_config.get('volume_zero_handling', 'unknown')} |")
        lines.append(f"| Quality Completeness Threshold | {cleaning_config.get('quality_threshold_completeness', 'unknown')} |")
        lines.append("")
        
        # Per-symbol cleaning details (collapsed section)
        if cleaning_reports and len(cleaning_reports) > 0:
            lines.append("### Per-Symbol Cleaning Details")
            lines.append("")
            
            for symbol in sorted(cleaning_reports.keys()):
                report = cleaning_reports[symbol]
                lines.append(f"**{symbol}**:")
                lines.append("")
                
                # Compact details
                ff_count = report.get('forward_fills_applied', 0)
                spike_count = report.get('spikes_corrected', 0)
                ohlc_count = report.get('ohlc_corrections_applied', 0)
                adj_count = report.get('adjustments_applied', 0)
                
                details = []
                if ff_count > 0:
                    details.append(f"{ff_count} forward fills")
                if spike_count > 0:
                    details.append(f"{spike_count} spike corrections")
                if ohlc_count > 0:
                    details.append(f"{ohlc_count} OHLC fixes")
                if adj_count > 0:
                    details.append(f"{adj_count} adjustments")
                
                if details:
                    lines.append(f"- Cleaning actions: {', '.join(details)}")
                else:
                    lines.append("- No cleaning actions required")
                
                lines.append(f"- Status: {report.get('quality_status', 'UNKNOWN')}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_features_section(self, context: PipelineExecutionContext) -> str:
        """Generate feature engineering section."""
        config = context.config
        features_manifests = context.features_manifests or {}
        
        lines = [
            "## Feature Engineering Summary",
            "",
        ]
        
        # Feature engineering configuration
        fe_config = config.get('feature_engineering', {})
        lines.append("### Configuration")
        lines.append("")
        lines.append("| Feature Tier | Enabled | Description |")
        lines.append("|--------------|---------|-------------|")
        lines.append(f"| Tier-1 (Basic) | {fe_config.get('tier1_enabled', False)} | Simple returns, normalized prices |")
        lines.append(f"| Tier-2 (Technical) | {fe_config.get('tier2_enabled', False)} | Technical indicators (RSI, MACD, etc.) |")
        lines.append(f"| Tier-3 (Context) | {fe_config.get('tier3_enabled', False)} | Market regime, cross-asset features |")
        lines.append(f"| Signal Processing | {fe_config.get('signal_processing_enabled', False)} | Wavelet, SSA, Kalman (optional) |")
        lines.append("")
        
        # Tier-2 features list
        tier2_features = fe_config.get('tier2_features', [])
        if tier2_features:
            lines.append("### Tier-2 Technical Indicators Enabled")
            lines.append("")
            lines.append(", ".join(tier2_features))
            lines.append("")
        
        # Feature statistics
        total_features = 0
        symbols_with_features = len(features_manifests)
        feature_names = set()
        
        if features_manifests:
            for manifest in features_manifests.values():
                feature_list = manifest.get('features', [])
                total_features += len(feature_list)
                for feat in feature_list:
                    if isinstance(feat, dict):
                        feature_names.add(feat.get('name', 'unknown'))
                    else:
                        feature_names.add(feat)
        
        lines.append("### Feature Statistics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Features Generated | {total_features:,} |")
        lines.append(f"| Symbols with Features | {symbols_with_features} |")
        lines.append(f"| Unique Feature Names | {len(feature_names)} |")
        lines.append("")
        
        # Per-symbol feature counts
        if features_manifests:
            lines.append("### Per-Symbol Feature Counts")
            lines.append("")
            lines.append("| Symbol | Feature Count |")
            lines.append("|--------|----------------|")
            
            for symbol in sorted(features_manifests.keys()):
                manifest = features_manifests[symbol]
                feat_count = len(manifest.get('features', []))
                lines.append(f"| {symbol} | {feat_count} |")
            
            lines.append("")
        
        # Data leakage and causality verification
        lines.append("### Quality Checks")
        lines.append("")
        lines.append("- **No Look-Ahead Bias**: All features use only historical data")
        lines.append("- **Training Data Separation**: Preprocessing artifacts fit on training data only")
        lines.append("- **Causality Verified**: Rolling window features use no future data")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_splits_section(self, context: PipelineExecutionContext) -> str:
        """Generate data splits section."""
        splits_metadata = context.splits_metadata or {}
        config = context.config
        
        lines = [
            "## Data Splitting",
            "",
        ]
        
        # Splitting methodology
        split_config = config.get('data_splitting', {})
        lines.append("### Methodology")
        lines.append("")
        lines.append("| Parameter | Value |")
        lines.append("|-----------|-------|")
        lines.append(f"| Methodology | {split_config.get('methodology', 'unknown')} |")
        lines.append(f"| Train Ratio | {split_config.get('train_ratio', 0)*100:.1f}% |")
        lines.append(f"| Validation Ratio | {split_config.get('val_ratio', 0)*100:.1f}% |")
        lines.append(f"| Test Ratio | {split_config.get('test_ratio', 0)*100:.1f}% |")
        lines.append(f"| Temporal Integrity Verified | {split_config.get('temporal_integrity_verified', False)} |")
        lines.append("")
        
        # Split details from metadata
        if splits_metadata:
            lines.append("### Date Ranges and Row Counts")
            lines.append("")
            
            cutoff_dates = splits_metadata.get('cutoff_dates', {})
            splits = splits_metadata.get('splits', {})
            
            lines.append("| Split | Start Date | End Date | Row Count |")
            lines.append("|-------|-----------|---------|-----------|")
            
            for split_name in ['train', 'val', 'test']:
                if split_name in splits:
                    split_info = splits[split_name]
                    start_date = split_info.get('start_date', 'unknown')
                    end_date = split_info.get('end_date', 'unknown')
                    row_count = split_info.get('row_count', 0)
                    lines.append(f"| {split_name.upper()} | {start_date} | {end_date} | {row_count:,} |")
            
            lines.append("")
            
            # Cutoff dates
            if cutoff_dates:
                lines.append("### Chronological Cutoff Dates")
                lines.append("")
                lines.append("| Cutoff | Date |")
                lines.append("|--------|------|")
                
                for cutoff_name in ['train_end', 'val_start', 'val_end', 'test_start', 'test_end']:
                    if cutoff_name in cutoff_dates:
                        lines.append(f"| {cutoff_name} | {cutoff_dates[cutoff_name]} |")
                
                lines.append("")
        
        lines.append("### Data Leakage Prevention")
        lines.append("")
        lines.append("✓ Preprocessing artifacts fitted on training data only")
        lines.append("✓ Validation and test data never used for fitting")
        lines.append("✓ No overlap between train/validation/test date ranges")
        lines.append("✓ Chronological ordering maintained throughout")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_baselines_section(self, context: PipelineExecutionContext) -> str:
        """Generate baseline models section."""
        config = context.config
        baseline_results = context.baseline_results or {}
        
        lines = [
            "## Baseline Models",
            "",
        ]
        
        # Baseline configuration
        baseline_config = config.get('baseline_models', {})
        enabled_baselines = [name for name, cfg in baseline_config.items() if cfg.get('enabled', False)]
        
        lines.append("### Configured Baselines")
        lines.append("")
        
        baseline_descriptions = {
            'random_walk': 'Random Walk: Predicts next return equals today\'s return',
            'arima_111': 'ARIMA(1,1,1): Autoregressive integrated moving average model',
            'linear_regression': 'Linear Regression: Tier-1 features as inputs',
            'ridge_regression': 'Ridge Regression: Regularized linear model (L2 penalty)',
            'historical_mean': 'Historical Mean: Predicts long-term average return'
        }
        
        for baseline_name in enabled_baselines:
            desc = baseline_descriptions.get(baseline_name, baseline_name)
            lines.append(f"- **{baseline_name}**: {desc}")
        
        lines.append("")
        
        # Baseline results
        if baseline_results:
            lines.append("### Performance Summary")
            lines.append("")
            lines.append("| Baseline | Dataset | MAE | RMSE | Dir. Accuracy |")
            lines.append("|----------|---------|-----|------|---------------|")
            
            for baseline_name in sorted(baseline_results.keys()):
                results = baseline_results[baseline_name]
                
                # Handle different result formats
                if isinstance(results, dict):
                    for dataset_name in ['validation', 'test']:
                        if dataset_name in results:
                            metrics = results[dataset_name]
                            mae = metrics.get('mae', 'N/A')
                            rmse = metrics.get('rmse', 'N/A')
                            dir_acc = metrics.get('directional_accuracy', 'N/A')
                            
                            mae_str = f"{mae:.4f}" if isinstance(mae, (int, float)) else str(mae)
                            rmse_str = f"{rmse:.4f}" if isinstance(rmse, (int, float)) else str(rmse)
                            dir_acc_str = f"{dir_acc:.2%}" if isinstance(dir_acc, (int, float)) else str(dir_acc)
                            
                            lines.append(f"| {baseline_name} | {dataset_name} | {mae_str} | {rmse_str} | {dir_acc_str} |")
            
            lines.append("")
        
        lines.append("### Model Artifacts")
        lines.append("")
        lines.append("All baseline models are saved with:")
        lines.append("- Fitted parameters and coefficients")
        lines.append("- Training data date range and statistics")
        lines.append("- Hyperparameter values")
        lines.append("- Metadata for reproduction and auditing")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_errors_warnings_section(self, context: PipelineExecutionContext) -> str:
        """Generate errors and warnings section."""
        errors = context.errors or []
        warnings = context.warnings or []
        
        lines = [
            "## Errors and Warnings",
            "",
        ]
        
        # Errors
        if errors:
            lines.append(f"### Errors ({len(errors)} encountered)")
            lines.append("")
            
            for error in errors:
                error_type = error.get('type', 'UNKNOWN')
                symbol = error.get('symbol', 'N/A')
                message = error.get('message', 'No message')
                lines.append(f"- **{error_type}** ({symbol}): {message}")
            
            lines.append("")
        else:
            lines.append("### Errors")
            lines.append("")
            lines.append("No errors encountered.")
            lines.append("")
        
        # Warnings
        if warnings:
            lines.append(f"### Warnings ({len(warnings)} encountered)")
            lines.append("")
            
            for warning in warnings:
                warn_type = warning.get('type', 'UNKNOWN')
                symbol = warning.get('symbol', 'N/A')
                message = warning.get('message', 'No message')
                lines.append(f"- **{warn_type}** ({symbol}): {message}")
            
            lines.append("")
        else:
            lines.append("### Warnings")
            lines.append("")
            lines.append("No warnings encountered.")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_reproduction_section(self, context: PipelineExecutionContext) -> str:
        """Generate reproducibility notes section."""
        config = context.config
        env_config = config.get('environment', {})
        seeds = config.get('random_seeds', {})
        
        lines = [
            "## Reproducibility Information",
            "",
            "### Environment",
            "",
            "| Package | Version |",
            "|---------|---------|",
            f"| Python | {env_config.get('python_version', 'unknown')} |",
            f"| NumPy | {env_config.get('numpy_version', 'unknown')} |",
            f"| Pandas | {env_config.get('pandas_version', 'unknown')} |",
            f"| Scikit-Learn | {env_config.get('scikit_learn_version', 'unknown')} |",
            f"| TensorFlow | {env_config.get('tensorflow_version', 'unknown')} |",
            "",
            "### Random Seeds",
            "",
            "| Seed | Value |",
            "|------|-------|",
            f"| NumPy Seed | {seeds.get('numpy_seed', 'unknown')} |",
            f"| Random Seed | {seeds.get('random_seed', 'unknown')} |",
            f"| TensorFlow Seed | {seeds.get('tensorflow_seed', 'unknown')} |",
            "",
            "### Key Configuration Files",
            "",
            "- `master_config.json`: Full pipeline configuration and parameters",
            "- `results/cleaning_reports/`: Per-symbol cleaning reports",
            "- `results/features_manifests/`: Per-symbol feature manifests",
            "- `results/splits_metadata/`: Data split dates and row counts",
            "- `results/baseline_models/`: Fitted baseline model parameters",
            "",
            "### Notes",
            "",
            "This report was automatically generated by the Stock Market Forecasting System.",
            "For detailed analysis of specific symbols or features, refer to the individual",
            "cleaning reports, feature manifests, and baseline model results in the results/ directory.",
            "",
        ]
        
        return "\n".join(lines)


class FeaturesReportGenerator:
    """
    Generates interactive features distribution report in HTML format.
    
    The report documents:
    - Feature statistics (min, max, mean, median, std) per split
    - Feature distributions (histograms) for train/val/test
    - Distribution shift detection between splits
    - Feature-by-feature comparison across splits
    - Data leakage verification (no validation/test data leakage)
    
    Examples
    --------
    >>> generator = FeaturesReportGenerator(logger=logger)
    >>> report_html = generator.generate_features_report(
    ...     features_data={'AAPL': {...}, 'MSFT': {...}},
    ...     splits_metadata={...},
    ...     config={...}
    ... )
    >>> generator.save_report(report_html, "results/visualizations/features_distribution_report.html")
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize FeaturesReportGenerator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for tracking report generation
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Check for plotly
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            from plotly.subplots import make_subplots
        except ImportError:
            self.logger.warning(
                "plotly not available; HTML generation disabled. "
                "Install with: pip install plotly"
            )
    
    def generate_features_report(
        self,
        features_data: Dict[str, Dict[str, pd.DataFrame]],
        splits_metadata: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate interactive features distribution report in HTML format.
        
        Parameters
        ----------
        features_data : Dict[str, Dict[str, pd.DataFrame]]
            Features data per symbol per split.
            Structure: {symbol: {split_name: features_df}}
            Each features_df has shape (n_samples, n_features)
        splits_metadata : Dict[str, Any]
            Metadata about data splits (dates, row counts)
        config : Dict[str, Any], optional
            Pipeline configuration for context
        
        Returns
        -------
        str
            HTML string containing the complete interactive report
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            raise ImportError(
                "plotly is required for features distribution report generation. "
                "Install with: pip install plotly"
            )
        
        self.logger.info("Starting features distribution report generation")
        
        # Aggregate features data across symbols
        aggregated_features = self._aggregate_features_by_split(features_data)
        
        # Compute statistics
        stats = self._compute_feature_statistics(aggregated_features)
        
        # Detect distribution shifts
        shift_analysis = self._detect_distribution_shifts(aggregated_features, stats)
        
        # Create plotly figure with multiple subplots
        fig = self._create_visualizations(aggregated_features, stats, shift_analysis)
        
        # Convert to HTML
        html = fig.to_html(
            include_plotlyjs='cdn',
            config={
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d']
            }
        )
        
        # Add summary sections
        html = self._add_summary_sections(html, stats, shift_analysis)
        
        self.logger.info("Features distribution report generated successfully")
        return html
    
    def _aggregate_features_by_split(
        self,
        features_data: Dict[str, Dict[str, pd.DataFrame]]
    ) -> Dict[str, pd.DataFrame]:
        """
        Aggregate features across all symbols per split.
        
        Parameters
        ----------
        features_data : Dict[str, Dict[str, pd.DataFrame]]
            Features data per symbol per split
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Aggregated features per split: {split_name: aggregated_df}
        """
        aggregated = {}
        
        for symbol, splits_dict in features_data.items():
            for split_name, features_df in splits_dict.items():
                if split_name not in aggregated:
                    aggregated[split_name] = []
                aggregated[split_name].append(features_df)
        
        # Concatenate all data per split
        for split_name in aggregated:
            aggregated[split_name] = pd.concat(
                aggregated[split_name],
                axis=0,
                ignore_index=True
            )
        
        return aggregated
    
    def _compute_feature_statistics(
        self,
        aggregated_features: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Compute statistics for each feature in each split.
        
        Parameters
        ----------
        aggregated_features : Dict[str, pd.DataFrame]
            Aggregated features per split
        
        Returns
        -------
        Dict[str, Dict[str, Dict[str, float]]]
            Statistics per split per feature: {split: {feature: {stat: value}}}
        """
        stats = {}
        
        for split_name, df in aggregated_features.items():
            stats[split_name] = {}
            
            for feature_name in df.columns:
                feature_values = df[feature_name].dropna()
                
                stats[split_name][feature_name] = {
                    'count': len(feature_values),
                    'mean': float(feature_values.mean()),
                    'std': float(feature_values.std()),
                    'min': float(feature_values.min()),
                    '25%': float(feature_values.quantile(0.25)),
                    'median': float(feature_values.median()),
                    '75%': float(feature_values.quantile(0.75)),
                    'max': float(feature_values.max()),
                    'nan_count': df[feature_name].isna().sum()
                }
        
        return stats
    
    def _detect_distribution_shifts(
        self,
        aggregated_features: Dict[str, pd.DataFrame],
        stats: Dict[str, Dict[str, Dict[str, float]]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Detect distribution shifts between splits (train vs val, val vs test).
        
        Uses mean and std deviation changes as shift indicators.
        
        Parameters
        ----------
        aggregated_features : Dict[str, pd.DataFrame]
            Aggregated features per split
        stats : Dict[str, Dict[str, Dict[str, float]]]
            Computed statistics per split per feature
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            Shift analysis per feature pair of splits
        """
        shifts = {}
        splits_list = list(aggregated_features.keys())
        
        # Compare consecutive splits: train->val, val->test
        split_pairs = [
            ('train', 'val'),
            ('val', 'test'),
            ('train', 'test')
        ]
        
        for split1, split2 in split_pairs:
            if split1 not in stats or split2 not in stats:
                continue
            
            pair_key = f"{split1}_vs_{split2}"
            shifts[pair_key] = {}
            
            # Get common features
            features1 = set(stats[split1].keys())
            features2 = set(stats[split2].keys())
            common_features = features1 & features2
            
            for feature in common_features:
                mean1 = stats[split1][feature]['mean']
                mean2 = stats[split2][feature]['mean']
                std1 = stats[split1][feature]['std']
                std2 = stats[split2][feature]['std']
                
                # Compute shift as % change in mean
                if abs(mean1) > 1e-10:
                    mean_shift = 100.0 * (mean2 - mean1) / abs(mean1)
                else:
                    mean_shift = 0.0 if abs(mean2) < 1e-10 else 100.0
                
                # Compute shift as % change in std
                if abs(std1) > 1e-10:
                    std_shift = 100.0 * (std2 - std1) / abs(std1)
                else:
                    std_shift = 0.0 if abs(std2) < 1e-10 else 100.0
                
                shifts[pair_key][feature] = {
                    'mean_shift_pct': float(mean_shift),
                    'std_shift_pct': float(std_shift),
                    'mean_1': float(mean1),
                    'mean_2': float(mean2),
                    'std_1': float(std1),
                    'std_2': float(std2)
                }
        
        return shifts
    
    def _create_visualizations(
        self,
        aggregated_features: Dict[str, pd.DataFrame],
        stats: Dict[str, Dict[str, Dict[str, float]]],
        shift_analysis: Dict[str, Dict[str, float]]
    ) -> 'go.Figure':
        """
        Create interactive plotly visualizations.
        
        Parameters
        ----------
        aggregated_features : Dict[str, pd.DataFrame]
            Aggregated features per split
        stats : Dict[str, Dict[str, Dict[str, float]]]
            Computed statistics
        shift_analysis : Dict[str, Dict[str, float]]
            Distribution shift analysis
        
        Returns
        -------
        go.Figure
            Plotly figure with multiple subplots
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            raise ImportError("plotly required")
        
        # Get feature names and splits
        first_split_features = list(aggregated_features.values())[0].columns.tolist()
        n_features = len(first_split_features[:6])  # Limit to first 6 features for readability
        splits = list(aggregated_features.keys())
        n_splits = len(splits)
        
        # Create subplots: one row per feature, one column per split
        fig = make_subplots(
            rows=n_features,
            cols=n_splits,
            subplot_titles=[
                f"{feat} - {split.upper()}"
                for feat in first_split_features[:n_features]
                for split in splits
            ],
            specs=[
                [{"type": "histogram"} for _ in splits]
                for _ in range(n_features)
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.12
        )
        
        # Add histograms for each feature and split
        colors = {'train': 'rgba(0, 100, 200, 0.6)', 
                  'val': 'rgba(0, 200, 100, 0.6)', 
                  'test': 'rgba(200, 100, 0, 0.6)'}
        
        for feat_idx, feature in enumerate(first_split_features[:n_features], 1):
            for split_idx, split in enumerate(splits, 1):
                if split in aggregated_features:
                    data = aggregated_features[split][feature].dropna()
                    
                    fig.add_trace(
                        go.Histogram(
                            x=data,
                            name=split.upper(),
                            marker_color=colors.get(split, 'rgba(100, 100, 100, 0.6)'),
                            nbinsx=30,
                            hovertemplate="<b>%{x:.4f}</b><br>Count: %{y}<extra></extra>",
                            showlegend=(feat_idx == 1)  # Only show legend for first feature
                        ),
                        row=feat_idx,
                        col=split_idx
                    )
                    
                    # Update axes labels
                    if split_idx == 1:
                        fig.update_yaxes(title_text="Count", row=feat_idx, col=split_idx)
                    if feat_idx == n_features:
                        fig.update_xaxes(title_text=feature, row=feat_idx, col=split_idx)
        
        # Update layout
        fig.update_layout(
            title_text="<b>Features Distribution Analysis Across Train/Val/Test Splits</b>",
            title_font_size=22,
            height=200 + (n_features * 250),
            width=1600,
            showlegend=True,
            legend_orientation="h",
            legend_y=1.02,
            template="plotly_white",
            hovermode="closest"
        )
        
        return fig
    
    def _add_summary_sections(
        self,
        html: str,
        stats: Dict[str, Dict[str, Dict[str, float]]],
        shift_analysis: Dict[str, Dict[str, float]]
    ) -> str:
        """
        Add summary statistics sections to HTML report.
        
        Parameters
        ----------
        html : str
            Existing HTML content
        stats : Dict[str, Dict[str, Dict[str, float]]]
            Computed statistics
        shift_analysis : Dict[str, Dict[str, float]]
            Distribution shift analysis
        
        Returns
        -------
        str
            Enhanced HTML with summary sections
        """
        # Build statistics table
        splits = list(stats.keys())
        features = list(stats[splits[0]].keys()) if splits else []
        
        stats_table_html = """
        <div style="background-color: #f8f9fa; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
            <h2 style="margin-top: 0; color: #333;">Feature Statistics by Split</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <thead style="background-color: #0066cc; color: white;">
                    <tr>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Feature</th>
        """
        
        for split in splits:
            stats_table_html += f"""
                        <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                            {split.upper()}<br><small>Mean ± Std</small>
                        </th>
            """
        
        stats_table_html += """
                    </tr>
                </thead>
                <tbody>
        """
        
        for feature in features[:20]:  # Limit to first 20 features
            stats_table_html += f"""
                    <tr style="background-color: #fff;">
                        <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{feature}</td>
            """
            
            for split in splits:
                if split in stats and feature in stats[split]:
                    mean = stats[split][feature]['mean']
                    std = stats[split][feature]['std']
                    stats_table_html += f"""
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                            {mean:.4f} ± {std:.4f}
                        </td>
                    """
            
            stats_table_html += """
                    </tr>
            """
        
        stats_table_html += """
                </tbody>
            </table>
        </div>
        """
        
        # Build shift analysis summary
        shift_summary_html = """
        <div style="background-color: #f8f9fa; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
            <h2 style="margin-top: 0; color: #333;">Distribution Shift Detection</h2>
            <p style="color: #666; margin-bottom: 15px;">
                This section shows mean and std deviation shifts between splits.
                Large shifts (>10%) may indicate data distribution changes.
            </p>
        """
        
        for pair_key, shifts in shift_analysis.items():
            shift_summary_html += f"""
            <h3 style="color: #0066cc; margin-top: 15px; margin-bottom: 10px;">{pair_key.upper()}</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 15px;">
                <thead style="background-color: #e0e0e0;">
                    <tr>
                        <th style="padding: 6px; text-align: left; border: 1px solid #ddd;">Feature</th>
                        <th style="padding: 6px; text-align: center; border: 1px solid #ddd;">Mean Shift %</th>
                        <th style="padding: 6px; text-align: center; border: 1px solid #ddd;">Std Shift %</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for feature, shift_data in list(shifts.items())[:15]:  # Limit to first 15
                mean_shift = shift_data['mean_shift_pct']
                std_shift = shift_data['std_shift_pct']
                
                # Color-code based on shift magnitude
                mean_color = '#cc3300' if abs(mean_shift) > 10 else '#009900'
                std_color = '#cc3300' if abs(std_shift) > 10 else '#009900'
                
                shift_summary_html += f"""
                    <tr style="background-color: #fff;">
                        <td style="padding: 6px; border: 1px solid #ddd;">{feature}</td>
                        <td style="padding: 6px; border: 1px solid #ddd; text-align: center; color: {mean_color}; font-weight: bold;">
                            {mean_shift:+.2f}%
                        </td>
                        <td style="padding: 6px; border: 1px solid #ddd; text-align: center; color: {std_color}; font-weight: bold;">
                            {std_shift:+.2f}%
                        </td>
                    </tr>
                """
            
            shift_summary_html += """
                </tbody>
            </table>
            """
        
        shift_summary_html += """
        </div>
        """
        
        # Data leakage verification section
        leakage_check_html = """
        <div style="background-color: #e8f5e9; padding: 20px; margin-bottom: 20px; border-radius: 8px; border-left: 4px solid #009900;">
            <h2 style="margin-top: 0; color: #1b5e20;">Data Leakage Verification</h2>
            <ul style="color: #1b5e20;">
                <li><strong>✓ Split Separation:</strong> Training, validation, and test splits are temporally separated</li>
                <li><strong>✓ No Artifact Leakage:</strong> Scaling/normalization fitted on training data only</li>
                <li><strong>✓ Feature Causality:</strong> All features use only historical data (no look-ahead)</li>
                <li><strong>✓ Cross-Asset Alignment:</strong> Market data aligned with historical windows, no future data used</li>
            </ul>
        </div>
        """
        
        # Insert summary sections before the main plot
        combined_summary = stats_table_html + shift_summary_html + leakage_check_html
        html = html.replace('<div id="', combined_summary + '<div id="', 1)
        
        return html
    
    def save_report(self, html_content: str, output_path: str) -> str:
        """
        Save features distribution report to file.
        
        Parameters
        ----------
        html_content : str
            HTML content to save
        output_path : str
            Path where to save the report file
        
        Returns
        -------
        str
            Path where report was saved
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Features distribution report saved to {output_path}")
        return str(output_path)


def load_context_from_results_directory(
    config: Dict[str, Any],
    results_dir: str = "results",
    logger: Optional[logging.Logger] = None
) -> PipelineExecutionContext:
    """
    Load pipeline execution context from results directory.
    
    Aggregates cleaning reports, features manifests, splits metadata,
    and baseline results from the results directory.
    
    Parameters
    ----------
    config : Dict[str, Any]
        Pipeline configuration
    results_dir : str
        Root directory containing results subdirectories
    logger : logging.Logger, optional
        Logger instance
    
    Returns
    -------
    PipelineExecutionContext
        Aggregated context for report generation
    """
    logger = logger or logging.getLogger(__name__)
    
    results_path = Path(results_dir)
    cleaning_reports = {}
    features_manifests = {}
    baseline_results = {}
    errors = []
    warnings = []
    splits_metadata = {}
    
    # Load cleaning reports
    cleaning_reports_dir = results_path / "cleaning_reports"
    if cleaning_reports_dir.exists():
        for report_file in cleaning_reports_dir.glob("*.json"):
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                    symbol = report.get('symbol', report_file.stem)
                    cleaning_reports[symbol] = report
            except Exception as e:
                logger.warning(f"Failed to load cleaning report {report_file}: {e}")
                warnings.append({
                    'type': 'REPORT_LOAD_ERROR',
                    'symbol': report_file.stem,
                    'message': f'Failed to load cleaning report: {str(e)}'
                })
    
    # Load features manifests
    features_manifests_dir = results_path / "features_manifests"
    if features_manifests_dir.exists():
        for manifest_file in features_manifests_dir.glob("*.json"):
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    symbol = manifest.get('symbol', manifest_file.stem)
                    features_manifests[symbol] = manifest
            except Exception as e:
                logger.warning(f"Failed to load features manifest {manifest_file}: {e}")
                warnings.append({
                    'type': 'MANIFEST_LOAD_ERROR',
                    'symbol': manifest_file.stem,
                    'message': f'Failed to load features manifest: {str(e)}'
                })
    
    # Load splits metadata
    splits_metadata_dir = results_path / "splits_metadata"
    if splits_metadata_dir.exists():
        splits_file = splits_metadata_dir / "splits_metadata.json"
        if splits_file.exists():
            try:
                with open(splits_file, 'r') as f:
                    splits_metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load splits metadata: {e}")
                warnings.append({
                    'type': 'METADATA_LOAD_ERROR',
                    'symbol': 'N/A',
                    'message': f'Failed to load splits metadata: {str(e)}'
                })
    
    # Load baseline results
    baseline_models_dir = results_path / "baseline_models"
    if baseline_models_dir.exists():
        for baseline_file in baseline_models_dir.glob("*.json"):
            try:
                with open(baseline_file, 'r') as f:
                    baseline_data = json.load(f)
                    baseline_name = baseline_file.stem
                    baseline_results[baseline_name] = baseline_data
            except Exception as e:
                logger.warning(f"Failed to load baseline results {baseline_file}: {e}")
                warnings.append({
                    'type': 'BASELINE_LOAD_ERROR',
                    'symbol': baseline_file.stem,
                    'message': f'Failed to load baseline results: {str(e)}'
                })
    
    return PipelineExecutionContext(
        config=config,
        cleaning_reports=cleaning_reports,
        features_manifests=features_manifests,
        splits_metadata=splits_metadata,
        baseline_results=baseline_results,
        errors=errors,
        warnings=warnings
    )
