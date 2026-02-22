"""
PHASE 3: Tune Signal Weights

Adjust signal scoring thresholds so outputs feel right.

Workflow:
1. Load listening history and group into sessions
2. Classify each with the current classifier
3. Manually classify what it SHOULD be
4. Compare outputs and aggregate statistics
5. Identify which signals need weight adjustment
6. Review metrics:
   - Confidence distribution (should vary 0.3-0.9, not just 0.33/0.8)
   - Secondary behavior frequency (should be 40-60%)
   - Evidence quality (specific > generic)

Usage:
    python scripts/phase3_tune_weights.py [--interactive] [--sample N]
    
    --interactive: Manual classification for each session
    --sample N:    Only analyze N sessions (default: all)
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Track
from analysis.behavior_signals import BehaviorClassifier, BehaviorBaseline


@dataclass
class SessionAnalysis:
    """Analysis of one session: predicted vs actual + metrics"""
    session_id: str
    start_time: str
    duration_minutes: float
    track_count: int
    predicted_state: str
    predicted_confidence: float
    actual_state: Optional[str] = None
    match: bool = False
    notes: str = ""
    
    # For detailed comparison
    predicted_secondary: List[Tuple[str, float]] = None
    predicted_evidence: List[str] = None


class SessionGrouper:
    """Group tracks into listening sessions."""
    
    # Two tracks are in same session if within this time window
    SESSION_GAP_MINUTES = 30  # If gap > 30 min, new session
    
    @classmethod
    def group_tracks(cls, tracks: List[Track]) -> List[List[Track]]:
        """
        Group tracks into sessions based on time gaps.
        
        Args:
            tracks: Sorted list of Track objects
            
        Returns:
            List of session (each session is list of tracks)
        """
        if not tracks:
            return []
        
        sessions = []
        current_session = [tracks[0]]
        
        for track in tracks[1:]:
            time_gap = (track.timestamp - current_session[-1].timestamp).total_seconds() / 60
            
            if time_gap <= cls.SESSION_GAP_MINUTES:
                current_session.append(track)
            else:
                # Start new session
                sessions.append(current_session)
                current_session = [track]
        
        # Don't forget last session
        if current_session:
            sessions.append(current_session)
        
        return sessions


class Phase3Tuner:
    """Main tuning workflow for signal weights."""
    
    def __init__(self, history_path: str):
        """Initialize with track history."""
        self.history_path = Path(history_path)
        self.tracks = self._load_tracks()
        self.classifier = BehaviorClassifier(self.tracks)
        self.sessions = SessionGrouper.group_tracks(self.tracks)
        self.analyses: List[SessionAnalysis] = []
        
    def _load_tracks(self) -> List[Track]:
        """Load tracks from CSV."""
        tracks = []
        
        with open(self.history_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(row["timestamp"])
                except:
                    timestamp = datetime.now()
                
                # Create Track object with minimal required fields
                track = Track(
                    timestamp=timestamp,
                    track_id=row.get("track_id", ""),
                    song_name=row.get("song_name", ""),
                    artist=row.get("artist", ""),
                    album=row.get("album", ""),
                    duration_ms=int(row.get("duration_ms", 0)),
                    duration_formatted=row.get("duration_formatted", "0:00"),
                )
                tracks.append(track)
        
        return sorted(tracks, key=lambda t: t.timestamp)
    
    def analyze_session(self, session_tracks: List[Track]) -> SessionAnalysis:
        """Analyze one session with classifier."""
        if not session_tracks:
            return None
        
        # Classify with current model
        behavior_state = self.classifier.classify_session(session_tracks)
        
        start_time = session_tracks[0].timestamp
        end_time = session_tracks[-1].timestamp
        duration_mins = (end_time - start_time).total_seconds() / 60
        
        analysis = SessionAnalysis(
            session_id=f"session_{start_time.isoformat()}",
            start_time=start_time.isoformat(),
            duration_minutes=duration_mins,
            track_count=len(session_tracks),
            predicted_state=behavior_state.state,
            predicted_confidence=behavior_state.confidence,
            predicted_secondary=behavior_state.secondary_behaviors,
            predicted_evidence=behavior_state.evidence,
        )
        return analysis
    
    def analyze_all_sessions(self, sample_size: Optional[int] = None) -> None:
        """Analyze all (or sample of) sessions."""
        sessions_to_analyze = self.sessions
        if sample_size:
            # Take most recent sessions for tuning
            sessions_to_analyze = self.sessions[-sample_size:]
        
        print(f"\n📊 Analyzing {len(sessions_to_analyze)} sessions...")
        for i, session in enumerate(sessions_to_analyze, 1):
            analysis = self.analyze_session(session)
            if analysis:
                self.analyses.append(analysis)
                print(f"  [{i}/{len(sessions_to_analyze)}] {analysis.start_time[:16]} | "
                      f"{analysis.predicted_state:15} ({analysis.predicted_confidence:.0%}) | "
                      f"{analysis.track_count} tracks")
    
    def interactive_classification(self) -> None:
        """Manually classify predictions for tuning."""
        print("\n🎯 MANUAL CLASSIFICATION")
        print("Marking which behavior predictions feel RIGHT or WRONG\n")
        
        correct = 0
        total = 0
        
        for analysis in self.analyses:
            print(f"\n---")
            print(f"Session: {analysis.start_time[:16]}")
            print(f"Duration: {analysis.duration_minutes:.0f} min | Tracks: {analysis.track_count}")
            print(f"Predicted: {analysis.predicted_state.upper()} ({analysis.predicted_confidence:.0%})")
            if analysis.predicted_secondary:
                secondary_str = ", ".join(f"{s[0]} ({s[1]:.0%})" for s in analysis.predicted_secondary[:1])
                print(f"Secondary: {secondary_str}")
            print(f"Evidence: {', '.join(analysis.predicted_evidence)}")
            
            # Ask for manual classification
            while True:
                response = input("\nDoes this feel RIGHT? (y/n): ").strip().lower()
                if response in ['y', 'n']:
                    analysis.match = (response == 'y')
                    break
            
            if analysis.match:
                correct += 1
            else:
                # If wrong, ask what it should be
                print("\nBehaviors: " + ", ".join(
                    f"{i+1}={b}" for i, b in enumerate([
                        "ruminating", "comfort_seeking", "searching",
                        "focused", "zoning_out", "casual", "anomaly_detected"
                    ])
                ))
                while True:
                    try:
                        choice = input("What should it be? (1-7): ").strip()
                        behaviors = ["ruminating", "comfort_seeking", "searching",
                                    "focused", "zoning_out", "casual", "anomaly_detected"]
                        if 1 <= int(choice) <= 7:
                            analysis.actual_state = behaviors[int(choice) - 1]
                            break
                    except:
                        pass
            
            total += 1
        
        accuracy = correct / total if total > 0 else 0
        print(f"\n✅ Accuracy: {accuracy:.0%} ({correct}/{total} correct)")
    
    def compute_metrics(self) -> Dict:
        """Compute tuning metrics."""
        if not self.analyses:
            return {}
        
        metrics = {
            "total_sessions": len(self.analyses),
            "accuracy": sum(1 for a in self.analyses if a.match) / len(self.analyses),
            
            # Confidence distribution
            "confidence": {
                "values": [a.predicted_confidence for a in self.analyses],
                "mean": statistics.mean(a.predicted_confidence for a in self.analyses),
                "stdev": statistics.stdev(a.predicted_confidence for a in self.analyses) if len(self.analyses) > 1 else 0,
                "min": min(a.predicted_confidence for a in self.analyses),
                "max": max(a.predicted_confidence for a in self.analyses),
                "distribution": self._histogram_confidence(),
            },
            
            # Secondary behavior frequency
            "secondary_behaviors": {
                "frequency": sum(1 for a in self.analyses if a.predicted_secondary) / len(self.analyses),
                "avg_count": statistics.mean(len(a.predicted_secondary or []) for a in self.analyses),
            },
            
            # State distribution
            "state_distribution": self._state_distribution(),
            
            # False predictions (most important for tuning)
            "false_predictions": self._get_false_predictions(),
        }
        
        return metrics
    
    def _histogram_confidence(self) -> str:
        """ASCII histogram of confidence distribution."""
        confidences = [a.predicted_confidence for a in self.analyses]
        bins = defaultdict(int)
        for conf in confidences:
            bin_label = f"{int(conf * 10) * 10}%"
            bins[bin_label] += 1
        
        histogram = ""
        for bin_label in sorted(bins.keys()):
            count = bins[bin_label]
            bar = "█" * count
            histogram += f"  {bin_label}: {bar} ({count})\n"
        
        return histogram
    
    def _state_distribution(self) -> Dict[str, int]:
        """Count predictions per state."""
        dist = defaultdict(int)
        for analysis in self.analyses:
            dist[analysis.predicted_state] += 1
        return dict(dist)
    
    def _get_false_predictions(self) -> List[Dict]:
        """Get analyses where prediction != actual."""
        false_preds = []
        for a in self.analyses:
            if not a.match and a.actual_state:
                false_preds.append({
                    "predicted": a.predicted_state,
                    "actual": a.actual_state,
                    "confidence": a.predicted_confidence,
                    "evidence": a.predicted_evidence,
                    "notes": a.notes,
                })
        return false_preds
    
    def print_report(self) -> None:
        """Print comprehensive tuning report."""
        metrics = self.compute_metrics()
        
        print("\n" + "="*70)
        print("PHASE 3 TUNING REPORT")
        print("="*70)
        
        # Overall accuracy
        print(f"\n📊 OVERALL ACCURACY: {metrics['accuracy']:.0%}")
        print(f"   Sessions analyzed: {metrics['total_sessions']}")
        
        # Confidence distribution
        print(f"\n📈 CONFIDENCE DISTRIBUTION:")
        print(f"   Mean: {metrics['confidence']['mean']:.0%}")
        print(f"   Stdev: {metrics['confidence']['stdev']:.0%}")
        print(f"   Range: {metrics['confidence']['min']:.0%} - {metrics['confidence']['max']:.0%}")
        print(f"\n   Histogram:")
        print(metrics['confidence']['distribution'], end='')
        
        # Check variance
        if metrics['confidence']['stdev'] < 0.1:
            print("   ⚠️  Low variance! Predictions too uniform (all ~33% or ~80%)")
            print("       → Adjust thresholds in individual signals to spread scores")
        else:
            print("   ✅ Good variance in confidence distribution")
        
        # Secondary behavior frequency
        print(f"\n🎯 SECONDARY BEHAVIORS:")
        print(f"   Frequency: {metrics['secondary_behaviors']['frequency']:.0%}")
        print(f"   Avg per session: {metrics['secondary_behaviors']['avg_count']:.1f}")
        if 0.4 <= metrics['secondary_behaviors']['frequency'] <= 0.6:
            print("   ✅ Healthy range (40-60%)")
        else:
            print("   ⚠️  Outside target range (should be 40-60%)")
            if metrics['secondary_behaviors']['frequency'] < 0.4:
                print("       → Secondary thresholds too high, lower them")
            else:
                print("       → Too many secondary behaviors, raise thresholds")
        
        # State distribution
        print(f"\n🔄 STATE DISTRIBUTION:")
        for state, count in sorted(metrics['state_distribution'].items(), key=lambda x: -x[1]):
            pct = count / metrics['total_sessions']
            bar = "█" * int(pct * 20)
            print(f"   {state:20} {bar:20} {count:2d} ({pct:5.0%})")
        
        # False predictions (key for tuning)
        if metrics['false_predictions']:
            print(f"\n❌ MISMATCHES ({len(metrics['false_predictions'])}):")
            print("   These are the key for tuning! Adjust signals based on patterns:\n")
            
            # Group by predicted state
            by_predicted = defaultdict(list)
            for fp in metrics['false_predictions']:
                by_predicted[fp['predicted']].append(fp)
            
            for predicted, items in sorted(by_predicted.items()):
                print(f"   [ Predicted: {predicted} ]")
                actual_counts = defaultdict(int)
                for item in items:
                    actual_counts[item['actual']] += 1
                    conf = item['confidence']
                    print(f"      → {item['actual']:15} (conf {conf:.0%}) {item['evidence'][0][:40]}")
                print()
        else:
            print(f"\n✅ PERFECT! All predictions match manual classifications!")
        
        print("="*70)
    
    def save_analysis(self, output_path: str = "phase3_analysis.json") -> None:
        """Save analysis to JSON for later review."""
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_sessions": len(self.analyses),
            "metrics": self.compute_metrics(),
            "analyses": [asdict(a) for a in self.analyses],
        }
        
        # Convert tuples in secondary_behaviors to lists
        for analysis_dict in output['analyses']:
            if analysis_dict.get('predicted_secondary'):
                analysis_dict['predicted_secondary'] = [
                    [name, score] for name, score in analysis_dict['predicted_secondary']
                ]
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n💾 Analysis saved to {output_path}")
    
    def suggest_adjustments(self) -> None:
        """Suggest signal weight adjustments based on mismatches."""
        metrics = self.compute_metrics()
        false_preds = metrics['false_predictions']
        
        if not false_preds:
            print("\n✅ No adjustment needed!")
            return
        
        print("\n" + "="*70)
        print("SUGGESTED ADJUSTMENTS")
        print("="*70)
        
        # Analyze patterns in false predictions
        by_predicted = defaultdict(list)
        for fp in false_preds:
            by_predicted[fp['predicted']].append(fp)
        
        for predicted, items in sorted(by_predicted.items()):
            actual_counts = defaultdict(int)
            for item in items:
                actual_counts[item['actual']] += 1
            
            total_miss = len(items)
            print(f"\n[ {predicted.upper()} ]")
            print(f"  Predicted this {total_miss} times, but should have been:")
            for actual, count in sorted(actual_counts.items(), key=lambda x: -x[1]):
                pct = count / total_miss
                print(f"    • {actual}: {count}x ({pct:.0%})")
            
            # Suggest which signal to adjust based on the behavior
            print(f"  → Suggestion: Lower threshold for {predicted} signal")
            print(f"               or increase competing signals")
        
        print("\n" + "="*70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3: Tune signal weights")
    parser.add_argument("--interactive", action="store_true", help="Manual classification")
    parser.add_argument("--sample", type=int, help="Number of recent sessions to analyze")
    parser.add_argument("--output", default="phase3_analysis.json", help="Output file")
    
    args = parser.parse_args()
    
    # Initialize tuner
    history_path = "song_history.csv"
    tuner = Phase3Tuner(history_path)
    
    # Analyze sessions
    tuner.analyze_all_sessions(sample_size=args.sample or 30)
    
    # Manual classification if requested
    if args.interactive:
        tuner.interactive_classification()
    else:
        print("\n💡 Tip: Use --interactive to manually classify sessions for training!")
    
    # Print report
    tuner.print_report()
    
    # Suggest adjustments
    if args.interactive:
        tuner.suggest_adjustments()
    
    # Save analysis
    tuner.save_analysis(args.output)


if __name__ == "__main__":
    main()
