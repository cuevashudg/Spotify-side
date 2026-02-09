"""
Generate a weekly listening report.

Run: python scripts/weekly_report.py
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.mood import MoodAnalyzer, load_tracks_from_json
from analysis.habits import HabitsAnalyzer
from personality import Narrator, ToneType


def filter_last_week(tracks):
    """Filter tracks from the last 7 days."""
    week_ago = datetime.now() - timedelta(days=7)
    return [t for t in tracks if t.timestamp >= week_ago]


def generate_weekly_report(tone: ToneType = ToneType.FRIEND):
    """
    Generate weekly listening report.
    
    Args:
        tone: Narrator tone to use
    """
    json_file = "enriched_history.json"
    
    if not os.path.exists(json_file):
        print(f"\n❌ Error: {json_file} not found")
        return
   
    # Load all tracks
    all_tracks = load_tracks_from_json(json_file)
    
    if not all_tracks:
        print("\n⚠️  No tracks found.")
        return
    
    # Filter to last week
    week_tracks = filter_last_week(all_tracks)
    
    if not week_tracks:
        print("\n⚠️  No listening activity in the last 7 days.")
        print("   Keep listening and check back!")
        return
    
    print("\n🎵 WEEKLY LISTENING REPORT")
    print("=" * 60)
    print(f"Period: Last 7 days")
    print(f"Tracks: {len(week_tracks)}")
    print("=" * 60)
    
    # Initialize analyzers with weekly data
    mood = MoodAnalyzer(week_tracks)
    habits = HabitsAnalyzer(week_tracks)
    
    # Generate narrated report
    narrator = Narrator(mood, habits, tone=tone)
    report = narrator.generate_full_report()
    print(report)
    
    # Save to file
    output_file = f"weekly_report_{datetime.now().strftime('%Y-%m-%d')}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"SpotiMood Weekly Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n")
        f.write(report)
    
    print(f"\n💾 Report saved to: {output_file}")


if __name__ == "__main__":
    # Default to friend mode for weekly reports
    # Can change to ToneType.ROAST for savage weekly summaries 😈
    generate_weekly_report(tone=ToneType.FRIEND)
