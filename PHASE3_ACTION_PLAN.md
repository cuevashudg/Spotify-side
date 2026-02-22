# Phase 3: Tune Weights - Action Plan

## Current Status ✅

**Baseline Analysis Complete:**
- ✅ Phase 3 tuning framework implemented
- ✅ Session grouping working
- ✅ Signal evaluation system ready
- ✅ Metrics collection enabled
- ✅ Analysis and suggestion tools created

**Baseline Metrics (4 sample sessions):**
- Confidence: 64% mean (17% stdev) - GOOD
- Secondary behaviors: 50% frequency - GOOD
- State distribution: varied across 3 behaviors - GOOD

---

## Next Steps: Manual Tuning Session

### Step 1: Collect Real Classification Data

Run interactive classification on 20-30 recent listening sessions:

```bash
python scripts/phase3_tune_weights.py --interactive --sample 30
```

This will:
1. Show each session's predicted behavior
2. Ask you: "Does this feel RIGHT?"
3. If wrong, ask what it should actually be
4. Track accuracy and mismatches

**Expected time:** 15-20 minutes for 30 sessions

---

### Step 2: Analyze Mismatches

After classification, analyze the results:

```bash
python scripts/phase3_analyze.py phase3_analysis.json --suggest-adjustments
```

This will show:
- Accuracy % (target: 70-80%)
- Confidence distribution (target: varied 30-90%)
- Mismatch patterns (most important!)
- Specific adjustment suggestions for each signal

---

### Step 3: Adjust Signals Based on Mismatches

The analysis will suggest which signals to tune. For example:

```
[ PREDICTED: routine_driven ]
  Happened 5x, but should have been:
    → comfort_seeking (3x, 60%)
    → searching (2x, 40%)

    ➜ Adjustment: ReplaySignal: Lower base score (0.5 → 0.4)
```

Edit the signals in `analysis/behavior_signals.py`:

```python
class ReplaySignal(BehaviorSignal):
    def evaluate(self, session, baseline, all_tracks):
        # OLD: comfort_score = 0.5 + (normalized_deviation * 0.4)
        # NEW: Lower the floor to make it less dominant
        comfort_score = 0.4 + (normalized_deviation * 0.4)  # 0.4-0.8 range
```

---

### Step 4: Validate Adjustments

Re-test after each adjustment:

```bash
# Save baseline
cp phase3_analysis.json baseline.json

# Make signal adjustments...

# Re-run tuning
python scripts/phase3_tune_weights.py --interactive --sample 30 --output tuned.json

# Compare results
python scripts/phase3_analyze.py baseline.json tuned.json --compare
```

---

## Key Signals to Understand

### LateNightSignal
- **What it detects:** Late-night (22:00-03:00) listening patterns
- **Output:** `ruminating` behavior
- **Tuning lever:** Base score (currently 0.7) and replay_factor dependency

### ReplaySignal  
- **What it detects:** Higher replay rate than baseline
- **Output:** `comfort_seeking` (primary), `routine_driven` (secondary)
- **Tuning lever:** Score range (0.5-0.9) and deviation multiplier

### SessionLengthSignal
- **What it detects:** Duration-based patterns
- **Output:** `focused` (60-90 min), `zoning_out` (90+ min), `routine_driven` (fallback)
- **Tuning lever:** FOCUSED_SESSION_MINUTES and score formulas

### ContextSwitchSignal
- **What it detects:** High skip/context changes
- **Output:** `searching` behavior
- **Tuning lever:** Baseline multiplier (currently 2x) and score range

### ConcernSignal
- **What it detects:** Anomalies (deviations from baseline)
- **Output:** `anomaly_detected` behavior
- **Tuning lever:** CONCERN_THRESHOLD and detection logic

---

## Tuning Checklist

- [ ] Run interactive classification on 30 sessions
- [ ] Review analysis report and mismatches
- [ ] Note which signals are over/under-triggering
- [ ] Make 1-2 signal adjustments
- [ ] Re-run and compare (should see improvement)
- [ ] Iterate until 70-80% accuracy
- [ ] Validate confidence distribution is varied
- [ ] Validate secondary behaviors are 40-60%
- [ ] Run full history (no sample) for final metrics
- [ ] Document which adjustments were made

---

## Success Criteria

✅ **Phase 3 Complete When:**

1. **Accuracy:** 70-80% (signals match your intuition)
2. **Confidence:** Mean 60-75%, stdev > 10% (not uniform)
3. **Secondaries:** 40-60% frequency (nuanced output)
4. **States:** Balanced distribution (no single behavior 80+%)
5. **Evidence:** Specific details, not generic
6. **Output:** Feels "right" when reading the narrator's comments

---

## Tools Reference

### Run Analysis
```bash
# Analyze recent sessions
python scripts/phase3_tune_weights.py --sample 30

# Interactive classification (for training data)
python scripts/phase3_tune_weights.py --interactive --sample 30

# Full history analysis
python scripts/phase3_tune_weights.py
```

### Analyze Results
```bash
# Summary and mismatches
python scripts/phase3_analyze.py phase3_analysis.json

# Show adjustment suggestions
python scripts/phase3_analyze.py phase3_analysis.json --suggest-adjustments

# Compare two runs
python scripts/phase3_analyze.py baseline.json tuned.json --compare
```

### Output Files
- `phase3_analysis.json` - Full analysis with all metrics and details
- Takes ~3-5 minutes to analyze 30 sessions

---

## Common Tuning Patterns

### If confidence always 50%
**Problem:** Signals tie equally
**Fix:** Differentiate score ranges
```python
# Make one signal dominant
LateNightSignal: 0.7-0.9  (high)
ReplaySignal: 0.4-0.65    (medium)
SessionLengthSignal: 0.3-0.6  (lower)
```

### If only secondary behaviors shown
**Problem:** Primary signal too weak
**Fix:** Raise primary signal floor
```python
# OLD: score = 0.5 + ...
# NEW: score = 0.65 + ...
```

### If no secondary behaviors
**Problem:** Secondary threshold too high
**Fix:** Lower the threshold in classify_session:
```python
# In BehaviorClassifier.classify_session()
if secondary_behaviors and secondary_behaviors[0][1] > 0.2:  # Lower than 0.3
```

---

## Next Session Recommendation

Once Phase 3 is complete, move to **Phase 4: Enhancement** to add:
- [X] Improved confidence scoring
- [ ] Tone templates for all states  
- [ ] Emergency mode for when signals disagree
- [ ] Custom behavior definitions
- [ ] User feedback loop (thumbs up/down)

---

**Ready to start tuning? Run:**
```bash
python scripts/phase3_tune_weights.py --interactive --sample 30
```

Good luck! 🎵
