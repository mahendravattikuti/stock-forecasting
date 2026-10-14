# Stock Market Forecasting System - Troubleshooting Guide

Welcome to the troubleshooting guide for the Stock Market Forecasting System. This document provides comprehensive guidance for diagnosing and resolving issues that may occur during pipeline execution.

## Table of Contents

1. [Common Error Patterns](#common-error-patterns)
2. [Error Messages Quick Reference](#error-messages-quick-reference)
3. [Debug Workflow by Phase](#debug-workflow-by-phase)
4. [FAQ](#faq)
5. [Known Issues & Workarounds](#known-issues--workarounds)
6. [Getting Help](#getting-help)

---

## Common Error Patterns

### Pattern 1: Data Acquisition Failures

**Error:** `Failed to fetch {symbol} after 3 attempts`

**Causes:**
- IEX Cloud API token invalid or expired
- Network connection issues
- Symbol not found or delisted
- Rate limiting exceeded

**Diagnosis Steps:**

1. **Check IEX_CLOUD_TOKEN environment variable:**
   ```bash
   echo $IEX_CLOUD_TOKEN
   # Should output your API token (not empty)
   ```

2. **Verify internet connection:**
   ```bash
   ping api.iexcloud.io
   # Should show successful responses with latency
   ```

3. **Check token validity at https://iexcloud.io/console**
   - Log in to IEX Cloud dashboard
   - Verify token is active and has available API calls

4. **Verify symbol is valid:**
   - Check if symbol trades on NYSE/NASDAQ/AMEX
   - Try symbol in yfinance: `python -c "import yfinance; print(yfinance.download('{symbol}', start='2014-01-01', end='2024-01-19'))"`

5. **Check acquisition logs:**
   ```bash
   tail -f logs/pipeline_*.log
   # Look for IEX Cloud request/response details
   ```

**Resolution:**

- **For invalid token:** 
  - Generate new token at https://iexcloud.io
  - Update `.env` file: `IEX_CLOUD_TOKEN=your_new_token`
  - Or set environment: `export IEX_CLOUD_TOKEN=your_new_token`

- **For network issues:**
  - Check VPN/proxy settings
  - Try fallback source (yfinance)
  - Retry after waiting

- **For delisted symbols:**
  - Remove from symbol list in `master_config.json`
  - Or set `data_acquisition.skip_invalid_symbols=true` to skip automatically

- **For rate limiting:**
  - Increase retry delay: `data_acquisition.retry_backoff_factor=4`
  - Reduce concurrent requests or add request throttling

---

### Pattern 2: Insufficient Data

**Error:** `Insufficient data: {N} trading days, need 2500`

**Causes:**
- Symbol has less than 10 years of history
- Data source incomplete for symbol
- Date range too narrow
- Recent IPO or newly listed symbol

**Diagnosis Steps:**

1. **Check actual trading days in yfinance:**
   ```python
   import yfinance as yf
   data = yf.download('{symbol}', start='2014-01-01', end='2024-10-12')
   print(f"Trading days: {len(data)}")
   print(f"Date range: {data.index[0]} to {data.index[-1]}")
   ```

2. **Verify data source has sufficient history:**
   - Check IEX Cloud API documentation for symbol
   - Check Yahoo Finance directly for symbol

3. **Check for delisting or recent IPO:**
   - Search company name + "IPO date" or "delisted"
   - Check NASDAQ/NYSE listing announcements

**Resolution:**

- **For recent IPO:** 
  - Adjust `min_trading_days` threshold in `master_config.json` (not recommended, may affect model)
  - Or exclude symbol from analysis for this phase

- **For incomplete data:**
  - Use fallback source if available
  - Exclude symbol from analysis
  - Check if multiple data sources can be combined

- **For date range issues:**
  - Extend `start_date` in `master_config.json` (default 2014)
  - Or reduce `lookback_years` if adequate data exists for shorter period

---

### Pattern 3: Data Cleaning Issues

**Error:** `No data after cleaning` or `Data cleaning complete: 0/{N} symbols`

**Causes:**
- Cleaning rules too aggressive (remove >95% of data)
- Data quality too poor
- OHLC relationship violations across entire dataset
- Missing data (all NaN)

**Diagnosis Steps:**

1. **Check cleaning report for each symbol:**
   ```bash
   cat results/cleaning_reports/{SYMBOL}_cleaning_report.json | jq .
   ```

2. **Review "cleaning_actions" section:**
   - How many rows forward-filled?
   - How many spikes removed?
   - How many OHLC violations corrected?

3. **Compare raw vs. cleaned statistics:**
   - Check `raw_data_stats.total_rows` vs `cleaned_data_stats.total_rows_retained`
   - If retention < 5%, data quality is too poor

4. **Look at "quality_assessment":**
   ```bash
   cat results/cleaning_reports/{SYMBOL}_cleaning_report.json | jq '.quality_assessment'
   ```

**Resolution:**

- **For aggressive cleaning:**
  - Reduce `spike_threshold` in `master_config.json` (default 0.20 = ±20%)
  - Try `spike_threshold: 0.30` to be less aggressive
  - Review spikes in cleaning report to see what's being removed

- **For poor quality data:**
  - Relax `min_completeness` threshold in cleaning config
  - Increase `max_forward_fill_days` (default 2) to allow longer gaps
  - Or exclude symbol if quality is unacceptable

- **For OHLC violations:**
  - Check original data source for errors
  - Try with fallback data source
  - If violations are systematic, may indicate data quality issue

- **For missing data:**
  - Increase `max_forward_fill_days` to fill longer gaps
  - Or use data imputation (if implemented)
  - Or exclude symbol if gaps are too large

---

### Pattern 4: Feature Engineering Failures

**Error:** `NaN detected in critical feature` or feature computation fails

**Causes:**
- Insufficient lookback window (e.g., RSI needs 14 days)
- Data has gaps preventing rolling calculations
- Features for first N rows will be NaN (expected)
- Look-ahead bias in feature computation

**Diagnosis Steps:**

1. **Check feature manifest for specific symbol:**
   ```bash
   cat results/features_manifests/{SYMBOL}_features_manifest.json | jq '.features'
   ```

2. **Count NaN values per feature:**
   ```bash
   cat results/features_manifests/{SYMBOL}_features_manifest.json | jq '.data_quality'
   ```

3. **Check if NaN only at beginning or scattered:**
   - Expected: NaN in first N rows only (where N = max lookback period)
   - Problem: NaN scattered throughout or after first N rows

4. **Verify rolling window calculations don't use future data:**
   - Search for `.shift()` with negative values (would indicate look-ahead)
   - Check that all rolling windows use `shift()` to avoid future data

**Resolution:**

- **For insufficient lookback (NaN at start):**
  - This is expected. RSI needs 14 periods, Bollinger Bands need 20, etc.
  - First N rows will have NaN. This is normal.
  - Features start being valid after lookback period

- **For scattered NaN:**
  - This indicates a problem in cleaned data
  - Go back to Pattern 3 (Data Cleaning Issues)
  - Check if missing values weren't properly filled

- **For look-ahead bias:**
  - Review feature implementation code
  - Verify all rolling calculations use only past data
  - Check for `.shift()` with negative values (bug)

---

### Pattern 5: Data Splitting Issues

**Error:** `Data for {symbol} is empty` or `ValueError: At least three unique timestamps required`

**Causes:**
- No data survived cleaning step
- After feature engineering, data reduced too much
- All data concentrated in one split
- No feature data to split

**Diagnosis Steps:**

1. **Check splits metadata:**
   ```bash
   cat results/splits_metadata/split_metadata.json | jq '.splits'
   ```

2. **Look at row_count per split:**
   - Should see train_count >> val_count >> test_count (roughly 70/15/15)
   - If any split is 0, there's a problem

3. **Check date ranges are properly separated:**
   ```bash
   cat results/splits_metadata/split_metadata.json | jq '.date_ranges'
   ```

4. **Verify temporal integrity:**
   ```bash
   cat results/splits_metadata/split_metadata.json | jq '.temporal_integrity_verified'
   # Should show true
   ```

**Resolution:**

- **For empty data:**
  - Symbol didn't survive cleaning phase
  - Debug using Pattern 3 (Data Cleaning Issues)
  - Check if symbol should be excluded from analysis

- **For data concentration:**
  - Check if train/val/test split ratio is correct
  - Verify split dates make sense for your data range
  - Check if some symbols have shorter history than others

- **For date range issues:**
  - Extend data collection window in `master_config.json`
  - Increase lookback years or change start_date
  - Verify all symbols have sufficient history

---

### Pattern 6: Preprocessing/Standardization Issues

**Error:** `Scaler fit on validation data - possible data leakage`

**Causes:**
- StandardScaler fit on wrong data split
- Scaler parameters same for train and validation (indicates leakage)
- Train-only fitting not enforced

**Diagnosis Steps:**

1. **Check preprocessing logs:**
   ```bash
   grep -i "scaler\|standardscaler" logs/pipeline_*.log
   ```

2. **Verify scaler artifact exists:**
   ```bash
   ls -la reproducibility_artifacts/v1_scalers.joblib
   ```

3. **Compare scaler parameters:**
   - If train and validation scalers have identical mean/std → leakage
   - Scalers should only be fit on training data

**Resolution:**

- **For leakage:**
  - Ensure scaler is ONLY fit on training data
  - Implementation: `StandardScaler.fit(train_data, split_name='train')`
  - Apply without refitting to validation/test: `StandardScaler.transform(val_data)`

- **Fix code pattern:**
  ```python
  # CORRECT: Fit on training only
  scaler = StandardScaler()
  scaler.fit(train_features)
  
  # Apply to all splits without refitting
  train_scaled = scaler.transform(train_features)
  val_scaled = scaler.transform(val_features)
  test_scaled = scaler.transform(test_features)
  
  # WRONG: This causes leakage
  # scaler.fit(train_features)  # OK
  # scaler.fit(val_features)     # BAD - refitting on val data
  ```

---

### Pattern 7: Baseline Model Training Failures

**Error:** `Failed to train {model_name}` or missing baseline_results.json

**Causes:**
- Insufficient training data
- NaN in input features
- ARIMA fails with non-stationary data
- Ridge regression CV fails

**Diagnosis Steps:**

1. **Check baseline results:**
   ```bash
   cat results/reports/baseline_results.json | jq '.results'
   ```

2. **Look for error messages per model:**
   ```bash
   cat results/reports/baseline_results.json | jq '.errors'
   ```

3. **Check training data shape and NaN count:**
   ```bash
   cat results/splits_metadata/split_metadata.json | jq '.splits.train_rows'
   ```

4. **Verify close prices are valid for ARIMA:**
   - Check if close prices have NaN values
   - Check if close prices are stationary (no strong trend)

**Resolution:**

- **For insufficient data:**
  - Use longer training period (extend date range)
  - Reduce number of features if overfitting is an issue

- **For NaN in features:**
  - Debug using Pattern 4 (Feature Engineering Failures)
  - Go back to data cleaning step

- **For ARIMA non-stationarity:**
  - Try differencing: `order=(1, 1, 1)` (default)
  - Check data has no permanent trend that breaks ARIMA assumptions

- **For CV failures:**
  - Increase number of CV splits (default 5)
  - Reduce hyperparameter search space
  - Check if training data is too small for CV

---

### Pattern 8: Report Generation Failures

**Error:** `Report generation failed` or missing pipeline_execution_report.md

**Causes:**
- No valid baseline results
- Missing context data
- Report template issues

**Diagnosis Steps:**

1. **Check if baseline_results.json exists and is valid:**
   ```bash
   cat results/reports/baseline_results.json | jq '.' 2>&1
   # If error, JSON is invalid
   ```

2. **Verify split_metadata.json is populated:**
   ```bash
   cat results/splits_metadata/split_metadata.json | jq '.splits'
   ```

3. **Check logs for report generation errors:**
   ```bash
   grep -i "report\|generation" logs/pipeline_*.log | tail -20
   ```

**Resolution:**

- **For missing results:**
  - Verify all previous phases completed successfully
  - Check if baselines trained correctly (Pattern 7)

- **For invalid JSON:**
  - Check JSON schema against design specs
  - Use `jq` to validate: `jq '.' file.json`

- **For template issues:**
  - Verify report generator config is correct
  - Check report template exists and is readable

---

## Error Messages Quick Reference

| Error | Phase | Common Cause | Quick Fix |
|-------|-------|--------------|-----------|
| `Failed to fetch {symbol} after 3 attempts` | Acquisition | Invalid API token or network issue | Check IEX_CLOUD_TOKEN, verify internet connection |
| `Insufficient data: {N} trading days, need 2500` | Validation | Symbol too new or insufficient history | Exclude or lower threshold in config |
| `No data after cleaning` | Cleaning | Aggressive cleaning rules or poor data quality | Reduce spike_threshold, relax min_completeness |
| `NaN detected in critical feature` | Features | Expected at start (lookback period) | Check if only first N rows affected |
| `Data for {symbol} is empty` | Splitting | No data survived cleaning | Debug cleaning phase, check exclusion reasons |
| `Scaler fit on validation data - possible leakage` | Preprocessing | Scaler fit on wrong split | Ensure scaler fit ONLY on training data |
| `Failed to train baseline` | Baselines | Poor data quality or insufficient training data | Check feature NaN count, increase training period |
| `Report generation failed` | Reporting | Missing artifacts or invalid JSON | Verify all prior phases completed |

---

## Debug Workflow by Phase

### Phase 1: Data Acquisition

**Debugging sequence:**

```
1. Check master_config.json data_acquisition section
   - cat master_config.json | jq '.data_acquisition'
   
2. Verify IEX_CLOUD_TOKEN is set
   - echo $IEX_CLOUD_TOKEN
   
3. Test symbol with yfinance
   - python -c "import yfinance as yf; print(yf.download('AAPL', start='2014-01-01'))"
   
4. Check logs for acquisition errors
   - tail -100 logs/pipeline_*.log | grep -i "iex\|acquisition\|error"
   
5. Review acquisition_log in pipeline coordinator
   - Check which symbols acquired successfully
```

**Common fixes:**
- Update IEX token
- Check network/firewall
- Switch to yfinance fallback
- Exclude problematic symbols

---

### Phase 2: Data Cleaning

**Debugging sequence:**

```
1. Check cleaning reports for each symbol
   - ls -la results/cleaning_reports/
   - cat results/cleaning_reports/{SYMBOL}_cleaning_report.json | jq '.cleaned_data_stats'
   
2. Compare raw vs. cleaned statistics
   - jq '.raw_data_stats, .cleaned_data_stats' results/cleaning_reports/{SYMBOL}_cleaning_report.json
   
3. Review cleaning actions
   - jq '.cleaning_actions' results/cleaning_reports/{SYMBOL}_cleaning_report.json
   
4. Check quality assessment
   - jq '.quality_assessment' results/cleaning_reports/{SYMBOL}_cleaning_report.json
   
5. Look at data audit trail
   - cat results/data_audit_trail.json | jq '.transformation_log | length'
```

**Common fixes:**
- Reduce spike_threshold (too aggressive)
- Increase max_forward_fill_days (for gaps)
- Check if symbol should be excluded

---

### Phase 3: Feature Engineering

**Debugging sequence:**

```
1. Check feature manifests
   - ls -la results/features_manifests/
   - cat results/features_manifests/{SYMBOL}_features_manifest.json | jq '.features'
   
2. Count NaN per feature
   - jq '.data_quality.nan_counts' results/features_manifests/{SYMBOL}_features_manifest.json
   
3. Verify computation methods
   - jq '.features[] | {name, computation_method, lookback_period}' results/features_manifests/{SYMBOL}_features_manifest.json
   
4. Check causality verification
   - jq '.features[] | select(.causality_verified == false)' results/features_manifests/{SYMBOL}_features_manifest.json
   
5. Look at error logs
   - grep -i "feature.*error" logs/pipeline_*.log
```

**Common fixes:**
- Check if NaN only at start (expected)
- Verify cleaning phase for scattered NaN
- Check for look-ahead bias in calculations

---

### Phase 4: Data Splitting

**Debugging sequence:**

```
1. Check splits metadata
   - cat results/splits_metadata/split_metadata.json | jq '.splits'
   
2. Verify date ranges
   - jq '.date_ranges' results/splits_metadata/split_metadata.json
   
3. Check temporal integrity
   - jq '.temporal_integrity_verified' results/splits_metadata/split_metadata.json
   
4. Look at row counts per split
   - jq '.splits | {train_rows, val_rows, test_rows}' results/splits_metadata/split_metadata.json
   
5. Verify no overlap
   - Date ranges should be: train_end < val_start < test_start
```

**Common fixes:**
- Extend data collection window
- Check if symbols have sufficient history
- Verify split dates are reasonable

---

### Phase 5: Preprocessing

**Debugging sequence:**

```
1. Verify scaler artifacts exist
   - ls -la reproducibility_artifacts/v1_scalers.joblib
   
2. Check preprocessing logs
   - grep -i "scaler\|standardscaler\|leakage" logs/pipeline_*.log
   
3. Verify scaler fitting
   - Should only be fit on training data
   - Check code: StandardScaler.fit(train_data)
   
4. Test scaler transformation
   - Load scaler, check mean/std
   - Apply to val/test without refitting
   
5. Check for NaN after scaling
   - Should have same NaN pattern as before (after train start)
```

**Common fixes:**
- Ensure scaler fit ONLY on training data
- Don't refit scaler on validation/test
- Check for NaN propagation through scaling

---

### Phase 6: Baseline Models

**Debugging sequence:**

```
1. Check baseline results
   - cat results/reports/baseline_results.json | jq '.results'
   
2. Look for per-model errors
   - jq '.errors' results/reports/baseline_results.json
   
3. Verify training data quality
   - cat results/splits_metadata/split_metadata.json | jq '.splits.train_rows'
   
4. Check feature statistics
   - jq '.data_quality | {mean, std, min, max}' results/features_manifests/{SYMBOL}_features_manifest.json
   
5. Look for model-specific errors
   - grep -i "arima\|ridge\|linear\|random" logs/pipeline_*.log | grep -i "error"
```

**Common fixes:**
- Check feature quality (NaN count, ranges)
- Verify training data is sufficient
- Try different hyperparameters for CV models

---

### Phase 7: Reporting

**Debugging sequence:**

```
1. Check pipeline execution report
   - cat results/reports/pipeline_execution_report.md
   - Look for any error messages or incomplete sections
   
2. Verify all sections populated
   - Should have: data sources, symbols, cleaning summary, feature summary, splits, baselines, metrics
   
3. Check model_card.md
   - cat results/reports/model_card.md
   
4. Review visualizations
   - ls -la results/visualizations/
   
5. Look for report generation errors
   - grep -i "report.*error\|generation.*failed" logs/pipeline_*.log
```

**Common fixes:**
- Verify all prior phases completed
- Check baseline results are valid JSON
- Verify report template is readable

---

## FAQ

### Q: Pipeline runs but produces no output

**A:** Check if any symbols were successfully acquired. If the acquisition step failed for all symbols, the pipeline will exit early.

**Steps to debug:**
1. Check logs: `tail -100 logs/pipeline_*.log | grep -i "acquisition\|symbol"`
2. Verify IEX_CLOUD_TOKEN is set correctly
3. Test with single symbol: `python -c "import yfinance as yf; print(len(yf.download('AAPL', start='2014-01-01')))"`
4. If yfinance works but pipeline doesn't, check configuration

---

### Q: "Data for {symbol} is empty" error

**A:** This typically means no data survived the cleaning phase. The symbol was acquired successfully but was removed during cleaning.

**To investigate:**
1. Check the cleaning report: `cat results/cleaning_reports/{SYMBOL}_cleaning_report.json`
2. Look at the cleaning_actions section to see what was removed
3. Check raw_data_stats vs cleaned_data_stats
4. If too much data was removed, adjust cleaning parameters or exclude symbol

---

### Q: Why do early rows have NaN for features?

**A:** This is expected. Technical indicators have lookback requirements:
- RSI needs 14 periods
- Bollinger Bands need 20 periods
- MACD needs 35 periods (26 for EMA26 + 9 for signal)

The first N rows will be NaN where N is the maximum lookback period. This is normal and expected.

---

### Q: How do I add more symbols?

**A:** Edit `master_config.json` or pass symbols to the pipeline:

```python
# Option 1: Edit master_config.json
# "symbols": {"list": ["AAPL", "MSFT", "GOOGL", "AMZN", ...]}

# Option 2: Pass to pipeline function
pipeline.run(symbols=['AAPL', 'MSFT', 'GOOGL'])
```

**Important:** Symbols must have at least 2,500 trading days (≈10 years) of history.

---

### Q: How do I verify no data leakage?

**A:** Follow these checks:

1. **Temporal integrity:**
   ```bash
   cat results/splits_metadata/split_metadata.json | jq '.temporal_integrity_verified'
   # Should be true
   ```

2. **Scaler fitting:**
   ```bash
   # Scaler should be fit only on training data
   # Check log: "Fitting scaler on training data only"
   ```

3. **Feature causality:**
   ```bash
   # All features should use only past data
   cat results/features_manifests/{SYMBOL}_features_manifest.json | jq '.features[].causality_verified'
   # Should all be true
   ```

4. **Manual verification:**
   - Check that train_end_date < val_start_date < test_start_date
   - Verify all splits have no overlapping dates

---

### Q: Can I use different data sources?

**A:** Yes, by implementing a new DataAdapter:

```python
# In preprocessing/data_acquisition/
class CustomAdapter(DataAdapter):
    def fetch(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # Your custom fetch logic
        pass
    
    def validate_response(self, df: pd.DataFrame) -> bool:
        # Validation logic
        pass
```

Then update `master_config.json` to use your adapter. IEX Cloud is optional—pipeline falls back to yfinance automatically.

---

### Q: How do I debug a specific symbol?

**A:** Run pipeline with single symbol:

```python
pipeline.run(symbols=['AAPL'])
```

Then check logs and reports:
```bash
# Check logs
tail -f logs/pipeline_*.log

# Check cleaning report
cat results/cleaning_reports/AAPL_cleaning_report.json

# Check feature manifest
cat results/features_manifests/AAPL_features_manifest.json

# Check split metadata
cat results/splits_metadata/split_metadata.json
```

---

### Q: What if cleaning removes too much data?

**A:** Adjust cleaning parameters in `master_config.json`:

```json
{
  "data_cleaning": {
    "spike_threshold": 0.30,        // Increase from 0.20 (less aggressive)
    "max_forward_fill_days": 3,     // Increase from 2 (allow longer gaps)
    "min_completeness": 0.80        // Decrease from 0.90 (accept lower quality)
  }
}
```

Then re-run cleaning phase and check new cleaning reports.

---

### Q: Why are some symbols excluded?

**A:** Check `results/exclusion_summary.json`:

```bash
cat results/exclusion_summary.json | jq '.excluded_symbols'
```

Common reasons:
- `insufficient_data`: Symbol has < 2,500 trading days
- `unfillable_gaps`: Too many consecutive missing days
- `data_quality_critical`: Data quality too poor
- `failed_acquisition`: Could not fetch data from any source

---

### Q: How do I handle symbol IPOs or delistings?

**A:** 

**For IPOs (new symbols):**
- If insufficient history: exclude from Stage 1
- Or reduce `min_trading_days` threshold (not recommended)
- Or start with later date (reduce `lookback_years`)

**For delistings (removed symbols):**
- Automatically excluded by validation
- Check `results/exclusion_summary.json` for exclusion reason
- Remove from symbol list to avoid re-processing

---

## Known Issues & Workarounds

### Issue 1: IEX Cloud not accessible

**Symptom:** All symbols fail to acquire from IEX Cloud

**Cause:** IEX Cloud API unreachable or token invalid

**Workaround:**
- IEX Cloud is optional
- Pipeline automatically falls back to yfinance
- Verify yfinance installation: `pip install yfinance`
- Test: `python -c "import yfinance; print(yfinance.download('AAPL'))"`

---

### Issue 2: Some symbols acquire successfully, others fail

**Symptom:** Mixed success—some symbols in results, others missing

**Cause:** Normal behavior. Symbols may have different data availability.

**Action:**
- Review acquisition logs: `grep -i "failed\|skipped" logs/pipeline_*.log`
- Check `results/exclusion_summary.json` for reasons
- May be: insufficient data, delisted, invalid symbol, or network timeout

---

### Issue 3: Data quality too poor for symbol

**Symptom:** Symbol excluded during validation or cleaning phase

**Cause:** Symbol has too many gaps, spikes, or data quality issues

**Action:**
- Symbol will be excluded from analysis (acceptable for Stage 1 MVP)
- Review cleaning report: `cat results/cleaning_reports/{SYMBOL}_cleaning_report.json`
- Future: Could implement data augmentation or cross-symbol transfer learning

---

### Issue 4: Memory usage too high

**Symptom:** Process killed, "Out of memory" error

**Cause:** Processing too many symbols with high-dimensional features

**Workaround:**
- Reduce symbol count: `"max_portfolio_size": 50` in config (default 100)
- Process symbols in batches
- Reduce feature dimensions (disable Tier-3, signal processing)
- Use server with more RAM

---

### Issue 5: Slow pipeline execution

**Symptom:** Pipeline takes very long (hours or days)

**Cause:** Large symbol set, complex features, or slow data source

**Workaround:**
- Reduce symbol count
- Disable optional features (Tier-3, signal processing)
- Use faster data source (local cache)
- Run on machine with more CPU cores
- Implement parallel processing (future enhancement)

---

## Getting Help

### Useful Commands

**Check pipeline logs:**
```bash
tail -100 logs/pipeline_*.log
tail -f logs/pipeline_*.log  # Follow in real-time
grep -i "error\|warning" logs/pipeline_*.log | head -20
```

**Review results:**
```bash
cat results/cleaning_reports/AAPL_cleaning_report.json | jq '.'
cat results/features_manifests/AAPL_features_manifest.json | jq '.data_quality'
cat results/splits_metadata/split_metadata.json | jq '.splits'
cat results/reports/baseline_results.json | jq '.results | keys'
```

**Validate JSON:**
```bash
jq '.' results/cleaning_reports/AAPL_cleaning_report.json
# If error, file is invalid or not found
```

**Test individual components:**
```bash
# Test data acquisition
python -c "import yfinance as yf; print(len(yf.download('AAPL', start='2014-01-01')))"

# Test cleaning
python -m preprocessing.data_cleaning.test_cleaner

# Test features
python -m features.test_tier1_features

# Test baselines
python -m baselines.test_baselines
```

### Reference Documentation

- **Design**: `.kiro/specs/stock-forecasting-system/design.md`
- **Requirements**: `.kiro/specs/stock-forecasting-system/requirements.md`
- **Architecture**: `ARCHITECTURE.md`
- **Data Guide**: `DATA_GUIDE.md`
- **Experiments**: `EXPERIMENTS.md`

### Common Tasks

**Run single symbol for debugging:**
```python
from pipeline import Pipeline
p = Pipeline(config='master_config.json')
p.run(symbols=['AAPL'])
```

**Re-run specific phase:**
```python
from preprocessing import DataCleaner
cleaner = DataCleaner(config)
cleaned_df, report = cleaner.clean_symbol('AAPL', raw_df)
```

**Check configuration:**
```python
from config import ConfigLoader
config = ConfigLoader().load_config('master_config.json')
print(config['data_acquisition'])
```

**Validate outputs:**
```bash
python -m tests.test_pipeline_e2e
```

---

## Quick Troubleshooting Checklist

Use this checklist to systematically debug issues:

- [ ] **Check logs**: `tail logs/pipeline_*.log`
- [ ] **Verify config**: `cat master_config.json | jq '.data_acquisition'`
- [ ] **Check environment**: `echo $IEX_CLOUD_TOKEN`
- [ ] **Review exclusions**: `cat results/exclusion_summary.json`
- [ ] **Check reports**: 
  - [ ] Cleaning reports exist: `ls results/cleaning_reports/`
  - [ ] Feature manifests exist: `ls results/features_manifests/`
  - [ ] Splits metadata exists: `ls results/splits_metadata/`
  - [ ] Baseline results exist: `ls results/reports/baseline_results.json`
- [ ] **Validate JSON**: `jq '.' results/cleaning_reports/SYMBOL_cleaning_report.json`
- [ ] **Test single symbol**: `pipeline.run(symbols=['AAPL'])`
- [ ] **Check data quality**: `jq '.cleaned_data_stats' results/cleaning_reports/SYMBOL_cleaning_report.json`
- [ ] **Verify no leakage**: `jq '.temporal_integrity_verified' results/splits_metadata/split_metadata.json`

---

## Still Stuck?

If you've tried the above steps and still can't resolve your issue:

1. **Review the full error message** - Copy exact error text
2. **Check the logs** - Look for stack traces or additional context
3. **Verify configuration** - Ensure `master_config.json` is valid
4. **Test with single symbol** - Simplify to isolate issue
5. **Review design document** - Check if your usage matches intended design
6. **Check requirements** - Verify your data meets system requirements
7. **Consult the codebase** - Look at implementation details in relevant modules

For reproducible research, always include:
- Error message (exact text)
- Configuration used
- Symbol(s) involved
- Relevant log entries
- Steps to reproduce
