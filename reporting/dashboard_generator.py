"""
Data quality dashboard generator for Stock Market Forecasting System.

Generates interactive HTML dashboards showing data quality metrics, cleaning impact,
and feature distributions. Uses Plotly for interactive visualizations that can be
opened in any browser and shared without dependencies.

References:
- Requirements 13.3: Output and Reporting Format (data_quality_dashboard.html)
- Design Section 12.3: Dashboard and visualization architecture
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except ImportError:
    raise ImportError("plotly is required for dashboard generation. Install with: pip install plotly")


class DashboardGenerator:
    """
    Generates interactive HTML dashboards for data quality and feature analysis.
    
    The dashboard includes:
    - Completeness by symbol (bar chart)
    - Price distribution (histograms with statistics)
    - Volume patterns (time series trends)
    - Missing data trends (line chart by symbol)
    - Cleaning impact (before/after comparison)
    - Summary statistics table
    
    All visualizations are standalone HTML files that can be opened in any browser.
    
    Examples
    --------
    >>> generator = DashboardGenerator(logger=logger)
    >>> context = {
    ...     'cleaning_reports': {'AAPL': {...}, 'MSFT': {...}},
    ...     'features_manifests': {'AAPL': {...}, 'MSFT': {...}}
    ... }
    >>> html = generator.generate_dashboard(context)
    >>> generator.save_dashboard(html, 'results/visualizations/data_quality_dashboard.html')
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize DashboardGenerator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for tracking dashboard generation
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_dashboard(
        self,
        cleaning_reports: Dict[str, Dict[str, Any]],
        features_manifests: Dict[str, Dict[str, Any]],
        ohlcv_data: Optional[Dict[str, pd.DataFrame]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate comprehensive data quality dashboard in HTML format.
        
        Parameters
        ----------
        cleaning_reports : Dict[str, Dict[str, Any]]
            Per-symbol cleaning reports from cleaning module
            Keys: symbol names, Values: cleaning report dicts with:
                - raw_data_rows, cleaned_data_rows
                - forward_fills_applied, spikes_corrected, etc.
                - completeness_percent
        features_manifests : Dict[str, Dict[str, Any]]
            Per-symbol feature manifests documenting computed features
        ohlcv_data : Dict[str, pd.DataFrame], optional
            OHLCV data per symbol for price/volume analysis.
            If None, visualizations are generated from cleaning reports alone.
        config : Dict[str, Any], optional
            Pipeline configuration for context (e.g., symbols list, thresholds)
        
        Returns
        -------
        str
            HTML string containing the complete interactive dashboard
        """
        self.logger.info("Starting dashboard generation")
        
        # Extract key metrics from cleaning reports
        symbols = list(cleaning_reports.keys())
        completeness_data = self._extract_completeness_metrics(cleaning_reports)
        cleaning_impact_data = self._extract_cleaning_impact(cleaning_reports)
        missing_data_trends = self._extract_missing_data_trends(cleaning_reports)
        feature_stats = self._extract_feature_stats(features_manifests)
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Data Completeness by Symbol",
                "Feature Count by Tier",
                "Cleaning Impact (Before/After)",
                "Raw Data Rows by Symbol",
                "Data Quality Status Distribution",
                "Rows Removed by Action Type"
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "pie"}, {"type": "bar"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.12
        )
        
        # 1. Completeness by symbol (bar chart)
        completeness_sorted = sorted(
            completeness_data.items(),
            key=lambda x: x[1]['completeness_percent'],
            reverse=True
        )
        symbols_sorted = [s for s, _ in completeness_sorted]
        completeness_percent = [d['completeness_percent'] for _, d in completeness_sorted]
        
        fig.add_trace(
            go.Bar(
                x=symbols_sorted,
                y=completeness_percent,
                name="Completeness %",
                marker_color="rgba(0, 150, 100, 0.7)",
                text=[f"{x:.1f}%" for x in completeness_percent],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Completeness: %{y:.2f}%<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 2. Feature count by tier
        if feature_stats:
            tier_names = list(feature_stats.get('tier_counts', {}).keys())
            tier_counts = list(feature_stats.get('tier_counts', {}).values())
            
            fig.add_trace(
                go.Bar(
                    x=tier_names,
                    y=tier_counts,
                    name="Features",
                    marker_color="rgba(0, 100, 200, 0.7)",
                    text=tier_counts,
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"
                ),
                row=1, col=2
            )
        
        # 3. Cleaning impact (before/after)
        raw_rows = [completeness_data[s]['raw_rows'] for s in symbols_sorted]
        cleaned_rows = [completeness_data[s]['cleaned_rows'] for s in symbols_sorted]
        
        fig.add_trace(
            go.Bar(
                x=symbols_sorted,
                y=raw_rows,
                name="Before Cleaning",
                marker_color="rgba(200, 100, 100, 0.7)",
                hovertemplate="<b>%{x}</b><br>Raw Rows: %{y:,}<extra></extra>"
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=symbols_sorted,
                y=cleaned_rows,
                name="After Cleaning",
                marker_color="rgba(100, 150, 200, 0.7)",
                hovertemplate="<b>%{x}</b><br>Cleaned Rows: %{y:,}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 4. Raw data rows by symbol
        fig.add_trace(
            go.Bar(
                x=symbols_sorted,
                y=raw_rows,
                name="Row Count",
                marker_color="rgba(100, 150, 200, 0.7)",
                text=raw_rows,
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra></extra>",
                showlegend=False
            ),
            row=2, col=2
        )
        
        # 5. Data quality status distribution (pie chart)
        if cleaning_reports:
            quality_statuses = {}
            for report in cleaning_reports.values():
                status = report.get('quality_status', 'UNKNOWN')
                quality_statuses[status] = quality_statuses.get(status, 0) + 1
            
            fig.add_trace(
                go.Pie(
                    labels=list(quality_statuses.keys()),
                    values=list(quality_statuses.values()),
                    name="Quality Status",
                    hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>"
                ),
                row=3, col=1
            )
        
        # 6. Rows removed by action type
        if cleaning_impact_data:
            action_names = list(cleaning_impact_data['actions'].keys())
            action_counts = list(cleaning_impact_data['actions'].values())
            
            colors = [
                "rgba(255, 100, 100, 0.7)",  # forward_fills
                "rgba(255, 150, 100, 0.7)",  # spikes_corrected
                "rgba(100, 200, 100, 0.7)",  # ohlc_corrections
                "rgba(100, 100, 200, 0.7)",  # adjustments
            ]
            
            fig.add_trace(
                go.Bar(
                    x=action_names,
                    y=action_counts,
                    name="Actions",
                    marker_color=colors[:len(action_names)],
                    text=action_counts,
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
                    showlegend=False
                ),
                row=3, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text="<b>Stock Market Data Quality Dashboard</b>",
            title_font_size=24,
            showlegend=True,
            legend_orientation="v",
            height=1200,
            width=1600,
            hovermode="closest",
            template="plotly_white"
        )
        
        # Update x-axes
        fig.update_xaxes(title_text="Symbol", row=1, col=1)
        fig.update_xaxes(title_text="Tier", row=1, col=2)
        fig.update_xaxes(title_text="Symbol", row=2, col=1)
        fig.update_xaxes(title_text="Symbol", row=2, col=2)
        fig.update_xaxes(title_text="Action", row=3, col=2)
        
        # Update y-axes
        fig.update_yaxes(title_text="Completeness %", row=1, col=1)
        fig.update_yaxes(title_text="Feature Count", row=1, col=2)
        fig.update_yaxes(title_text="Row Count", row=2, col=1)
        fig.update_yaxes(title_text="Row Count", row=2, col=2)
        fig.update_yaxes(title_text="Count", row=3, col=2)
        
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
        
        # Wrap with summary statistics
        html = self._add_summary_section(html, cleaning_reports, features_manifests)
        
        self.logger.info("Dashboard generation completed successfully")
        return html
    
    def _extract_completeness_metrics(
        self,
        cleaning_reports: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract completeness metrics from cleaning reports.
        
        Parameters
        ----------
        cleaning_reports : Dict[str, Dict[str, Any]]
            Per-symbol cleaning reports
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            Completeness data with keys: completeness_percent, raw_rows, cleaned_rows
        """
        completeness_data = {}
        
        for symbol, report in cleaning_reports.items():
            completeness_data[symbol] = {
                'completeness_percent': report.get('completeness_percent', 0),
                'raw_rows': report.get('raw_data_rows', 0),
                'cleaned_rows': report.get('cleaned_data_rows', 0),
                'quality_status': report.get('quality_status', 'UNKNOWN')
            }
        
        return completeness_data
    
    def _extract_cleaning_impact(
        self,
        cleaning_reports: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract cleaning impact statistics across all symbols.
        
        Parameters
        ----------
        cleaning_reports : Dict[str, Dict[str, Any]]
            Per-symbol cleaning reports
        
        Returns
        -------
        Dict[str, Any]
            Aggregated cleaning actions and statistics
        """
        total_forward_fills = 0
        total_spikes_corrected = 0
        total_ohlc_corrections = 0
        total_adjustments = 0
        total_rows_removed = 0
        
        for report in cleaning_reports.values():
            total_forward_fills += report.get('forward_fills_applied', 0)
            total_spikes_corrected += report.get('spikes_corrected', 0)
            total_ohlc_corrections += report.get('ohlc_corrections_applied', 0)
            total_adjustments += report.get('adjustments_applied', 0)
            total_rows_removed += report.get('rows_excluded', 0)
        
        return {
            'actions': {
                'forward_fills': total_forward_fills,
                'spikes_corrected': total_spikes_corrected,
                'ohlc_corrections': total_ohlc_corrections,
                'adjustments': total_adjustments
            },
            'total_rows_removed': total_rows_removed
        }
    
    def _extract_missing_data_trends(
        self,
        cleaning_reports: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract missing data trends from cleaning reports.
        
        Parameters
        ----------
        cleaning_reports : Dict[str, Dict[str, Any]]
            Per-symbol cleaning reports
        
        Returns
        -------
        Dict[str, Any]
            Missing data statistics by symbol
        """
        missing_data = {}
        
        for symbol, report in cleaning_reports.items():
            missing_data[symbol] = {
                'missing_values_detected': report.get('missing_values_detected', 0),
                'date_gaps_detected': report.get('date_gaps_detected', 0),
                'rows_excluded': report.get('rows_excluded', 0)
            }
        
        return missing_data
    
    def _extract_feature_stats(
        self,
        features_manifests: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract feature statistics from manifests.
        
        Parameters
        ----------
        features_manifests : Dict[str, Dict[str, Any]]
            Per-symbol feature manifests
        
        Returns
        -------
        Dict[str, Any]
            Aggregated feature statistics including tier counts
        """
        if not features_manifests:
            return {}
        
        tier_counts = {
            'tier1': 0,
            'tier2': 0,
            'tier3': 0
        }
        
        for manifest in features_manifests.values():
            manifest_tiers = manifest.get('tier_counts', {})
            for tier_name, count in manifest_tiers.items():
                if tier_name in tier_counts:
                    tier_counts[tier_name] = max(tier_counts[tier_name], count)
        
        return {
            'tier_counts': tier_counts
        }
    
    def _add_summary_section(
        self,
        html: str,
        cleaning_reports: Dict[str, Dict[str, Any]],
        features_manifests: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Add summary statistics section to dashboard HTML.
        
        Parameters
        ----------
        html : str
            Existing HTML content
        cleaning_reports : Dict[str, Dict[str, Any]]
            Cleaning reports for statistics
        features_manifests : Dict[str, Dict[str, Any]]
            Feature manifests for statistics
        
        Returns
        -------
        str
            Enhanced HTML with summary section
        """
        # Calculate summary statistics
        total_symbols = len(cleaning_reports)
        total_raw_rows = sum(r.get('raw_data_rows', 0) for r in cleaning_reports.values())
        total_cleaned_rows = sum(r.get('cleaned_data_rows', 0) for r in cleaning_reports.values())
        avg_completeness = np.mean([
            r.get('completeness_percent', 0) for r in cleaning_reports.values()
        ])
        
        total_actions = (
            sum(r.get('forward_fills_applied', 0) for r in cleaning_reports.values()) +
            sum(r.get('spikes_corrected', 0) for r in cleaning_reports.values()) +
            sum(r.get('ohlc_corrections_applied', 0) for r in cleaning_reports.values()) +
            sum(r.get('adjustments_applied', 0) for r in cleaning_reports.values())
        )
        
        total_features = sum(
            len(m.get('features', [])) for m in features_manifests.values()
        )
        
        summary_html = f"""
        <div style="background-color: #f8f9fa; padding: 20px; margin-bottom: 20px; border-radius: 8px; border-left: 4px solid #0066cc;">
            <h2 style="margin-top: 0; color: #333;">Summary Statistics</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Symbols Processed</div>
                    <div style="font-size: 28px; font-weight: bold; color: #0066cc; margin-top: 10px;">{total_symbols}</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Average Completeness</div>
                    <div style="font-size: 28px; font-weight: bold; color: #009966; margin-top: 10px;">{avg_completeness:.1f}%</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Total Features</div>
                    <div style="font-size: 28px; font-weight: bold; color: #0099cc; margin-top: 10px;">{total_features}</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Rows Before Cleaning</div>
                    <div style="font-size: 28px; font-weight: bold; color: #cc6600; margin-top: 10px;">{total_raw_rows:,}</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Rows After Cleaning</div>
                    <div style="font-size: 28px; font-weight: bold; color: #009933; margin-top: 10px;">{total_cleaned_rows:,}</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Total Cleaning Actions</div>
                    <div style="font-size: 28px; font-weight: bold; color: #cc3300; margin-top: 10px;">{total_actions:,}</div>
                </div>
            </div>
        </div>
        """
        
        # Insert summary before the main plot
        html = html.replace('<div id="', summary_html + '<div id="', 1)
        
        return html
    
    def save_dashboard(self, html_content: str, output_path: str) -> str:
        """
        Save dashboard HTML to file.
        
        Parameters
        ----------
        html_content : str
            HTML content to save
        output_path : str
            Path where to save the dashboard file
        
        Returns
        -------
        str
            Path where dashboard was saved
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Data quality dashboard saved to {output_path}")
        return str(output_path)


class AblationDashboardGenerator:
    """
    Generates interactive HTML dashboards for ablation study results.
    
    The dashboard includes:
    - Bar charts of feature contributions (impact on MAE/RMSE/directional accuracy)
    - Heatmaps of metric deltas vs. baseline performance
    - Feature importance ranking (contribution to model performance)
    - Comparison of different feature tiers (Tier-1, Tier-2, Tier-3 impact)
    - Summary table of all ablation results
    
    All visualizations are standalone HTML files that can be opened in any browser.
    
    Examples
    --------
    >>> generator = AblationDashboardGenerator(logger=logger)
    >>> ablation_results = load_ablation_results('results/ablation/')
    >>> html = generator.generate_ablation_dashboard(ablation_results)
    >>> generator.save_dashboard(html, 'results/visualizations/ablation_dashboard.html')
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize AblationDashboardGenerator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for tracking dashboard generation
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_ablation_dashboard(
        self,
        ablation_results: Dict[str, Any],
        ablation_plan: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate interactive ablation study dashboard in HTML format.
        
        Parameters
        ----------
        ablation_results : Dict[str, Any]
            Ablation study results with structure:
            {
                'baseline': {'mae': float, 'rmse': float, 'directional_accuracy': float, ...},
                'ablations': [
                    {
                        'name': str,
                        'description': str,
                        'removed_columns': [str, ...],
                        'validation_metrics': {'mae': float, 'rmse': float, ...},
                        'test_metrics': {'mae': float, 'rmse': float, ...},
                        'delta_validation': {'mae': float, 'rmse': float, ...},
                        'delta_test': {'mae': float, 'rmse': float, ...}
                    },
                    ...
                ]
            }
        ablation_plan : Dict[str, Any], optional
            Ablation plan with feature group descriptions for context
        
        Returns
        -------
        str
            HTML string containing the complete interactive ablation dashboard
        """
        self.logger.info("Starting ablation dashboard generation")
        
        # Extract ablation data
        ablations = ablation_results.get('ablations', [])
        baseline = ablation_results.get('baseline', {})
        
        if not ablations:
            self.logger.warning("No ablation results provided")
            return self._generate_empty_dashboard()
        
        # Sort ablations by MAE delta (most impactful first)
        sorted_ablations = self._sort_ablations_by_impact(ablations)
        
        # Extract ablation names and metrics
        ablation_names = [a['name'] for a in sorted_ablations]
        test_mae_deltas = [a.get('delta_test', {}).get('mae', 0) for a in sorted_ablations]
        test_rmse_deltas = [a.get('delta_test', {}).get('rmse', 0) for a in sorted_ablations]
        test_dir_acc_deltas = [a.get('delta_test', {}).get('directional_accuracy', 0) for a in sorted_ablations]
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Feature Importance: Impact on Test MAE",
                "Feature Importance: Impact on Test RMSE",
                "Feature Importance: Impact on Directional Accuracy",
                "Metric Deltas Heatmap (Test Set)",
                "Ablation Summary Table (Top Metrics)",
                "Feature Tier Contribution (Test MAE)"
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "heatmap"}],
                [{"type": "table"}, {"type": "bar"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.12
        )
        
        # 1. Feature Importance: Impact on Test MAE (bar chart)
        fig.add_trace(
            go.Bar(
                y=ablation_names,
                x=test_mae_deltas,
                orientation='h',
                name="MAE Delta",
                marker_color=['rgba(255, 100, 100, 0.7)' if x > 0 else 'rgba(100, 150, 200, 0.7)' 
                             for x in test_mae_deltas],
                text=[f"{x:.4f}" for x in test_mae_deltas],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>MAE Delta: %{x:.6f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 2. Feature Importance: Impact on Test RMSE (bar chart)
        fig.add_trace(
            go.Bar(
                y=ablation_names,
                x=test_rmse_deltas,
                orientation='h',
                name="RMSE Delta",
                marker_color=['rgba(200, 100, 100, 0.7)' if x > 0 else 'rgba(100, 100, 200, 0.7)' 
                             for x in test_rmse_deltas],
                text=[f"{x:.4f}" for x in test_rmse_deltas],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>RMSE Delta: %{x:.6f}<extra></extra>"
            ),
            row=1, col=2
        )
        
        # 3. Feature Importance: Impact on Directional Accuracy (bar chart)
        fig.add_trace(
            go.Bar(
                y=ablation_names,
                x=test_dir_acc_deltas,
                orientation='h',
                name="Dir.Acc. Delta",
                marker_color=['rgba(100, 200, 100, 0.7)' if x < 0 else 'rgba(200, 100, 100, 0.7)' 
                             for x in test_dir_acc_deltas],
                text=[f"{x:.4f}" for x in test_dir_acc_deltas],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Dir.Acc. Delta: %{x:.6f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 4. Metric Deltas Heatmap
        heatmap_data, heatmap_labels_y, heatmap_labels_x = self._prepare_heatmap_data(sorted_ablations)
        
        fig.add_trace(
            go.Heatmap(
                z=heatmap_data,
                y=heatmap_labels_y,
                x=heatmap_labels_x,
                colorscale='RdYlGn_r',
                name="Metric Delta",
                hovertemplate="<b>%{y}</b><br>%{x}: %{z:.6f}<extra></extra>"
            ),
            row=2, col=2
        )
        
        # 5. Summary table
        table_data = self._prepare_summary_table(baseline, sorted_ablations[:10])  # Top 10
        
        fig.add_trace(
            table_data,
            row=3, col=1
        )
        
        # 6. Feature Tier Contribution (if available)
        tier_contributions = self._extract_tier_contributions(sorted_ablations, ablation_plan)
        if tier_contributions:
            tier_names = list(tier_contributions.keys())
            tier_mae_impacts = [abs(v) for v in tier_contributions.values()]
            
            fig.add_trace(
                go.Bar(
                    x=tier_names,
                    y=tier_mae_impacts,
                    name="Avg MAE Impact",
                    marker_color=['rgba(100, 150, 200, 0.7)', 'rgba(150, 100, 200, 0.7)', 
                                 'rgba(200, 150, 100, 0.7)'][:len(tier_names)],
                    text=[f"{x:.4f}" for x in tier_mae_impacts],
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Avg Impact: %{y:.6f}<extra></extra>"
                ),
                row=3, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text="<b>Ablation Study: Feature Importance Analysis</b>",
            title_font_size=24,
            showlegend=True,
            legend_orientation="v",
            height=1400,
            width=1800,
            hovermode="closest",
            template="plotly_white"
        )
        
        # Update axes
        fig.update_xaxes(title_text="MAE Delta", row=1, col=1)
        fig.update_xaxes(title_text="RMSE Delta", row=1, col=2)
        fig.update_xaxes(title_text="MAE Delta", row=2, col=1)
        fig.update_xaxes(title_text="Feature Tier", row=3, col=2)
        
        fig.update_yaxes(title_text="Ablation", row=1, col=1)
        fig.update_yaxes(title_text="Ablation", row=1, col=2)
        fig.update_yaxes(title_text="Ablation", row=2, col=1)
        
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
        
        # Wrap with summary and interpretation
        html = self._add_ablation_summary_section(html, baseline, sorted_ablations)
        
        self.logger.info("Ablation dashboard generation completed successfully")
        return html
    
    def _sort_ablations_by_impact(self, ablations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort ablations by impact (MAE delta) in descending order.
        
        Parameters
        ----------
        ablations : List[Dict[str, Any]]
            List of ablation results
        
        Returns
        -------
        List[Dict[str, Any]]
            Sorted ablations (most impactful first)
        """
        return sorted(
            ablations,
            key=lambda x: abs(x.get('delta_test', {}).get('mae', 0)),
            reverse=True
        )
    
    def _prepare_heatmap_data(
        self,
        ablations: List[Dict[str, Any]]
    ) -> Tuple[List[List[float]], List[str], List[str]]:
        """
        Prepare data for heatmap visualization.
        
        Parameters
        ----------
        ablations : List[Dict[str, Any]]
            Sorted ablation results
        
        Returns
        -------
        Tuple[List, List, List]
            (z_data, y_labels, x_labels) for heatmap
        """
        metrics = ['mae', 'rmse', 'directional_accuracy']
        z_data = []
        
        for ablation in ablations:
            delta_test = ablation.get('delta_test', {})
            row = [delta_test.get(metric, 0) for metric in metrics]
            z_data.append(row)
        
        y_labels = [a['name'] for a in ablations]
        x_labels = ['MAE Delta', 'RMSE Delta', 'Dir.Acc. Delta']
        
        return z_data, y_labels, x_labels
    
    def _prepare_summary_table(
        self,
        baseline: Dict[str, Any],
        ablations: List[Dict[str, Any]]
    ) -> go.Table:
        """
        Prepare summary table trace.
        
        Parameters
        ----------
        baseline : Dict[str, Any]
            Baseline metrics
        ablations : List[Dict[str, Any]]
            Ablation results to display
        
        Returns
        -------
        go.Table
            Plotly Table trace
        """
        names = ['BASELINE'] + [a['name'] for a in ablations]
        test_mae = [baseline.get('mae', 0)] + [a.get('test_metrics', {}).get('mae', 0) for a in ablations]
        test_rmse = [baseline.get('rmse', 0)] + [a.get('test_metrics', {}).get('rmse', 0) for a in ablations]
        test_dir_acc = [baseline.get('directional_accuracy', 0)] + \
                      [a.get('test_metrics', {}).get('directional_accuracy', 0) for a in ablations]
        mae_delta = [0] + [a.get('delta_test', {}).get('mae', 0) for a in ablations]
        
        return go.Table(
            header=dict(
                values=['<b>Ablation</b>', '<b>Test MAE</b>', '<b>Test RMSE</b>', 
                       '<b>Test Dir.Acc.</b>', '<b>MAE Delta</b>'],
                fill_color='rgba(0, 100, 200, 0.7)',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=[
                    names,
                    [f"{x:.6f}" for x in test_mae],
                    [f"{x:.6f}" for x in test_rmse],
                    [f"{x:.4f}" for x in test_dir_acc],
                    [f"{x:+.6f}" for x in mae_delta]
                ],
                fill_color='rgba(240, 240, 240, 0.5)',
                align='left',
                font=dict(size=11),
                height=30
            )
        )
    
    def _extract_tier_contributions(
        self,
        ablations: List[Dict[str, Any]],
        ablation_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Extract feature tier contributions from ablation results.
        
        Parameters
        ----------
        ablations : List[Dict[str, Any]]
            Ablation results
        ablation_plan : Dict[str, Any], optional
            Ablation plan for tier classification
        
        Returns
        -------
        Dict[str, float]
            Average impact per feature tier
        """
        tier_impacts = {
            'Tier-1': [],
            'Tier-2': [],
            'Tier-3': []
        }
        
        for ablation in ablations:
            name = ablation.get('name', '').lower()
            mae_delta = abs(ablation.get('delta_test', {}).get('mae', 0))
            
            # Classify by name heuristic
            if 'tier1' in name or 'return' in name or 'normalized' in name:
                tier_impacts['Tier-1'].append(mae_delta)
            elif 'tier2' in name or 'signal' in name or 'wavelet' in name or 'ssa' in name or 'kalman' in name:
                tier_impacts['Tier-2'].append(mae_delta)
            elif 'tier3' in name or 'regime' in name or 'cross' in name or 'correlation' in name:
                tier_impacts['Tier-3'].append(mae_delta)
        
        # Calculate averages
        tier_contributions = {}
        for tier, impacts in tier_impacts.items():
            if impacts:
                tier_contributions[tier] = np.mean(impacts)
        
        return tier_contributions
    
    def _add_ablation_summary_section(
        self,
        html: str,
        baseline: Dict[str, Any],
        ablations: List[Dict[str, Any]]
    ) -> str:
        """
        Add ablation summary and interpretation section to dashboard HTML.
        
        Parameters
        ----------
        html : str
            Existing HTML content
        baseline : Dict[str, Any]
            Baseline metrics
        ablations : List[Dict[str, Any]]
            Ablation results
        
        Returns
        -------
        str
            Enhanced HTML with summary section
        """
        # Find most impactful ablations
        top_ablations = ablations[:3]
        
        # Calculate key insights
        avg_mae_delta = np.mean([abs(a.get('delta_test', {}).get('mae', 0)) for a in ablations])
        max_mae_impact_ablation = top_ablations[0] if top_ablations else {}
        max_mae_impact = abs(max_mae_impact_ablation.get('delta_test', {}).get('mae', 0))
        
        baseline_mae = baseline.get('mae', 0)
        worst_case_mae = baseline_mae + max_mae_impact
        best_case_mae = baseline_mae - min(
            [abs(a.get('delta_test', {}).get('mae', 0)) for a in ablations],
            default=0
        )
        
        # Count ablation types
        tier_counts = {
            'Tier-1': sum(1 for a in ablations if 'tier1' in a.get('name', '').lower()),
            'Tier-2': sum(1 for a in ablations if 'tier2' in a.get('name', '').lower() or 
                         any(x in a.get('name', '').lower() for x in ['signal', 'wavelet', 'ssa', 'kalman'])),
            'Tier-3': sum(1 for a in ablations if 'tier3' in a.get('name', '').lower() or
                         any(x in a.get('name', '').lower() for x in ['regime', 'cross']))
        }
        
        summary_html = f"""
        <div style="background-color: #f8f9fa; padding: 20px; margin-bottom: 20px; border-radius: 8px; border-left: 4px solid #0066cc;">
            <h2 style="margin-top: 0; color: #333;">Ablation Study Summary</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Baseline Test MAE</div>
                    <div style="font-size: 28px; font-weight: bold; color: #0066cc; margin-top: 10px;">{baseline_mae:.6f}</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Avg Feature Impact</div>
                    <div style="font-size: 28px; font-weight: bold; color: #009966; margin-top: 10px;">+{avg_mae_delta:.6f}</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Total Ablations</div>
                    <div style="font-size: 28px; font-weight: bold; color: #0099cc; margin-top: 10px;">{len(ablations)}</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Most Impactful Feature</div>
                    <div style="font-size: 18px; font-weight: bold; color: #cc3300; margin-top: 10px;">{max_mae_impact_ablation.get('name', 'N/A')}</div>
                    <div style="font-size: 12px; color: #999; margin-top: 5px;">Impact: +{max_mae_impact:.6f} MAE</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Worst Case (Baseline + Max)</div>
                    <div style="font-size: 18px; font-weight: bold; color: #cc6600; margin-top: 10px;">{worst_case_mae:.6f}</div>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #666; font-size: 14px; text-transform: uppercase; font-weight: bold;">Best Case (Baseline - Min)</div>
                    <div style="font-size: 18px; font-weight: bold; color: #009933; margin-top: 10px;">{best_case_mae:.6f}</div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                <h3 style="color: #333; margin-top: 0;">Key Findings</h3>
                <ul style="color: #666; line-height: 1.8;">
                    <li><b>Most Impactful Ablation:</b> {max_mae_impact_ablation.get('name', 'N/A')} 
                        (removes {len(max_mae_impact_ablation.get('removed_columns', []))} features, 
                        MAE impact: +{max_mae_impact:.6f})</li>
                    <li><b>Average Feature Importance:</b> Each ablated feature group impacts MAE by ~{avg_mae_delta:.6f} on average</li>
                    <li><b>Feature Count by Tier:</b> Tier-1: {tier_counts.get('Tier-1', 0)}, 
                        Tier-2: {tier_counts.get('Tier-2', 0)}, Tier-3: {tier_counts.get('Tier-3', 0)}</li>
                    <li><b>Model Robustness:</b> Removing most impactful features increases MAE by 
                        {(max_mae_impact/baseline_mae*100):.1f}% (from {baseline_mae:.6f} to {baseline_mae + max_mae_impact:.6f})</li>
                </ul>
            </div>
        </div>
        """
        
        # Insert summary before the main plot
        html = html.replace('<div id="', summary_html + '<div id="', 1)
        
        return html
    
    def _generate_empty_dashboard(self) -> str:
        """
        Generate a minimal dashboard when no ablation results are provided.
        
        Returns
        -------
        str
            HTML with empty state message
        """
        fig = go.Figure()
        fig.add_annotation(
            text="No ablation results available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        
        html = fig.to_html(include_plotlyjs='cdn')
        return html
    
    def save_dashboard(self, html_content: str, output_path: str) -> str:
        """
        Save dashboard HTML to file.
        
        Parameters
        ----------
        html_content : str
            HTML content to save
        output_path : str
            Path where to save the dashboard file
        
        Returns
        -------
        str
            Path where dashboard was saved
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Ablation dashboard saved to {output_path}")
        return str(output_path)


def load_context_from_results_directory(results_dir: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Load cleaning reports and features manifests from results directory.
    
    Parameters
    ----------
    results_dir : str
        Path to results directory containing cleaning_reports/ and features_manifests/ subdirectories
    
    Returns
    -------
    Tuple[Dict, Dict]
        (cleaning_reports, features_manifests) loaded from JSON files
    """
    results_path = Path(results_dir)
    cleaning_reports = {}
    features_manifests = {}
    
    # Load cleaning reports
    cleaning_dir = results_path / "cleaning_reports"
    if cleaning_dir.exists():
        for report_file in cleaning_dir.glob("*.json"):
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                    symbol = report_file.stem
                    cleaning_reports[symbol] = report
            except Exception as e:
                logging.warning(f"Failed to load cleaning report {report_file}: {e}")
    
    # Load feature manifests
    manifest_dir = results_path / "features_manifests"
    if manifest_dir.exists():
        for manifest_file in manifest_dir.glob("*.json"):
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    symbol = manifest_file.stem
                    features_manifests[symbol] = manifest
            except Exception as e:
                logging.warning(f"Failed to load feature manifest {manifest_file}: {e}")
    
    return cleaning_reports, features_manifests


def load_ablation_results(results_dir: str = 'results/') -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load ablation results and plan from results directory.
    
    Parameters
    ----------
    results_dir : str
        Path to results directory
    
    Returns
    -------
    Tuple[Dict, Dict]
        (ablation_results, ablation_plan) loaded from JSON files
    """
    results_path = Path(results_dir)
    
    ablation_results = {}
    ablation_plan = {}
    
    # Try to load ablation results from multiple possible locations
    ablation_results_paths = [
        results_path / "ablation_studies" / "ablation_results.json",
        results_path / "ablation_results.json",
        Path("ablation_results.json"),
        Path("results") / "ablation_results.json"
    ]
    
    for path in ablation_results_paths:
        if path.exists():
            try:
                with open(path, 'r') as f:
                    ablation_results = json.load(f)
                    break
            except Exception as e:
                logging.warning(f"Failed to load ablation results from {path}: {e}")
    
    # Try to load ablation plan from multiple possible locations
    ablation_plan_paths = [
        results_path / "ablation_plan.json",
        Path("ablation_plan.json"),
        Path("results") / "ablation_plan.json"
    ]
    
    for path in ablation_plan_paths:
        if path.exists():
            try:
                with open(path, 'r') as f:
                    ablation_plan = json.load(f)
                    break
            except Exception as e:
                logging.warning(f"Failed to load ablation plan from {path}: {e}")
    
    return ablation_results, ablation_plan
