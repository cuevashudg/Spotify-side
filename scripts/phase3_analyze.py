"""
Phase 3 Tuning Assistant - Analyze results and suggest adjustments.

Usage:
    python scripts/phase3_analyze.py phase3_analysis.json
    
    Compare two runs:
    python scripts/phase3_analyze.py baseline.json tuned.json --compare
    
    Get specific signal adjustment suggestions:
    python scripts/phase3_analyze.py phase3_analysis.json --suggest-adjustments
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import statistics


class TuningAnalyzer:
    """Analyze Phase 3 tuning results and suggest improvements."""
    
    def __init__(self, analysis_path: str):
        """Load analysis file."""
        with open(analysis_path) as f:
            self.data = json.load(f)
        
        self.metrics = self.data.get('metrics', {})
        self.analyses = self.data.get('analyses', [])
    
    def print_summary(self) -> None:
        """Print summary of analysis."""
        print("\n" + "="*70)
        print("PHASE 3 TUNING ANALYSIS")
        print("="*70)
        
        metrics = self.metrics
        
        # Header stats
        print(f"\n📋 Sessions Analyzed: {metrics.get('total_sessions', 0)}")
        print(f"✅ Accuracy: {metrics.get('accuracy', 0):.0%}")
        
        # Confidence metrics
        conf = metrics.get('confidence', {})
        print(f"\n📊 CONFIDENCE:")
        print(f"   Mean: {conf.get('mean', 0):.0%}")
        print(f"   Stdev: {conf.get('stdev', 0):.0%}")
        print(f"   Range: {conf.get('min', 0):.0%} - {conf.get('max', 0):.0%}")
        
        # Diagnose confidence issues
        stdev = conf.get('stdev', 0)
        if stdev < 0.08:
            print("   ⚠️  LOW VARIANCE - Signals too uniform")
        elif stdev > 0.25:
            print("   ⚠️  HIGH VARIANCE - Signals differ too much")
        else:
            print("   ✅ Good variance")
        
        # Secondary behaviors
        secondary = metrics.get('secondary_behaviors', {})
        freq = secondary.get('frequency', 0)
        print(f"\n🎯 SECONDARY BEHAVIORS:")
        print(f"   Frequency: {freq:.0%}")
        if freq < 0.4:
            print("   ⚠️  TOO LOW - Raise secondary thresholds")
        elif freq > 0.6:
            print("   ⚠️  TOO HIGH - Lower secondary thresholds")
        else:
            print("   ✅ In target range (40-60%)")
        
        print(f"   Avg per session: {secondary.get('avg_count', 0):.1f}")
        
        # State distribution
        print(f"\n🔄 STATE DISTRIBUTION:")
        dist = metrics.get('state_distribution', {})
        for state, count in sorted(dist.items(), key=lambda x: -x[1]):
            pct = count / metrics.get('total_sessions', 1)
            bar = "█" * int(pct * 25)
            print(f"   {state:18} {bar:25} {pct:5.0%}")
    
    def print_mismatches(self) -> None:
        """Print mismatches with analysis."""
        false_preds = self.metrics.get('false_predictions', [])
        if not false_preds:
            print("\n✅ No mismatches! Perfect tuning!")
            return
        
        print(f"\n❌ MISMATCHES ({len(false_preds)}):")
        print("-" * 70)
        
        # Group by predicted state
        by_predicted = defaultdict(list)
        for fp in false_preds:
            by_predicted[fp['predicted']].append(fp)
        
        for predicted, items in sorted(by_predicted.items(), key=lambda x: -len(x[1])):
            actual_counts = defaultdict(int)
            for item in items:
                actual_counts[item['actual']] += 1
            
            print(f"\n[ PREDICTED: {predicted.upper()} ]")
            print(f"  Happened {len(items)}x, but should have been:")
            
            for actual, count in sorted(actual_counts.items(), key=lambda x: -x[1]):
                pct = count / len(items)
                print(f"    →  {actual:15} ({count}x, {pct:.0%})")
                
                # Show evidence for this mismatch
                examples = [it for it in items if it['actual'] == actual][:2]
                for ex in examples:
                    print(f"         Evidence: {ex['evidence'][0][:50]}")
    
    def suggest_signal_adjustments(self) -> None:
        """Suggest specific signal adjustments based on mismatches."""
        false_preds = self.metrics.get('false_predictions', [])
        if not false_preds:
            print("\n✅ No adjustments needed!")
            return
        
        print("\n" + "="*70)
        print("SIGNAL ADJUSTMENT RECOMMENDATIONS")
        print("="*70)
        
        # Analyze mismatch patterns
        by_predicted = defaultdict(lambda: defaultdict(int))
        for fp in false_preds:
            by_predicted[fp['predicted']][fp['actual']] += 1
        
        # Generate suggestions
        suggestions = []
        
        for predicted, actual_map in by_predicted.items():
            dominant_actual = max(actual_map.items(), key=lambda x: x[1])
            actual_state, count = dominant_actual
            total = len([fp for fp in false_preds if fp['predicted'] == predicted])
            
            if total == 0:
                continue
            
            accuracy = count / total
            
            print(f"\n[ {predicted.upper()} ]")
            print(f"  Misclassified {total}x")
            print(f"  → {count}/{total} ({accuracy:.0%}) should be {actual_state}")
            
            # Map signal to suggested adjustment
            signal_map = {
                'routine_driven': {
                    'comfort_seeking': "LateNightSignal: Lower late-night threshold / ReplaySignal: Raise score threshold",
                    'searching': "SessionLengthSignal: Increase baseline threshold",
                    'focused': "SessionLengthSignal: Lower FOCUSED_SESSION_MINUTES"
                },
                'comfort_seeking': {
                    'routine_driven': "ReplaySignal: Lower base score (0.5 → 0.4)",
                    'ruminating': "LateNightSignal: Raise replay_factor requirement",
                    'searching': "ReplaySignal: Add context-switch check"
                },
                'searching': {
                    'routine_driven': "ContextSwitchSignal: Raise baseline multiplier (2 → 3)",
                    'comfort_seeking': "ContextSwitchSignal + ReplaySignal competition needed",
                    'zoning_out': "ContextSwitchSignal: Require context_switches > 2"
                },
                'focused': {
                    'zoning_out': "SessionLengthSignal: Lower FOCUSED_SESSION_MINUTES or add interruption check",
                    'routine_driven': "SessionLengthSignal: Raise focus_score threshold",
                    'comfort_seeking': "ReplaySignal: Lower threshold, compete with focused"
                },
                'zoning_out': {
                    'focused': "SessionLengthSignal: Raise ZONING_OUT_MINUTES (90 → 120)",
                    'routine_driven': "SessionLengthSignal: Add passive behavior detection"
                },
                'ruminating': {
                    'comfort_seeking': "LateNightSignal: Raise base score (0.7 → 0.8)",
                    'routine_driven': "LateNightSignal: Add session-length requirement"
                }
            }
            
            if predicted in signal_map and actual_state in signal_map[predicted]:
                adj = signal_map[predicted][actual_state]
                print(f"  ➜ Adjustment: {adj}")
                suggestions.append((predicted, actual_state, adj))
        
        print("\n" + "="*70)
        print("ADJUSTMENT PRIORITY")
        print("="*70)
        
        # Show by frequency
        print("\nMost common mismatches (fix these first):")
        sorted_suggests = sorted(suggestions, key=lambda x: len(false_preds), reverse=True)
        for i, (pred, actual, adj) in enumerate(sorted_suggests[:5], 1):
            count = sum(1 for fp in false_preds if fp['predicted'] == pred and fp['actual'] == actual)
            print(f"{i}. {pred} → {actual} ({count}x)")
            print(f"   {adj}\n")


def compare_runs(path1: str, path2: str) -> None:
    """Compare two tuning runs."""
    with open(path1) as f:
        data1 = json.load(f)
    with open(path2) as f:
        data2 = json.load(f)
    
    m1 = data1.get('metrics', {})
    m2 = data2.get('metrics', {})
    
    print("\n" + "="*70)
    print(f"COMPARISON: {Path(path1).name} vs {Path(path2).name}")
    print("="*70)
    
    # Accuracy
    acc1 = m1.get('accuracy', 0)
    acc2 = m2.get('accuracy', 0)
    delta = acc2 - acc1
    symbol = "↑" if delta > 0 else "↓" if delta < 0 else "→"
    print(f"\n✅ Accuracy: {acc1:.0%} → {acc2:.0%} {symbol} {delta:+.0%}")
    
    # Confidence
    std1 = m1.get('confidence', {}).get('stdev', 0)
    std2 = m2.get('confidence', {}).get('stdev', 0)
    delta = std2 - std1
    symbol = "↑" if delta > 0 else "↓" if delta < 0 else "→"
    print(f"📊 Stdev: {std1:.0%} → {std2:.0%} {symbol} {delta:+.0%}")
    
    # Secondary frequency
    freq1 = m1.get('secondary_behaviors', {}).get('frequency', 0)
    freq2 = m2.get('secondary_behaviors', {}).get('frequency', 0)
    delta = freq2 - freq1
    symbol = "↑" if delta > 0 else "↓" if delta < 0 else "→"
    print(f"🎯 Secondary frequency: {freq1:.0%} → {freq2:.0%} {symbol} {delta:+.0%}")
    
    print("\n" + "="*70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Phase 3 tuning results")
    parser.add_argument("analysis", help="Analysis JSON file")
    parser.add_argument("comparison", nargs="?", help="Second file for comparison")
    parser.add_argument("--compare", action="store_true", help="Compare two runs")
    parser.add_argument("--suggest-adjustments", action="store_true", help="Show adjustment suggestions")
    
    args = parser.parse_args()
    
    # If comparison file provided, do comparison
    if args.comparison:
        compare_runs(args.analysis, args.comparison)
        return
    
    # Otherwise analyze single file
    analyzer = TuningAnalyzer(args.analysis)
    analyzer.print_summary()
    
    if args.suggest_adjustments or analyzer.metrics.get('false_predictions'):
        analyzer.print_mismatches()
        analyzer.suggest_signal_adjustments()


if __name__ == "__main__":
    main()
