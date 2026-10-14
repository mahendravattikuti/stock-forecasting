"""
Example usage of the PipelineReportGenerator.

This script demonstrates how to:
1. Load pipeline execution context from results directory
2. Generate a comprehensive markdown report
3. Save the report to disk

Usage:
    python reporting/example_usage.py
"""

import json
import logging
from pathlib import Path
from reporting.report_generator import (
    PipelineReportGenerator,
    load_context_from_results_directory
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Generate pipeline execution report from results directory."""
    
    # Load master config
    logger.info("Loading configuration...")
    with open('master_config.json', 'r') as f:
        config = json.load(f)
    
    # Load execution context from results directory
    logger.info("Loading pipeline execution results...")
    context = load_context_from_results_directory(
        config=config,
        results_dir='results',
        logger=logger
    )
    
    # Generate report
    logger.info("Generating pipeline execution report...")
    generator = PipelineReportGenerator(logger=logger)
    report = generator.generate_pipeline_report(context)
    
    # Save report
    output_path = 'results/reports/pipeline_execution_report.md'
    logger.info(f"Saving report to {output_path}...")
    saved_path = generator.save_report(report, output_path)
    
    logger.info(f"✓ Report successfully generated and saved to {saved_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("Pipeline Execution Report Generated")
    print("=" * 70)
    print(f"Output: {saved_path}")
    print(f"Size: {Path(saved_path).stat().st_size:,} bytes")
    print("\nReport Summary:")
    print("-" * 70)
    
    # Count major sections
    section_count = report.count('\n## ')
    print(f"- Major sections: {section_count}")
    print(f"- Tables: {report.count('|')}")
    print(f"- Symbols documented: {len(context.cleaning_reports)}")
    print(f"- Features manifests: {len(context.features_manifests)}")
    print(f"- Baseline results: {len(context.baseline_results)}")
    
    print("\nFirst 500 characters of report:")
    print("-" * 70)
    print(report[:500] + "...\n")


if __name__ == '__main__':
    main()
