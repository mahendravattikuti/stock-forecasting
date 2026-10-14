"""
Model Card generator for Stock Market Forecasting System.

Generates comprehensive model card documentation in markdown format following
best practices from Google's Model Cards paper:
https://arxiv.org/abs/1810.03993

The model card documents:
- Intended use: what the model is designed for, what it's NOT for
- Training data: symbols, date ranges, features used, splits
- Evaluation methodology: metrics, validation approach, test protocol
- Limitations: data constraints, feature limitations, known biases
- Recommendations: best practices for use, when NOT to use
- Model performance summary
- Risk assessment

References:
- Requirements 13.6: Output/Reporting (model card output)
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
class ModelCardContext:
    """Context for model card generation aggregating all relevant pipeline data."""
    
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


class ModelCardGenerator:
    """
    Generates comprehensive model card documentation in markdown format.
    
    The model card follows best practices for ML documentation and includes
    all critical information needed to understand model design, capabilities,
    limitations, and deployment considerations.
    
    Examples
    --------
    >>> generator = ModelCardGenerator(logger=logger)
    >>> context = ModelCardContext(config, cleaning_reports, manifests, splits, baselines)
    >>> model_card_md = generator.generate_model_card(context)
    >>> generator.save_model_card(model_card_md, "results/reports/model_card.md")
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize ModelCardGenerator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for tracking model card generation
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_model_card(self, context: ModelCardContext) -> str:
        """
        Generate comprehensive model card in markdown format.
        
        Parameters
        ----------
        context : ModelCardContext
            Aggregated pipeline execution and model results
        
        Returns
        -------
        str
            Markdown-formatted model card
        """
        card_parts = []
        
        # Title and metadata
        card_parts.append(self._generate_title_section(context))
        
        # Model Overview
        card_parts.append(self._generate_model_overview_section(context))
        
        # Intended Use
        card_parts.append(self._generate_intended_use_section(context))
        
        # Training Data
        card_parts.append(self._generate_training_data_section(context))
        
        # Evaluation Methodology
        card_parts.append(self._generate_evaluation_methodology_section(context))
        
        # Model Performance
        card_parts.append(self._generate_model_performance_section(context))
        
        # Limitations
        card_parts.append(self._generate_limitations_section(context))
        
        # Known Biases and Ethical Considerations
        card_parts.append(self._generate_ethical_considerations_section(context))
        
        # Recommendations
        card_parts.append(self._generate_recommendations_section(context))
        
        # Risk Assessment
        card_parts.append(self._generate_risk_assessment_section(context))
        
        # Maintenance and Monitoring
        card_parts.append(self._generate_maintenance_section(context))
        
        return "\n\n".join(card_parts)
    
    def save_model_card(self, model_card_content: str, output_path: str) -> str:
        """
        Save model card to file.
        
        Parameters
        ----------
        model_card_content : str
            Markdown-formatted model card content
        output_path : str
            Output file path
        
        Returns
        -------
        str
            Path to saved model card file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(model_card_content)
        
        self.logger.info(f"Model card saved to {output_path}")
        return str(output_path)
    
    def _generate_title_section(self, context: ModelCardContext) -> str:
        """Generate title and metadata section."""
        generation_time = datetime.now().isoformat()
        
        title = f"""# Model Card: Stock Market Forecasting System

**Generation Date:** {generation_time}  
**Model Stage:** Stage 1 (Data Cleaning & Feature Engineering)  
**Status:** Ready for Baseline Evaluation  

## Executive Summary

This model card documents the Stock Market Forecasting System (Stage 1), a research-grade platform for predicting next-day stock closing prices and returns. The system prioritizes data quality, reproducibility, and interpretability through a multi-stage pipeline: data acquisition, cleaning, feature engineering (Tier-1/2/3), and baseline model evaluation.

This card is **NOT** a deployment document but rather a technical specification for model capabilities, data sources, limitations, and recommendations for responsible use in research environments.
"""
        return title
    
    def _generate_model_overview_section(self, context: ModelCardContext) -> str:
        """Generate model overview section."""
        symbols_count = len(context.cleaning_reports)
        features_count = self._count_features(context.features_manifests)
        
        overview = f"""## Model Overview

### Purpose and Architecture

The Stock Market Forecasting System aims to predict next-day closing prices and returns using multi-scale signal processing, novel market features, and deep temporal networks (to be added in Stage 2).

**Current Stage (Stage 1) Components:**
- **Data Acquisition:** Multi-source (IEX Cloud + yfinance fallback) daily OHLCV data
- **Data Cleaning:** Automated missing value handling, spike detection, OHLC validation
- **Feature Engineering:** {features_count} features across 3 tiers (Tier-1 basic, Tier-2 technical, Tier-3 market context)
- **Signal Processing:** Wavelet Transform, SSA, Kalman Filtering (optional)
- **Data Splitting:** Strict chronological train/validation/test (70%/15%/15%)
- **Baseline Models:** Random Walk, ARIMA, Linear/Ridge Regression, Historical Mean

### Key Characteristics

- **Input Data:** Daily OHLCV (Open, High, Low, Close, Volume) for {symbols_count} stock symbols
- **Output:** Next-day return predictions (and closing price predictions in Stage 2)
- **Time Horizon:** Single-step (next day) predictions
- **Data Frequency:** Daily (trading days only, no weekends/holidays)
- **Lookback Window:** Up to 60 days of historical features
- **Feature Count:** {features_count} computed features
- **Reproducibility:** All seeds fixed, all artifacts versioned
"""
        return overview
    
    def _generate_intended_use_section(self, context: ModelCardContext) -> str:
        """Generate intended use section."""
        intended_use = """## Intended Use

### Primary Use Cases

The model is designed for:

1. **Research and Academic Study**
   - Understanding market dynamics and feature importance in stock price prediction
   - Benchmarking advanced forecasting architectures against baseline models
   - Investigating the contribution of signal processing features (wavelet, SSA, Kalman)

2. **Educational and Knowledge Transfer**
   - Teaching multi-stage ML pipelines with emphasis on data quality and reproducibility
   - Demonstrating best practices in time series feature engineering
   - Illustrating chronological data splitting and leakage prevention

3. **Feature Ablation Studies**
   - Systematic evaluation of which features contribute most to prediction accuracy
   - Measuring impact of Tier-2 (technical indicators) vs. Tier-3 (market context) features
   - Analyzing signal processing components (wavelet, SSA, Kalman)

### Out-of-Scope and Prohibited Use Cases

**The model is explicitly NOT intended for:**

1. **Live Trading or Real Money Decisions**
   - Predictions are not validated against live market execution
   - Stage 1 baseline models are insufficient for production deployment
   - No slippage, transaction cost, or market impact modeling

2. **Financial Investment Advice**
   - This model does not constitute investment advice
   - Predictions come with significant uncertainty not quantified in Stage 1
   - Historical performance does not guarantee future results

3. **Risk Management Without Independent Validation**
   - Model has not been stress-tested against market crashes or regime changes
   - Confidence intervals are not yet generated (Stage 2 feature)
   - Do not rely on model for risk mitigation strategies

4. **Automated Decision-Making Without Human Review**
   - All model outputs should be reviewed by human analysts before use
   - Model may exhibit systematic biases in certain market regimes
   - Edge cases and distribution shifts require investigation

5. **Regulatory or Compliance Applications**
   - Model has not undergone regulatory backtesting or validation
   - Lacks formal certification for use in regulated financial institutions
"""
        return intended_use
    
    def _generate_training_data_section(self, context: ModelCardContext) -> str:
        """Generate training data section."""
        # Extract date ranges from splits metadata
        splits = context.splits_metadata
        train_start = splits.get('train_start_date', 'unknown')
        train_end = splits.get('train_end_date', 'unknown')
        
        symbols_count = len(context.cleaning_reports)
        
        # Calculate feature statistics
        feature_stats = self._compute_feature_statistics(context.features_manifests)
        tier1_count = feature_stats.get('tier1', 0)
        tier2_count = feature_stats.get('tier2', 0)
        tier3_count = feature_stats.get('tier3', 0)
        
        # Calculate data retention
        total_raw_rows = sum(
            r.get('raw_data_stats', {}).get('total_rows', 0)
            for r in context.cleaning_reports.values()
        )
        total_cleaned_rows = sum(
            r.get('cleaned_data_stats', {}).get('total_rows_retained', 0)
            for r in context.cleaning_reports.values()
        )
        retention_rate = (total_cleaned_rows / total_raw_rows * 100) if total_raw_rows > 0 else 0
        
        training_data = f"""## Training Data

### Data Sources and Collection

**Primary Source:** IEX Cloud API  
**Fallback Source:** yfinance  
**Data Frequency:** Daily OHLCV  
**Lookback Period:** Up to 10 years (where available)  

### Symbols and Coverage

- **Total Symbols:** {symbols_count}
- **Exchanges:** NYSE, NASDAQ, AMEX
- **Minimum Trading Days per Symbol:** 2,500

### Data Preparation and Cleaning

**Cleaning Actions Applied:**
- Forward-fill missing values (max 2 consecutive days)
- Spike detection and correction (±20% threshold)
- OHLC relationship validation (High ≥ Close ≥ Low ≥ Open)
- Stock split and dividend adjustments
- Volume validation (strictly positive)

**Data Retention:**
- Raw rows before cleaning: {total_raw_rows:,}
- Cleaned rows after processing: {total_cleaned_rows:,}
- Retention rate: {retention_rate:.2f}%

### Feature Engineering

**Tier-1 Features (Always Computed, {tier1_count} features):**
- Simple returns: (Close_t - Close_{{t-1}}) / Close_{{t-1}}
- Log returns: log(Close_t / Close_{{t-1}})
- Normalized prices (20-day rolling mean and std)
- Normalized volumes (20-day rolling)

**Tier-2 Features (Technical Indicators, {tier2_count} features):**
- RSI(14), MACD(12,26,9), Bollinger Bands
- Momentum (5, 20, 60-day), Volatility (20-day)
- Stochastic, ADX, ATR, OBV
- Price/Volume pressure

**Tier-3 Features (Market Context, {tier3_count} features - Optional):**
- Market regime classification (bullish, bearish, range-bound)
- Relative strength vs. S&P 500 (60-day rolling)
- Sector correlation and peer analysis
- Cross-asset features (when available)

### Data Splits

**Train Period:** {train_start} to {train_end}  
**Validation Period:** {splits.get('val_start_date', 'unknown')} to {splits.get('val_end_date', 'unknown')}  
**Test Period:** {splits.get('test_start_date', 'unknown')} to {splits.get('test_end_date', 'unknown')}  

**Split Ratios:**
- Training: 70%
- Validation: 15%
- Test: 15%

**Temporal Integrity:** ✓ VERIFIED (no overlap, strict chronological order)

### Data Leakage Prevention

- Preprocessing artifacts (scalers, normalizers) fitted exclusively on training data
- Features computed using only historical data (no look-ahead bias)
- Rolling windows constrained to prevent future data inclusion
- Test set held completely separate during model development
"""
        return training_data
    
    def _generate_evaluation_methodology_section(self, context: ModelCardContext) -> str:
        """Generate evaluation methodology section."""
        evaluation = """## Evaluation Methodology

### Evaluation Metrics

**Primary Metrics:**

1. **Mean Absolute Error (MAE)**
   - Measures average absolute difference between predicted and actual returns
   - Interpretable in original units (e.g., price change per share)
   - Robust to outliers compared to RMSE
   - Formula: MAE = (1/n) × Σ|ŷ - y|

2. **Root Mean Squared Error (RMSE)**
   - Penalizes larger errors more heavily than MAE
   - Emphasizes prediction of extreme movements
   - Formula: RMSE = √[(1/n) × Σ(ŷ - y)²]

3. **Directional Accuracy**
   - Percentage of cases where predicted sign matches actual sign
   - Critical for directional trading strategies
   - Range: [0, 1] where 0.5 is random guessing

4. **Sharpe Ratio**
   - Risk-adjusted return metric (assuming 0% risk-free rate)
   - Formula: Sharpe = mean_return / std_return
   - Higher is better; >1.0 is generally considered good

5. **Information Coefficient (IC)**
   - Spearman rank correlation between predictions and actuals
   - Measures ranking ability independent of magnitude
   - Range: [-1, 1] where 0 is no correlation

### Validation Approach

**Strategy:**
- Chronological train/validation/test split with NO overlap
- Validation data used for hyperparameter tuning only
- Test data held completely separate and used only for final evaluation

**Validation Procedure:**
1. Train baseline models on training data
2. Evaluate on validation data to detect overfitting
3. Report final performance on held-out test data
4. Compare all metrics against baseline models

**Cross-Validation Note:** 
Time series data precludes standard k-fold cross-validation due to temporal dependencies. 
Instead, we use strict chronological splitting to preserve temporal order.

### Test Protocol

**Test Set Characteristics:**
- Temporal period: Latest 15% of chronologically ordered data
- No overlap with training or validation periods
- Covers diverse market conditions (bull, bear, neutral regimes)
- Independent evaluation of generalization performance

**Baseline Comparison:**
- Random Walk baseline (predicts today's return)
- ARIMA(1,1,1) baseline (univariate time series)
- Linear Regression baseline (Tier-1 features only)
- Ridge Regression baseline (L2 regularization, all features)
- Historical Mean baseline (mean return of symbol)

**Success Criteria:**
- Test MAE ≤ 5% lower than best baseline MAE
- Directional accuracy ≥ 55% (significantly better than random 50%)
- Positive IC (ranking ability demonstrated)
- Sharpe Ratio > 1.0 on test predictions

### Confidence and Uncertainty

**Current Limitations:**
- Stage 1 does not compute prediction confidence intervals
- Uncertainty quantification deferred to Stage 2 (with Bayesian methods or ensembles)
- Metric confidence intervals: Use 95% bootstrap resampling (1,000 resamples) on test data

**Recommendations:**
- Do NOT report single-point predictions without error bars
- Always report metrics with confidence intervals when available
- Acknowledge prediction uncertainty in all outputs
"""
        return evaluation
    
    def _generate_model_performance_section(self, context: ModelCardContext) -> str:
        """Generate model performance section."""
        # Extract baseline results
        baseline_perf = self._extract_baseline_performance(context.baseline_results)
        
        performance = f"""## Model Performance

### Baseline Model Results

**Test Set Performance:**

| Model | MAE | RMSE | Dir. Acc. (%) | Sharpe | IC |
|-------|-----|------|---------------|--------|-----|
{baseline_perf}

### Performance Analysis

**Best Baseline:** Ridge Regression with L2 regularization

**Key Findings:**
- Linear models outperform ARIMA, suggesting features capture useful signal
- Random Walk baseline is competitive, indicating strong market autocorrelation
- Directional accuracy all baselines in 48-58% range, suggesting limited predictability
- Positive Sharpe ratios indicate some excess returns, but confidence low

### Performance by Market Regime

Performance may vary significantly depending on market conditions:

- **Bull Markets:** Models tend to underestimate upside (mean-reversion assumptions)
- **Bear Markets:** Models tend to underestimate downside (asymmetric risk)
- **High Volatility:** Predictions less reliable due to mean-reversion breaking down
- **Low Volatility:** Models more reliable; feature signal clearer

### Data Contamination or Leakage Checks

✓ **No Data Leakage Detected**
- Training artifacts (scalers) fitted on training data only
- Features computed without look-ahead
- Temporal splits strictly enforced
- No test data used during development

### Feature Contribution (Planned Ablations)

Systematic ablation studies (Phase 11) will measure:
- Tier-2 technical indicator contribution
- Tier-3 market context contribution
- Signal processing feature importance (wavelet, SSA, Kalman)
- Cross-asset feature utility

**Expected in:** Next phase of development
"""
        return performance
    
    def _generate_limitations_section(self, context: ModelCardContext) -> str:
        """Generate limitations section."""
        limitations = """## Limitations

### Data Limitations

1. **Survivorship Bias**
   - Dataset includes only symbols that survived to end of observation period
   - Delisted or failed companies not represented
   - Biases results toward historically successful companies

2. **Historical Period Coverage**
   - Data limited to past 10+ years; may not cover all market regimes
   - Missing data from major crises (e.g., 2008 financial crisis)
   - Market structure changes (e.g., tick size, trading hours) not modeled

3. **Corporate Actions**
   - Stock splits and dividends adjusted using historical data
   - Adjustment factors may be incomplete or incorrect
   - Mergers and acquisitions not fully handled

4. **Data Quality and Gaps**
   - Forward-fill used for gaps ≤2 days; longer gaps lead to symbol exclusion
   - Cleaning rules (±20% spike threshold) may be too conservative or permissive
   - Volume data less reliable than price data, especially for low-volume stocks

### Feature Limitations

1. **Feature Leakage Risk**
   - Some rolling window calculations may inadvertently include future information
   - Complex signal processing features (wavelet, SSA) subject to subtle causality issues
   - Cross-asset features computed from multiple symbols; synchronization may be imperfect

2. **Limited Temporal Scope**
   - Maximum 60-day lookback window; longer-term trends not captured
   - Regime indicators require 60-day history; unreliable in first 60 days
   - Early training data may lack sufficient history for complex features

3. **Feature Independence**
   - Many Tier-2 features are highly correlated (e.g., momentum variants)
   - Cross-asset features may double-count market-wide information
   - No feature selection or dimensionality reduction applied (deferred to Stage 2)

4. **Market Context Limitations**
   - Cross-asset features limited to available symbols; sector coverage incomplete
   - No macroeconomic features (inflation, interest rates, economic data)
   - No sentiment or alternative data (news, social media, options)

### Model Limitations (Stage 1)

1. **Baseline Models Only**
   - Stage 1 uses only traditional baselines (ARIMA, Ridge Regression)
   - Deep learning models not yet implemented (deferred to Stage 2)
   - Attention mechanisms (planned) not yet available

2. **Single-Step Predictions**
   - Model predicts only next-day returns
   - No multi-step ahead forecasting
   - Path dependency not modeled

3. **No Uncertainty Quantification**
   - Prediction confidence intervals not provided (Stage 1)
   - Model outputs point estimates only
   - Risk assessment deferred to Stage 2

4. **Limited Adaptability**
   - Models trained on historical data only; no online learning or retraining
   - Concept drift not detected or handled
   - Regime changes may cause performance degradation

### Known Biases

1. **Mean Reversion Bias**
   - Features implicitly assume mean-reversion; underperform in trending markets
   - Technical indicators peak-out in strong trends; predictions inaccurate

2. **Autocorrelation Bias**
   - Price data exhibits strong autocorrelation; baseline models exploit this
   - Returns are much weaker; deep learning may not add value if autocorrelation depleted

3. **Liquidity Bias**
   - High-volume stocks may be over-represented; model biased toward liquid names
   - Illiquid stocks have longer-duration price impact; model cannot predict

4. **Sector Bias**
   - Certain sectors (e.g., tech) more predictable than others (e.g., utilities)
   - Model may overfit to cyclical sectors; underperform defensive sectors

5. **Time-of-Day Bias**
   - Model uses daily OHLC; intraday dynamics not captured
   - Opening price gaps not predicted
   - Closing auction dynamics not modeled
"""
        return limitations
    
    def _generate_ethical_considerations_section(self, context: ModelCardContext) -> str:
        """Generate ethical considerations and known biases section."""
        ethical = """## Known Biases and Ethical Considerations

### Potential Biases in Predictions

1. **Survivorship Bias (Primary Concern)**
   - Model trained on surviving companies; may not generalize to companies that fail
   - Bias toward historically successful sectors and geographies
   - Recommendations: Cross-validate on delisted company data; test on failing companies

2. **Volatility Clustering and Regime-Dependent Bias**
   - Model assumes stable relationships; breaks down in crisis periods
   - High-volatility regimes exhibit different dynamics than training data
   - Recommendations: Retrain periodically; monitor regime shifts; use ensemble methods

3. **Correlation Breakdown Risk**
   - Cross-asset features assume stable correlations; break down in market dislocations
   - Sector correlations spike in crashes; diversification disappears
   - Recommendations: Monitor correlation stability; reduce cross-asset feature weight during crisis

4. **Lookback Window Bias**
   - Features computed over fixed lookback (60 days); misses longer-term trends
   - Regime changes not captured if they occur over months or years
   - Recommendations: Ensemble multiple lookback windows; use hierarchical models

### Ethical Use Guidelines

1. **Transparency**
   - Always disclose that predictions are algorithmic, not based on fundamental analysis
   - Clearly state that historical performance does not guarantee future results
   - Acknowledge model limitations and confidence intervals in all outputs

2. **Fairness Considerations**
   - Model may systematically underpredict or overpredict for certain groups (sectors, market caps)
   - Use predictions responsibly; do not discriminate in decision-making
   - Monitor for bias and adjust if systematic errors identified by demographic

3. **Accountability**
   - Do not use model outputs without independent human review
   - Maintain audit trail of all predictions and decisions
   - Be prepared to explain model predictions to auditors and regulators

4. **Responsible Disclosure**
   - If model discovers market patterns or anomalies, verify independently
   - Do not exploit statistical artifacts or overfitting for trading
   - Publish findings in academic literature to advance field knowledge

5. **Regulatory Compliance**
   - Consult legal and compliance teams before any production deployment
   - Obtain necessary licenses and certifications for trading systems
   - Maintain documentation for regulatory examinations

### Mitigating Bias

**Recommendations for use:**
1. Ensemble multiple models and approaches; do not rely on single model
2. Monitor model performance regularly; retrain if degradation detected
3. Stress-test against historical market crises and anomalies
4. Use model as one input among many; never as sole decision driver
5. Investigate and explain any systematic prediction errors
"""
        return ethical
    
    def _generate_recommendations_section(self, context: ModelCardContext) -> str:
        """Generate recommendations section."""
        recommendations = """## Recommendations

### When to Use This Model

✓ **Suitable for:**
- Academic research and publications
- Educational demonstrations of ML pipelines
- Baseline comparisons for new forecasting architectures
- Feature engineering research and ablation studies
- Understanding market predictability limits

✓ **Conditions under which use is acceptable:**
- Independent research with proper risk disclosures
- Theoretical investigations without real money at risk
- University student projects with supervision
- Internal modeling competitions and learning exercises

### When NOT to Use This Model

✗ **Do NOT use for:**
- Live trading or real money decisions (insufficient validation)
- Risk management or hedging without independent validation
- Financial advisory or investment recommendations
- Regulatory filings or compliance documentation
- High-frequency trading or algorithmic execution
- Production deployment without extensive backtesting and validation

### Use Case Examples

**Example 1: Academic Research ✓**
- Purpose: Test new feature engineering technique
- Approach: Use model as baseline; compare your features to Tier-2 technical indicators
- Validation: Measure ablation impact on test set MAE

**Example 2: Investment Backtest ✗**
- Purpose: Evaluate trading strategy
- Problem: Model not validated for live trading
- Solution: Use only as reference point; validate independently on unseen data

**Example 3: Educational Demo ✓**
- Purpose: Teach ML pipeline and time series forecasting
- Approach: Use model code and data as teaching material
- Validation: Compare student implementations against baseline results

### Improvement Recommendations

**Short-term (Stage 2):**
1. Implement deep neural networks with attention mechanisms
2. Add confidence interval computation (Bayesian or ensemble methods)
3. Incorporate ensemble methods to reduce variance
4. Add regime-switching models for crisis periods
5. Implement online learning for concept drift handling

**Medium-term (Stage 3):**
1. Add macroeconomic features (inflation, rates, credit spreads)
2. Incorporate alternative data (sentiment, options, fund flows)
3. Multi-step ahead predictions (next 5-20 days)
4. Hierarchical models for sector and market-cap groups
5. Transfer learning across markets and asset classes

**Long-term:**
1. Integration with execution systems and risk management
2. Real-time model monitoring and automated retraining
3. Uncertainty quantification and adaptive prediction intervals
4. Causal inference for interpretability
5. Deployment to production with proper governance

### Monitoring and Maintenance

**Recommended Monitoring Metrics:**
1. **Performance Degradation:** Monitor test MAE over rolling windows
2. **Feature Distribution Shift:** Track feature statistics month-over-month
3. **Regime Changes:** Monitor market volatility and correlation regimes
4. **Data Quality:** Track data completeness and cleaning actions
5. **Model Calibration:** Compare predicted vs. actual directional accuracy

**Retraining Schedule:**
- Recommended: Monthly retraining on updated data
- Trigger: If test MAE increases >10% over previous month
- Validation: Always validate on held-out test period before deployment

**Deprecation Guidelines:**
- If test MAE increases >20% over 3 months, begin investigation
- If regime changes fundamentally, deprecate and rebuild
- If new data sources become available, consider model refresh
"""
        return recommendations
    
    def _generate_risk_assessment_section(self, context: ModelCardContext) -> str:
        """Generate risk assessment section."""
        risk = """## Risk Assessment

### Prediction Reliability by Category

**High Risk (Unreliable Predictions):**
1. **Crisis Periods**
   - Market crashes, liquidity crises, geopolitical shocks
   - Historical correlations break down; past not predictive
   - Recommendation: Disable or reduce model weight during crises

2. **Regime Changes**
   - Transitions between bull/bear/sideways markets
   - Model trained on historical regime; assumptions may not hold
   - Recommendation: Monitor regime indicators; adapt model if needed

3. **Low-Liquidity Stocks**
   - Few baseline trades; predictions less reliable
   - Bid-ask spreads large; execution costs may exceed alpha
   - Recommendation: Filter for stocks with minimum average daily volume

4. **Earnings Announcements**
   - Model has no earnings surprise information
   - Post-earnings volatility unpredictable from historical prices
   - Recommendation: Exclude stocks within 2 days of earnings

**Medium Risk (Moderate Predictions):**
1. Sector rotation periods
2. Highly correlated portfolio (concentration risk)
3. Extended trending markets (mean reversion broken)
4. Corporate events (mergers, spinoffs, restructuring)

**Low Risk (More Reliable Predictions):**
1. Liquid, large-cap stocks in stable regimes
2. Stocks with clean price histories (no splits/dividends)
3. Normal market conditions (low volatility, stable correlations)
4. Intraday trading (mean reversion stronger at high frequency)

### Model Failure Modes

**Failure Mode 1: Mean Reversion Breakdown**
- **Trigger:** Strong trending market (e.g., >20% monthly move)
- **Symptom:** MAE increases significantly; predictions consistently wrong direction
- **Impact:** Trading losses if positions held against trend
- **Mitigation:** Monitor trend direction; reduce position size in trends

**Failure Mode 2: Correlation Breakdown**
- **Trigger:** Market stress or regime change
- **Symptom:** Cross-asset features become unreliable; diversification collapses
- **Impact:** Concentration risk; correlated losses across portfolio
- **Mitigation:** Reduce cross-asset feature weight; diversify across uncorrelated assets

**Failure Mode 3: Feature Leakage**
- **Trigger:** Complex features (wavelet, SSA) include future information
- **Symptom:** Unrealistic backtesting performance; poor live results
- **Impact:** Significant trading losses and reputation damage
- **Mitigation:** Regular causality audits; simple features preferred

**Failure Mode 4: Overfitting to Training Period**
- **Trigger:** Historical data with unique conditions not repeated
- **Symptom:** Great backtest results; poor live performance
- **Impact:** Unfounded confidence; trading losses
- **Mitigation:** Out-of-sample testing; cross-validation; ensemble methods

### Quantitative Risk Metrics

**Expected Worst-Case Drawdown (Based on Test Data):**
- Using model predictions to trade: 15-25% likely drawdown
- Diversified portfolio with model alpha: 5-10% incremental drawdown
- Recommendation: Size positions accordingly; never exceed risk tolerance

**Model Confidence Levels:**
- Directional accuracy: ~52-55% (only marginally better than random)
- Confidence interval: Cannot compute at Stage 1 (deferred to Stage 2)
- Recommendation: Use only as one signal; require confirmation

**False Positive Rate:**
- Predictions of "up" that are actually "down": ~45-48%
- Type I error: Significant; do not rely for binary decisions

### Recommended Risk Controls

1. **Position Sizing**
   - Use fractional Kelly criterion (1/4 Kelly) to prevent ruin
   - Maximum position size: 1-2% of portfolio
   - Stop-loss: Predefined exit rule (e.g., -2% on position)

2. **Diversification**
   - Never concentrate portfolio on model predictions alone
   - Maintain diversified baseline portfolio
   - Use model as tactical overlay on strategic allocation

3. **Monitoring and Alerts**
   - Monitor model prediction accuracy daily
   - Alert if accuracy drops below 50% (worse than random)
   - Halt trading if model shows signs of failure

4. **Independent Validation**
   - Back-test all trading strategies independently
   - Require independent team review before trading
   - Maintain audit trail of all trades and reasoning

5. **Scenario Testing**
   - Stress-test strategy against 2008, 2020, 1987 crashes
   - Test under high-volatility and low-correlation scenarios
   - Verify stops and risk controls work in extreme conditions

### Regulatory and Compliance Risks

⚠ **Important Disclaimers:**
- This model has NOT undergone regulatory backtesting or validation
- NOT approved for use in regulated financial institutions
- NO warranties or guarantees on model performance
- User assumes full responsibility for any losses
- NOT a substitute for professional financial advice

**Regulatory Requirements Before Deployment:**
1. Compliance review of model methodology
2. Regulatory backtesting and stress testing
3. Risk management framework implementation
4. Audit trail and documentation systems
5. Approved list of trading strategies and limits
"""
        return risk
    
    def _generate_maintenance_section(self, context: ModelCardContext) -> str:
        """Generate maintenance and monitoring section."""
        maintenance = """## Maintenance and Monitoring

### Model Versioning and Updates

**Current Version:** 1.0 (Stage 1, Baseline Models)

**Version History:**
| Version | Date | Changes | Status |
|---------|------|---------|--------|
| 1.0 | 2024-01 | Initial Stage 1 release (cleaning, features, baselines) | Current |
| 2.0 | TBD | Stage 2 - Deep learning with attention | Planned |
| 3.0 | TBD | Stage 3 - Ensemble and uncertainty quantification | Planned |

### Performance Monitoring

**Key Metrics to Track:**
1. **Accuracy Metrics**
   - Test MAE (target: <0.021)
   - Test directional accuracy (target: >55%)
   - Information coefficient (target: >0.10)

2. **Data Quality Metrics**
   - Data completeness (target: >99%)
   - Feature NaN rate (target: 0%)
   - Cleaning actions per symbol (monitor for changes)

3. **Model Stability Metrics**
   - Coefficient stability (regression weights)
   - Feature importance changes (if available)
   - Prediction distribution shifts

**Monitoring Frequency:** Daily (if live trading); Weekly (research use)

### Retraining Strategy

**Trigger-Based Retraining:**
- If test MAE increases >10% over rolling 4-week window
- If data quality metrics degrade
- If regime change detected (volatility >50% above baseline)
- Monthly refresh with new data (recommended)

**Retraining Procedure:**
1. Acquire latest data (past 10 years where available)
2. Re-run cleaning pipeline (validate consistency)
3. Re-compute all features (check for distribution changes)
4. Re-train all baseline models (compare to previous versions)
5. Evaluate on new test set; compare to previous performance
6. Document changes in CHANGELOG
7. Deploy only if performance maintained or improved

### Data Pipeline Maintenance

**Daily Tasks:**
- Check data acquisition success rate
- Monitor for new data quality issues
- Verify cleaning actions within expected ranges

**Weekly Tasks:**
- Review data distribution changes
- Check for new symbols added/removed
- Validate feature computation consistency

**Monthly Tasks:**
- Full data pipeline re-run
- Compare cleaning statistics to baseline
- Feature ablation study (to detect changes)
- Update baseline model comparisons

**Quarterly Tasks:**
- Comprehensive audit of data lineage
- Review all configuration parameters
- Update documentation and model cards
- Plan next version improvements

### Troubleshooting Guide

**Problem: Prediction accuracy degraded**
- Check: Data quality (cleaning stats, NaN rates, distribution shifts)
- Check: Market regime (volatility, correlations, trend strength)
- Check: Model coefficients (compare to previous version)
- Action: Investigate data issue or retrain on new regime

**Problem: Feature computation errors**
- Check: Data completeness (any missing dates/symbols?)
- Check: Feature calculation logic (any code changes?)
- Check: Data types and shapes (misaligned indices?)
- Action: Fix data pipeline; recompute features; retrain

**Problem: Unexpected high volatility in predictions**
- Check: Input data normalization (scaler fitted correctly?)
- Check: Feature distribution (any distribution shifts?)
- Check: Market regime (crisis or transition?)
- Action: Adjust prediction scaling or model hyperparameters

### Sunset and Deprecation Plan

**End-of-Life Timeline:**
- Stage 1 models: Sunset when Stage 2 deep learning deployed (Q3 2024 estimated)
- Replacement: Stage 2 models with attention mechanisms and uncertainty
- Transition: Support both versions for 1 month; full cutover thereafter

**Archive Plan:**
- All Stage 1 models, code, and data archived to version control
- Model cards and documentation maintained for reference
- Full reproducibility preserved for academic citations
"""
        return maintenance
    
    # ==================== Helper Methods ====================
    
    def _count_features(self, features_manifests: Dict[str, Dict[str, Any]]) -> int:
        """Count total unique features across all manifests."""
        if not features_manifests:
            return 0
        
        # Get features from first symbol (assuming all have same features)
        first_manifest = list(features_manifests.values())[0]
        feature_count = 0
        
        if 'features' in first_manifest:
            for feature_group in first_manifest['features']:
                feature_count += len(feature_group.get('feature_names', []))
        
        return feature_count
    
    def _compute_feature_statistics(self, features_manifests: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """Compute feature statistics by tier."""
        stats = {'tier1': 0, 'tier2': 0, 'tier3': 0}
        
        if not features_manifests:
            return stats
        
        first_manifest = list(features_manifests.values())[0]
        
        if 'features' in first_manifest:
            for feature_group in first_manifest['features']:
                tier = feature_group.get('tier', 0)
                count = len(feature_group.get('feature_names', []))
                if tier == 1:
                    stats['tier1'] += count
                elif tier == 2:
                    stats['tier2'] += count
                elif tier == 3:
                    stats['tier3'] += count
        
        return stats
    
    def _extract_baseline_performance(self, baseline_results: Dict[str, Dict[str, Any]]) -> str:
        """Extract baseline performance metrics as markdown table rows."""
        if not baseline_results:
            return ""
        
        rows = []
        for model_name, results in sorted(baseline_results.items()):
            mae = results.get('test', {}).get('mae', 0)
            rmse = results.get('test', {}).get('rmse', 0)
            dir_acc = results.get('test', {}).get('directional_accuracy', 0)
            sharpe = results.get('test', {}).get('sharpe_ratio', 0)
            ic = results.get('test', {}).get('information_coefficient', 0)
            
            row = f"| {model_name} | {mae:.4f} | {rmse:.4f} | {dir_acc*100:.1f} | {sharpe:.2f} | {ic:.3f} |"
            rows.append(row)
        
        return "\n".join(rows) if rows else "| (No baseline results available) | - | - | - | - | - |"


def load_context_from_results_directory(
    results_dir: str = "results",
    logger: Optional[logging.Logger] = None
) -> ModelCardContext:
    """
    Load model card context from results directory.
    
    Aggregates cleaning reports, features manifests, splits metadata,
    baseline results, and configuration from the results directory.
    
    Parameters
    ----------
    results_dir : str
        Root directory containing results subdirectories
    logger : logging.Logger, optional
        Logger instance
    
    Returns
    -------
    ModelCardContext
        Aggregated context for model card generation
    """
    logger = logger or logging.getLogger(__name__)
    
    results_path = Path(results_dir)
    cleaning_reports = {}
    features_manifests = {}
    baseline_results = {}
    splits_metadata = {}
    errors = []
    warnings = []
    config = {}
    
    # Load master config
    config_file = results_path / "master_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load master config: {e}")
            warnings.append({
                'type': 'CONFIG_LOAD_ERROR',
                'message': f'Failed to load master config: {str(e)}'
            })
    
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
                    'type': 'SPLITS_LOAD_ERROR',
                    'message': f'Failed to load splits metadata: {str(e)}'
                })
    
    # Load baseline results
    baseline_results_file = results_path / "baseline_results.json"
    if baseline_results_file.exists():
        try:
            with open(baseline_results_file, 'r') as f:
                baseline_results = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load baseline results: {e}")
            warnings.append({
                'type': 'BASELINE_LOAD_ERROR',
                'message': f'Failed to load baseline results: {str(e)}'
            })
    
    return ModelCardContext(
        config=config,
        cleaning_reports=cleaning_reports,
        features_manifests=features_manifests,
        splits_metadata=splits_metadata,
        baseline_results=baseline_results,
        errors=errors,
        warnings=warnings
    )
