"""
Example usage of ModelCardGenerator.

This example demonstrates how to:
1. Load pipeline context from results directory
2. Generate a model card
3. Save the model card to file
"""

from reporting.model_card_generator import (
    ModelCardGenerator,
    load_context_from_results_directory
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Generate and save model card for the pipeline."""
    
    # Load context from results directory
    logger.info("Loading pipeline context from results directory...")
    context = load_context_from_results_directory(
        results_dir="results",
        logger=logger
    )
    
    logger.info(f"Loaded context for {len(context.cleaning_reports)} symbols")
    logger.info(f"Loaded {len(context.baseline_results)} baseline models")
    
    # Generate model card
    logger.info("Generating model card...")
    generator = ModelCardGenerator(logger=logger)
    model_card = generator.generate_model_card(context)
    
    logger.info(f"Generated model card ({len(model_card)} characters)")
    
    # Save model card
    logger.info("Saving model card to results/reports/model_card.md...")
    output_path = generator.save_model_card(
        model_card,
        "results/reports/model_card.md"
    )
    
    logger.info(f"Model card saved successfully to {output_path}")
    
    # Print summary
    print("\n" + "="*70)
    print("MODEL CARD GENERATION COMPLETE")
    print("="*70)
    print(f"Symbols Analyzed: {len(context.cleaning_reports)}")
    print(f"Baseline Models: {len(context.baseline_results)}")
    print(f"Model Card Size: {len(model_card):,} characters")
    print(f"Output Location: {output_path}")
    print("="*70)
    
    # Print first section of model card
    print("\nFirst 1000 characters of model card:\n")
    print(model_card[:1000])
    print("\n... (see full model card in results/reports/model_card.md)\n")


if __name__ == "__main__":
    main()
