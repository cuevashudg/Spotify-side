# Phase 3: Tune Signal Weights - Complete Guide

## Overview

This phase adjusts the scoring thresholds in individual signals so that:
- **Confidence distribution** is varied (not always 33% or 80%)
- **Secondary behaviors** appear 40-60% of the time
- **Evidence** is specific and meaningful

---

## Workflow

### Step 1: Run Baseline Analysis

Get current performance on your recent sessions:

```bash
python scripts/phase3_tune_weights.py --sample 30
```

This will:
- Load your listening history
- Group tracks into sessions
- Classify each with current signals
- Print a baseline report with metrics

**Sample Output:**
```
📊 Analyzing 30 sessions...
  [1/30] 2026-02-09 06:39 | routine_driven  (50%) | 15 tracks
  [2/30] 2026-02-09 07:50 | comfort_seeking (81%) | 6 tracks
  ...

📊 OVERALL ACCURACY: 0%
📈 CONFIDENCE DISTRIBUTION:
   Mean: 64%
   Stdev: 17%
   Range: 50% - 81%
   ✅ Good variance in confidence distribution
```

**Key Metrics to Track:**
- **Mean Confidence**: Should be 60-75% (varies by behavior)
- **Stdev**: Should be > 10% (not too uniform)
- **Range**: Should span from ~30% to ~90%
- **Secondary Frequency**: Target 40-60%

---

### Step 2: Manual Classification (Interactive Mode)

Train the tuner with manual labels of what each session SHOULD be:

```bash
python scripts/phase3_tune_weights.py --interactive --sample 20
```

For each session, you'll see:

```
---
Session: 2026-02-09T06:39

Duration: 32 min | Tracks: 15
Predicted: routine_driven (50%)
Secondary: comfort_seeking (40%)
Evidence: Regular session length, Elevated replay rate: 33% vs baseline 15%

Does this feel RIGHT? (y/n):
```

**Classification Guide:**

| Behavior | Indicators |
|----------|-----------|
| **ruminating** | Late night (22:00-03:00) + replay loops |
| **comfort_seeking** | High replay rate, familiar patterns |
| **searching** | Many context switches, high skip rate |
| **focused** | 60-90 min, low interruption, low replay |
| **zoning_out** | 90+ min passive listening |
| **casual** | Normal, balanced patterns |
| **anomaly_detected** | Large deviations from baseline |

---

### Step 3: Analyze Mismatches

After classification, the report shows:

```
❌ MISMATCHES (5):
   [ Predicted: routine_driven ]
      → comfort_seeking (conf 50%) "Elevated replay rate: 33% vs baseline 15%"
      → comfort_seeking (conf 50%) "Regular session length"
      → searching (conf 45%) "High context switching: 3"
```

**This is the tuning roadmap!**

---

## Signal Adjustment Guide

Each signal in `behavior_signals.py` has tunable thresholds. Here's how to adjust them:

### 1. LateNightSignal

**Current Logic:**
```python
LATE_NIGHT_START = 22
LATE_NIGHT_END = 3
late_night_score = 0.7 * replay_factor  # Base 0.7
```

**If ruminating misses some sessions:**
- Lower the base score (0.7 → 0.6)
- Reduce replay_factor dependency

**If ruminating triggers too easily:**
- Require higher replay_factor
- Add additional condition (e.g., require 2+ hours listening)

---

### 2. ReplaySignal

**Current Logic:**
```python
replay_deviation = replay_rate - baseline_replay
comfort_score = 0.5 + (normalized_deviation * 0.4)  # 0.5-0.9 range
```

**If comfort_seeking misses:**
- Lower the floor (0.5 → 0.4)
- Increase deviation multiplier (0.4 → 0.5)

**If comfort_seeking triggers on barely-elevated replay:**
- Increase the floor (0.5 → 0.6)
- Require deviation > threshold first

---

### 3. SessionLengthSignal

**Current Logic:**
```python
FOCUSED_SESSION_MINUTES = 60
ZONING_OUT_MINUTES = 90
focus_score = min(duration / (self.FOCUSED_SESSION_MINUTES * 2), 0.9)
```

**If focused appears less often:**
- Lower FOCUSED_SESSION_MINUTES (60 → 45)
- Increase base score

**If zoning_out is too common:**
- Raise ZONING_OUT_MINUTES (90 → 120)
- Add requirement for context switches (low activity = passive)

---

### 4. ContextSwitchSignal

**Current Logic:**
```python
switch_factor = min(switches / max(baseline_switches * 2, 3), 1.0)
search_score = 0.6 + (switch_factor * 0.3)  # 0.6-0.9
```

**If searching underdetected:**
- Lower baseline multiplier (2 → 1.5)
- Increase base score (0.6 → 0.7)

**If searching triggers too easily:**
- Require higher multiplier (2 → 3)
- Add skip rate condition

---

## Example Tuning Session

**Problem:** Confidence always 50% or 80%, need more variance

**Step 1:** Run analysis
```bash
python scripts/phase3_tune_weights.py --sample 30
```

**Step 2:** Check distribution
```
Histogram:
  30%: (0)
  50%: ████ (4)     ← Cluster here
  70%: █ (1)
  80%: ███ (3)      ← And here
  90%: (0)
```

**Step 3:** Identify the issue
- Too many 50% means signals compete equally
- Too many 80% means one signal dominates

**Step 4:** Adjust thresholds
In `ReplaySignal.evaluate`:
```python
# OLD: 0.5 + (deviation * 0.4) → range 0.5-0.9
# NEW: Different ranges for different signals
if normalized_deviation < 0.3:
    comfort_score = 0.35  # Lower for mild elevation
elif normalized_deviation < 0.6:
    comfort_score = 0.60
else:
    comfort_score = 0.85  # High for major elevation
```

**Step 5:** Re-test
```bash
python scripts/phase3_tune_weights.py --sample 30
```

Check that confidence now spreads across 30%-90% range

---

## Key Tuning Principles

### 1. **Avoid Equal Scores**
If multiple signals fire with same score, they tie and confidence = 0.50.

```python
# BAD: All signals return scores 0.0-1.0 uniformly
# GOOD: Different ranges per signal
LateNightSignal: 0.6-0.9
ReplaySignal: 0.4-0.75
SessionLengthSignal: 0.3-0.85
```

### 2. **Normalize by Deviation**
Don't just count occurrences—measure how far from baseline:

```python
# GOOD
deviation = (current_value - baseline) / baseline
score = base + (deviation * multiplier)

# BAD  
score = 1.0 if current > baseline else 0.0
```

### 3. **Allow Behavioral Competition**
Multiple behaviors can compete; secondaries capture nuance:

```python
# GOOD: Both behaviors score, one wins
"ruminating": 0.7
"comfort_seeking": 0.6

# BAD: Only first signal matters
"ruminating": 0.95
"comfort_seeking": 0.05
```

### 4. **Secondary Behavior Thresholds**
Control when secondaries appear (target 40-60%):

```python
# SHOW secondary if:
# - Its score > 0.3, AND
# - It's close to primary (not too far behind)
if secondary_score > 0.3 and (primary_score - secondary_score) < 0.2:
    include_secondary = True
```

---

## Metrics to Track

### Confidence Distribution
```
Mean:        60-75% (varies)
Stdev:       >10% (avoid clustering)
Range:       25%-95% (broad spread)
Mode:        No heavy clustering at single value
```

### Secondary Behavior Frequency
```
Current:     40-60% target
Too low:     Raise secondary thresholds
Too high:    Lower secondary thresholds or increase primary scores
```

### State Distribution
```python
# Track how often each behavior is PREDICTED (not actual)
routine_driven: 40-50% (most common)
comfort_seeking: 15-25%
focused: 10-20%
searching: 5-10%
zoning_out: 5-10%
ruminating: 3-8%
```

### Mismatch Patterns
```
If routine_driven predicted but comfort_seeking expected:
→ Replay signal scoring too low
→ Increase replay_score floor

If comfort_seeking predicted but searching expected:
→ Context switches not being weighted enough
→ Increase search_score or add bonus for multiple switches
```

---

## Save & Compare Results

Each run saves results to `phase3_analysis.json`:

```bash
# Run 1: Baseline
python scripts/phase3_tune_weights.py --sample 30 --output baseline.json

# Adjust signals...

# Run 2: After tuning
python scripts/phase3_tune_weights.py --sample 30 --output tuned.json
```

**Compare:**
```python
import json

baseline = json.load(open("baseline.json"))
tuned = json.load(open("tuned.json"))

print(f"Confidence variance improved: {baseline['metrics']['confidence']['stdev']:.2f} → {tuned['metrics']['confidence']['stdev']:.2f}")
print(f"Secondary frequency: {baseline['metrics']['secondary_behaviors']['frequency']:.0%} → {tuned['metrics']['secondary_behaviors']['frequency']:.0%}")
```

---

## Quick Reference: Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Always 50% confidence | Signals tie equally | Differentiate score ranges |
| Only 80% confidence | One signal dominates | Reduce its base score |
| No secondaries | Thresholds too high | Lower threshold to 0.2-0.3 |
| Too many secondaries | Thresholds too low | Raise to 0.4+ |
| Wrong predictions | Signal logic off | Recalibrate thresholds or add conditions |
| Generic evidence | Missing detail extraction | Add specific metrics to evidence strings |

---

## Final Checklist

- [ ] Run `--sample 30` to get baseline metrics
- [ ] Identify which metrics are off
- [ ] Run `--interactive` on 20-30 sessions
- [ ] Get accuracy target: 70-80%
- [ ] Review mismatch patterns
- [ ] Adjust 1-2 signals at a time
- [ ] Re-test and compare JSON results
- [ ] Iterate until comfortable with output
- [ ] Run full history (no --sample) for final tuning

Good luck with tuning! 🎵
