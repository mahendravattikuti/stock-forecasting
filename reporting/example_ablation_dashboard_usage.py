"""
Example usage of AblationDashboardGenerator.

This example demonstrates how to:
1. Load ablation results from JSON files
2. Generate an interactive ablation dashboard
3. Save the dashboard to HTML
4. Interpret the results
"""

import logging
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from reporting.dashboard_generator import AblationDashboardGenerator, load_ablation_results

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main example function demonstrating ablation dashboard generation.
    """
    
    # 1. Initialize the generator
    logger.info("Initializing AblationDashboardGenerator...")
    ablation_generator = AblationDashboardGenerator(logger=logger)
    
    # 2. Load ablation results and plan
    logger.info("Loading ablation results and plan...")
    try:
        ablation_results, ablation_plan = load_ablation_results(results_dir='results/')
        
        if not ablation_results:
            logger.warning("No ablation results found. Using example data for demonstration.")
            
            # Use example ablation results for demonstration
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
                        'validation_metrics': {'mae': 0.0195, 'rmse': 0.0255, 'directional_accuracy': 0.550},
                        'test_metrics': {'mae': 0.0210, 'rmse': 0.0275, 'directional_accuracy': 0.545},
                        'delta_validation': {'mae': 0.0010, 'rmse': 0.0010, 'directional_accuracy': -0.012},
                        'delta_test': {'mae': 0.0025, 'rmse': 0.0030, 'directional_accuracy': -0.017}
                    },
                    {
                        'name': 'remove_macd',
                        'description': 'Remove MACD family features',
                        'removed_columns': ['macd_line', 'macd_signal', 'macd_histogram'],
                        'validation_metrics': {'mae': 0.0192, 'rmse': 0.0250, 'directional_accuracy': 0.555},
                        'test_metrics': {'mae': 0.0198, 'rmse': 0.0262, 'directional_accuracy': 0.552},
                        'delta_validation': {'mae': 0.0007, 'rmse': 0.0005, 'directional_accuracy': -0.007},
                        'delta_test': {'mae': 0.0013, 'rmse': 0.0017, 'directional_accuracy': -0.010}
                    },
                    {
                        'name': 'remove_tier2',
                        'description': 'Remove all Tier-2 technical indicators',
                        'removed_columns': ['rsi_14', 'macd_line', 'macd_signal', 'bollinger_upper', 
                                           'bollinger_lower', 'stochastic_k', 'atr_14', 'adx_14', 
                                           'obv', 'momentum', 'volatility'],
                        'validation_metrics': {'mae': 0.0225, 'rmse': 0.0290, 'directional_accuracy': 0.530},
                        'test_metrics': {'mae': 0.0245, 'rmse': 0.0310, 'directional_accuracy': 0.520},
                        'delta_validation': {'mae': 0.0040, 'rmse': 0.0045, 'directional_accuracy': -0.032},
                        'delta_test': {'mae': 0.0060, 'rmse': 0.0065, 'directional_accuracy': -0.042}
                    },
                    {
                        'name': 'remove_tier3',
                        'description': 'Remove Tier-3 market context features',
                        'removed_columns': ['market_regime', 'sector_momentum', 'market_beta', 'cross_asset_correlation'],
                        'validation_metrics': {'mae': 0.0188, 'rmse': 0.0248, 'directional_accuracy': 0.560},
                        'test_metrics': {'mae': 0.0192, 'rmse': 0.0255, 'directional_accuracy': 0.558},
                        'delta_validation': {'mae': 0.0003, 'rmse': 0.0003, 'directional_accuracy': -0.002},
                        'delta_test': {'mae': 0.0007, 'rmse': 0.0010, 'directional_accuracy': -0.004}
                    },
                    {
                        'name': 'remove_signal_processing',
                        'description': 'Remove all signal-processing features',
                        'removed_columns': ['wavelet_approximation', 'wavelet_detail', 'wavelet_energy', 
                                           'ssa_component_1', 'ssa_component_2', 'ssa_reconstruction',
                                           'kalman_state', 'kalman_smoothed', 'kalman_gain'],
                        'validation_metrics': {'mae': 0.0198, 'rmse': 0.0258, 'directional_accuracy': 0.545},
                        'test_metrics': {'mae': 0.0218, 'rmse': 0.0282, 'directional_accuracy': 0.535},
                        'delta_validation': {'mae': 0.0013, 'rmse': 0.0013, 'directional_accuracy': -0.017},
                        'delta_test': {'mae': 0.0033, 'rmse': 0.0037, 'directional_accuracy': -0.027}
                    }
                ]
            }
    except Exception as e:
        logger.error(f"Failed to load ablation results: {e}")
        raise
    
    # 3. Generate ablation dashboard
    logger.info("Generating ablation dashboard...")
    html = ablation_generator.generate_ablation_dashboard(
        ablation_results=ablation_results,
        ablation_plan=ablation_plan if ablation_plan else None
    )
    
    # 4. Save the dashboard
    output_dir = Path('results/visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'ablation_dashboard.html'
    
    logger.info(f"Saving ablation dashboard to {output_path}...")
    saved_path = ablation_generator.save_dashboard(html, str(output_path))
    logger.info(f"Ablation dashboard saved successfully to: {saved_path}")
    
    # 5. Print summary statistics
    if ablation_results and 'ablations' in ablation_results:
        baseline = ablation_results.get('baseline', {})
        ablations = ablation_results['ablations']
        
        logger.info("\n" + "="*70)
        logger.info("ABLATION STUDY SUMMARY")
        logger.info("="*70)
        logger.info(f"Baseline MAE: {baseline.get('mae', 0):.6f}")
        logger.info(f"Baseline RMSE: {baseline.get('rmse', 0):.6f}")
        logger.info(f"Baseline Directional Accuracy: {baseline.get('directional_accuracy', 0):.4f}")
        logger.info(f"\nTotal Ablations: {len(ablations)}")
        logger.info("\nMost Impactful Ablations (by MAE delta):")
        
        # Sort by MAE delta
        sorted_ablations = sorted(
            ablations,
            key=lambda x: abs(x.get('delta_test', {}).get('mae', 0)),
            reverse=True
        )
        
        for i, ablation in enumerate(sorted_ablations[:5], 1):
            mae_delta = ablation.get('delta_test', {}).get('mae', 0)
            rmse_delta = ablation.get('delta_test', {}).get('rmse', 0)
            dir_acc_delta = ablation.get('delta_test', {}).get('directional_accuracy', 0)
            
            logger.info(f"\n{i}. {ablation['name']}")
            logger.info(f"   Description: {ablation.get('description', 'N/A')}")
            logger.info(f"   Removed Columns: {len(ablation.get('removed_columns', []))} features")
            logger.info(f"   MAE Delta: {mae_delta:+.6f} (Impact: {mae_delta/baseline.get('mae', 1)*100:+.1f}%)")
            logger.info(f"   RMSE Delta: {rmse_delta:+.6f}")
            logger.info(f"   Dir.Acc. Delta: {dir_acc_delta:+.4f}")
        
        logger.info("\n" + "="*70)


if __name__ == '__main__':
    main()
