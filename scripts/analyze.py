"""
Unified analysis script - behavioral analysis + personality-driven reports.

Modes:
  Default:     python scripts/analyze.py [--roast]
  Interactive: python scripts/analyze.py --interactive
"""

import sys
import os
import io

# Fix encoding for emojis on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.mood import MoodAnalyzer, load_tracks_from_json
from analysis.habits import HabitsAnalyzer
from analysis.behavior import BehaviorClassifier
from personality.roast_engine import RoastEngine
from personality import Narrator, ToneType


def print_section(title: str, emoji: str = "📊"):
    """Print formatted section header."""
    print("\n" + emoji + " " + title)
    print("=" * 60)


def load_data(json_file: str = "enriched_history.json"):
    """Load and validate data."""
    if not os.path.exists(json_file):
        print(f"\n❌ Error: {json_file} not found")
        print("   Run the collector first: python -m core.collector")
        return None
    
    tracks = load_tracks_from_json(json_file)
    
    if len(tracks) < 5:
        print("\n⚠️  Not enough data yet. Keep listening!")
        return None
    
    return tracks


def behavioral_mode(tracks, savage_mode: bool = False):
    """
    Behavioral analysis report mode (default).
    
    Args:
        tracks: List of Track objects
        savage_mode: If True, includes roasts
    """
    print("\n🧠 BEHAVIORAL ANALYSIS REPORT")
    if savage_mode:
        print("(Roast Mode: ENABLED 🔥)")
    print("=" * 60)
    print(f"✅ Loaded {len(tracks)} tracks\n")
    
    # Initialize analyzers
    habits = HabitsAnalyzer(tracks)
    behavior = BehaviorClassifier(tracks)
    
    # === BEHAVIORAL CLASSIFICATION ===
    print_section("BEHAVIORAL STATE", "🧠")
    
    overall_state = behavior.classify_overall()
    print(f"\nState: {overall_state.state.upper().replace('_', ' ')}")
    print(f"Confidence: {overall_state.confidence:.0%}")
    print(f"Intensity: {overall_state.intensity:.2f}/1.0")
    
    if overall_state.evidence:
        print("\nEvidence:")
        for evidence in overall_state.evidence:
            print(f"  • {evidence}")
    
    # Intensity & deviation
    intensity = behavior.get_intensity_score()
    print(f"\n📈 Listening Intensity: {intensity:.2f}/1.0")
    
    # Recent deviation
    recent_tracks = tracks[-min(20, len(tracks)):]
    deviation = behavior.get_deviation_score(recent_tracks)
    if deviation > 0.3:
        print(f"⚠️  Deviation from baseline: {deviation:.0%} (behavior changed recently)")
    
    if savage_mode and deviation > 0.5:
        roast = RoastEngine.roast_event({
            "type": "deviation_high",
            "deviation": deviation
        })
        print(f"\n🔥 {roast}")
    
    # === BEHAVIORAL EVENTS ===
    events = behavior.detect_behavioral_events()
    
    if events:
        print_section("BEHAVIORAL EVENTS DETECTED", "🚨")
        
        # Group by type
        event_summary = {}
        for event in events:
            event_type = event["type"]
            event_summary[event_type] = event_summary.get(event_type, 0) + 1
        
        for event_type, count in event_summary.items():
            readable_type = event_type.replace("_", " ").title()
            print(f"\n  • {readable_type}: {count} occurrences")
        
        if savage_mode:
            print_section("ROAST TIME", "🔥")
            roasts = RoastEngine.roast_multiple_events(events, max_roasts=3)
            for roast in roasts:
                print(f"\n  💀 {roast}")
    
    # === LISTENING PATTERNS ===
    print_section("LISTENING PATTERNS", "📊")
    
    hours = habits.get_listening_hours()
    if "error" not in hours:
        peak = hours['most_active_hour']
        print(f"\n⏰ Peak Hour: {peak}:00")
        
        if savage_mode and (peak >= 22 or peak <= 3):
            roast = RoastEngine.roast_event({"type": "late_night_listener"})
            print(f"   🔥 {roast}")
    
    days = habits.get_day_of_week_pattern()
    if "error" not in days:
        print(f"📅 Most Active: {days['most_active_day']}")
        
        if savage_mode and days.get('is_weekend_listener'):
            roast = RoastEngine.roast_event({"type": "weekend_only"})
            print(f"   🔥 {roast}")
    
    # === TOP ARTISTS ===
    print_section("TOP ARTISTS", "⭐")
    
    top_artists = habits.get_top_artists(limit=3)
    for i, artist in enumerate(top_artists, 1):
        print(f"\n  {i}. {artist['artist']}")
        print(f"     {artist['play_count']} plays ({artist['percentage']}%)")
        
        if savage_mode and i == 1 and artist['percentage'] > 20:
            roast = RoastEngine.roast_event({
                "type": "artist_obsessed",
                "artist": artist['artist'],
                "percentage": artist['percentage']
            })
            print(f"     🔥 {roast}")
    
    # === REPEAT BEHAVIOR ===
    print_section("REPEAT BEHAVIOR", "🔁")
    
    repeats = habits.get_repeat_behavior()
    print(f"\n  Unique tracks: {repeats['total_unique_tracks']}")
    print(f"  Repeated tracks: {repeats['repeated_tracks']} ({repeats['repeat_percentage']}%)")
    print(f"  Diversity score: {repeats['diversity_score']}")
    
    if savage_mode:
        if repeats['repeat_percentage'] > 30:
            roast = RoastEngine.roast_event({
                "type": "high_replay_rate",
                "replay_pct": repeats['repeat_percentage']
            })
            print(f"\n  🔥 {roast}")
        
        # Most repeated song
        most_repeated = repeats.get('most_repeated', [])
        if most_repeated and most_repeated[0]['play_count'] >= 5:
            top_repeat = most_repeated[0]
            roast = RoastEngine.roast_event({
                "type": "song_addiction",
                "song": top_repeat['song'],
                "count": top_repeat['play_count']
            })
            print(f"  🔥 {roast}")
    
    # === CLOSING ===
    print("\n" + "=" * 60)
    
    if savage_mode:
        print(RoastEngine.closing_roast())
    else:
        print("Analysis complete! Run with --roast for savage commentary.")
    
    print("=" * 60 + "\n")


def interactive_mode(tracks):
    """
    Interactive mode - choose analysis style.
    
    Args:
        tracks: List of Track objects
    """
    print("\n🎵 SpotiMood Analysis - Interactive Mode")
    print("=" * 60)
    print(f"✅ Loaded {len(tracks)} tracks\n")
    
    print("Choose your analysis style:")
    print("  1. 🧠 Behavioral Analysis (technical)")
    print("  2. 💙 Friend Mode (supportive)")
    print("  3. 📊 Analyst Mode (objective)")
    print("  4. 🔥 Roast Mode (savage)")
    print("  5. Show all three narratives")
    
    choice = input("\nEnter 1-5 (or press Enter for behavioral): ").strip()
    
    mood = MoodAnalyzer(tracks)
    habits = HabitsAnalyzer(tracks)
    
    if choice == "1" or choice == "":
        behavioral_mode(tracks, savage_mode=False)
    
    elif choice == "2":
        narrator = Narrator(mood, habits, tone=ToneType.FRIEND)
        print("\n" + narrator.generate_full_report())
    
    elif choice == "3":
        narrator = Narrator(mood, habits, tone=ToneType.ANALYST)
        print("\n" + narrator.generate_full_report())
    
    elif choice == "4":
        narrator = Narrator(mood, habits, tone=ToneType.ROAST)
        print("\n" + narrator.generate_full_report())
    
    elif choice == "5":
        print("\n" + "🎵" * 30)
        print("SHOWING ALL PERSONALITY STYLES")
        print("🎵" * 30)
        
        for tone in [ToneType.FRIEND, ToneType.ANALYST, ToneType.ROAST]:
            narrator = Narrator(mood, habits, tone=tone)
            print("\n" + narrator.generate_full_report())
            if tone != ToneType.ROAST:
                input("\nPress Enter for next style...")
    
    else:
        print("\n❌ Invalid choice. Running behavioral analysis instead...")
        behavioral_mode(tracks, savage_mode=False)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Unified Spotify behavioral analysis & reporting"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode (choose analysis style)"
    )
    parser.add_argument(
        "--roast", "-r",
        action="store_true",
        help="Include roast mode commentary in behavioral analysis"
    )
    
    args = parser.parse_args()
    
    # Load data
    tracks = load_data()
    if not tracks:
        return
    
    # Run appropriate mode
    if args.interactive:
        interactive_mode(tracks)
    else:
        # Default behavioral mode
        if not args.roast:
            print("\n💡 Tip: Add --roast for savage mode or --interactive for menu")
            print("   Examples:")
            print("     python scripts/analyze.py --roast")
            print("     python scripts/analyze.py --interactive\n")
        
        behavioral_mode(tracks, savage_mode=args.roast)


if __name__ == "__main__":
    main()
