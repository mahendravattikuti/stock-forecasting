# Ablation Dashboard Generator

## Overview

The `AblationDashboardGenerator` class creates interactive HTML dashboards that visualize and analyze the results of ablation studies. Ablation studies systematically remove or modify features to measure their individual and combined contributions to model performance.

The ablation dashboard provides comprehensive insights into:
- Feature importance rankings based on performance metrics
- Impact of removing specific feature groups on model accuracy
- Comparison across Tier-1, Tier-2, and Tier-3 features
- Interactive heatmaps showing metric deltas
- Summary tables with detailed statistics

## Features

### Visualizations Included

1. **Bar Charts of Feature Contributions**
   - Test MAE delta for each ablation (most impactful first)
   - Test RMSE delta showing prediction volatility impact
   - Directional accuracy delta showing classification performance impact
   - Color-coded bars: red for increased error, blue for decreased error

2. **Metric Deltas Heatmap**
   - Visual representation of how each metric changes with ablations
   - Color gradient from green (improvement) to red (degradation)
   - Allows quick identification of which ablations hurt which metrics

3. **Feature Importance Ranking**
   - Ablations sorted by absolute MAE impact
   - Most impactful ablations appear at the top
   - Helps identify critical vs. optional features

4. **Feature Tier Contribution Comparison**
   - Average impact of ablating each feature tier
   - Comparison of Tier-1 (basic), Tier-2 (technical), Tier-3 (advanced) features
   - Quantifies the value of each feature hierarchy level

5. **Summary Statistics Table**
   - Top 10 most impactful ablations
   - Test set MAE, RMSE, and directional accuracy for each
   - MAE delta showing performance change
   - Baseline row for reference

6. **Ablation Study Summary**
   - Key findings and insights
   - Baseline metrics
   - Average feature importance
   - Model robustness analysis
   - Count of ablations by feature tier

## Installation

The `AblationDashboardGenerator` requires Plotly for visualization:

```bash
pip install plotly pandas numpy
```

## Usage

### Basic Usage

```python
from reporting.dashboard_generator import AblationDashboardGenerator, load_ablation_results

# Initialize generator
generator = AblationDashboardGenerator()

# Load ablation results (from JSON files)
ablation_results, ablation_plan = load_ablation_results(results_dir='results/')

# Generate dashboard
html = generator.generate_ablation_dashboard(
    ablation_results=ablation_results,
    ablation_plan=ablation_plan
)

# Save to file
generator.save_dashboard(html, 'results/visualizations/ablation_dashboard.html')
```

### With Sample Data

```python
from reporting.dashboard_generator import AblationDashboardGenerator

# Create generator
generator = AblationDashboardGenerator()

# Define ablation results
ablation_results = {
    'baseline': {
        'mae': 0.0185,
        'rmse': 0.0245,
        'directional_accuracy': 0.562
    },
    'ablations': [
        {
            'name': 'remove_rsi',
            'description': 'Remove RSI-based momentum features',
            'removed_columns': ['rsi_14', 'rsi_9', 'rsi_21'],
            'test_metrics': {
                'mae': 0.0210,
                'rmse': 0.0275,
                'directional_accuracy': 0.545
            },
            'delta_test': {
                'mae': 0.0025,
                'rmse': 0.0030,
                'directional_accuracy': -0.017
            }
        },
        # ... more ablations
    ]
}

# Generate and save
html = generator.generate_ablation_dashboard(ablation_results)
generator.save_dashboard(html, 'ablation_dashboard.html')
```

## Input Data Format

### Ablation Results Structure

```json
{
  "baseline": {
    "mae": 0.0185,
    "rmse": 0.0245,
    "directional_accuracy": 0.562
  },
  "ablations": [
    {
      "name": "remove_rsi",
      "description": "Remove RSI-based momentum features",
      "removed_columns": ["rsi_14", "rsi_9", "rsi_21"],
      "validation_metrics": {
        "mae": 0.0195,
        "rmse": 0.0255,
        "directional_accuracy": 0.550
      },
      "test_metrics": {
        "mae": 0.0210,
        "rmse": 0.0275,
        "directional_accuracy": 0.545
      },
      "delta_validation": {
        "mae": 0.0010,
        "rmse": 0.0010,
        "directional_accuracy": -0.012
      },
      "delta_test": {
        "mae": 0.0025,
        "rmse": 0.0030,
        "directional_accuracy": -0.017
      }
    }
  ]
}
```

### Ablation Plan Structure (Optional)

```json
{
  "name": "phase_15_default",
  "feature_groups": {
    "remove_rsi": {
      "columns": ["rsi_14", "rsi_9", "rsi_21"],
      "description": "Remove RSI-based momentum features"
    },
    "remove_tier2": {
      "columns": ["rsi_14", "macd_line", "bollinger_upper", "..."],
      "description": "Remove all Tier-2 technical indicators"
    }
  }
}
```

## Output

The generated HTML dashboard includes:

- **Interactive Plotly charts** that can be zoomed, panned, and hovered for details
- **Responsive design** that works on desktop and mobile browsers
- **Summary statistics** section with key findings
- **CDN-hosted Plotly library** for no external dependencies when viewing
- **Color-coded visualizations** for quick visual interpretation

## Example Output

The dashboard displays:

1. **Feature Importance by MAE Impact** (Top Left)
   - Horizontal bar chart showing which ablations hurt MAE most
   - Sorted by impact for easy identification

2. **Feature Importance by RMSE Impact** (Top Right)
   - Horizontal bar chart for RMSE metric
   - Shows prediction volatility sensitivity

3. **Directional Accuracy Impact** (Middle Left)
   - Bar chart showing how ablations affect classification accuracy
   - Important for direction prediction tasks

4. **Metric Deltas Heatmap** (Middle Right)
   - Color-coded matrix of all metric changes
   - Green = improvement, Red = degradation

5. **Summary Table** (Bottom Left)
   - Top 10 ablations with full statistics
   - Baseline row for reference

6. **Feature Tier Contribution** (Bottom Right)
   - Comparison of average impact by feature tier
   - Shows relative importance of each tier

## Interpretation Guide

### Key Metrics

- **MAE Delta**: Mean absolute error change (positive = worse, negative = better)
- **RMSE Delta**: Root mean squared error change
- **Directional Accuracy Delta**: Change in directional accuracy (positive = better for accuracy)

### Understanding Results

- **High positive MAE delta**: This feature group is critical for model performance
- **Low MAE delta**: This feature group provides marginal improvements or is redundant
- **Negative directional accuracy delta**: Removing this feature hurts directional prediction
- **Feature tier comparison**: Identifies which feature engineering effort is most valuable

### Example Interpretation

If `remove_tier2` shows:
- MAE Delta: +0.006 (32% increase from baseline)
- Feature count: 11
- Impact per feature: ~0.0005 per feature

This indicates Tier-2 features are critical and worth the computational cost.

## Methods

### `generate_ablation_dashboard(ablation_results, ablation_plan=None) -> str`

Generates the complete interactive ablation dashboard.

**Parameters:**
- `ablation_results` (Dict): Ablation study results with baseline and ablations
- `ablation_plan` (Dict, optional): Feature group descriptions for context

**Returns:**
- HTML string containing the complete dashboard

### `save_dashboard(html_content, output_path) -> str`

Saves the generated HTML to a file.

**Parameters:**
- `html_content` (str): HTML content to save
- `output_path` (str): Path where to save the HTML file

**Returns:**
- Path to saved file

## Performance Considerations

- Dashboard generation is fast (~1-2 seconds) even with many ablations
- HTML file size is typically 2-5 MB depending on data size
- Plotly library is loaded from CDN, requires internet connection for viewing

## Testing

Comprehensive tests are included in `test_dashboard_generator.py`:

```bash
# Run all ablation dashboard tests
pytest reporting/test_dashboard_generator.py::TestAblationDashboardGenerator -v

# Run integration tests
pytest reporting/test_dashboard_generator.py::TestAblationDashboardIntegration -v

# Run all dashboard tests
pytest reporting/test_dashboard_generator.py -v
```

## Example Script

See `example_ablation_dashboard_usage.py` for a complete working example:

```bash
python reporting/example_ablation_dashboard_usage.py
```

This will:
1. Generate sample ablation results
2. Create an interactive dashboard
3. Save it to `results/visualizations/ablation_dashboard.html`
4. Print summary statistics to console

## Files Modified/Created

- `reporting/dashboard_generator.py` - Added `AblationDashboardGenerator` class and helper functions
- `reporting/test_dashboard_generator.py` - Added 15+ comprehensive tests
- `reporting/example_ablation_dashboard_usage.py` - Complete working example
- `reporting/ABLATION_DASHBOARD_README.md` - This documentation

## References

- Requirements: 13.5 (Output/Reporting - ablation visualizations)
- Task: 16.5 (Phase 16: Create ablation summary visualizations)
- Design: Section 12 (Output and Reporting Architecture)

## Future Enhancements

- PNG export capability (300 DPI for publication)
- Statistical significance testing display
- Feature interaction analysis
- Confidence interval visualization
- Comparison across multiple ablation studies
